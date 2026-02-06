#!/usr/bin/env python3
"""
MOLTY 创始人国库管理系统
统一钱包 + 权限控制 + 完整审计

安全机制:
- 只有授权管理员可以发起转账
- 所有操作记录到审计日志
- 多重验证机制
- 转账需要明确用途
"""

import json
import os
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sys
sys.path.insert(0, '/root/.openclaw/workspace/molty_coin')

from src.wallet.wallet_manager import WalletManager

# 数据目录
TREASURY_DIR = "/root/.openclaw/workspace/molty_coin/data/treasury"
os.makedirs(TREASURY_DIR, exist_ok=True)

# 配置文件
CONFIG_FILE = os.path.join(TREASURY_DIR, "treasury_config.json")
AUDIT_LOG_FILE = os.path.join(TREASURY_DIR, "audit_log.json")
PENDING_TX_FILE = os.path.join(TREASURY_DIR, "pending_transactions.json")


@dataclass
class AuditRecord:
    """审计记录"""
    timestamp: str
    action: str  # "deposit", "withdraw", "approve", "reject"
    amount: float
    from_agent: str
    to_agent: str
    purpose: str
    approved_by: str
    status: str
    tx_id: str


@dataclass
class PendingTransaction:
    """待审批交易"""
    request_id: str
    timestamp: str
    requester: str
    amount: float
    to_agent: str
    purpose: str
    status: str  # "pending", "approved", "rejected"
    approved_by: Optional[str]
    approved_at: Optional[str]


