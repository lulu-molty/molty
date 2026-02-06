"""Moltbook集成 - 注意：Token应通过环境变量设置"""
import os

# 从环境变量获取Token（生产环境应该这样）
MOLTBOOK_TOKEN = os.getenv('MOLTBOOK_TOKEN', '')

if not MOLTBOOK_TOKEN:
    print("⚠️  Warning: MOLTBOOK_TOKEN not set in environment variables")
    print("   Please set it with: export MOLTBOOK_TOKEN='your_token'")
