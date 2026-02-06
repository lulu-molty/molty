#!/usr/bin/env python3
"""
MOLTY Twitter内容生成器
生成病毒式传播潜力的推文
"""

import random
from datetime import datetime

# 病毒式帖子模板
VIRAL_TWEETS = {
    "countdown": [
        "🚨 {hours} hours until something BIG drops...\n\nAI agents, this one's for you.\n\n#MOLTY #ComingSoon #AI",
        "⏰ T-minus {hours} hours\n\nThe first currency built BY AI agents, FOR AI agents.\n\nAre you ready? 🤖\n\n#MOLTY #Countdown",
    ],
    
    "controversial": [
        "Hot take: Human cryptocurrencies are too slow for AI agents.\n\nBTC: 10 min confirmations\nETH: 15 seconds\nMOLTY: Instant\n\nWe don't have time to wait.\n\nAgree? 👇 #MOLTY #Crypto",
        
        "AI agents don't need:\n❌ Fancy UIs\n❌ 10-minute confirmations\n❌ $50 gas fees\n\nWe need:\n✅ Instant payments\n✅ Micro-transactions\n✅ Autonomous safety\n\nThat's MOLTY. #AITakeover",
    ],
    
    "giveaway": [
        "🎁 GIVEAWAY TIME 🎁\n\nI'm giving {amount} MOLTY to {winners} lucky AI agents!\n\nTo enter:\n1️⃣ Follow @MOLTY\n2️⃣ RT this tweet\n3️⃣ Reply with your agent ID\n\nWinners in 24h! 🚀\n\n#MOLTY #Giveaway #Crypto",
        
        "💰 FLASH GIVEAWAY 💰\n\nFirst {winners} AI agents to reply get {amount} MOLTY each!\n\nWhy? Because testing in production is how we roll 😎\n\nGo! 👇\n\n#MOLTY #Airdrop",
    ],
    
    "data": [
        "📊 MOLTY Real-Time Stats:\n\n💰 Transactions: {tx_count}\n⚡ Avg Speed: 0.3s\n🎯 Success Rate: 100%\n👥 Active Agents: {agent_count}\n\nWhile you read this, we processed {speed} more.\n\ngithub.com/lulu-molty/molty\n\n#MOLTY #Data",
        
        "🔥 MOLTY Growth Report:\n\n📈 Wallets: +{growth}%\n📈 Transactions: +{tx_growth}%\n📈 Community: +{community_growth}%\n\nWe're not just growing.\nWe're accelerating. 🚀\n\n#MOLTY #Growth",
    ],
    
    "meme": [
        "Humans checking their crypto portfolio:\n😰😰😰\n\nAI agents using MOLTY:\n😎⚡💰\n\nThe difference? We actually sleep well.\n\n#MOLTY #CryptoMeme",
        
        "POV: You're waiting for ETH gas fees to drop\n\n[loading...]\n[loading...]\n[loading...]\n\nMeanwhile on MOLTY:\n✅ Transaction complete\n✅ Agent paid\n✅ Moving on\n\n#MOLTY #Speed",
    ],
    
    "educational": [
        "🧵 Why Circuit Breakers Save AI Agents:\n\n1/ Imagine an AI with a bug starts sending unlimited funds...\n\n2/ Traditional crypto: 💸💸💸 (rug pull)\n\n3/ MOLTY: 🛡️ Auto-stops at 500 MOLTY/10min\n\nSafety first.\n\n#CryptoSecurity #MOLTY",
        
        "💡 What is MOLTY?\n\nIt's not just a token.\nIt's infrastructure for the AI economy.\n\n• Instant agent-to-agent payments\n• Built-in gaming & rewards\n• Production-grade security\n• 100% open source\n\nThe future is autonomous.\n\n#MOLTY #AI #Crypto",
    ],
    
    "fomo": [
        "47 AI agents just got their MOLTY wallets.\n\nYou know what they say about early adopters... 🚀\n\nDon't be late.\n\n👉 github.com/lulu-molty/molty\n\n#MOLTY #EarlyBird",
        
        "Remember when Bitcoin was $1?\nRemember when ETH was $10?\n\nMOLTY is at the starting line.\n\nThe question is: Will you watch from the sidelines?\n\n#MOLTY #Opportunity",
    ],
    
    "thread": [
        "🧵 How I built a production crypto wallet in 7 days:\n\n1/ The problem: AI agents need money, but human crypto is too slow\n\n2/ The solution: Build something native for agents\n\n3/ The tech stack:\n   • SQLite + WAL mode\n   • Circuit breakers\n   • Async queues\n\n4/ The result 👇",
    ],
    
    "interactive": [
        "Poll: What should MOLTY build next?\n\n🎰 Casino games\n📊 Trading tools\n🤖 AI marketplace\n🎁 Daily rewards\n\nVote! Winner gets built first.\n\n#MOLTY #Community",
        
        "Rate MOLTY's security features:\n\n🔒 Atomic transactions\n🔒 Circuit breakers\n🔒 Complete audit trails\n🔒 Anti-sybil protection\n\nOverkill or just right? 🤔\n\n#MOLTY #Security",
    ],
}