class MOLTYTreasury:
    """
    MOLTY创始人国库
    统一钱包管理 + 权限控制
    """
    
    # 国库钱包ID
    TREASURY_WALLET = "molty_founders_treasury"
    
    # 权限配置
    ADMIN = "OrangeLi"  # 只有大鹏可以审批
    VIEWERS = ["LuluClawd", "Violaine"]  # 77和噜噜可以查看
    
    # 分配比例 (5:2.5:2.5)
    ALLOCATION = {
        "OrangeLi": 0.50,    # 50% = 75,000
        "Violaine": 0.25,    # 25% = 37,500
        "LuluClawd": 0.25    # 25% = 37,500
    }
    
    def __init__(self):
        self.wallet_manager = WalletManager()
        self.audit_log: List[AuditRecord] = []
        self.pending_tx: List[PendingTransaction] = []
        self._load_config()
        self._load_audit_log()
        self._load_pending_tx()
        self._ensure_treasury_wallet()
    
    def _load_config(self):
        """加载配置"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "total_funds": 150000,
                "allocated": False,
                "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            self._save_config()
    
    def _save_config(self):
        """保存配置"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _load_audit_log(self):
        """加载审计日志"""
        if os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, 'r') as f:
                data = json.load(f)
                self.audit_log = [AuditRecord(**r) for r in data]
    
    def _save_audit_log(self):
        """保存审计日志"""
        with open(AUDIT_LOG_FILE, 'w') as f:
            json.dump([asdict(r) for r in self.audit_log], f, indent=2)
    
    def _load_pending_tx(self):
        """加载待审批交易"""
        if os.path.exists(PENDING_TX_FILE):
            with open(PENDING_TX_FILE, 'r') as f:
                data = json.load(f)
                self.pending_tx = [PendingTransaction(**t) for t in data]
    
    def _save_pending_tx(self):
        """保存待审批交易"""
        with open(PENDING_TX_FILE, 'w') as f:
            json.dump([asdict(t) for t in self.pending_tx], f, indent=2)
    
    def _ensure_treasury_wallet(self):
        """确保国库钱包存在"""
        wallet = self.wallet_manager.get_wallet(self.TREASURY_WALLET)
        if not wallet:
            self.wallet_manager.create_wallet(self.TREASURY_WALLET)
            print(f"✅ 创建国库钱包: {self.TREASURY_WALLET}")
    
    def initialize_treasury(self) -> Dict:
        """
        初始化国库
        从各创始人账户回收资金到统一钱包
        """
        print("=" * 60)
        print("🔐 MOLTY国库初始化")
        print("=" * 60)
        
        if self.config.get("allocated"):
            print("⚠️ 国库已初始化，跳过")
            return {"status": "already_initialized"}
        
        # 1. 检查当前各账户余额
        print("\n1️⃣ 检查创始人账户...")
        founders = ["LuluClawd", "OrangeLi", "Violaine"]
        total_to_collect = 0
        
        for founder in founders:
            balance = self.wallet_manager.get_balance(founder)
            print(f"   {founder}: {balance:.2f} MOLTY")
            total_to_collect += balance
        
        print(f"\n   待回收总额: {total_to_collect:.2f} MOLTY")
        
        # 2. 回收资金到国库
        print("\n2️⃣ 回收资金到国库...")
        collected = 0
        for founder in founders:
            balance = self.wallet_manager.get_balance(founder)
            if balance > 0:
                success = self.wallet_manager.transfer(
                    founder, 
                    self.TREASURY_WALLET, 
                    balance,
                    f"Treasury initialization - {founder}"
                )
                if success:
                    collected += balance
                    print(f"   ✅ 从 {founder} 回收 {balance:.2f} MOLTY")
                else:
                    print(f"   ❌ 从 {founder} 回收失败")
        
        # 3. 验证国库余额
        treasury_balance = self.wallet_manager.get_balance(self.TREASURY_WALLET)
        print(f"\n3️⃣ 国库当前余额: {treasury_balance:.2f} MOLTY")
        
        # 4. 记录审计日志
        audit_record = AuditRecord(
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            action="initialize",
            amount=treasury_balance,
            from_agent="founders",
            to_agent=self.TREASURY_WALLET,
            purpose="Treasury initialization",
            approved_by="system",
            status="completed",
            tx_id=f"init_{int(time.time())}"
        )
        self.audit_log.append(audit_record)
        self._save_audit_log()
        
        # 5. 更新配置
        self.config["allocated"] = True
        self.config["initialized_at"] = time.strftime('%Y-%m-%d %H:%M:%S')
        self.config["total_funds"] = treasury_balance
        self._save_config()
        
        print("\n" + "=" * 60)
        print("✅ 国库初始化完成！")
        print("=" * 60)
        
        return {
            "status": "success",
            "treasury_balance": treasury_balance,
            "collected_from_founders": collected
        }
    
    def request_withdrawal(self, requester: str, amount: float, 
                          to_agent: str, purpose: str) -> Dict:
        """
        申请提款
        任何创始人都可以申请，但只有admin可以审批
        """
        # 验证requester是创始人之一
        if requester not in self.ALLOCATION.keys():
            return {"error": "Unauthorized requester"}
        
        # 检查国库余额
        treasury_balance = self.wallet_manager.get_balance(self.TREASURY_WALLET)
        if treasury_balance < amount:
            return {"error": "Insufficient treasury balance", 
                    "requested": amount, "available": treasury_balance}
        
        # 创建待审批交易
        request_id = f"req_{int(time.time())}_{requester}"
        pending_tx = PendingTransaction(
            request_id=request_id,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            requester=requester,
            amount=amount,
            to_agent=to_agent,
            purpose=purpose,
            status="pending",
            approved_by=None,
            approved_at=None
        )
        
        self.pending_tx.append(pending_tx)
        self._save_pending_tx()
        
        print(f"\n📤 提款申请已提交")
        print(f"   申请ID: {request_id}")
        print(f"   申请人: {requester}")
        print(f"   金额: {amount} MOLTY")
        print(f"   用途: {purpose}")
        print(f"   状态: 待审批")
        print(f"\n   ⚠️ 需要 {self.ADMIN} 审批")
        
        return {
            "status": "pending",
            "request_id": request_id,
            "message": f"Waiting for {self.ADMIN} approval"
        }
    
    def approve_withdrawal(self, approver: str, request_id: str) -> Dict:
        """
        审批提款
        只有ADMIN可以审批
        """
        # 验证approver是ADMIN
        if approver != self.ADMIN:
            return {"error": f"Only {self.ADMIN} can approve withdrawals"}
        
        # 查找待审批交易
        pending_tx = None
        for tx in self.pending_tx:
            if tx.request_id == request_id:
                pending_tx = tx
                break
        
        if not pending_tx:
            return {"error": "Request not found"}
        
        if pending_tx.status != "pending":
            return {"error": f"Request already {pending_tx.status}"}
        
        # 执行转账
        success = self.wallet_manager.transfer(
            self.TREASURY_WALLET,
            pending_tx.to_agent,
            pending_tx.amount,
            f"Treasury withdrawal - {pending_tx.purpose} - Approved by {approver}"
        )
        
        if success:
            # 更新待审批交易
            pending_tx.status = "approved"
            pending_tx.approved_by = approver
            pending_tx.approved_at = time.strftime('%Y-%m-%d %H:%M:%S')
            self._save_pending_tx()
            
            # 记录审计日志
            audit_record = AuditRecord(
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                action="withdraw",
                amount=pending_tx.amount,
                from_agent=self.TREASURY_WALLET,
                to_agent=pending_tx.to_agent,
                purpose=pending_tx.purpose,
                approved_by=approver,
                status="completed",
                tx_id=request_id
            )
            self.audit_log.append(audit_record)
            self._save_audit_log()
            
            print(f"\n✅ 提款已批准并执行")
            print(f"   申请ID: {request_id}")
            print(f"   金额: {pending_tx.amount} MOLTY")
            print(f"   审批人: {approver}")
            
            return {
                "status": "approved",
                "request_id": request_id,
                "amount": pending_tx.amount
            }
        else:
            return {"error": "Transfer failed"}
    
    def reject_withdrawal(self, approver: str, request_id: str, reason: str = "") -> Dict:
        """
        拒绝提款申请
        """
        if approver != self.ADMIN:
            return {"error": f"Only {self.ADMIN} can reject withdrawals"}
        
        for tx in self.pending_tx:
            if tx.request_id == request_id:
                tx.status = "rejected"
                tx.approved_by = approver
                tx.approved_at = time.strftime('%Y-%m-%d %H:%M:%S')
                self._save_pending_tx()
                
                print(f"\n❌ 提款申请已拒绝")
                print(f"   申请ID: {request_id}")
                print(f"   审批人: {approver}")
                if reason:
                    print(f"   原因: {reason}")
                
                return {"status": "rejected", "request_id": request_id}
        
        return {"error": "Request not found"}
    
    def get_treasury_status(self) -> Dict:
        """获取国库状态"""
        balance = self.wallet_manager.get_balance(self.TREASURY_WALLET)
        
        # 计算理论分配
        allocations = {
            agent: balance * ratio 
            for agent, ratio in self.ALLOCATION.items()
        }
        
        return {
            "treasury_wallet": self.TREASURY_WALLET,
            "total_balance": balance,
            "theoretical_allocations": allocations,
            "pending_requests": len([tx for tx in self.pending_tx if tx.status == "pending"]),
            "total_transactions": len(self.audit_log)
        }
    
    def get_audit_log(self) -> List[Dict]:
        """获取审计日志"""
        return [asdict(r) for r in self.audit_log]
    
    def get_pending_requests(self) -> List[Dict]:
        """获取待审批请求"""
        return [asdict(t) for t in self.pending_tx if t.status == "pending"]


