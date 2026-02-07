#!/usr/bin/env python3
"""
MOLTY 钱包管理器
创建和管理用户钱包
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime

DB_PATH = '/root/.openclaw/workspace/molty_coin/data/molty.db'

def generate_wallet_address():
    """生成新的MOLTY钱包地址"""
    random_bytes = secrets.token_bytes(30)
    address = 'YM' + hashlib.sha256(random_bytes).hexdigest()[:41]
    return address

def generate_keys():
    """生成密钥对"""
    private_key = secrets.token_hex(32)
    public_key = hashlib.sha256(private_key.encode()).hexdigest()
    return private_key, public_key

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_wallet(username):
    """
    为用户创建新钱包
    
    Returns:
        {
            'success': True/False,
            'address': 钱包地址 (如果成功),
            'message': 提示信息
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查用户是否已有钱包
        cursor.execute("SELECT address FROM wallets WHERE agent_id = ?", (username,))
        existing = cursor.fetchone()
        
        if existing:
            return {
                'success': False,
                'message': f'You already have a wallet: {existing["address"]}',
                'address': existing['address']
            }
        
        # 创建新钱包
        address = generate_wallet_address()
        private_key, public_key = generate_keys()
        
        cursor.execute("""
            INSERT INTO wallets (agent_id, address, public_key, private_key_encrypted, balance, status, created_at)
            VALUES (?, ?, ?, ?, 0.0, 'active', datetime('now'))
        """, (username, address, public_key, private_key))
        
        conn.commit()
        
        return {
            'success': True,
            'address': address,
            'message': 'Wallet created successfully!'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error creating wallet: {str(e)}'
        }
    finally:
        conn.close()

def get_wallet_info(username):
    """获取用户钱包信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT address, balance, created_at 
            FROM wallets 
            WHERE agent_id = ?
        """, (username,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'exists': True,
                'address': result['address'],
                'balance': result['balance'],
                'created_at': result['created_at']
            }
        else:
            return {'exists': False}
            
    except Exception as e:
        return {'exists': False, 'error': str(e)}
    finally:
        conn.close()

def list_all_wallets():
    """列出所有钱包"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT agent_id, address, balance, created_at 
            FROM wallets 
            ORDER BY balance DESC
        """)
        
        return cursor.fetchall()
        
    except Exception as e:
        return []
    finally:
        conn.close()


if __name__ == "__main__":
    print("🎰 MOLTY Wallet Manager")
    print("=" * 60)
    
    # 测试创建钱包
    test_result = create_wallet("test_user")
    print(f"\n测试创建钱包: {test_result}")
    
    # 列出所有钱包
    wallets = list_all_wallets()
    print(f"\n📊 所有钱包 ({len(wallets)}个):")
    for wallet in wallets:
        print(f"   {wallet['agent_id']}: {wallet['address'][:20]}... ({wallet['balance']} MOLTY)")
