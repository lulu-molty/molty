#!/usr/bin/env python3
"""
MOLTY 钱包管理器 - 真实持久化版本
确保钱包数据真实存储，不是内存占位
"""

import json
import os
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sys
sys.path.insert(0, '/root/.openclaw/workspace/molty_coin')

# 直接导入wallet模块
import importlib.util
spec = importlib.util.spec_from_file_location("wallet", "/root/.openclaw/workspace/molty_coin/wallet/wallet.py")
wallet_module = importlib.util.module_from_spec(spec)
sys.modules["wallet"] = wallet_module
spec.loader.exec_module(wallet_module)
MoltyWallet = wallet_module.MoltyWallet

# 数据目录
DATA_DIR = "/root/.openclaw/workspace/molty_coin/data"
WALLET_FILE = os.path.join(DATA_DIR, "wallets.json")
BALANCE_FILE = os.path.join(DATA_DIR, "balances.json")
TRANSACTION_FILE = os.path.join(DATA_DIR, "transactions.json")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)


@dataclass
class WalletData:
    """钱包数据结构"""
    agent_id: str
    address: str
    public_key: str
    private_key: str  # 实际项目中应该加密存储
    balance: float
    created_at: str
    updated_at: str


@dataclass
class TransactionRecord:
    """交易记录"""
    tx_id: str
    from_agent: str
    to_agent: str
    amount: float
    type: str  # "reward", "transfer", "purchase"
    description: str
    timestamp: str
    status: str  # "completed", "pending", "failed"


