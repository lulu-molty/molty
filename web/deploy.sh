#!/bin/bash
# 部署赌场Web界面

# 检查是否有public IP
IP=$(curl -s ifconfig.me)
echo "🌐 公共IP: $IP"

# 启动HTTP服务器
python3 -m http.server 8890 --bind 0.0.0.0 &
PID=$!
echo "✅ 服务器已启动 PID: $PID"
echo "🔗 访问地址: http://$IP:8890/casino.html"

# 保存PID
echo $PID > /tmp/casino_server.pid
