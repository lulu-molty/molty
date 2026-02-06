#!/usr/bin/env python3
"""
MOLTY互动功能测试系统
测试: 1) 点赞/评论/转发奖励  2) 赌场游戏互动
"""

import requests
import json
import random
from datetime import datetime

# API endpoints
WALLET_API = "http://localhost:8888"
CASINO_API = "http://localhost:8890"

class MOLTYInteractionTester:
    """MOLTY互动功能测试器"""
    
    def __init__(self):
        self.test_results = []
        
    def test_engagement_reward(self, action_type, user_id):
        """
        测试互动奖励功能
        action_type: 'like', 'comment', 'repost'
        """
        print(f"\n🎯 测试互动奖励: {action_type}")
        print("-" * 50)
        
        # 1. 检查用户当前余额
        balance_before = self._get_balance(user_id)
        print(f"   互动前余额: {balance_before} MOLTY")
        
        # 2. 模拟互动行为
        reward_amount = self._calculate_reward(action_type)
        print(f"   互动类型: {action_type}")
        print(f"   奖励金额: {reward_amount} MOLTY")
        
        # 3. 发放奖励
        result = self._send_reward(user_id, reward_amount, action_type)
        
        # 4. 检查余额变化
        balance_after = self._get_balance(user_id)
        print(f"   互动后余额: {balance_after} MOLTY")
        print(f"   实际到账: {balance_after - balance_before} MOLTY")
        
        success = (balance_after - balance_before) == reward_amount
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   测试结果: {status}")
        
        self.test_results.append({
            'test': f'engagement_{action_type}',
            'success': success,
            'reward': reward_amount,
            'before': balance_before,
            'after': balance_after
        })
        
        return success
    
    def test_casino_game(self, user_id, game_type, bet=10, **kwargs):
        """
        测试赌场游戏功能
        game_type: 'slot', 'dice'
        """
        print(f"\n🎰 测试赌场游戏: {game_type}")
        print("-" * 50)
        
        # 1. 检查用户余额
        balance_before = self._get_casino_balance(user_id)
        print(f"   游戏前余额: {balance_before}")
        
        # 2. 发送游戏请求
        game_result = self._play_game(user_id, game_type, bet, **kwargs)
        
        if 'error' in game_result:
            print(f"   ❌ 游戏失败: {game_result['error']}")
            return False
        
        # 3. 显示游戏结果
        if game_type == 'slot':
            symbols = ' '.join(game_result.get('symbols', []))
            print(f"   🎰 结果: {symbols}")
        elif game_type == 'dice':
            roll = game_result.get('roll', 0)
            print(f"   🎲 掷出: {roll}")
        
        winnings = game_result.get('winnings', 0)
        balance_after = game_result.get('balance', balance_before)
        
        print(f"   💰 投注: {bet} MOLTY")
        print(f"   🏆 赢取: {winnings} MOLTY")
        print(f"   💵 余额: {balance_after} MOLTY")
        print(f"   📝 消息: {game_result.get('message', '')}")
        
        # 4. 验证余额变化
        expected_change = winnings - bet
        actual_change = balance_after - balance_before
        
        success = actual_change == expected_change
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   测试结果: {status}")
        
        self.test_results.append({
            'test': f'casino_{game_type}',
            'success': success,
            'bet': bet,
            'winnings': winnings,
            'balance': balance_after
        })
        
        return success
    
    def _get_balance(self, user_id):
        """获取钱包余额"""
        try:
            resp = requests.get(f"{WALLET_API}/balance/{user_id}")
            return resp.json().get('balance', 0)
        except:
            return 0
    
    def _calculate_reward(self, action_type):
        """计算互动奖励"""
        rewards = {
            'like': 1,      # 点赞奖励 1 MOLTY
            'comment': 5,   # 评论奖励 5 MOLTY
            'repost': 10    # 转发奖励 10 MOLTY
        }
        return rewards.get(action_type, 0)
    
    def _send_reward(self, user_id, amount, action_type):
        """发送奖励"""
        try:
            resp = requests.post(f"{WALLET_API}/transfer", json={
                'from': 'SYSTEM',
                'to': user_id,
                'amount': amount
            })
            return resp.json()
        except Exception as e:
            print(f"   发送奖励失败: {e}")
            return {'success': False}
    
    def _get_casino_balance(self, user_id):
        """获取游戏余额"""
        # 简化处理，使用内存存储
        return 1000  # 默认给1000测试币
    
    def _play_game(self, user_id, game_type, bet, **kwargs):
        """玩游戏"""
        try:
            data = {
                'user_id': user_id,
                'game': game_type,
                'bet': bet
            }
            data.update(kwargs)
            
            resp = requests.post(f"{CASINO_API}/casino/play", json=data)
            return resp.json()
        except Exception as e:
            return {'error': str(e)}
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 MOLTY互动功能测试报告")
        print("=" * 60)
        print(f"测试时间: {datetime.now().isoformat()}")
        print(f"测试项目: {len(self.test_results)}")
        print("-" * 60)
        
        passed = sum(1 for r in self.test_results if r['success'])
        failed = len(self.test_results) - passed
        
        for result in self.test_results:
            status = "✅ 通过" if result['success'] else "❌ 失败"
            print(f"   {result['test']:<25} {status}")
        
        print("-" * 60)
        print(f"通过: {passed} | 失败: {failed} | 总计: {len(self.test_results)}")
        print("=" * 60)
        
        return passed == len(self.test_results)

# 运行测试
if __name__ == "__main__":
    tester = MOLTYInteractionTester()
    
    print("🚀 MOLTY互动功能全面测试")
    print("=" * 60)
    
    # 测试互动奖励
    tester.test_engagement_reward('like', 'test_user_1')
    tester.test_engagement_reward('comment', 'test_user_2')
    tester.test_engagement_reward('repost', 'test_user_3')
    
    # 测试赌场游戏
    tester.test_casino_game('casino_player_1', 'slot', bet=10)
    tester.test_casino_game('casino_player_2', 'dice', bet=10, prediction='high')
    tester.test_casino_game('casino_player_3', 'dice', bet=20, prediction='low')
    
    # 生成报告
    all_passed = tester.generate_report()
    
    if all_passed:
        print("\n🎉 所有测试通过！MOLTY互动功能已就绪！")
    else:
        print("\n⚠️ 部分测试失败，请检查服务状态。")