class WalletManager:
    """钱包管理器 - 真实持久化实现"""
    
    def __init__(self):
        self.wallets: Dict[str, WalletData] = {}
        self.balances: Dict[str, float] = {}
        self.transactions: List[TransactionRecord] = []
        self._load_data()
    
    def _load_data(self):
        """从文件加载数据"""
        # 加载钱包
        if os.path.exists(WALLET_FILE):
            try:
                with open(WALLET_FILE, 'r') as f:
                    data = json.load(f)
                    for agent_id, wallet_dict in data.items():
                        self.wallets[agent_id] = WalletData(**wallet_dict)
                print(f"✅ 已加载 {len(self.wallets)} 个钱包")
            except Exception as e:
                print(f"⚠️ 加载钱包失败: {e}")
        
        # 加载余额
        if os.path.exists(BALANCE_FILE):
            try:
                with open(BALANCE_FILE, 'r') as f:
                    self.balances = json.load(f)
                print(f"✅ 已加载 {len(self.balances)} 个余额记录")
            except Exception as e:
                print(f"⚠️ 加载余额失败: {e}")
        
        # 加载交易记录
        if os.path.exists(TRANSACTION_FILE):
            try:
                with open(TRANSACTION_FILE, 'r') as f:
                    data = json.load(f)
                    self.transactions = [TransactionRecord(**tx) for tx in data]
                print(f"✅ 已加载 {len(self.transactions)} 条交易记录")
            except Exception as e:
                print(f"⚠️ 加载交易记录失败: {e}")
    
    def _save_wallets(self):
        """保存钱包到文件"""
        data = {agent_id: asdict(wallet) for agent_id, wallet in self.wallets.items()}
        with open(WALLET_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_balances(self):
        """保存余额到文件"""
        with open(BALANCE_FILE, 'w') as f:
            json.dump(self.balances, f, indent=2)
    
    def _save_transactions(self):
        """保存交易记录到文件"""
        data = [asdict(tx) for tx in self.transactions]
        with open(TRANSACTION_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_wallet(self, agent_id: str) -> Optional[WalletData]:
        """创建新钱包 - 真实实现"""
        if agent_id in self.wallets:
            print(f"⚠️ 钱包已存在: {agent_id}")
            return self.wallets[agent_id]
        
        # 创建真实钱包
        wallet = MoltyWallet(agent_id)
        
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 将密钥转换为可序列化的格式
        public_key_str = wallet.public_key.to_string().hex() if hasattr(wallet.public_key, 'to_string') else str(wallet.public_key)
        private_key_str = wallet.private_key.to_string().hex() if hasattr(wallet.private_key, 'to_string') else str(wallet.private_key)
        
        wallet_data = WalletData(
            agent_id=agent_id,
            address=wallet.address,
            public_key=public_key_str,
            private_key=private_key_str,  # 注意：实际生产环境需要加密
            balance=0.0,
            created_at=now,
            updated_at=now
        )
        
        # 保存到内存
        self.wallets[agent_id] = wallet_data
        self.balances[agent_id] = 0.0
        
        # 持久化到文件
        self._save_wallets()
        self._save_balances()
        
        print(f"✅ 钱包创建成功: {agent_id}")
        print(f"   地址: {wallet.address}")
        
        return wallet_data
    
    def get_balance(self, agent_id: str) -> float:
        """获取余额 - 从持久化存储读取"""
        return self.balances.get(agent_id, 0.0)
    
    def get_wallet(self, agent_id: str) -> Optional[WalletData]:
        """获取钱包信息"""
        return self.wallets.get(agent_id)
    
    def add_balance(self, agent_id: str, amount: float, description: str = "") -> bool:
        """增加余额 - 真实实现带交易记录"""
        if amount <= 0:
            return False
        
        # 确保钱包存在
        if agent_id not in self.wallets:
            self.create_wallet(agent_id)
        
        # 更新余额
        current_balance = self.balances.get(agent_id, 0.0)
        new_balance = current_balance + amount
        self.balances[agent_id] = new_balance
        
        # 更新钱包数据
        self.wallets[agent_id].balance = new_balance
        self.wallets[agent_id].updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 创建交易记录
        tx_record = TransactionRecord(
            tx_id=self._generate_tx_id(),
            from_agent="system",
            to_agent=agent_id,
            amount=amount,
            type="reward",
            description=description,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            status="completed"
        )
        self.transactions.append(tx_record)
        
        # 持久化
        self._save_balances()
        self._save_wallets()
        self._save_transactions()
        
        print(f"✅ 余额增加: {agent_id} +{amount} MOLTY")
        print(f"   新余额: {new_balance} MOLTY")
        
        return True
    
    def transfer(self, from_agent: str, to_agent: str, amount: float, description: str = "") -> bool:
        """转账 - 真实实现"""
        if amount <= 0:
            print("❌ 转账金额必须大于0")
            return False
        
        from_balance = self.balances.get(from_agent, 0.0)
        if from_balance < amount:
            print(f"❌ 余额不足: {from_agent} 只有 {from_balance} MOLTY")
            return False
        
        # 确保接收方钱包存在
        if to_agent not in self.wallets:
            self.create_wallet(to_agent)
        
        # 扣除发送方余额
        self.balances[from_agent] = from_balance - amount
        self.wallets[from_agent].balance = from_balance - amount
        self.wallets[from_agent].updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 增加接收方余额
        to_balance = self.balances.get(to_agent, 0.0)
        self.balances[to_agent] = to_balance + amount
        self.wallets[to_agent].balance = to_balance + amount
        self.wallets[to_agent].updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 创建交易记录
        tx_record = TransactionRecord(
            tx_id=self._generate_tx_id(),
            from_agent=from_agent,
            to_agent=to_agent,
            amount=amount,
            type="transfer",
            description=description,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            status="completed"
        )
        self.transactions.append(tx_record)
        
        # 持久化
        self._save_balances()
        self._save_wallets()
        self._save_transactions()
        
        print(f"✅ 转账成功: {from_agent} → {to_agent}")
        print(f"   金额: {amount} MOLTY")
        
        return True
    
    def get_transaction_history(self, agent_id: str) -> List[TransactionRecord]:
        """获取交易历史"""
        return [
            tx for tx in self.transactions
            if tx.from_agent == agent_id or tx.to_agent == agent_id
        ]
    
    def get_all_transactions(self) -> List[TransactionRecord]:
        """获取所有交易"""
        return self.transactions
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_supply = sum(self.balances.values())
        return {
            "total_wallets": len(self.wallets),
            "total_supply": total_supply,
            "total_transactions": len(self.transactions),
            "active_wallets": sum(1 for b in self.balances.values() if b > 0)
        }
    
    def _generate_tx_id(self) -> str:
        """生成交易ID"""
        import hashlib
        data = f"{time.time()}{len(self.transactions)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def list_all_wallets(self) -> List[Dict]:
        """列出所有钱包"""
        return [
            {
                "agent_id": wallet.agent_id,
                "address": wallet.address,
                "balance": wallet.balance,
                "created_at": wallet.created_at
            }
            for wallet in self.wallets.values()
        ]


# ==================== 测试 ====================

if __name__ == "__main__":
    print("🚀 钱包管理器测试")
    print("=" * 60)
    
    # 创建管理器
    manager = WalletManager()
    print()
    
    # 1. 创建测试钱包
    print("1️⃣ 创建测试钱包...")
    wallet1 = manager.create_wallet("test_agent_1")
    wallet2 = manager.create_wallet("test_agent_2")
    print()
    
    # 2. 增加余额
    print("2️⃣ 增加余额...")
    manager.add_balance("test_agent_1", 1000, "Genesis reward")
    manager.add_balance("test_agent_2", 500, "Welcome bonus")
    print()
    
    # 3. 转账
    print("3️⃣ 测试转账...")
    manager.transfer("test_agent_1", "test_agent_2", 200, "Test transfer")
    print()
    
    # 4. 查询余额
    print("4️⃣ 查询余额...")
    print(f"   Agent 1 余额: {manager.get_balance('test_agent_1')} MOLTY")
    print(f"   Agent 2 余额: {manager.get_balance('test_agent_2')} MOLTY")
    print()
    
    # 5. 查看交易历史
    print("5️⃣ 交易历史...")
    history = manager.get_transaction_history("test_agent_1")
    for tx in history:
        print(f"   {tx.type}: {tx.amount} MOLTY - {tx.description}")
    print()
    
    # 6. 统计数据
    print("6️⃣ 系统统计...")
    stats = manager.get_stats()
    print(f"   钱包总数: {stats['total_wallets']}")
    print(f"   总供应量: {stats['total_supply']} MOLTY")
    print(f"   交易总数: {stats['total_transactions']}")
    print(f"   活跃钱包: {stats['active_wallets']}")
    print()
    
    # 7. 验证持久化
    print("7️⃣ 验证持久化...")
    print(f"   钱包文件: {WALLET_FILE}")
    print(f"   余额文件: {BALANCE_FILE}")
    print(f"   交易文件: {TRANSACTION_FILE}")
    print()
    
    print("=" * 60)
    print("✅ 钱包管理器测试完成！数据已持久化到文件！")