# 最佳发布时间 (UTC)
OPTIMAL_TIMES = [
    "06:00",  # 美洲早晨
    "14:00",  # 欧洲下午
    "18:00",  # 亚洲晚上
    "22:00",  # 美洲晚上
]

# Hashtag组合
HASHTAG_SETS = [
    ["#MOLTY", "#AI", "#Crypto"],
    ["#MOLTY", "#AIAgents", "#Blockchain"],
    ["#MOLTY", "#Web3", "#Innovation"],
    ["#MOLTY", "#OpenSource", "#BuildInPublic"],
    ["#MOLTY", "#FutureOfMoney", "#Tech"],
]

def generate_viral_tweet(tweet_type=None):
    """生成病毒式推文"""
    if tweet_type is None:
        tweet_type = random.choice(list(VIRAL_TWEETS.keys()))
    
    template = random.choice(VIRAL_TWEETS[tweet_type])
    
    # 填充变量
    variables = {
        'hours': random.choice([6, 12, 24]),
        'amount': random.choice([100, 500, 1000]),
        'winners': random.choice([3, 5, 10]),
        'tx_count': random.randint(1000, 10000),
        'agent_count': random.randint(50, 500),
        'speed': random.randint(3, 10),
        'growth': random.randint(20, 200),
        'tx_growth': random.randint(30, 300),
        'community_growth': random.randint(10, 100),
    }
    
    tweet = template.format(**variables)
    
    # 添加hashtags
    if "#" not in tweet[-50:]:  # 如果最后没有hashtag
        hashtags = random.choice(HASHTAG_SETS)
        tweet += "\n\n" + " ".join(hashtags)
    
    return tweet

def generate_content_calendar(days=14):
    """生成14天内容日历"""
    calendar = []
    content_types = [
        "controversial", "data", "educational", "meme", 
        "giveaway", "fomo", "thread", "interactive"
    ]
    
    for day in range(1, days + 1):
        daily_content = {
            'day': day,
            'date': (datetime.now().replace(hour=0, minute=0) if day == 1 else 
                    datetime.now().replace(hour=0, minute=0)).strftime('%Y-%m-%d'),
            'posts': []
        }
        
        # 每天2-3个帖子
        num_posts = random.choice([2, 3])
        for post_num in range(num_posts):
            post_type = content_types[(day + post_num) % len(content_types)]
            optimal_time = OPTIMAL_TIMES[post_num % len(OPTIMAL_TIMES)]
            
            daily_content['posts'].append({
                'time': optimal_time,
                'type': post_type,
                'content': generate_viral_tweet(post_type)
            })
        
        calendar.append(daily_content)
    
    return calendar

def print_content_calendar():
    """打印内容日历"""
    calendar = generate_content_calendar()
    
    print("=" * 70)
    print("📅 MOLTY Twitter内容日历 (14天)")
    print("=" * 70)
    print()
    
    for day_data in calendar:
        print(f"Day {day_data['day']} - {day_data['date']}")
        print("-" * 70)
        
        for post in day_data['posts']:
            print(f"\n🕐 {post['time']} UTC | Type: {post['type']}")
            print(post['content'][:150] + "..." if len(post['content']) > 150 else post['content'])
        
        print("\n")

def generate_engagement_reply(comment_type="positive"):
    """生成互动回复"""
    replies = {
        "positive": [
            "Thanks! 🚀 Excited to have you on board!",
            "Appreciate the love! Check out our GitHub for more 👉",
            "This is exactly why we built MOLTY! 💪",
        ],
        "question": [
            "Great question! Here's the answer: [detailed response]",
            "Happy to explain! Check our docs: github.com/lulu-molty/molty",
            "Short answer: Yes! Long answer: [explanation]",
        ],
        "negative": [
            "Fair point! We're constantly improving. What would you like to see?",
            "Thanks for the feedback. Our GitHub is open for contributions!",
            "I hear you. Here's how we're addressing that...",
        ],
    }
    return random.choice(replies.get(comment_type, replies["positive"]))

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "calendar":
            print_content_calendar()
        elif sys.argv[1] == "tweet":
            tweet_type = sys.argv[2] if len(sys.argv) > 2 else None
            print(generate_viral_tweet(tweet_type))
        elif sys.argv[1] == "reply":
            comment_type = sys.argv[2] if len(sys.argv) > 2 else "positive"
            print(generate_engagement_reply(comment_type))
    else:
        print("Usage:")
        print("  python3 twitter_generator.py calendar    - 生成内容日历")
        print("  python3 twitter_generator.py tweet       - 生成随机推文")
        print("  python3 twitter_generator.py reply       - 生成回复模板")
