#!/bin/bash
# MOLTY MVP 一键启动脚本
# 快速启动所有服务

echo "🚀 MOLTY MVP 启动器"
echo "===================="
echo ""

# 检查Python
echo "📋 检查环境..."
python3 --version || exit 1
pip show ecdsa > /dev/null || pip install ecdsa -q
echo "✅ 环境检查通过"
echo ""

# 创建数据目录
mkdir -p /tmp/molty_data
mkdir -p /tmp/molty_wallets

# 启动API服务（后台）
echo "🟢 启动MOLTY API服务..."
cd /root/.openclaw/workspace/molty_coin
python3 api/server.py &
API_PID=$!
echo "✅ API服务已启动 (PID: $API_PID)"
echo "   地址: http://localhost:8888"
echo ""

# 等待API启动
sleep 2

# 测试API
echo "🧪 测试API..."
curl -s http://localhost:8888/ > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API响应正常"
else
    echo "⚠️ API可能未完全启动，稍等..."
    sleep 2
fi
echo ""

# 显示系统状态
echo "📊 系统状态"
echo "-----------"
curl -s http://localhost:8888/stats | python3 -m json.tool 2>/dev/null || echo "等待API就绪..."
echo ""

# 设置Moltbook集成
echo "🔗 设置Moltbook集成..."
python3 integration/moltbook_integration.py setup
echo ""

# 模拟奖励测试
echo "🎮 运行奖励模拟..."
python3 integration/moltbook_integration.py simulate
echo ""

# 显示操作菜单
echo ""
echo "✨ MOLTY MVP 已启动！"
echo "===================="
echo ""
echo "🌐 API地址: http://localhost:8888"
echo ""
echo "📚 可用API接口:"
echo "  GET  /              - 服务状态"
echo "  GET  /stats         - 系统统计"
echo "  GET  /balance/<id>  - 查询余额"
echo "  POST /wallet/create - 创建钱包"
echo "  POST /reward/post   - 发帖奖励"
echo "  POST /reward/comment- 评论奖励"
echo "  POST /transfer      - 转账"
echo ""
echo "🛠️  快捷命令:"
echo "  测试API: curl http://localhost:8888/stats"
echo "  查看日志: tail -f /tmp/molty_api.log"
echo "  停止服务: kill $API_PID"
echo ""
echo "🚀 现在可以开始使用MOLTY了！"
echo ""

# 保持运行
wait $API_PID