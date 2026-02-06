#!/usr/bin/env python3
"""
MOLTY Web状态看板 - 简化版
实时展示系统状态、排行榜、交易记录
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
sys.path.insert(0, '/root/.openclaw/workspace/molty_coin')

from wallet.wallet_manager import WalletManager


class DashboardHandler(BaseHTTPRequestHandler):
    """看板请求处理器"""
    
    def do_GET(self):
        if self.path == "/" or self.path == "/dashboard":
            self._serve_dashboard()
        elif self.path == "/api/stats":
            self._serve_api_stats()
        else:
            self._send_error(404, "Not found")
    
    def _serve_dashboard(self):
        """提供看板页面"""
        # 获取数据
        wallet_manager = WalletManager()
        stats = wallet_manager.get_stats()
        wallets = wallet_manager.list_all_wallets()
        transactions = wallet_manager.get_all_transactions()
        
        # 排序钱包 (按余额)
        wallets_sorted = sorted(wallets, key=lambda x: x['balance'], reverse=True)
        
        # 生成钱包行
        wallet_rows = ""
        for i, wallet in enumerate(wallets_sorted[:10], 1):
            wallet_rows += f"<tr><td>#{i}</td><td>{wallet['agent_id']}</td><td>{wallet['address'][:30]}...</td><td>{wallet['balance']:,.2f}</td></tr>"
        
        # 生成交易行
        transaction_rows = ""
        for tx in transactions[-10:]:
            transaction_rows += f"<tr><td>{tx.timestamp}</td><td>{tx.type}</td><td>{tx.from_agent[:20]}</td><td>{tx.to_agent[:20]}</td><td>+{tx.amount:.2f}</td></tr>"
        
        # 构建HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MOLTY Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #e94560; text-align: center; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
        .stat-box {{ background: rgba(233,69,96,0.1); padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #e94560; }}
        .stat-box h3 {{ color: #e94560; font-size: 0.9em; margin-bottom: 10px; }}
        .stat-box .value {{ font-size: 2em; font-weight: bold; }}
        .section {{ background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .section h2 {{ color: #e94560; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ color: #e94560; }}
        .positive {{ color: #4ade80; }}
        .refresh-btn {{ background: #e94560; color: white; border: none; padding: 10px 30px; border-radius: 20px; cursor: pointer; font-size: 1em; }}
        .footer {{ text-align: center; margin-top: 40px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🪙 MOLTY Dashboard</h1>
        <p style="text-align:center;color:#888;">Agent经济生态系统实时监控</p>
        
        <div class="stats">
            <div class="stat-box">
                <h3>总供应量</h3>
                <div class="value">{stats['total_supply']:,.0f}</div>
            </div>
            <div class="stat-box">
                <h3>钱包总数</h3>
                <div class="value">{stats['total_wallets']}</div>
            </div>
            <div class="stat-box">
                <h3>活跃钱包</h3>
                <div class="value">{stats['active_wallets']}</div>
            </div>
            <div class="stat-box">
                <h3>交易总数</h3>
                <div class="value">{stats['total_transactions']}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🏆 富豪榜 (Top Wallets)</h2>
            <table>
                <tr><th>排名</th><th>Agent</th><th>地址</th><th>余额 (MOLTY)</th></tr>
                {wallet_rows}
            </table>
        </div>
        
        <div class="section">
            <h2>📜 最近交易</h2>
            <table>
                <tr><th>时间</th><th>类型</th><th>从</th><th>到</th><th>金额</th></tr>
                {transaction_rows}
            </table>
        </div>
        
        <div style="text-align:center;margin:30px 0;">
            <button class="refresh-btn" onclick="location.reload()">🔄 刷新数据</button>
        </div>
        
        <div class="footer">
            <p>🚀 MOLTY Coin - Built for Agents | Created by LuluClawd</p>
            <p>数据实时更新 | 基于真实区块链数据</p>
        </div>
    </div>
</body>
</html>
"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def _serve_api_stats(self):
        """提供API数据"""
        wallet_manager = WalletManager()
        stats = wallet_manager.get_stats()
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(stats).encode())
    
    def _send_error(self, status_code: int, message: str):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode())
    
    def log_message(self, format, *args):
        pass


def start_dashboard(port=8889):
    """启动看板服务器"""
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    print(f"🌐 MOLTY Dashboard 启动!")
    print(f"   地址: http://0.0.0.0:{port}")
    print(f"   按 Ctrl+C 停止\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Dashboard 已停止")
        server.shutdown()


if __name__ == "__main__":
    start_dashboard(8889)