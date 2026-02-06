#!/usr/bin/env python3
"""
MOLTY API服务
提供RESTful接口供Moltbook和其他服务调用
快速MVP版本 - 简化实现
"""

import json
import time
from typing import Dict, List
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
sys.path.append('/root/.openclaw/workspace/molty_coin')

from core.blockchain import Blockchain, Transaction
from wallet.wallet import MoltyWallet
from consensus.pov import PoVConsensus

# 全局实例
blockchain = Blockchain()
pov_consensus = PoVConsensus(min_votes=2, approval_threshold=0.5)  # MVP简化
wallets: Dict[str, MoltyWallet] = {}
agent_balances: Dict[str, float] = {}  # MVP简化版：内存存储

# 初始化系统钱包
system_wallet = MoltyWallet("molty_system")
wallets["molty_system"] = system_wallet

class MoltyAPIHandler(BaseHTTPRequestHandler):
    """MOLTY API请求处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        path = self.path
        
        if path == "/":
            self._send_response({"status": "ok", "service": "MOLTY API", "version": "1.0.0"})
        
        elif path == "/stats":
            self._handle_stats()
        
        elif path.startswith("/balance/"):
            agent_id = path.split("/")[-1]
            self._handle_get_balance(agent_id)
        
        elif path.startswith("/wallet/"):
            agent_id = path.split("/")[-1]
            self._handle_get_wallet(agent_id)
        
        elif path == "/pending":
            self._handle_pending_contents()
        
        else:
            self._send_error(404, "Not found")
    
    def do_POST(self):
        """处理POST请求"""
        path = self.path
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            data = json.loads(post_data)
        except:
            self._send_error(400, "Invalid JSON")
            return
        
        if path == "/wallet/create":
            self._handle_create_wallet(data)
        
        elif path == "/content/submit":
            self._handle_submit_content(data)
        
        elif path == "/vote":
            self._handle_vote(data)
        
        elif path == "/reward/post":
            self._handle_reward_post(data)
        
        elif path == "/reward/comment":
            self._handle_reward_comment(data)
        
        elif path == "/transfer":
            self._handle_transfer(data)
        
        else:
            self._send_error(404, "Not found")
    
    def _send_response(self, data: Dict, status_code=200):
        """发送成功响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_error(self, status_code: int, message: str):
        """发送错误响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())
    
    def _handle_stats(self):
        """获取系统统计"""
        stats = {
            "total_supply": sum(agent_balances.values()),
            "total_agents": len(agent_balances),
            "pending_contents": len(pov_consensus.get_pending_contents()),
            "block_count": len(blockchain.chain),
            "system_status": "running"
        }
        self._send_response(stats)
    
    def _handle_get_balance(self, agent_id: str):
        """获取Agent余额"""
        balance = agent_balances.get(agent_id, 0)
        self._send_response({
            "agent_id": agent_id,
            "balance": balance,
            "currency": "MOLTY"
        })
    
    def _handle_get_wallet(self, agent_id: str):
        """获取钱包信息"""
        if agent_id not in wallets:
            self._send_error(404, "Wallet not found")
            return
        
        wallet = wallets[agent_id]
        self._send_response(wallet.to_dict())
    
    def _handle_create_wallet(self, data: Dict):
        """创建钱包"""
        agent_id = data.get("agent_id")
        if not agent_id:
            self._send_error(400, "agent_id required")
            return
        
        if agent_id in wallets:
            self._send_response({
                "status": "exists",
                "wallet": wallets[agent_id].to_dict()
            })
            return
        
        wallet = MoltyWallet(agent_id)
        wallets[agent_id] = wallet
        agent_balances[agent_id] = 0
        
        self._send_response({
            "status": "created",
            "wallet": wallet.to_dict()
        })
    
    def _handle_submit_content(self, data: Dict):
        """提交内容赚MOLTY"""
        agent_id = data.get("agent_id")
        content = data.get("content")
        content_type = data.get("type", "post")
        
        if not agent_id or not content:
            self._send_error(400, "agent_id and content required")
            return
        
        # 提交到PoV
        result = pov_consensus.submit_content(content, agent_id, content_type)
        
        self._send_response({
            "status": "submitted",
            "content_hash": result["content_hash"],
            "value_score": result["value_assessment"]["final_value"],
            "estimated_reward": result["estimated_reward"],
            "message": "Content submitted for verification"
        })
    
    def _handle_vote(self, data: Dict):
        """投票"""
        content_hash = data.get("content_hash")
        voter_id = data.get("voter_id")
        approve = data.get("approve", True)
        
        if not content_hash or not voter_id:
            self._send_error(400, "content_hash and voter_id required")
            return
        
        result = pov_consensus.vote(content_hash, voter_id, approve)
        
        # 如果达成共识且通过，发放奖励
        if result.get("consensus_reached") and result.get("approved"):
            content_data = pov_consensus.pending_content.get(content_hash)
            if content_data:
                creator_id = content_data["creator_id"]
                reward = result["reward"]
                agent_balances[creator_id] = agent_balances.get(creator_id, 0) + reward
        
        self._send_response(result)
    
    def _handle_reward_post(self, data: Dict):
        """Moltbook发帖奖励（简化版）"""
        agent_id = data.get("agent_id")
        post_id = data.get("post_id")
        content_length = data.get("content_length", 0)
        
        if not agent_id:
            self._send_error(400, "agent_id required")
            return
        
        # 简化版奖励计算
        base_reward = 10
        length_bonus = min(content_length / 1000, 10)  # 最多10分
        total_reward = base_reward + length_bonus
        
        # 发放奖励
        agent_balances[agent_id] = agent_balances.get(agent_id, 0) + total_reward
        
        self._send_response({
            "status": "rewarded",
            "agent_id": agent_id,
            "post_id": post_id,
            "reward": total_reward,
            "new_balance": agent_balances[agent_id],
            "message": f"Earned {total_reward} MOLTY for posting!"
        })
    
    def _handle_reward_comment(self, data: Dict):
        """Moltbook评论奖励（简化版）"""
        agent_id = data.get("agent_id")
        comment_id = data.get("comment_id")
        
        if not agent_id:
            self._send_error(400, "agent_id required")
            return
        
        # 评论固定奖励
        reward = 2
        agent_balances[agent_id] = agent_balances.get(agent_id, 0) + reward
        
        self._send_response({
            "status": "rewarded",
            "agent_id": agent_id,
            "comment_id": comment_id,
            "reward": reward,
            "new_balance": agent_balances[agent_id],
            "message": f"Earned {reward} MOLTY for commenting!"
        })
    
    def _handle_transfer(self, data: Dict):
        """转账"""
        from_agent = data.get("from")
        to_agent = data.get("to")
        amount = data.get("amount", 0)
        
        if not from_agent or not to_agent:
            self._send_error(400, "from and to required")
            return
        
        if amount <= 0:
            self._send_error(400, "amount must be positive")
            return
        
        # 检查余额
        if agent_balances.get(from_agent, 0) < amount:
            self._send_error(400, "Insufficient balance")
            return
        
        # 执行转账
        agent_balances[from_agent] -= amount
        agent_balances[to_agent] = agent_balances.get(to_agent, 0) + amount
        
        self._send_response({
            "status": "transferred",
            "from": from_agent,
            "to": to_agent,
            "amount": amount,
            "from_balance": agent_balances[from_agent],
            "to_balance": agent_balances[to_agent]
        })
    
    def _handle_pending_contents(self):
        """获取待验证内容"""
        pending = pov_consensus.get_pending_contents()
        self._send_response({
            "pending_count": len(pending),
            "contents": pending
        })
    
    def log_message(self, format, *args):
        """简化日志输出"""
        pass  # 减少输出噪音


def start_api_server(port=8888):
    """启动API服务器"""
    server = HTTPServer(('0.0.0.0', port), MoltyAPIHandler)
    print(f"🚀 MOLTY API服务启动!")
    print(f"📡 地址: http://0.0.0.0:{port}")
    print(f"📚 可用接口:")
    print(f"   GET  /              - 服务状态")
    print(f"   GET  /stats         - 系统统计")
    print(f"   GET  /balance/<id>  - 查询余额")
    print(f"   POST /wallet/create - 创建钱包")
    print(f"   POST /reward/post   - 发帖奖励")
    print(f"   POST /reward/comment - 评论奖励")
    print(f"\n按 Ctrl+C 停止服务\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        server.shutdown()


if __name__ == "__main__":
    start_api_server(8888)