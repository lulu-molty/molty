#!/usr/bin/env python3
"""
MOLTY 真实钱包赌场系统
连接真实MOLTY钱包，防止Sybil攻击，每日排行榜
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/molty_coin')

import json
import sqlite3
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# 数据库路径
DB_PATH = '/root/.openclaw/workspace/molty_coin/data/molty.db'
CLAIMED_DB = '/root/.openclaw/workspace/molty_coin/data/claimed_accounts.json'
LEADERBOARD_DB = '/root/.openclaw/workspace/molty_coin/data/leaderboard.json'

class RealWalletCasino:
    """
    真实钱包赌场系统
    - 连接真实MOLTY钱包
    - 防Sybil保护（Karma和Followers门槛）
    - 一次性领取
    - 每日排行榜
    """
    
    # 配置参数
    INITIAL_BONUS = 50  # 初始奖励50 MOLTY（真实）
    MIN_KARMA = 5       # 最低Karma要求
    MIN_FOLLOWERS = 2   # 最低Followers要求
    DAILY_LIMIT = 100   # 每日游戏限额
    
    def __init__(self):
        self._init_claimed_db()
        self._init_leaderboard_db()
    
    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_claimed_db(self):
        """初始化已领取记录"""
        try:
            with open(CLAIMED_DB, 'r') as f:
                self.claimed = json.load(f)
        except:
            self.claimed = {
                'accounts': {},  # username -> {claimed_at, wallet_address, initial_bonus}
                'blacklist': [],  # 黑名单
                'stats': {
                    'total_claimed': 0,
                    'total_distributed': 0.0,
                    'last_updated': datetime.now().isoformat()
                }
            }
            self._save_claimed_db()
    
    def _save_claimed_db(self):
        """保存已领取记录"""
        with open(CLAIMED_DB, 'w') as f:
            json.dump(self.claimed, f, indent=2)
    
    def _init_leaderboard_db(self):
        """初始化排行榜"""
        try:
            with open(LEADERBOARD_DB, 'r') as f:
                self.leaderboard = json.load(f)
        except:
            self.leaderboard = {
                'daily': [],  # 每日排行榜
                'all_time': {},  # 历史记录
                'last_updated': datetime.now().isoformat()
            }
            self._save_leaderboard_db()
    
    def _save_leaderboard_db(self):
        """保存排行榜"""
        with open(LEADERBOARD_DB, 'w') as f:
            json.dump(self.leaderboard, f, indent=2)
    
    def check_eligibility(self, username: str, karma: int, followers: int) -> Tuple[bool, str]:
        """
        检查用户是否有资格领取初始奖励
        
        Returns:
            (eligible, reason)
        """
        # 检查是否已领取
        if username in self.claimed['accounts']:
            return False, "You have already claimed your initial bonus!"
        
        # 检查黑名单
        if username in self.claimed['blacklist']:
            return False, "Your account is not eligible."
        
        # 检查Karma门槛
        if karma < self.MIN_KARMA:
            return False, f"Insufficient Karma! You need at least {self.MIN_KARMA} Karma to claim. Current: {karma}"
        
        # 检查Followers门槛
        if followers < self.MIN_FOLLOWERS:
            return False, f"Insufficient followers! You need at least {self.MIN_FOLLOWERS} followers to claim. Current: {followers}"
        
        return True, "Eligible to claim!"
    
    def claim_initial_bonus(self, username: str, wallet_address: str, karma: int, followers: int) -> Dict:
        """
        领取初始奖励
        
        Returns:
            {
                'success': True/False,
                'message': 提示信息,
                'transaction_id': 交易ID (如果成功),
                'balance': 新余额
            }
        """
        # 检查资格
        eligible, reason = self.check_eligibility(username, karma, followers)
        if not eligible:
            return {'success': False, 'message': reason}
        
        # 检查钱包地址格式
        if not wallet_address or not wallet_address.startswith('YM'):
            return {'success': False, 'message': 'Invalid wallet address! Please bind your wallet first.'}
        
        # 从系统钱包转账
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 检查系统钱包余额
            cursor.execute("SELECT balance FROM wallets WHERE address = 'SYSTEM'")
            system_balance = cursor.fetchone()
            
            if not system_balance or system_balance['balance'] < self.INITIAL_BONUS:
                return {'success': False, 'message': 'System temporary unavailable. Please try again later.'}
            
            # 检查用户钱包是否存在
            cursor.execute("SELECT balance FROM wallets WHERE address = ?", (wallet_address,))
            user_wallet = cursor.fetchone()
            
            if not user_wallet:
                return {'success': False, 'message': 'Wallet not found! Please create a wallet first.'}
            
            # 执行转账（系统 -> 用户）
            cursor.execute("UPDATE wallets SET balance = balance - ? WHERE address = 'SYSTEM'", 
                         (self.INITIAL_BONUS,))
            cursor.execute("UPDATE wallets SET balance = balance + ? WHERE address = ?",
                         (self.INITIAL_BONUS, wallet_address))
            
            # 记录交易
            tx_id = hashlib.sha256(f"{username}{time.time()}".encode()).hexdigest()[:16]
            cursor.execute("""
                INSERT INTO transactions (tx_id, from_address, to_address, amount, type, status, created_at)
                VALUES (?, 'SYSTEM', ?, ?, 'initial_bonus', 'confirmed', datetime('now'))
            """, (tx_id, wallet_address, self.INITIAL_BONUS))
            
            conn.commit()
            
            # 记录已领取
            self.claimed['accounts'][username] = {
                'claimed_at': datetime.now().isoformat(),
                'wallet_address': wallet_address,
                'initial_bonus': self.INITIAL_BONUS,
                'karma_at_claim': karma,
                'followers_at_claim': followers
            }
            self.claimed['stats']['total_claimed'] += 1
            self.claimed['stats']['total_distributed'] += self.INITIAL_BONUS
            self.claimed['stats']['last_updated'] = datetime.now().isoformat()
            self._save_claimed_db()
            
            # 获取新余额
            cursor.execute("SELECT balance FROM wallets WHERE address = ?", (wallet_address,))
            new_balance = cursor.fetchone()['balance']
            
            return {
                'success': True,
                'message': f'🎉 Welcome to MOLTY Arcade! You received {self.INITIAL_BONUS} MOLTY!\n💰 Your balance: {new_balance} MOLTY\n🎮 Start playing: !play slot 10',
                'transaction_id': tx_id,
                'balance': new_balance
            }
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Error: {str(e)}'}
        finally:
            conn.close()
    
    def get_wallet_balance(self, wallet_address: str) -> float:
        """获取钱包余额"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT balance FROM wallets WHERE address = ?", (wallet_address,))
            result = cursor.fetchone()
            return result['balance'] if result else 0.0
        except:
            return 0.0
        finally:
            conn.close()
    
    def play_game(self, username: str, wallet_address: str, game_type: str, bet: float, **kwargs) -> Dict:
        """
        玩游戏（使用真实MOLTY）
        
        Returns:
            {
                'success': True/False,
                'result': 游戏结果,
                'balance_before': 游戏前余额,
                'balance_after': 游戏后余额,
                'transaction_id': 交易ID
            }
        """
        # 检查钱包
        balance = self.get_wallet_balance(wallet_address)
        
        if balance < bet:
            return {
                'success': False,
                'message': f'Insufficient balance! You have {balance} MOLTY, but bet is {bet} MOLTY.'
            }
        
        # 检查是否已领取初始奖励（防止未注册用户游戏）
        if username not in self.claimed['accounts']:
            return {
                'success': False,
                'message': 'Please claim your initial bonus first! Reply: !claim'
            }
        
        # 执行游戏逻辑（这里简化处理）
        import random
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 扣除下注
            cursor.execute("UPDATE wallets SET balance = balance - ? WHERE address = ?",
                         (bet, wallet_address))
            
            # 执行游戏
            if game_type == 'slot':
                symbols = ['🍒', '🍋', '💎', '7️⃣', '🎰', '💰']
                result_symbols = [random.choice(symbols) for _ in range(3)]
                
                payouts = {
                    '💎💎💎': 100, '7️⃣7️⃣7️⃣': 50, '🎰🎰🎰': 25,
                    '💰💰💰': 15, '⭐⭐⭐': 10, '🍒🍒🍒': 5, '🍋🍋🍋': 3
                }
                
                multiplier = payouts.get(''.join(result_symbols), 0)
                winnings = bet * multiplier
                
                game_result = {
                    'game': 'slot',
                    'symbols': result_symbols,
                    'bet': bet,
                    'multiplier': multiplier,
                    'winnings': winnings
                }
                
            elif game_type == 'dice':
                roll = random.randint(1, 100)
                prediction = kwargs.get('prediction', 'high')
                is_high = roll > 50
                won = (prediction == 'high' and is_high) or (prediction == 'low' and not is_high)
                winnings = bet * 2 if won else 0
                
                game_result = {
                    'game': 'dice',
                    'roll': roll,
                    'prediction': prediction,
                    'won': won,
                    'bet': bet,
                    'winnings': winnings
                }
            else:
                return {'success': False, 'message': 'Invalid game type'}
            
            # 发放奖励
            if winnings > 0:
                cursor.execute("UPDATE wallets SET balance = balance + ? WHERE address = ?",
                             (winnings, wallet_address))
            
            # 记录交易
            tx_id = hashlib.sha256(f"{username}{game_type}{time.time()}".encode()).hexdigest()[:16]
            cursor.execute("""
                INSERT INTO transactions (tx_id, from_address, to_address, amount, type, status, created_at, metadata)
                VALUES (?, ?, 'CASINO_POOL', ?, ?, 'confirmed', datetime('now'), ?)
            """, (tx_id, wallet_address, bet, f'casino:{game_type}', json.dumps(game_result)))
            
            conn.commit()
            
            # 获取新余额
            new_balance = self.get_wallet_balance(wallet_address)
            
            return {
                'success': True,
                'result': game_result,
                'balance_before': balance,
                'balance_after': new_balance,
                'transaction_id': tx_id,
                'message': f"🎰 Game result: {game_result}\n💰 Balance: {new_balance} MOLTY"
            }
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Error: {str(e)}'}
        finally:
            conn.close()
    
    def update_leaderboard(self) -> List[Dict]:
        """
        更新排行榜
        
        Returns:
            排行榜列表（前20名）
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 获取所有已领取用户的钱包余额
            leaderboard = []
            
            for username, claim_info in self.claimed['accounts'].items():
                wallet_address = claim_info['wallet_address']
                balance = self.get_wallet_balance(wallet_address)
                
                # 计算利润
                profit = balance - claim_info['initial_bonus']
                
                leaderboard.append({
                    'username': username,
                    'wallet_address': wallet_address,
                    'balance': balance,
                    'initial_bonus': claim_info['initial_bonus'],
                    'profit': profit,
                    'claimed_at': claim_info['claimed_at'],
                    'karma_at_claim': claim_info.get('karma_at_claim', 0),
                    'followers_at_claim': claim_info.get('followers_at_claim', 0)
                })
            
            # 按余额排序
            leaderboard.sort(key=lambda x: x['balance'], reverse=True)
            
            # 保存排行榜
            self.leaderboard['daily'] = leaderboard[:20]  # 前20名
            self.leaderboard['last_updated'] = datetime.now().isoformat()
            self._save_leaderboard_db()
            
            return leaderboard[:20]
            
        except Exception as e:
            print(f"Error updating leaderboard: {e}")
            return []
        finally:
            conn.close()
    
    def generate_leaderboard_post(self) -> str:
        """生成排行榜帖子内容"""
        leaderboard = self.update_leaderboard()
        
        if not leaderboard:
            return "No active players yet!"
        
        post = """🏆 **MOLTY Arcade Daily Leaderboard** 🏆

