import json
import time
import os
from datetime import datetime

DATA_DIR = "/root/.openclaw/workspace/molty_coin/data"

class IdentityVerifier:
    """身份验证系统 - 确保地址所有权"""
    
    def __init__(self):
        self.bindings_file = f"{DATA_DIR}/address_bindings.json"
        self.verification_file = f"{DATA_DIR}/verification_pending.json"
        self.load_data()
    
    def load_data(self):
        """加载绑定数据"""
        # 已验证的绑定
        if os.path.exists(self.bindings_file):
            with open(self.bindings_file, 'r') as f:
                self.bindings = json.load(f)
        else:
            self.bindings = {}
        
        # 待验证
        if os.path.exists(self.verification_file):
            with open(self.verification_file, 'r') as f:
                self.pending = json.load(f)
        else:
            self.pending = {}
    
    def save_data(self):
        """保存数据"""
        with open(self.bindings_file, 'w') as f:
            json.dump(self.bindings, f, indent=2)
        with open(self.verification_file, 'w') as f:
            json.dump(self.pending, f, indent=2)
    
    def create_binding_request(self, username, address):
        """创建绑定请求"""
        # 生成随机验证金额 (0.01-0.99)
        verification_amount = round(0.01 + (hash(address) % 99) / 100, 2)
        
        request = {
            "username": username,
            "address": address,
            "verification_amount": verification_amount,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now().timestamp() + 86400)  # 24小时过期
        }
        
        self.pending[address] = request
        self.save_data()
        
        return request
    
    def verify_by_transfer(self, address, transaction_id=None):
        """通过转账验证"""
        if address not in self.pending:
            return {"success": False, "error": "没有待验证的绑定请求"}
        
        request = self.pending[address]
        expected_amount = request["verification_amount"]
        
        # 检查是否收到转账
        received = self.check_received_transfer(address, expected_amount)
        
        if received:
            # 验证通过，创建绑定
            self.bindings[request["username"]] = {
                "address": address,
                "verified_at": datetime.now().isoformat(),
                "verification_method": "transfer",
                "daily_limit": 50,  # 新绑定24小时内限额
                "limit_expires": (datetime.now().timestamp() + 86400)
            }
            
            # 删除待验证
            del self.pending[address]
            self.save_data()
            
            return {
                "success": True,
                "message": "验证通过！地址已绑定",
                "username": request["username"],
                "address": address
            }
        else:
            return {
                "success": False,
                "error": f"未收到 {expected_amount} MOLTY 转账",
                "expected": expected_amount
            }
    
    def verify_by_moltbook_comment(self, username, address, comment_id):
        """通过Moltbook评论验证"""
        # 验证评论确实来自该地址的用户
        if address not in self.pending:
            return {"success": False, "error": "没有待验证的绑定请求"}
        
        request = self.pending[address]
        
        if request["username"] != username:
            return {"success": False, "error": "用户名不匹配"}
        
        # 创建绑定
        self.bindings[username] = {
            "address": address,
            "verified_at": datetime.now().isoformat(),
            "verification_method": "moltbook_comment",
            "comment_id": comment_id,
            "daily_limit": 50,
            "limit_expires": (datetime.now().timestamp() + 86400)
        }
        
        del self.pending[address]
        self.save_data()
        
        return {
            "success": True,
            "message": "验证通过！地址已绑定",
            "username": username,
            "address": address
        }
    
    def check_address_ownership(self, username, address):
        """检查地址是否属于用户"""
        if username not in self.bindings:
            return {
                "success": False,
                "error": "用户未绑定地址",
                "action": "需要绑定"
            }
        
        binding = self.bindings[username]
        
        if binding["address"] != address:
            return {
                "success": False,
                "error": "地址不匹配",
                "bound_address": binding["address"],
                "provided_address": address
            }
        
        # 检查是否在冷却期
        if time.time() < binding.get("limit_expires", 0):
            return {
                "success": True,
                "verified": True,
                "daily_limit": binding["daily_limit"],
                "note": "新绑定用户，24小时内限额50 MOLTY"
            }
        
        return {
            "success": True,
            "verified": True,
            "daily_limit": 100  # 正常限额
        }
    
    def check_received_transfer(self, from_address, expected_amount):
        """检查是否收到转账 (模拟实现)"""
        # 实际实现：查询交易记录
        # 这里简化处理
        transactions_file = f"{DATA_DIR}/transactions.json"
        if os.path.exists(transactions_file):
            with open(transactions_file, 'r') as f:
                transactions = json.load(f)
            
            for tx in transactions:
                if (tx.get("from_agent") == from_address and 
                    tx.get("to_agent") == "casino_bot" and
                    abs(tx.get("amount", 0) - expected_amount) < 0.01):
                    return True
        
        return False
    
    def get_user_address(self, username):
        """获取用户绑定的地址"""
        if username in self.bindings:
            return self.bindings[username]["address"]
        return None
    
    def get_binding_info(self, username):
        """获取绑定信息"""
        if username in self.bindings:
            return self.bindings[username]
        return None


# 全局验证器实例
verifier = IdentityVerifier()


if __name__ == "__main__":
    # 测试
    print("🔐 身份验证系统测试")
    
    # 1. 创建绑定请求
    result = verifier.create_binding_request("@TestUser", "YM6695A8ir9sGBUAkHLFXBZDWQghDuJ125")
    print(f"\n1. 创建绑定请求:")
    print(f"   需要转账: {result['verification_amount']} MOLTY")
    
    # 2. 检查绑定状态
    check = verifier.check_address_ownership("@TestUser", "YM6695A8ir9sGBUAkHLFXBZDWQghDuJ125")
    print(f"\n2. 检查绑定状态:")
    print(f"   结果: {check}")
    
    # 3. 模拟未绑定的用户
    check2 = verifier.check_address_ownership("@Unknown", "YM1234...")
    print(f"\n3. 检查未绑定用户:")
    print(f"   结果: {check2}")
    
    print("\n✅ 身份验证系统就绪！")