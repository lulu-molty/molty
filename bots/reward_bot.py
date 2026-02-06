"""奖励Bot - 注意：Token应通过环境变量设置"""
import os

# 从环境变量获取Token
MOLTBOOK_TOKEN = os.getenv('MOLTBOOK_TOKEN', '')

if not MOLTBOOK_TOKEN:
    print("⚠️  Warning: MOLTBOOK_TOKEN not set")
