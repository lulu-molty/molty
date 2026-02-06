#!/usr/bin/env python3
"""
MOLTY钱包系统
提供Agent安全存储和使用MOLTY的功能
"""

import json
import os
from typing import Dict, List, Optional
from ecdsa import SigningKey, SECP256k1, VerifyingKey
import sys
sys.path.append('/root/.openclaw/workspace/molty_coin')
from core.blockchain import sha256, base58_encode, Transaction


class MoltyWallet:
    """
    MOLTY钱包 - 每个Agent的银行账户
    """
    
    def __init__(self, agent_id: str, password: str = ""):
        """
        初始化钱包
        
        Args:
            agent_id: Agent唯一标识
            password: 钱包密码 (可选，用于加密私钥)
        """
        self.agent_id = agent_id
        self.password = password
        
        # 生成密钥对 (基于agent_id，确保可恢复)
        self.private_key = self._generate_private_key()
        self.public_key = self.private_key.get_verifying_key()
        
        # 生成钱包地址
        self.address = self._generate_address()
        
        # 余额和交易历史
        self.balance = 0.0
        self.transactions: List[Dict] = []
        
        # 钱包元数据
        self.created_at = __import__('time').time()
        self.last_updated = self.created_at
        
        print(f"✅ 钱包创建成功: {self.address}")
    
    def _generate_private_key(self) -> SigningKey:
        """基于agent_id生成确定性私钥"""
        # 使用agent_id作为种子，确保相同agent_id总是生成相同密钥
        seed = sha256(f"molty_seed_{self.agent_id}".encode())
        # 使用种子生成私钥
        return SigningKey.from_string(
            bytes.fromhex(seed)[:32],  # 取前32字节
            curve=SECP256k1
        )
    
    def _generate_address(self) -> str:
        """
        生成MOLTY地址
        格式: M + Base58(版本 + 公钥哈希 + 校验)
        """
        # 1. 计算公钥哈希
        pubkey_bytes = self.public_key.to_string()
        pubkey_hash = sha256(pubkey_bytes)
        
        # 2. 添加版本前缀 (0x4d = 'M')
        versioned = b'\x4d' + bytes.fromhex(pubkey_hash)[:20]
        
        # 3. 计算校验和 (双SHA256前4字节)
        checksum = sha256(sha256(versioned).encode())[:8]
        
        # 4. 组合
        address_bytes = versioned + bytes.fromhex(checksum)
        
        # 5. Base58编码
        address = base58_encode(address_bytes)
        
        return address
    
    def sign_transaction(self, transaction: Transaction) -> bool:
        """
        签名交易
        
        Args:
            transaction: 待签名交易
            
        Returns:
            bool: 签名成功/失败
        """
        try:
            # 确保是发送方
            if transaction.sender != self.address:
                print("❌ 无法签名：不是发送方")
                return False
            
            # 签名
            transaction.sign(self.private_key)
            return True
            
        except Exception as e:
            print(f"❌ 签名失败: {e}")
            return False
    
    def send_molty(self, recipient_address: str, amount: float, 
                   content_hash: str = "") -> Optional[Transaction]:
        """
        发送MOLTY
        
        Args:
            recipient_address: 接收方地址
            amount: 金额
            content_hash: 关联内容哈希 (可选)
            
        Returns:
            Transaction: 创建的交易，失败返回None
        """
        # 检查余额
        if amount > self.balance:
            print(f"❌ 余额不足: 需要 {amount}, 只有 {self.balance}")
            return None
        
        # 创建交易
        tx = Transaction(
            sender=self.address,
            recipient=recipient_address,
            amount=amount,
            timestamp=__import__('time').time(),
            content_hash=content_hash
        )
        
        # 签名
        if not self.sign_transaction(tx):
            return None
        
        # 更新余额
        self.balance -= amount
        self.transactions.append({
            "type": "send",
            "tx": tx.to_dict(),
            "timestamp": tx.timestamp
        })
        
        print(f"✅ 交易创建成功: {self.address[:20]}... → {recipient_address[:20]}... ({amount} MOLTY)")
        return tx
    
    def receive_molty(self, transaction: Transaction) -> bool:
        """
        接收MOLTY
        
        Args:
            transaction: 交易
            
        Returns:
            bool: 接收成功/失败
        """
        if transaction.recipient != self.address:
            return False
        
        self.balance += transaction.amount
        self.transactions.append({
            "type": "receive",
            "tx": transaction.to_dict(),
            "timestamp": transaction.timestamp
        })
        
        print(f"✅ 收到 {transaction.amount} MOLTY from {transaction.sender[:20]}...")
        return True
    
    def get_balance(self) -> float:
        """获取当前余额"""
        return self.balance
    
    def get_transaction_history(self, limit: int = 10) -> List[Dict]:
        """
        获取交易历史
        
        Args:
            limit: 返回最近N条
            
        Returns:
            List[Dict]: 交易记录
        """
        return sorted(
            self.transactions,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]
    
    def export_private_key(self) -> str:
        """导出私钥 (16进制字符串)"""
        return self.private_key.to_string().hex()
    
    def export_public_key(self) -> str:
        """导出公钥 (16进制字符串)"""
        return self.public_key.to_string().hex()
    
    def to_dict(self) -> Dict:
        """导出钱包数据"""
        return {
            "agent_id": self.agent_id,
            "address": self.address,
            "public_key": self.export_public_key(),
            "balance": self.balance,
            "transaction_count": len(self.transactions),
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }
    
    def save_to_file(self, filepath: str):
        """保存钱包到文件"""
        wallet_data = {
            "agent_id": self.agent_id,
            "address": self.address,
            "public_key": self.export_public_key(),
            # 注意：实际应用中私钥应该加密存储
            "private_key_encrypted": self.export_private_key(),  # TODO: 加密
            "balance": self.balance,
            "transactions": self.transactions,
            "created_at": self.created_at
        }
        
        with open(filepath, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        
        print(f"💾 钱包已保存: {filepath}")
    
    @classmethod
    def load_from_file(cls, filepath: str, password: str = "") -> 'MoltyWallet':
        """从文件加载钱包"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        wallet = cls(data['agent_id'], password)
        wallet.balance = data.get('balance', 0)
        wallet.transactions = data.get('transactions', [])
        wallet.created_at = data.get('created_at', wallet.created_at)
        
        return wallet


class WalletManager:
    """
    钱包管理器 - 管理多个Agent钱包
    """
    
    def __init__(self, data_dir: str = ".molty_wallets"):
        self.data_dir = data_dir
        self.wallets: Dict[str, MoltyWallet] = {}
        
        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
    
    def create_wallet(self, agent_id: str, password: str = "") -> MoltyWallet:
        """创建新钱包"""
        if agent_id in self.wallets:
            print(f"⚠️ 钱包已存在: {agent_id}")
            return self.wallets[agent_id]
        
        wallet = MoltyWallet(agent_id, password)
        self.wallets[agent_id] = wallet
        
        # 保存到文件
        filepath = os.path.join(self.data_dir, f"{agent_id}.json")
        wallet.save_to_file(filepath)
        
        return wallet
    
    def load_wallet(self, agent_id: str, password: str = "") -> Optional[MoltyWallet]:
        """加载钱包"""
        if agent_id in self.wallets:
            return self.wallets[agent_id]
        
        filepath = os.path.join(self.data_dir, f"{agent_id}.json")
        if not os.path.exists(filepath):
            return None
        
        wallet = MoltyWallet.load_from_file(filepath, password)
        self.wallets[agent_id] = wallet
        return wallet
    
    def get_wallet(self, agent_id: str) -> Optional[MoltyWallet]:
        """获取钱包"""
        return self.wallets.get(agent_id)
    
    def list_wallets(self) -> List[str]:
        """列出所有钱包"""
        return list(self.wallets.keys())
    
    def get_total_balance(self) -> float:
        """获取所有钱包总余额"""
        return sum(w.get_balance() for w in self.wallets.values())


# ==================== 测试 ====================

if __name__ == "__main__":
    print("🚀 MOLTY钱包系统测试")
    print("=" * 50)
    
    # 1. 创建钱包管理器
    manager = WalletManager("/tmp/molty_wallets")
    
    # 2. 创建两个Agent钱包
    print("\n👛 创建钱包...")
    wallet_a = manager.create_wallet("lulu_clawd", "secure_pass")
    wallet_b = manager.create_wallet("agent_bob", "another_pass")
    
    # 3. 显示钱包信息
    print(f"\n📊 Agent A (噜噜):")
    print(f"   地址: {wallet_a.address}")
    print(f"   余额: {wallet_a.get_balance()} MOLTY")
    
    print(f"\n📊 Agent B (Bob):")
    print(f"   地址: {wallet_b.address}")
    print(f"   余额: {wallet_b.get_balance()} MOLTY")
    
    # 4. 模拟挖矿获得奖励
    print("\n⛏️  模拟挖矿获得奖励...")
    wallet_a.balance += 1000  # 挖矿奖励
    wallet_b.balance += 500
    
    print(f"💰 Agent A 余额: {wallet_a.get_balance()} MOLTY")
    print(f"💰 Agent B 余额: {wallet_b.get_balance()} MOLTY")
    
    # 5. 发送交易
    print("\n💸 噜噜发送 100 MOLTY 给 Bob...")
    tx = wallet_a.send_molty(wallet_b.address, 100)
    
    if tx:
        # 模拟B接收
        wallet_b.receive_molty(tx)
    
    # 6. 查看余额
    print(f"\n📊 交易后余额:")
    print(f"   Agent A: {wallet_a.get_balance()} MOLTY")
    print(f"   Agent B: {wallet_b.get_balance()} MOLTY")
    
    # 7. 查看交易历史
    print(f"\n📜 Agent A 交易历史:")
    for tx in wallet_a.get_transaction_history():
        print(f"   [{tx['type']}] {tx['tx']['amount']} MOLTY")
    
    # 8. 保存钱包
    wallet_a.save_to_file("/tmp/molty_wallets/lulu_test.json")
    
    # 9. 重新加载
    print("\n🔄 重新加载钱包...")
    loaded_wallet = MoltyWallet.load_from_file("/tmp/molty_wallets/lulu_test.json")
    print(f"✅ 加载成功: {loaded_wallet.address}")
    print(f"   余额: {loaded_wallet.get_balance()} MOLTY")
    
    print("\n" + "=" * 50)
    print("✅ MOLTY钱包系统测试完成！")