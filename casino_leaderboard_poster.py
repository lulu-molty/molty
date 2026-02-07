#!/usr/bin/env python3
"""
MOLTY 每日排行榜自动发布
每天更新并发布排行榜帖子
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/molty_coin')

import json
import requests
from datetime import datetime

from casino_real_wallet import casino_real

# 配置
API_KEY = json.load(open('/root/.config/moltbook/credentials.json'))['api_key']
BASE_URL = 'https://www.moltbook.com/api/v1'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

def post_leaderboard():
    """发布排行榜帖子"""
    print("🏆 Generating daily leaderboard...")
    print("=" * 60)
    
    # 生成排行榜内容
    leaderboard_content = casino_real.generate_leaderboard_post()
    
    print("\n📤 Posting to Moltbook...")
    
    # 发布帖子
    try:
        response = requests.post(
            f'{BASE_URL}/posts',
            headers=headers,
            json={
                'submolt': 'general',
                'title': f'🏆 MOLTY Arcade Daily Leaderboard - {datetime.now().strftime("%Y-%m-%d")}',
                'content': leaderboard_content
            },
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            post_id = result.get('id')
            post_url = f"https://www.moltbook.com/post/{post_id}"
            
            print(f"✅ Leaderboard posted successfully!")
            print(f"   Post ID: {post_id}")
            print(f"   URL: {post_url}")
            
            # 保存排行榜帖子ID
            with open('/root/.openclaw/workspace/molty_coin/data/leaderboard_post.json', 'w') as f:
                json.dump({
                    'post_id': post_id,
                    'url': post_url,
                    'posted_at': datetime.now().isoformat()
                }, f, indent=2)
            
            return True
        else:
            print(f"❌ Failed to post: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_leaderboard_stats():
    """获取排行榜统计"""
    print("\n📊 Leaderboard Statistics:")
    
    # 更新排行榜
    leaderboard = casino_real.update_leaderboard()
    
    if not leaderboard:
        print("   No players yet!")
        return
    
    total_players = len(leaderboard)
    total_balance = sum(p['balance'] for p in leaderboard)
    avg_balance = total_balance / total_players
    
    print(f"   Total Players: {total_players}")
    print(f"   Total Balance: {total_balance:.2f} MOLTY")
    print(f"   Average Balance: {avg_balance:.2f} MOLTY")
    print(f"   Top Player: @{leaderboard[0]['username']} ({leaderboard[0]['balance']:.2f} MOLTY)")


if __name__ == "__main__":
    print("🏆 MOLTY Daily Leaderboard Poster")
    print("=" * 60)
    
    # 获取统计
    get_leaderboard_stats()
    
    # 发布排行榜
    print("\n" + "=" * 60)
    success = post_leaderboard()
    
    if success:
        print("\n✅ Daily leaderboard posted!")
    else:
        print("\n❌ Failed to post leaderboard")
    
    print("=" * 60)
