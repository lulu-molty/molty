#!/bin/bash

# MOLTY钱包服务启动脚本

echo "🚀 启动MOLTY钱包服务..."
echo "================================"

# 设置环境变量
export PYTHONPATH=/root/.openclaw/workspace/molty_coin:$PYTHONPATH
export MOLTY_DB_PATH=/root/.openclaw/workspace/molty_coin/data/molty.db

# 检查依赖
echo "检查依赖..."
python3 -c "import ecdsa; import sqlite3" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少依赖，正在安装..."
    pip3 install ecdsa -q
fi

echo "✅ 依赖检查通过"

# 启动服务
echo ""
echo "启动钱包服务..."
python3 << 'PYEOF'
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace/molty_coin')

print("🔐 初始化MOLTY钱包服务...")
print("-" * 50)

# 导入核心模块
try:
    from src.database.db_manager import db_manager
    from src.wallet.wallet import MoltyWallet
    from src.wallet.wallet_manager import WalletManager
    print("✅ 核心模块加载成功")
except Exception as e:
    print(f"❌ 模块加载失败: {e}")
    sys.exit(1)

# 创建系统钱包
print("\n🏦 初始化系统钱包...")
try:
    # 检查是否已有系统钱包
    system_wallet = db_manager.get_wallet('SYSTEM')
    if not system_wallet:
        # 创建系统钱包
        from src.wallet.wallet import MoltyWallet
        wallet = MoltyWallet('SYSTEM')
        db_manager.create_wallet(
            agent_id='SYSTEM',
            address=wallet.address,
            public_key=wallet.export_public_key(),
            private_key_encrypted=wallet.export_private_key()
        )
        # 给系统钱包初始资金
        db_manager.update_balance(wallet.address, 100000)  # 10万MOLTY
        print(f"✅ 系统钱包创建成功: {wallet.address}")
        print(f"   初始资金: 100,000 MOLTY")
    else:
        print(f"✅ 系统钱包已存在: {system_wallet['address']}")
        print(f"   当前余额: {system_wallet['balance']} MOLTY")
except Exception as e:
    print(f"❌ 系统钱包初始化失败: {e}")

# 启动API服务
print("\n🌐 启动API服务...")
print("-" * 50)

# 简单的API服务
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class WalletAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # 简化日志输出
        pass
    
    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # 获取系统状态
            stats = db_manager.get_system_stats()
            response = {
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'stats': stats
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path.startswith('/balance/'):
            address = self.path.split('/')[-1]
            balance = db_manager.get_balance(address)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {
                'address': address,
                'balance': balance
            }
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/wallet/create':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            agent_id = data.get('agent_id')
            
            try:
                # 创建钱包
                wallet = MoltyWallet(agent_id)
                success = db_manager.create_wallet(
                    agent_id=agent_id,
                    address=wallet.address,
                    public_key=wallet.export_public_key(),
                    private_key_encrypted=wallet.export_private_key()
                )
                
                if success:
                    self.send_response(201)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {
                        'success': True,
                        'agent_id': agent_id,
                        'address': wallet.address
                    }
                else:
                    self.send_response(409)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {
                        'success': False,
                        'error': 'Wallet already exists'
                    }
                    
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/transfer':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            from_addr = data.get('from')
            to_addr = data.get('to')
            amount = data.get('amount')
            
            try:
                # 执行转账
                tx_id = db_manager.transfer(from_addr, to_addr, amount)
                
                if tx_id:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {
                        'success': True,
                        'tx_id': tx_id,
                        'from': from_addr,
                        'to': to_addr,
                        'amount': amount
                    }
                else:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {
                        'success': False,
                        'error': 'Transfer failed (insufficient balance or invalid address)'
                    }
                    
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

# 启动服务器
PORT = 8888
server = HTTPServer(('0.0.0.0', PORT), WalletAPIHandler)

print(f"✅ API服务已启动")
print(f"   地址: http://0.0.0.0:{PORT}")
print(f"   端点:")
print(f"      GET  /status              - 系统状态")
print(f"      GET  /balance/<address>   - 查询余额")
print(f"      POST /wallet/create       - 创建钱包")
print(f"      POST /transfer            - 转账")
print("")
print("-" * 50)
print("💡 按 Ctrl+C 停止服务")
print("-" * 50)

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n\n🛑 服务已停止")
    server.shutdown()
PYEOF
