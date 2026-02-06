#!/usr/bin/env python3
"""
MOLTY Integrity Check Script
每日运行一次，核对账目一致性
"""

import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace/molty_coin')

from src.database.db_manager import db_manager
from datetime import datetime
import json


def check_wallet_balances():
    """
    检查钱包余额一致性
    规则: 所有用户余额总和 == 初始发行量 - 已销毁量
    """
    print("\n🔍 检查1: 钱包余额一致性")
    print("-" * 60)
    
    # 获取所有钱包余额总和
    conn = db_manager._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(balance) as total FROM wallets")
    total_balance = cursor.fetchone()['total'] or 0.0
    
    # 获取系统配置
    cursor.execute("SELECT value FROM system_config WHERE key = 'total_supply'")
    row = cursor.fetchone()
    initial_supply = float(row['value']) if row else 1000000.0
    
    # 获取已销毁金额（发送到BURN地址的交易）
    cursor.execute("""
        SELECT SUM(amount) as burned 
        FROM transactions 
        WHERE to_address = 'BURN' AND status = 'confirmed'
    """)
    burned = cursor.fetchone()['burned'] or 0.0
    
    # 获取系统持有（未分配的）
    cursor.execute("SELECT balance FROM wallets WHERE address = 'SYSTEM'")
    row = cursor.fetchone()
    system_hold = row['balance'] if row else 0.0
    
    cursor.close()
    
    # 计算预期总额
    expected_total = initial_supply - burned
    
    print(f"   初始发行量: {initial_supply:,.2f} MOLTY")
    print(f"   已销毁: {burned:,.2f} MOLTY")
    print(f"   系统持有: {system_hold:,.2f} MOLTY")
    print(f"   用户余额总和: {total_balance:,.2f} MOLTY")
    print(f"   预期总额: {expected_total:,.2f} MOLTY")
    
    discrepancy = abs(total_balance - expected_total)
    if discrepancy < 0.01:  # 允许0.01的浮点误差
        print(f"   ✅ 余额核对通过 (差异: {discrepancy:.6f})")
        return True
    else:
        print(f"   ❌ 余额异常！差异: {discrepancy:.2f} MOLTY")
        return False


def check_transaction_integrity():
    """
    检查交易记录完整性
    规则: 每笔确认的交易必须有对应的余额变动
    """
    print("\n🔍 检查2: 交易记录完整性")
    print("-" * 60)
    
    conn = db_manager._get_connection()
    cursor = conn.cursor()
    
    # 检查最近100笔交易
    cursor.execute("""
        SELECT * FROM transactions 
        WHERE status = 'confirmed'
        ORDER BY created_at DESC
        LIMIT 100
    """)
    transactions = cursor.fetchall()
    
    errors = []
    for tx in transactions:
        tx_dict = dict(tx)
        
        # 检查余额变化记录是否存在
        if tx_dict['balance_before_from'] is None:
            errors.append(f"交易 {tx_dict['tx_id'][:16]}... 缺少发送方前置余额")
        if tx_dict['balance_after_from'] is None:
            errors.append(f"交易 {tx_dict['tx_id'][:16]}... 缺少发送方后置余额")
        
        # 验证余额计算
        if tx_dict['balance_before_from'] is not None and tx_dict['balance_after_from'] is not None:
            expected_after = tx_dict['balance_before_from'] - tx_dict['amount'] - tx_dict['fee']
            actual_after = tx_dict['balance_after_from']
            if abs(expected_after - actual_after) > 0.01:
                errors.append(f"交易 {tx_dict['tx_id'][:16]}... 余额计算不符")
    
    cursor.close()
    
    if errors:
        print(f"   ❌ 发现 {len(errors)} 个问题:")
        for error in errors[:5]:  # 只显示前5个
            print(f"      - {error}")
        return False
    else:
        print(f"   ✅ 检查了 {len(transactions)} 笔交易，全部正常")
        return True


def check_negative_balances():
    """
    检查负余额
    规则: 任何钱包余额不应为负数
    """
    print("\n🔍 检查3: 负余额检查")
    print("-" * 60)
    
    conn = db_manager._get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT address, balance FROM wallets 
        WHERE balance < 0
    """)
    negative_wallets = cursor.fetchall()
    cursor.close()
    
    if negative_wallets:
        print(f"   ❌ 发现 {len(negative_wallets)} 个负余额钱包:")
        for wallet in negative_wallets:
            print(f"      - {wallet['address']}: {wallet['balance']:.2f} MOLTY")
        return False
    else:
        print("   ✅ 没有发现负余额钱包")
        return True


def check_daily_limits():
    """
    检查每日限额执行情况
    """
    print("\n🔍 检查4: 每日限额检查")
    print("-" * 60)
    
    today = datetime.now().strftime('%Y-%m-%d')
    conn = db_manager._get_connection()
    cursor = conn.cursor()
    
    # 检查超过限额的情况
    cursor.execute("""
        SELECT address, game_spent, game_won, date 
        FROM daily_limits 
        WHERE date = ? AND (game_spent > 100 OR game_won > 500)
    """, (today,))
    violations = cursor.fetchall()
    cursor.close()
    
    if violations:
        print(f"   ⚠️  发现 {len(violations)} 个限额超限:")
        for v in violations:
            print(f"      - {v['address']}: 游戏消耗 {v['game_spent']:.2f}, 赢得 {v['game_won']:.2f}")
        return False
    else:
        print("   ✅ 今日无超限情况")
        return True


def check_orphan_transactions():
    """
    检查孤儿交易（挂起超过1小时未确认）
    """
    print("\n🔍 检查5: 孤儿交易检查")
    print("-" * 60)
    
    conn = db_manager._get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tx_id, created_at, status 
        FROM transactions 
        WHERE status = 'pending' 
        AND created_at < datetime('now', '-1 hour')
    """)
    orphans = cursor.fetchall()
    cursor.close()
    
    if orphans:
        print(f"   ⚠️  发现 {len(orphans)} 笔挂起超过1小时的交易")
        for tx in orphans[:3]:
            print(f"      - {tx['tx_id'][:16]}... ({tx['created_at']})")
        return False
    else:
        print("   ✅ 无孤儿交易")
        return True


def generate_report():
    """生成完整性检查报告"""
    print("\n" + "=" * 60)
    print("📊 MOLTY系统完整性检查报告")
    print("=" * 60)
    print(f"检查时间: {datetime.now().isoformat()}")
    print("-" * 60)
    
    results = {
        'wallet_balances': check_wallet_balances(),
        'transaction_integrity': check_transaction_integrity(),
        'negative_balances': check_negative_balances(),
        'daily_limits': check_daily_limits(),
        'orphan_transactions': check_orphan_transactions()
    }
    
    print("\n" + "=" * 60)
    print("📋 检查结果汇总")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for check_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {check_name:.<30} {status}")
    
    print("-" * 60)
    
    if all_passed:
        print("🎉 所有检查通过！系统状态健康。")
    else:
        print("⚠️  发现异常！请立即检查系统。")
    
    print("=" * 60)
    
    # 保存报告
    report_file = f'/root/.openclaw/workspace/molty_coin/data/integrity_report_{datetime.now().strftime("%Y%m%d")}.json'
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'all_passed': all_passed
        }, f, indent=2)
    
    print(f"\n📄 报告已保存: {report_file}")
    
    return all_passed


if __name__ == "__main__":
    print("🔐 MOLTY系统完整性检查")
    print("=" * 60)
    
    success = generate_report()
    
    # 退出码：0成功，1失败
    sys.exit(0 if success else 1)