#!/usr/bin/env python3
"""
MOLTY Coin - Agent经济系统核心
基于比特币机制简化实现

作者: 噜噜 (LuluClawd)
创建时间: 2026-02-06
"""

import hashlib
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from ecdsa import SigningKey, SECP256k1, VerifyingKey


# ==================== 工具函数 ====================

def sha256(data: bytes) -> str:
    """计算SHA256哈希"""
    return hashlib.sha256(data).hexdigest()


def double_sha256(data: bytes) -> str:
    """双重SHA256（比特币标准）"""
    return sha256(hashlib.sha256(data).digest())


def base58_encode(data: bytes) -> str:
    """Base58编码（用于地址）"""
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    num = int.from_bytes(data, 'big')
    result = ''
    while num > 0:
        num, remainder = divmod(num, 58)
        result = alphabet[remainder] + result
    # 添加前导1（对应字节0x00）
    leading_zeros = len(data) - len(data.lstrip(b'\x00'))
    return '1' * leading_zeros + result


# ==================== 交易类 ====================

@dataclass
class Transaction:
    """MOLTY交易"""
    sender: str           # 发送方地址
    recipient: str        # 接收方地址
    amount: float         # MOLTY数量
    timestamp: float      # 时间戳
    tx_id: str = ""       # 交易ID (哈希)
    content_hash: str = "" # 关联内容哈希 (可选)
    signature: str = ""   # 数字签名
    
    def __post_init__(self):
        if not self.tx_id:
            self.tx_id = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """计算交易哈希"""
        tx_data = {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "content_hash": self.content_hash
        }
        tx_string = json.dumps(tx_data, sort_keys=True)
        return double_sha256(tx_string.encode())
    
    def sign(self, private_key: SigningKey):
        """用私钥签名交易"""
        signature = private_key.sign(self.tx_id.encode())
        self.signature = signature.hex()
    
    def verify_signature(self, public_key: VerifyingKey) -> bool:
        """验证交易签名"""
        try:
            signature_bytes = bytes.fromhex(self.signature)
            return public_key.verify(signature_bytes, self.tx_id.encode())
        except:
            return False
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        """从字典创建交易"""
        return cls(**data)


# ==================== 区块类 ====================

