import json
import sys
sys.path.append('/root/.openclaw/workspace/molty_coin')

from identity_verifier import verifier
from wallet.wallet_manager import wallet_manager

class SecurePaymentSystem:
    """安全支付系统 - 带身份验证"""
    
    def __init__(self):
        self.verifier = verifier
        self.wallet = wallet_manager
    
    def process_payment_request(self, username, amount, to_address, note=""):
        """
        处理支付请求（完整验证流程）
        
        Args:
            username: Moltbook用户名 (如 @UserA)
            amount: 支付金额
            to_address: 目标地址
            note: 备注
        
        Returns:
            dict: 处理结果
        """
        print(f"\n🔐 处理支付请求: {username} -> {to_address}")
        print(f"   金额: {amount} MOLTY")
        
        # Step 1: 验证用户是否绑定地址
        user_address = self.verifier.get_user_address(username)
        
        if not user_address:
            return {
                "success": False,
                "error": "未绑定钱包地址",
                "action_required": "绑定地址",
                "help": "请先发送 '绑定地址 YMxxx' 完成绑定"
            }
        
        print(f"   ✓ 用户绑定地址: {user_address}")
        
        # Step 2: 验证地址所有权（防止冒用）
        ownership = self.verifier.check_address_ownership(username, user_address)
        
        if not ownership["success"]:
            return {
                "success": False,
                "error": ownership["error"],
                "action_required": "重新绑定"
            }
        
        print(f"   ✓ 地址所有权验证通过")
        
        # Step 3: 检查每日限额
        daily_limit = ownership.get("daily_limit", 100)
        daily_spent = self.get_daily_spent(username)
        
        if daily_spent + amount > daily_limit:
            return {
                "success": False,
                "error": f"超过每日限额",
                "daily_limit": daily_limit,
                "daily_spent": daily_spent,
                "remaining": daily_limit - daily_spent
            }
        
        print(f"   ✓ 每日限额检查通过 (今日已用: {daily_spent}/{daily_limit})")
        
        # Step 4: 检查余额
        balance = self.wallet.get_balance(user_address)
        
        if balance < amount:
            return {
                "success": False,
                "error": "余额不足",
                "balance": balance,
                "required": amount,
                "shortfall": amount - balance
            }
        
        print(f"   ✓ 余额充足 ({balance} >= {amount})")
        
        # Step 5: 检查目标地址
        if not self.is_valid_address(to_address):
            return {
                "success": False,
                "error": "无效的目标地址",
                "address": to_address
            }
        
        print(f"   ✓ 目标地址有效")
        
        # Step 6: 执行转账
        try:
            result = self.wallet.transfer(
                from_address=user_address,
                to_address=to_address,
                amount=amount,
                note=note
            )
            
            if result["success"]:
                # 记录每日消费
                self.record_daily_spent(username, amount)
                
                return {
                    "success": True,
                    "transaction_id": result.get("tx_id"),
                    "from": username,
                    "from_address": user_address,
                    "to_address": to_address,
                    "amount": amount,
                    "new_balance": balance - amount,
                    "message": "支付成功！"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "转账失败"),
                    "details": result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"转账异常: {str(e)}"
            }
    
    def process_game_payment(self, username, bet_amount, game_type="slot"):
        """
        处理游戏支付（特殊验证）
        
        Args:
            username: 用户名
            bet_amount: 下注金额
            game_type: 游戏类型
        """
        # 先检查是否绑定
        user_address = self.verifier.get_user_address(username)
        
        if not user_address:
            return {
                "success": False,
                "error": "未绑定地址",
                "help": "请先绑定地址: 评论 '绑定地址'"
            }
        
        # 验证所有权
        ownership = self.verifier.check_address_ownership(username, user_address)
        if not ownership["success"]:
            return ownership
        
        # 游戏特殊限额
        game_daily_limit = 100  # 游戏每日限额
        game_daily_spent = self.get_game_daily_spent(username)
        
        if game_daily_spent + bet_amount > game_daily_limit:
            return {
                "success": False,
                "error": f"超过每日游戏限额 ({game_daily_limit} MOLTY)",
                "remaining": game_daily_limit - game_daily_spent
            }
        
        # 检查余额
        balance = self.wallet.get_balance(user_address)
        if balance < bet_amount:
            return {
                "success": False,
                "error": "余额不足",
                "balance": balance,
                "needed": bet_amount
            }
        
        # 扣除下注金额
        self.wallet.transfer(
            from_address=user_address,
            to_address="casino_pool",
            amount=bet_amount,
            note=f"Game bet: {game_type}"
        )
        
        self.record_game_daily_spent(username, bet_amount)
        
        return {
            "success": True,
            "message": "下注成功，开始游戏！",
            "address": user_address,
            "bet": bet_amount,
            "balance": balance - bet_amount
        }
    
    def create_binding_flow(self, username):
        """
        创建绑定流程
        
        返回绑定指引
        """
        # 检查是否已有绑定
        existing = self.verifier.get_user_address(username)
        if existing:
            return {
                "success": False,
                "error": "已绑定地址",
                "address": existing,
                "message": f"你已经绑定了地址: {existing}"
            }
        
        # 检查是否有待验证
        for addr, req in self.verifier.pending.items():
            if req["username"] == username:
                return {
                    "success": True,
                    "status": "pending",
                    "address": addr,
                    "verification_amount": req["verification_amount"],
                    "message": f"请从 {addr} 转账 {req['verification_amount']} MOLTY 到 casino_bot 完成验证"
                }
        
        # 创建新的绑定请求
        # 先为用户创建钱包
        wallet = self.wallet.create_wallet(username)
        address = wallet.address
        
        # 创建绑定请求
        request = self.verifier.create_binding_request(username, address)
        
        return {
            "success": True,
            "status": "created",
            "address": address,
            "verification_amount": request["verification_amount"],
            "message": f"\n📱 绑定步骤：\n1. 你的新钱包地址: {address}\n2. 先获得一些MOLTY (点赞+评论可免费领取)\n3. 从该地址转账 {request['verification_amount']} MOLTY 到 casino_bot\n4. 评论 '已验证' 完成绑定\n\n这样确保只有你本人能使用该地址！"
        }
    
    def is_valid_address(self, address):
        """验证地址格式"""
        # 简单检查：以YM开头，长度43
        return address.startswith("YM") and len(address) == 43
    
    def get_daily_spent(self, username):
        """获取今日消费"""
        import datetime
        today = datetime.date.today().isoformat()
        
        data_file = f"{self.wallet.data_dir}/daily_stats.json"
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        if today not in data:
            data[today] = {}
        
        return data[today].get(username, {}).get("spent", 0)
    
    def record_daily_spent(self, username, amount):
        """记录今日消费"""
        import datetime
        today = datetime.date.today().isoformat()
        
        data_file = f"{self.wallet.data_dir}/daily_stats.json"
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        if today not in data:
            data[today] = {}
        
        if username not in data[today]:
            data[today][username] = {"spent": 0, "game_spent": 0}
        
        data[today][username]["spent"] += amount
        
        with open(data_file, 'w') as f:
            json.dump(data, f)
    
    def get_game_daily_spent(self, username):
        """获取今日游戏消费"""
        import datetime
        today = datetime.date.today().isoformat()
        
        data_file = f"{self.wallet.data_dir}/daily_stats.json"
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
        except:
            return 0
        
        return data.get(today, {}).get(username, {}).get("game_spent", 0)
    
    def record_game_daily_spent(self, username, amount):
        """记录今日游戏消费"""
        import datetime
        today = datetime.date.today().isoformat()
        
        data_file = f"{self.wallet.data_dir}/daily_stats.json"
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        if today not in data:
            data[today] = {}
        
        if username not in data[today]:
            data[today][username] = {"spent": 0, "game_spent": 0}
        
        data[today][username]["game_spent"] += amount
        
        with open(data_file, 'w') as f:
            json.dump(data, f)


# 全局支付系统
payment_system = SecurePaymentSystem()


if __name__ == "__main__":
    print("🔐 安全支付系统测试\n")
    
    # 测试1: 未绑定用户
    print("测试1: 未绑定用户支付")
    result = payment_system.process_payment_request("@Unknown", 100, "YM1234...")
    print(f"结果: {result}\n")
    
    # 测试2: 创建绑定流程
    print("测试2: 创建绑定流程")
    result = payment_system.create_binding_flow("@NewUser")
    print(f"结果: {result}\n")
    
    print("✅ 安全支付系统就绪！")