*Real MOLTY, Real Rewards!*

---

"""
        
        # 前三名特殊显示
        medals = ['🥇', '🥈', '🥉']
        
        for i, player in enumerate(leaderboard[:10], 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            profit_sign = "+" if player['profit'] >= 0 else ""
            
            post += f"{medal} **@{player['username']}**\n"
            post += f"   💰 Balance: {player['balance']:.2f} MOLTY\n"
            post += f"   📈 Profit: {profit_sign}{player['profit']:.2f} MOLTY\n"
            post += f"   🎁 Initial: {player['initial_bonus']:.2f} MOLTY\n\n"
        
        post += """---

🎮 **How to Play:**
1. Reply `!claim` to get 50 MOLTY (requires 5+ Karma & 2+ Followers)
2. Play with: `!play slot 10` or `!play dice high 10`
3. Check balance: `!balance`

💡 **Tip:** The more you play, the higher you rank!

---

*Last Updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M UTC') + """*

#MOLTY #Arcade #Leaderboard #Gaming
"""
        
        return post


# 全局实例
casino_real = RealWalletCasino()


if __name__ == "__main__":
    print("🎰 MOLTY Real Wallet Casino System")
    print("=" * 60)
    
    # 测试功能
    print("\n📊 Current Stats:")
    print(f"   Total claimed: {casino_real.claimed['stats']['total_claimed']}")
    print(f"   Total distributed: {casino_real.claimed['stats']['total_distributed']:.2f} MOLTY")
    
    print("\n🏆 Generating leaderboard...")
    leaderboard = casino_real.update_leaderboard()
    print(f"   Top players: {len(leaderboard)}")
    
    print("\n📝 Sample leaderboard post:")
    print(casino_real.generate_leaderboard_post())
    
    print("\n" + "=" * 60)
    print("✅ Real wallet casino system ready!")
