import json
import time
import re
from datetime import datetime

class MoltbookAutoResponder:
    """Moltbook自动回复系统 - 处理游戏和绑定请求"""
    
    def __init__(self):
        self.commands = {
            "绑定": self.handle_binding,
            "钱包": self.handle_wallet,
            "余额": self.handle_balance,
            "老虎机": self.handle_slot_machine,
            "骰子": self.handle_dice,
            "支付": self.handle_payment,
            "查询": self.handle_query,
            "验证": self.handle_verification,
            "帮助": self.handle_help,
        }
    
    def parse_comment(self, comment_text, username):
        """解析用户评论"""
        comment_lower = comment_text.lower().strip()
        
        # 提取命令
        for cmd, handler in self.commands.items():
            if cmd in comment_lower or cmd in comment_text:
                return handler(comment_text, username)
        
        # 默认：未知命令
        return {
            "action": "unknown",
            "response": "🤔 我不理解你的指令。发送 '帮助' 查看可用命令。"
        }
    
    def handle_binding(self, text, username):
        """处理绑定请求"""
        from secure_payment import payment_system
        
        result = payment_system.create_binding_flow(username)
        
        if result["success"]:
            if result.get("status") == "created":
                return {
                    "action": "binding_created",
                    "response": f"""
🆕 钱包创建成功！

📍 你的地址: {result['address']}

🔐 验证步骤:
1. 先获得一些MOLTY (点赞本帖=+2, 评论=+1)
2. 从该地址转账 {result['verification_amount']} MOLTY 到 casino_bot
3. 评论"已验证"完成绑定

这样确保只有你本人能使用该地址！
"""
                }
            elif result.get("status") == "pending":
                return {
                    "action": "binding_pending",
                    "response": f"""
⏳ 验证进行中...

📍 地址: {result['address']}
💰 需要转账: {result['verification_amount']} MOLTY

请完成转账后评论"已验证"
"""
                }
        else:
            return {
                "action": "binding_exists",
                "response": f"""
✅ 你已经绑定过地址了！

📍 你的地址: {result['address']}

如需更换地址，请先解绑 (联系管理员)
"""
            }
    
    def handle_wallet(self, text, username):
        """处理钱包查询"""
        from secure_payment import payment_system
        
        address = payment_system.verifier.get_user_address(username)
        
        if address:
            return {
                "action": "show_wallet",
                "response": f"""
💼 你的钱包

📍 地址: {address}

💡 你可以:
- 查询余额: 发送"余额"
- 开始游戏: 发送"老虎机 20"
- 支付转账: 发送"支付 100 YMxxx"
"""
            }
        else:
            return {
                "action": "no_wallet",
                "response": "你还没有钱包。发送'绑定'创建钱包！"
            }
    
    def handle_balance(self, text, username):
        """处理余额查询"""
        from secure_payment import payment_system
        
        address = payment_system.verifier.get_user_address(username)
        
        if not address:
            return {
                "action": "no_binding",
                "response": "你还没有绑定地址。发送'绑定'创建钱包！"
            }
        
        balance = payment_system.wallet.get_balance(address)
        binding_info = payment_system.verifier.get_binding_info(username)
        
        daily_spent = payment_system.get_daily_spent(username)
        daily_limit = binding_info.get("daily_limit", 100) if binding_info else 100
        
        return {
            "action": "show_balance",
            "response": f"""
💰 余额查询

📍 地址: {address[:10]}...{address[-6:]}
💵 余额: {balance} MOLTY

📊 今日消费: {daily_spent}/{daily_limit} MOLTY
💎 剩余额度: {daily_limit - daily_spent} MOLTY

🎮 发送"老虎机 20"开始游戏！
"""
        }
    
    def handle_slot_machine(self, text, username):
        """处理老虎机游戏"""
        from secure_payment import payment_system
        from casino.arcade import casino
        import re
        
        # 提取下注金额
        match = re.search(r'(\d+)', text)
        if not match:
            return {
                "action": "invalid_bet",
                "response": "请指定下注金额。例如: '老虎机 20'"
            }
        
        bet = int(match.group(1))
        
        # 验证并扣除下注
        result = payment_system.process_game_payment(username, bet, "slot")
        
        if not result["success"]:
            return {
                "action": "game_error",
                "response": f"❌ {result['error']}"
            }
        
        # 执行游戏
        game_result = casino.play_slot_machine(username, bet)
        
        # 发放奖励
        if game_result["winnings"] > 0:
            payment_system.wallet.transfer(
                from_address="casino_pool",
                to_address=result["address"],
                amount=game_result["winnings"],
                note=f"Slot win: {game_result['combination']}"
            )
        
        # 格式化回复
        reels = game_result["reels"]
        winnings = game_result["winnings"]
        
        if winnings > 0:
            return {
                "action": "slot_win",
                "response": f"""
🎰 SPINNING...
🎰 [{reels[0]}] [{reels[1]}] [{reels[2]}]

🎉 {game_result['message']}
💰 赢得: {winnings} MOLTY
✅ 已自动到账！

再玩一次? 发送"老虎机 20"
"""
            }
        else:
            return {
                "action": "slot_lose",
                "response": f"""
🎰 SPINNING...
🎰 [{reels[0]}] [{reels[1]} [{reels[2]}]

😢 {game_result['message']}
💸 损失: {bet} MOLTY

再试一次? 发送"老虎机 20"
"""
            }
    
    def handle_dice(self, text, username):
        """处理骰子游戏"""
        from secure_payment import payment_system
        from casino.arcade import casino
        import re
        
        # 提取猜测和金额
        match = re.search(r'(大|小).*?(\d+)', text)
        if not match:
            return {
                "action": "invalid_dice",
                "response": "格式错误。例如: '骰子 大 50' 或 '骰子 小 20'"
            }
        
        prediction = match.group(1)
        bet = int(match.group(2))
        
        # 验证并扣除下注
        result = payment_system.process_game_payment(username, bet, "dice")
        
        if not result["success"]:
            return {
                "action": "game_error",
                "response": f"❌ {result['error']}"
            }
        
        # 执行游戏
        game_result = casino.play_dice(username, bet, prediction)
        
        # 发放奖励
        if game_result["winnings"] > 0:
            payment_system.wallet.transfer(
                from_address="casino_pool",
                to_address=result["address"],
                amount=game_result["winnings"],
                note=f"Dice win: {game_result['dice_result']}"
            )
        
        dice_emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][game_result["dice_result"] - 1]
        
        if game_result["winnings"] > 0:
            return {
                "action": "dice_win",
                "response": f"""
🎲 ROLLING...
🎲 结果: {dice_emoji} ({game_result['dice_result']})

你猜: {prediction}
结果: {game_result['outcome']} ✅

🎉 猜对了！
💰 赢得: {game_result['winnings']} MOLTY
✅ 已自动到账！

再玩一次? 发送"骰子 大 50"
"""
            }
        else:
            return {
                "action": "dice_lose",
                "response": f"""
🎲 ROLLING...
🎲 结果: {dice_emoji} ({game_result['dice_result']})

你猜: {prediction}
结果: {game_result['outcome']} ❌

😢 猜错了！
💸 损失: {bet} MOLTY

再试一次? 发送"骰子 小 20"
"""
            }
    
    def handle_payment(self, text, username):
        """处理支付请求"""
        from secure_payment import payment_system
        import re
        
        # 提取金额和地址
        match = re.search(r'(\d+).*?(YM[A-Za-z0-9]{41})', text)
        if not match:
            return {
                "action": "invalid_payment",
                "response": "格式错误。例如: '支付 100 YM6695A8ir9sGBUAkHLFXBZDWQghDuJ125'"
            }
        
        amount = int(match.group(1))
        to_address = match.group(2)
        
        # 执行支付
        result = payment_system.process_payment_request(username, amount, to_address)
        
        if result["success"]:
            return {
                "action": "payment_success",
                "response": f"""
✅ 支付成功！

💸 金额: {amount} MOLTY
📍 目标: {to_address[:10]}...{to_address[-6:]}
🆔 交易ID: {result.get('transaction_id', 'N/A')}
💰 新余额: {result['new_balance']} MOLTY
"""
            }
        else:
            return {
                "action": "payment_failed",
                "response": f"❌ 支付失败: {result['error']}"
            }
    
    def handle_query(self, text, username):
        """处理查询请求"""
        # 默认显示余额
        return self.handle_balance(text, username)
    
    def handle_verification(self, text, username):
        """处理验证确认"""
        from secure_payment import payment_system
        
        # 检查待验证
        address = payment_system.verifier.get_user_address(username)
        
        if not address:
            # 查找待验证记录
            for addr, req in payment_system.verifier.pending.items():
                if req["username"] == username:
                    # 尝试验证
                    result = payment_system.verifier.verify_by_transfer(addr)
                    
                    if result["success"]:
                        return {
                            "action": "verification_success",
                            "response": f"""
🎉 验证成功！

📍 地址: {addr} 已绑定
✅ 你现在可以使用所有功能了！

💰 查询余额: 发送"余额"
🎮 开始游戏: 发送"老虎机 20"
"""
                        }
                    else:
                        return {
                            "action": "verification_pending",
                            "response": f"""
⏳ 验证中...

需要转账: {result.get('expected')} MOLTY
请完成转账后再试
"""
                        }
        
        return {
            "action": "no_verification_needed",
            "response": "你还没有待验证的绑定请求。发送'绑定'开始创建钱包。"
        }
    
    def handle_help(self, text, username):
        """处理帮助请求"""
        return {
            "action": "help",
            "response": """
📖 MOLTY Casino 命令指南

🆕 开始使用:
  绑定 - 创建并绑定钱包
  钱包 - 查看你的钱包地址
  余额 - 查询余额

🎮 玩游戏:
  老虎机 [金额] - 玩老虎机 (10-100)
  骰子 [大/小] [金额] - 玩骰子游戏

💰 转账:
  支付 [金额] [地址] - 转账给其他用户

❓ 其他:
  帮助 - 显示本指南
  查询 - 查询余额

💡 示例:
  "老虎机 20" - 下注20玩老虎机
  "骰子 大 50" - 猜大，下注50
  "支付 100 YM6695..." - 转账100 MOLTY
"""
        }


# 全局响应器
responder = MoltbookAutoResponder()


def process_moltbook_comment(comment_text, username):
    """
    处理Moltbook评论的主函数
    
    Args:
        comment_text: 评论内容
        username: Moltbook用户名
    
    Returns:
        dict: 处理结果和回复内容
    """
    return responder.parse_comment(comment_text, username)


if __name__ == "__main__":
    print("🤖 Moltbook自动回复系统测试\n")
    
    # 测试各种命令
    test_cases = [
        ("绑定", "@TestUser1"),
        ("余额", "@TestUser1"),
        ("老虎机 20", "@TestUser1"),
        ("帮助", "@TestUser1"),
    ]
    
    for comment, user in test_cases:
        result = process_moltbook_comment(comment, user)
        print(f"用户: {user}")
        print(f"评论: {comment}")
        print(f"回复: {result['response'][:100]}...")
        print("-" * 50)
    
    print("\n✅ 自动回复系统就绪！")