#!/usr/bin/env python3
"""
MOLTY钱包服务管理工具
Usage: python3 wallet_cli.py <command>
"""

import sys
import os
import json
import requests

# API基础URL
API_BASE = "http://localhost:8888"

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def cmd_status():
    """查看服务状态"""
    print_header("服务状态")
    try:
        resp = requests.get(f"{API_BASE}/status")
        data = resp.json()
        
        print(f"✅ 服务状态: {data['status']}")
        print(f"📅 系统时间: {data['timestamp']}")
        print(f"📦 版本: {data['version']}")
        print(f"\n📊 系统统计:")
        stats = data['stats']
        print(f"   钱包总数: {stats['wallet_count']}")
        print(f"   总供应量: {stats['total_supply']:,.2f} MOLTY")
        print(f"   交易总数: {stats['transaction_count']}")
        print(f"   今日交易: {stats['today_transaction_count']}")
    except Exception as e:
        print(f"❌ 获取状态失败: {e}")

def cmd_balance(address):
    """查询余额"""
    print_header(f"查询余额: {address}")
    try:
        resp = requests.get(f"{API_BASE}/balance/{address}")
        data = resp.json()
        print(f"📍 地址: {data['address']}")
        print(f"💰 余额: {data['balance']:,.2f} MOLTY")
    except Exception as e:
        print(f"❌ 查询失败: {e}")

def cmd_create(agent_id):
    """创建钱包"""
    print_header(f"创建钱包: {agent_id}")
    try:
        resp = requests.post(
            f"{API_BASE}/wallet/create",
            json={"agent_id": agent_id}
        )
        data = resp.json()
        
        if data.get('success'):
            print(f"✅ 钱包创建成功!")
            print(f"   Agent ID: {data['agent_id']}")
            print(f"   地址: {data['address']}")
        else:
            print(f"❌ 创建失败: {data.get('error')}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def cmd_transfer(from_addr, to_addr, amount):
    """转账"""
    print_header("转账")
    try:
        amount = float(amount)
        resp = requests.post(
            f"{API_BASE}/transfer",
            json={
                "from": from_addr,
                "to": to_addr,
                "amount": amount
            }
        )
        data = resp.json()
        
        if data.get('success'):
            print(f"✅ 转账成功!")
            print(f"   交易ID: {data['tx_id']}")
            print(f"   从: {data['from']}")
            print(f"   到: {data['to']}")
            print(f"   金额: {data['amount']} MOLTY")
        else:
            print(f"❌ 转账失败: {data.get('error')}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def cmd_help():
    """显示帮助"""
    print_header("MOLTY钱包CLI工具")
    print("""
使用方法: python3 wallet_cli.py <命令> [参数]

命令:
  status                          查看服务状态
  balance <address>               查询余额
  create <agent_id>               创建新钱包
  transfer <from> <to> <amount>   转账
  help                            显示帮助

示例:
  python3 wallet_cli.py status
  python3 wallet_cli.py balance YM6695A8ir9sGBUAkHLFXBZDWQghDuJ125
  python3 wallet_cli.py create my_user
  python3 wallet_cli.py transfer ADDR1 ADDR2 100
""")

def main():
    if len(sys.argv) < 2:
        cmd_help()
        return
    
    command = sys.argv[1]
    
    if command == "status":
        cmd_status()
    elif command == "balance":
        if len(sys.argv) < 3:
            print("❌ 请提供地址")
            return
        cmd_balance(sys.argv[2])
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ 请提供Agent ID")
            return
        cmd_create(sys.argv[2])
    elif command == "transfer":
        if len(sys.argv) < 5:
            print("❌ 请提供发送方、接收方和金额")
            return
        cmd_transfer(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == "help":
        cmd_help()
    else:
        print(f"❌ 未知命令: {command}")
        cmd_help()

if __name__ == "__main__":
    main()