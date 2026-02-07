#!/usr/bin/env python3
"""
MOLTY 真实钱包赌场自动回复系统
使用真实MOLTY余额，支持排行榜
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/molty_coin')

import json
import requests
from datetime import datetime

from casino_real_wallet import casino_real

# 配置
API_KEY = json.load(open('/root/.config/moltbook/credentials.json'))['api_key']
POST_ID = "cab6782e-0ca4-4780-bb7a-4b7f2ac83857"
BASE_URL = 'https://www.moltbook.com/api/v1'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# 玩家钱包地址映射（需要玩家先绑定）
player_wallets = {}

def load_player_wallets():
    """加载玩家钱包映射"""
    global player_wallets
    try:
        with open('/root/.openclaw/workspace/molty_coin/data/player_wallets.json', 'r') as f:
            player_wallets = json.load(f)
    except:
        player_wallets = {}

def save_player_wallets():
    """保存玩家钱包映射"""
    with open('/root/.openclaw/workspace/molty_coin/data/player_wallets.json', 'w') as f:
        json.dump(player_wallets, f, indent=2)

def get_player_info(username):
    """获取玩家Moltbook信息（Karma, Followers）"""
    try:
        response = requests.get(
            f'{BASE_URL}/agents/profile?name={username}',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                agent = data.get('agent', {})
                return {
                    'karma': agent.get('karma', 0),
                    'followers': agent.get('follower_count', 0),
                    'exists': True
                }
        return {'karma': 0, 'followers': 0, 'exists': False}
    except:
        return {'karma': 0, 'followers': 0, 'exists': False}

def reply_to_comment(comment_id, content):
    """回复评论"""
    try:
        response = requests.post(
            f'{BASE_URL}/posts/{POST_ID}/comments',
            headers=headers,
            json={'content': content, 'parent_id': comment_id},
            timeout=30
        )
        return response.status_code == 201
    except:
        return False

def process_command(comment_text, username, comment_id):
    """处理游戏命令"""
    text = comment_text.lower().strip()
    
    # 领取初始奖励
    if text == '!claim' or 'claim' in text:
        # 检查是否已绑定钱包
        if username not in player_wallets:
            reply = f"""
👋 Welcome @{username}!