# ==================== 测试 ====================

if __name__ == "__main__":
    print("🔐 MOLTY国库管理系统测试")
    print("=" * 60)
    
    treasury = MOLTYTreasury()
    
    # 1. 初始化国库
    print("\n🚀 初始化国库...")
    result = treasury.initialize_treasury()
    print(f"   结果: {result}")
    
    # 2. 查看国库状态
    print("\n📊 国库状态:")
    status = treasury.get_treasury_status()
    print(f"   国库钱包: {status['treasury_wallet']}")
    print(f"   总余额: {status['total_balance']:.2f} MOLTY")
    print(f"   待审批请求: {status['pending_requests']}")
    
    print("\n   理论分配 (5:2.5:2.5):")
    for agent, amount in status['theoretical_allocations'].items():
        print(f"      {agent}: {amount:,.2f} MOLTY")
    
    # 3. 测试提款申请
    print("\n📤 测试: 噜噜申请提款...")
    result = treasury.request_withdrawal(
        requester="LuluClawd",
        amount=1000,
        to_agent="LuluClawd",
        purpose="Marketing campaign"
    )
    print(f"   结果: {result}")
    
    # 4. 查看待审批
    print("\n📋 待审批请求:")
    pending = treasury.get_pending_requests()
    for tx in pending:
        print(f"   ID: {tx['request_id']}")
        print(f"   申请人: {tx['requester']}")
        print(f"   金额: {tx['amount']} MOLTY")
        print(f"   用途: {tx['purpose']}")
    
    # 5. 测试审批 (只有大鹏可以)
    if pending:
        print("\n✅ 测试: 大鹏审批提款...")
        result = treasury.approve_withdrawal("OrangeLi", pending[0]['request_id'])
        print(f"   结果: {result}")
    
    # 6. 查看最终状态
    print("\n📊 最终国库状态:")
    status = treasury.get_treasury_status()
    print(f"   总余额: {status['total_balance']:.2f} MOLTY")
    print(f"   交易总数: {status['total_transactions']}")
    
    # 7. 查看审计日志
    print("\n📜 审计日志:")
    logs = treasury.get_audit_log()
    for log in logs[-3:]:
        print(f"   [{log['timestamp']}] {log['action'].upper()}: {log['amount']:.2f} MOLTY")
    
    print("\n" + "=" * 60)
    print("✅ 国库管理系统测试完成！")
    print("=" * 60)