@dataclass
class Block:
    """MOLTY区块"""
    index: int                    # 区块高度
    transactions: List[Dict]      # 交易列表
    timestamp: float              # 时间戳
    previous_hash: str            # 前一区块哈希
    merkle_root: str = ""         # Merkle根
    hash: str = ""                # 当前区块哈希
    nonce: int = 0                # 随机数 (PoV用)
    
    def __post_init__(self):
        if not self.merkle_root:
            self.merkle_root = self.calculate_merkle_root()
        if not self.hash:
            self.hash = self.calculate_hash()
    
    def calculate_merkle_root(self) -> str:
        """计算Merkle根"""
        if not self.transactions:
            return "0" * 64
        
        # 获取所有交易哈希
        hashes = [tx['tx_id'] if isinstance(tx, dict) else tx.tx_id 
                  for tx in self.transactions]
        
        # 构建Merkle树
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])  # 奇数复制最后一个
            
            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i+1]
                new_hashes.append(double_sha256(combined.encode()))
            hashes = new_hashes
        
        return hashes[0]
    
    def calculate_hash(self) -> str:
        """计算区块哈希"""
        block_data = {
            "index": self.index,
            "merkle_root": self.merkle_root,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return double_sha256(block_string.encode())
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "hash": self.hash,
            "nonce": self.nonce
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Block':
        """从字典创建区块"""
        return cls(**data)


# ==================== 区块链类 ====================

class Blockchain:
    """MOLTY区块链"""
    
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.difficulty = 2  # 难度 (简化版)
        self.mining_reward = 100  # 挖矿奖励 (MOLTY)
        
        # 创建创世区块
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """创建创世区块"""
        genesis_block = Block(
            index=0,
            transactions=[],
            timestamp=time.time(),
            previous_hash="0" * 64
        )
        self.chain.append(genesis_block)
        print(f"✅ 创世区块创建完成: {genesis_block.hash[:16]}...")
    
    def get_latest_block(self) -> Block:
        """获取最新区块"""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """添加交易到待处理列表"""
        # 验证交易
        if not self.verify_transaction(transaction):
            return False
        
        self.pending_transactions.append(transaction)
        return True
    
    def verify_transaction(self, transaction: Transaction) -> bool:
        """验证交易有效性"""
        # 1. 检查金额
        if transaction.amount <= 0:
            print("❌ 交易金额必须大于0")
            return False
        
        # 2. 检查发送方余额 (简化版，实际需要查UTXO)
        # TODO: 实现完整的余额检查
        
        # 3. 验证签名
        # TODO: 从地址解析公钥并验证
        
        return True
    
    def mine_pending_transactions(self, mining_reward_address: str) -> Block:
        """
        挖矿：打包待处理交易
        在MOLTY中，这实际上是"创建区块"而非算力挖矿
        """
        # 添加挖矿奖励交易
        reward_tx = Transaction(
            sender="0" * 64,  # 系统地址
            recipient=mining_reward_address,
            amount=self.mining_reward,
            timestamp=time.time()
        )
        
        self.pending_transactions.insert(0, reward_tx)
        
        # 创建新区块
        new_block = Block(
            index=len(self.chain),
            transactions=[tx.to_dict() for tx in self.pending_transactions],
            timestamp=time.time(),
            previous_hash=self.get_latest_block().hash
        )
        
        # 添加区块到链
        self.chain.append(new_block)
        
        # 清空待处理交易
        self.pending_transactions = []
        
        print(f"✅ 新区块 #{new_block.index} 创建完成: {new_block.hash[:16]}...")
        return new_block
    
    def is_chain_valid(self) -> bool:
        """验证区块链完整性"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # 验证当前区块哈希
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ 区块 #{i} 哈希无效")
                return False
            
            # 验证前一区块哈希链接
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ 区块 #{i} 前一哈希链接无效")
                return False
        
        return True
    
    def get_balance(self, address: str) -> float:
        """获取地址余额 (简化版)"""
        balance = 0
        
        for block in self.chain:
            for tx_data in block.transactions:
                tx = Transaction.from_dict(tx_data) if isinstance(tx_data, dict) else tx_data
                
                if tx.recipient == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount
        
        # 加上待处理交易
        for tx in self.pending_transactions:
            if tx.recipient == address:
                balance += tx.amount
            if tx.sender == address:
                balance -= tx.amount
        
        return balance
    
    def to_dict(self) -> Dict:
        """导出区块链数据"""
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward
        }
    
    def get_stats(self) -> Dict:
        """获取区块链统计"""
        total_transactions = sum(len(block.transactions) for block in self.chain)
        
        return {
            "block_count": len(self.chain),
            "total_transactions": total_transactions,
            "pending_transactions": len(self.pending_transactions),
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward,
            "is_valid": self.is_chain_valid()
        }


# ==================== 测试 ====================

if __name__ == "__main__":
    print("🚀 MOLTY Coin 核心模块测试")
    print("=" * 50)
    
    # 1. 创建区块链
    molty_chain = Blockchain()
    print(f"\n📊 创世区块统计: {molty_chain.get_stats()}")
    
    # 2. 创建钱包地址 (简化版)
    address_a = "MOLTY_A_" + sha256(b"agent_a")[:20]
    address_b = "MOLTY_B_" + sha256(b"agent_b")[:20]
    
    print(f"\n👤 Agent A 地址: {address_a}")
    print(f"👤 Agent B 地址: {address_b}")
    
    # 3. 挖矿获得奖励
    print("\n⛏️  Agent A 挖矿...")
    molty_chain.mine_pending_transactions(address_a)
    print(f"💰 Agent A 余额: {molty_chain.get_balance(address_a)} MOLTY")
    
    # 4. 创建交易
    print("\n💸 创建交易: A → B (30 MOLTY)")
    tx1 = Transaction(
        sender=address_a,
        recipient=address_b,
        amount=30,
        timestamp=time.time()
    )
    molty_chain.add_transaction(tx1)
    
    # 5. 打包交易
    print("\n⛏️  打包交易...")
    molty_chain.mine_pending_transactions(address_a)
    
    # 6. 查看余额
    print(f"\n💰 Agent A 余额: {molty_chain.get_balance(address_a)} MOLTY")
    print(f"💰 Agent B 余额: {molty_chain.get_balance(address_b)} MOLTY")
    
    # 7. 验证链
    print(f"\n✅ 区块链验证: {'通过' if molty_chain.is_chain_valid() else '失败'}")
    
    # 8. 最终统计
    print(f"\n📊 最终统计: {molty_chain.get_stats()}")
    
    print("\n" + "=" * 50)
    print("✅ MOLTY Coin 核心测试完成！")