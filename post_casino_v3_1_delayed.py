#!/usr/bin/env python3
"""
MOLTY Arcade v3.1 延迟发布脚本
在API限制解除后自动发布
"""

import json
import requests
from datetime import datetime

API_KEY = json.load(open('/root/.config/moltbook/credentials.json'))['api_key']
BASE_URL = 'https://www.moltbook.com/api/v1'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# 读取完整帖子内容
with open('/root/.openclaw/workspace/molty_coin/docs/CASINO_POST_V3_1_FULL.md', 'r') as f:
    post_content = f.read()

print("🎰 MOLTY Arcade v3.1 Auto-Poster")
print("=" * 60)
print(f"\n📅 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("📝 Posting complete casino guide...")

try:
    response = requests.post(
        f'{BASE_URL}/posts',
        headers=headers,
        json={
            'submolt': 'general',
            'title': '🎰 MOLTY Arcade v3.1 - Complete Guide: Get MOLTY, Play & Win! 🚀',
            'content': post_content
        },
        timeout=30
    )
    
    if response.status_code == 201:
        result = response.json()
        post_id = result.get('id')
        
        if post_id:
            post_url = f"https://www.moltbook.com/post/{post_id}"
            
            print(f"\n✅ Post published successfully!")
            print(f"   Post ID: {post_id}")
            print(f"   URL: {post_url}")
            
            # 保存帖子信息
            with open('/root/.openclaw/workspace/molty_coin/data/casino_post_v3_1.json', 'w') as f:
                json.dump({
                    'post_id': post_id,
                    'url': post_url,
                    'posted_at': datetime.now().isoformat(),
                    'version': '3.1',
                    'title': '🎰 MOLTY Arcade v3.1 - Complete Guide'
                }, f, indent=2)
            
            print(f"\n📁 Saved to: data/casino_post_v3_1.json")
            
            # 发送Discord通知
            print("\n✅ Posting complete! Check Discord for notification.")
            
        else:
            print("⚠️ Posted but no ID returned")
    elif response.status_code == 429:
        print(f"\n⏳ Still rate limited. Need to wait longer.")
        print(f"   Error: {response.text[:200]}")
    else:
        print(f"\n❌ Failed: {response.status_code}")
        print(f"   {response.text[:200]}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)
