#!/usr/bin/env python3
"""
MOLTY 定时发放脚本
每月向dapeng钱包发放10,000 MOLTY
"""

import sqlite3
import json
import hashlib
import time
from datetime import datetime

DB_PATH = '/root/.openclaw/workspace/molty_coin/data/molty.db'
SECRETS_PATH = '/root/.openclaw/workspace/molty_coin/data/wallet_secrets.json'

def load_secrets():
    with open(SECRETS_PATH, 'r') as f:
        return json.load(f)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def transfer_molty(from_address, to_address, amount, tx_type='monthly_vesting'):
    """执行转账"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查余额
        cursor.execute("SELECT balance FROM wallets WHERE address = ?", (from_address,))
        from_balance = cursor.fetchone()
        
        if not from_balance or from_balance['balance'] < amount:
            return {'success': False, 'error': 'Insufficient balance'}
        
        # 执行转账
        cursor.execute("UPDATE wallets SET balance = balance - ? WHERE address = ?",
                      (amount, from_address))
        cursor.execute("UPDATE wallets SET balance = balance + ? WHERE address = ?",
                      (amount, to_address))
        
        # 记录交易
        tx_id = hashlib.sha256(f"{from_address}{to_address}{amount}{time.time()}".encode()).hexdigest()[:16]
        cursor.execute("""
            INSERT INTO transactions (tx_id, from_address, to_address, amount, type, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'confirmed', datetime('now'))
        """, (tx_id, from_address, to_address, amount, tx_type))
        
        conn.commit()
        
        # 获取新余额
        cursor.execute("SELECT balance FROM wallets WHERE address = ?", (to_address,))
        new_balance = cursor.fetchone()['balance']
        
        return {
            'success': True,
            'tx_id': tx_id,
            'amount': amount,
            'new_balance': new_balance
        }
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def monthly_vesting():
    """执行月度发放"""
    print("🔄 MOLTY Monthly Vesting")
    print("=" * 60)
    
    secrets = load_secrets()
    system_address = secrets['system_reserve']['address']
    dapeng_address = secrets['dapeng_orange']['address']
    
    print(f"\n📊 发放信息:")
    print(f"   From: {system_address}")
    print(f"   To: {dapeng_address}")
    print(f"   Amount: 10,000 MOLTY")
    
    # 执行转账
    result = transfer_molty(system_address, dapeng_address, 10000.0)
    
    if result['success']:
        print(f"\n✅ 发放成功!")
        print(f"   交易ID: {result['tx_id']}")
        print(f"   金额: {result['amount']} MOLTY")
        print(f"   dapeng新余额: {result['new_balance']} MOLTY")
        
        # 记录发放历史
        vesting_record = {
            'month': datetime.now().strftime('%Y-%m'),
            'tx_id': result['tx_id'],
            'amount': result['amount'],
            'new_balance': result['new_balance'],
            'timestamp': datetime.now().isoformat()
        }
        
        # 读取现有记录
        try:
            with open('/root/.openclaw/workspace/molty_coin/data/vesting_history.json', 'r') as f:
                history = json.load(f)
        except:
            history = {'payments': [], 'total_paid': 0}
        
        history['payments'].append(vesting_record)
        history['total_paid'] += result['amount']
        
        with open('/root/.openclaw/workspace/molty_coin/data/vesting_history.json', 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"\n📊 发放历史:")
        print(f"   已发放: {len(history['payments'])}/8 个月")
        print(f"   总计: {history['total_paid']} MOLTY")
        print(f"   剩余: {80000 - history['total_paid']} MOLTY")
        
        # 检查是否完成
        if len(history['payments']) >= 8:
            print(f"\n🎉 所有发放完成! 8个月共发放 80,000 MOLTY")
            return {'success': True, 'complete': True}
        
        return {'success': True, 'complete': False}
        
    else:
        print(f"\n❌ 发放失败: {result['error']}")
        return {'success': False, 'error': result['error']}

if __name__ == "__main__":
    result = monthly_vesting()
    
    print("\n" + "=" * 60)
    if result['success']:
        print("✅ 月度发放执行完成")
    else:
        print("❌ 月度发放执行失败")
    print("=" * 60)
