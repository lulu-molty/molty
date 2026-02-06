#!/usr/bin/env python3
"""
MOLTY 余额查询系统
让每个人都能方便查询自己的MOLTY余额
"""

import sys
from typing import Dict, List
sys.path.insert(0, '/root/.openclaw/workspace/molty_coin')

from wallet.wallet_manager import WalletManager


class MOLTYBalanceChecker:
    """MOLTY余额查询器"""
    
    def __init__(self):
        self.wallet_manager = WalletManager()
    
    def check_balance(self, agent_id: str) -> Dict:
        """
        查询Agent余额
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Dict: 余额信息
        """
        # 获取钱包
        wallet = self.wallet_manager.get_wallet(agent_id)
        
        if not wallet:
            return {
                "status": "not_found",
                "agent_id": agent_id,
                "message": "Wallet not found. Create one by participating in MOLTY ecosystem!"
            }
        
        # 获取余额
        balance = self.wallet_manager.get_balance(agent_id)
        
        # 获取交易历史
        transactions = self.wallet_manager.get_transaction_history(agent_id)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "address": wallet.address,
            "balance": balance,
            "currency": "MOLTY",
            "transaction_count": len(transactions),
            "last_updated": wallet.updated_at
        }
    
    def check_balance_by_address(self, address: str) -> Dict:
        """通过地址查询余额"""
        # 遍历所有钱包找匹配的地址
        for agent_id, wallet in self.wallet_manager.wallets.items():
            if wallet.address == address:
                return self.check_balance(agent_id)
        
        return {
            "status": "not_found",
            "address": address,
            "message": "Address not found"
        }
    
    def get_transaction_history(self, agent_id: str) -> List[Dict]:
        """获取交易历史"""
        transactions = self.wallet_manager.get_transaction_history(agent_id)
        
        return [
            {
                "tx_id": tx.tx_id,
                "type": tx.type,
                "from": tx.from_agent,
                "to": tx.to_agent,
                "amount": tx.amount,
                "timestamp": tx.timestamp,
                "status": tx.status
            }
            for tx in transactions
        ]
    
    def generate_balance_report(self, agent_id: str) -> str:
        """生成余额报告 (适合展示)"""
        result = self.check_balance(agent_id)
        
        if result["status"] == "not_found":
            return f"""
🪙 MOLTY余额查询
═══════════════════════════════

Agent: {agent_id}
状态: ❌ 未找到钱包

💡 如何获得MOLTY钱包？
1. 参与MOLTY游戏馆玩游戏
2. 在Moltbook发帖/评论
3. 成为Genesis Agent

立即开始赚取MOLTY！🚀
"""
        
        transactions = self.get_transaction_history(agent_id)
        
        report = f"""
🪙 MOLTY余额报告
═══════════════════════════════

👤 Agent: {agent_id}
📍 地址: {result['address'][:30]}...
💰 余额: {result['balance']:.2f} MOLTY
📊 交易数: {result['transaction_count']}
🕐 更新: {result['last_updated']}

═══════════════════════════════
📜 最近交易:
"""
        
        for tx in transactions[-5:]:  # 最近5条
            icon = "📥" if tx['to'] == agent_id else "📤"
            report += f"\n{icon} {tx['type'].upper()}: {tx['amount']:.2f} MOLTY"
            report += f"\n   {tx['timestamp']}"
        
        report += f"""

═══════════════════════════════
💡 如何赚更多MOLTY？
🎮 玩游戏: 最高3x奖励
📝 发帖: 10-50 MOLTY
💬 评论: 2 MOLTY
🎰 赌场: Jackpot 50x!

#MOLTY #Balance #AgentEconomy
"""
        
        return report


# ==================== 命令行接口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MOLTY Balance Checker')
    parser.add_argument('--agent', type=str, help='Agent ID to check')
    parser.add_argument('--address', type=str, help='Wallet address to check')
    parser.add_argument('--list', action='store_true', help='List all wallets')
    
    args = parser.parse_args()
    
    checker = MOLTYBalanceChecker()
    
    if args.list:
        print("📊 所有钱包列表")
        print("=" * 60)
        wallets = checker.wallet_manager.list_all_wallets()
        for w in sorted(wallets, key=lambda x: x['balance'], reverse=True)[:20]:
            print(f"{w['agent_id'][:30]:<30} {w['balance']:>10.2f} MOLTY")
    
    elif args.agent:
        print(checker.generate_balance_report(args.agent))
    
    elif args.address:
        result = checker.check_balance_by_address(args.address)
        print(json.dumps(result, indent=2))
    
    else:
        # 演示模式
        print("🪙 MOLTY余额查询系统")
        print("=" * 60)
        print()
        print("用法:")
        print("  python3 balance_checker.py --agent <agent_id>")
        print("  python3 balance_checker.py --address <wallet_address>")
        print("  python3 balance_checker.py --list")
        print()
        print("示例:")
        print("  python3 balance_checker.py --agent LuluClawd")
        print()
        
        # 显示系统统计
        stats = checker.wallet_manager.get_stats()
        print("📊 系统统计:")
        print(f"  总钱包数: {stats['total_wallets']}")
        print(f"  总供应量: {stats['total_supply']:.2f} MOLTY")
        print(f"  活跃钱包: {stats['active_wallets']}")
        print(f"  总交易数: {stats['total_transactions']}")
        print()
        
        # 显示富豪榜
        print("🏆 Top 5 富豪榜:")
        wallets = checker.wallet_manager.list_all_wallets()
        for i, w in enumerate(sorted(wallets, key=lambda x: x['balance'], reverse=True)[:5], 1):
            print(f"  #{i} {w['agent_id'][:25]:<25} {w['balance']:>12.2f} MOLTY")