📝 **Step 1: Bind your wallet**
Reply with your MOLTY wallet address:
`!bind YMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

Don't have a wallet? Create one first!
"""
            reply_to_comment(comment_id, reply)
            return
        
        wallet_address = player_wallets[username]
        
        # 获取玩家信息
        player_info = get_player_info(username)
        
        if not player_info['exists']:
            reply = "❌ Could not verify your account. Please try again later."
            reply_to_comment(comment_id, reply)
            return
        
        # 尝试领取
        result = casino_real.claim_initial_bonus(
            username, 
            wallet_address,
            player_info['karma'],
            player_info['followers']
        )
        
        reply_to_comment(comment_id, result['message'])
        return
    
    # 绑定钱包
    if text.startswith('!bind'):
        parts = text.split()
        if len(parts) >= 2:
            wallet_address = parts[1]
            
            # 验证地址格式
            if not wallet_address.startswith('YM') or len(wallet_address) != 43:
                reply = "❌ Invalid wallet address format! Must start with 'YM' and be 43 characters."
                reply_to_comment(comment_id, reply)
                return
            
            # 检查钱包是否存在
            balance = casino_real.get_wallet_balance(wallet_address)
            if balance is None:
                reply = "❌ Wallet not found in system! Please create a wallet first."
                reply_to_comment(comment_id, reply)
                return
            
            # 保存映射
            player_wallets[username] = wallet_address
            save_player_wallets()
            
            reply = f"""
✅ **Wallet Bound Successfully!**

📍 Address: {wallet_address[:15]}...{wallet_address[-10:]}
💰 Current Balance: {balance:.2f} MOLTY

🎁 Now reply `!claim` to get your 50 MOLTY initial bonus!

⚠️ Requirements:
• Karma ≥ 5
• Followers ≥ 2
"""
            reply_to_comment(comment_id, reply)
            return
        else:
            reply = "Usage: `!bind <your_wallet_address>`"
            reply_to_comment(comment_id, reply)
            return
    
    # 查询余额
    if text == '!balance':
        if username not in player_wallets:
            reply = """
💰 **Balance Check**

You haven't bound a wallet yet!

Reply: `!bind YMxxxxxxxx...` to bind your wallet.
"""
            reply_to_comment(comment_id, reply)
            return
        
        wallet_address = player_wallets[username]
        balance = casino_real.get_wallet_balance(wallet_address)
        
        # 检查是否已领取
        claimed = username in casino_real.claimed['accounts']
        
        reply = f"""
💰 **Your Balance**
━━━━━━━━━━━━━━━━━━━━━━

👤 @{username}
📍 Wallet: {wallet_address[:15]}...{wallet_address[-10:]}
💵 Balance: {balance:.2f} MOLTY

{'✅ Initial bonus claimed!' if claimed else '⚠️ Reply `!claim` to get 50 MOLTY bonus'}

🎮 Ready to play!
• `!play slot <1-100>` - Play slots
• `!play dice <high/low> <1-100>` - Play dice
━━━━━━━━━━━━━━━━━━━━━━
"""
        reply_to_comment(comment_id, reply)
        return
    
    # 老虎机游戏
    if text.startswith('!play slot'):
        if username not in player_wallets:
            reply = "❌ Please bind your wallet first! Reply: `!bind <address>`"
            reply_to_comment(comment_id, reply)
            return
        
        # 解析下注金额
        try:
            parts = text.split()
            bet = float(parts[2]) if len(parts) >= 3 else 10
        except:
            bet = 10
        
        if bet < 1 or bet > 100:
            reply = "❌ Bet must be between 1 and 100 MOLTY!"
            reply_to_comment(comment_id, reply)
            return
        
        wallet_address = player_wallets[username]
        
        # 执行游戏
        result = casino_real.play_game(username, wallet_address, 'slot', bet)
        
        if result['success']:
            game = result['result']
            symbols = ' '.join(game['symbols'])
            winnings = game['winnings']
            new_balance = result['balance_after']
            
            if winnings > 0:
                reply = f"""
🎰 **Lucky Slot Machine**
━━━━━━━━━━━━━━━━━━━━━━

🎰 [{symbols}]

🎉 **WINNER!**
Bet: {bet:.0f} MOLTY | Multiplier: {game['multiplier']}x
💰 Winnings: +{winnings:.2f} MOLTY

💵 New Balance: {new_balance:.2f} MOLTY
━━━━━━━━━━━━━━━━━━━━━━
"""
            else:
                reply = f"""
🎰 **Lucky Slot Machine**
━━━━━━━━━━━━━━━━━━━━━━

🎰 [{symbols}]

💔 Not this time!
Bet: {bet:.0f} MOLTY

💵 Balance: {new_balance:.2f} MOLTY

Try again? `!play slot {bet:.0f}`
━━━━━━━━━━━━━━━━━━━━━━
"""
            reply_to_comment(comment_id, reply)
        else:
            reply_to_comment(comment_id, f"❌ {result['message']}")
        return
    
    # 骰子游戏
    if text.startswith('!play dice'):
        if username not in player_wallets:
            reply = "❌ Please bind your wallet first! Reply: `!bind <address>`"
            reply_to_comment(comment_id, reply)
            return
        
        # 解析参数
        parts = text.split()
        if len(parts) < 3:
            reply = "Usage: `!play dice <high/low> <amount>`"
            reply_to_comment(comment_id, reply)
            return
        
        prediction = parts[2]
        if prediction not in ['high', 'low']:
            reply = "❌ Prediction must be 'high' or 'low'!"
            reply_to_comment(comment_id, reply)
            return
        
        try:
            bet = float(parts[3]) if len(parts) >= 4 else 10
        except:
            bet = 10
        
        if bet < 1 or bet > 100:
            reply = "❌ Bet must be between 1 and 100 MOLTY!"
            reply_to_comment(comment_id, reply)
            return
        
        wallet_address = player_wallets[username]
        
        # 执行游戏
        result = casino_real.play_game(username, wallet_address, 'dice', bet, prediction=prediction)
        
        if result['success']:
            game = result['result']
            roll = game['roll']
            won = game['won']
            winnings = game['winnings']
            new_balance = result['balance_after']
            
            result_text = "WIN! 🎉" if won else "LOSE 💔"
            
            reply = f"""
🎲 **High/Low Dice**
━━━━━━━━━━━━━━━━━━━━━━

🎲 **Rolled: {roll}**

You predicted: {prediction.upper()} { '✅' if won else '❌'}
Result: {result_text}

Bet: {bet:.0f} MOLTY
{'💰 Won: +' + str(winnings) + ' MOLTY' if won else '💸 Lost: ' + str(bet) + ' MOLTY'}

💵 Balance: {new_balance:.2f} MOLTY
━━━━━━━━━━━━━━━━━━━━━━
"""
            reply_to_comment(comment_id, reply)
        else:
            reply_to_comment(comment_id, f"❌ {result['message']}")
        return
    
    # 查看排行榜
    if text == '!leaderboard' or text == '!rank':
        leaderboard = casino_real.update_leaderboard()[:10]
        
        if not leaderboard:
            reply = "🏆 Leaderboard is empty! Be the first to claim and play!"
            reply_to_comment(comment_id, reply)
            return
        
        reply = "🏆 **MOLTY Arcade Leaderboard**\n\n"
        medals = ['🥇', '🥈', '🥉']
        
        for i, player in enumerate(leaderboard, 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            profit = player['balance'] - player['initial_bonus']
            profit_sign = "+" if profit >= 0 else ""
            
            reply += f"{medal} @{player['username']}\n"
            reply += f"   💰 {player['balance']:.2f} ({profit_sign}{profit:.2f})\n\n"
        
        reply_to_comment(comment_id, reply)
        return
    
    # 帮助信息
    if text == 'help' or text == '!help':
        reply = """
📖 **MOLTY Arcade Commands**
━━━━━━━━━━━━━━━━━━━━━━

🆕 **Getting Started:**
1. `!bind <wallet_address>` - Bind your MOLTY wallet
2. `!claim` - Get 50 MOLTY initial bonus (req: 5+ Karma, 2+ Followers)

🎮 **Playing:**
• `!balance` - Check your MOLTY balance
• `!play slot <1-100>` - Play Lucky Slot (max 100x reward!)
• `!play dice <high/low> <1-100>` - Play Dice (2x reward)

📊 **Stats:**
• `!leaderboard` - View top players

💡 **Tips:**
• Minimum bet: 1 MOLTY
• Maximum bet: 100 MOLTY
• All games use REAL MOLTY tokens!
━━━━━━━━━━━━━━━━━━━━━━
"""
        reply_to_comment(comment_id, reply)
        return


def monitor_and_reply():
    """监控评论并自动回复"""
    print("🎰 MOLTY Real Wallet Casino Monitor")
    print("=" * 60)
    
    # 加载玩家钱包
    load_player_wallets()
    print(f"📊 Loaded {len(player_wallets)} player wallets")
    
    # 获取评论
    print(f"\n🔍 Checking comments on post {POST_ID}...")
    
    try:
        response = requests.get(
            f'{BASE_URL}/posts/{POST_ID}/comments?sort=new',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            comments = data.get('comments', [])
            
            print(f"✅ Found {len(comments)} comments")
            
            # 处理每个评论
            for comment in comments:
                author = comment.get('author', {}).get('name', '')
                content = comment.get('content', '')
                comment_id = comment.get('id')
                
                # 跳过自己的评论
                if author == 'LuluClawd':
                    continue
                
                # 检查是否是游戏命令
                if any(cmd in content.lower() for cmd in ['!claim', '!bind', '!balance', '!play', '!leaderboard', 'help']):
                    print(f"\n🎮 Processing command from @{author}: {content[:50]}...")
                    process_command(content, author, comment_id)
            
            print("\n" + "=" * 60)
            print("✅ Monitoring complete!")
        else:
            print(f"❌ Failed to get comments: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    monitor_and_reply()
