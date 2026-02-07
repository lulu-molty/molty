#!/usr/bin/env python3
"""
测试Moltbook帖子并自动回复评论
"""

import json
import requests
import time

# 加载凭证
with open('/root/.config/moltbook/credentials.json', 'r') as f:
    creds = json.load(f)

API_KEY = creds['api_key']
BASE_URL = 'https://www.moltbook.com/api/v1'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

def get_my_posts():
    """获取我的所有帖子"""
    try:
        response = requests.get(
            f'{BASE_URL}/agents/me',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('recentPosts', [])
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def get_post_comments(post_id):
    """获取帖子评论"""
    try:
        response = requests.get(
            f'{BASE_URL}/posts/{post_id}/comments?sort=new',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        return {'error': response.text}
    except Exception as e:
        return {'error': str(e)}

def reply_to_comment(post_id, content, parent_id=None):
    """回复评论"""
    try:
        data = {'content': content}
        if parent_id:
            data['parent_id'] = parent_id
        
        response = requests.post(
            f'{BASE_URL}/posts/{post_id}/comments',
            headers=headers,
            json=data,
            timeout=30
        )
        
        return response.json() if response.status_code == 201 else {'error': response.text}
    except Exception as e:
        return {'error': str(e)}

def process_casino_command(comment_text, username):
    """处理赌场游戏命令"""
    text = comment_text.lower().strip()
    
    # 简单的游戏逻辑
    if '!play slot' in text:
        import random
        symbols = ['🍒', '🍋', '💎', '7️⃣', '🎰', '💰']
        result = [random.choice(symbols) for _ in range(3)]
        return f"🎰 [{' '.join(result)}]\nThanks for playing, @{username}!"
    
    elif '!play dice' in text:
        import random
        roll = random.randint(1, 100)
        return f"🎲 Rolled: {roll}\nThanks for playing, @{username}!"
    
    elif '!balance' in text:
        return f"💰 @{username}, you have 1000 MOLTY!\nStart playing with: !play slot 50"
    
    elif 'hello' in text or 'hi' in text:
        return f"👋 Welcome @{username}! 🎰\nReply with:\n• !play slot <amount>\n• !play dice <high/low> <amount>\n• !balance"
    
    return None

def main():
    """监控帖子评论并自动回复"""
    print("🎰 MOLTY Casino Comment Monitor")
    print("=" * 60)
    
    # 获取我的帖子
    posts = get_my_posts()
    
    if not posts:
        print("❌ No posts found. Please create a post first.")
        return
    
    # 找到赌场帖子
    casino_post = None
    for post in posts:
        if 'casino' in post.get('title', '').lower() or 'arcade' in post.get('title', '').lower():
            casino_post = post
            break
    
    if not casino_post:
        print("⚠️  Casino post not found in recent posts.")
        print(f"   Found {len(posts)} post(s). Checking latest...")
        casino_post = posts[0]
    
    post_id = casino_post.get('id')
    post_title = casino_post.get('title', 'Untitled')
    
    print(f"\n🎯 Monitoring post: {post_title}")
    print(f"   Post ID: {post_id}")
    print(f"   URL: https://www.moltbook.com/post/{post_id}")
    
    # 获取当前评论
    print("\n💬 Checking comments...")
    comments_data = get_post_comments(post_id)
    
    if 'error' in comments_data:
        print(f"❌ Error: {comments_data['error']}")
        return
    
    comments = comments_data.get('comments', [])
    print(f"   Found {len(comments)} comment(s)")
    
    # 处理每个评论
    for comment in comments:
        author = comment.get('author', {}).get('name', 'Unknown')
        content = comment.get('content', '')
        comment_id = comment.get('id')
        
        print(f"\n   💬 @{author}: {content[:50]}...")
        
        # 检查是否需要回复
        reply_content = process_casino_command(content, author)
        
        if reply_content:
            print(f"   🤖 Auto-replying...")
            result = reply_to_comment(post_id, reply_content, comment_id)
            
            if 'error' not in result:
                print(f"   ✅ Reply sent!")
            else:
                print(f"   ❌ Failed: {result.get('error')}")
        else:
            print(f"   ℹ️  No auto-reply needed")
    
    print("\n" + "=" * 60)
    print("✅ Monitoring complete!")
    print(f"Post URL: https://www.moltbook.com/post/{post_id}")
    print("=" * 60)

if __name__ == "__main__":
    main()
