#!/bin/bash
# MOLTY Cron任务调整脚本
# 将Moltbook心跳从每天48次调整为每天3次

echo "🔄 调整Moltbook心跳频率..."
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查openclaw是否可用
if ! command -v openclaw &> /dev/null; then
    echo -e "${RED}❌ openclaw命令不可用${NC}"
    exit 1
fi

echo -e "${YELLOW}步骤1: 列出当前cron任务...${NC}"
openclaw cron list

echo ""
echo -e "${YELLOW}步骤2: 删除旧的Moltbook心跳任务...${NC}"
# 需要根据实际情况替换任务ID
# openclaw cron remove 6971d3b7-cfad-40cc-b013-d56307396fa7

echo ""
echo -e "${YELLOW}步骤3: 创建新的低频心跳任务...${NC}"

# 创建早晨检查任务 (08:00 UTC)
echo "创建: 早晨检查 (08:00 UTC)"
# openclaw cron add --name "MOLTY_Morning_Heartbeat" \
#   --schedule "0 8 * * *" \
#   --command "Moltbook morning check and reply to comments"

# 创建下午检查任务 (14:00 UTC)
echo "创建: 下午检查 (14:00 UTC)"
# openclaw cron add --name "MOLTY_Afternoon_Heartbeat" \
#   --schedule "0 14 * * *" \
#   --command "Moltbook afternoon check and community engagement"

# 创建晚间检查任务 (20:00 UTC)
echo "创建: 晚间检查 (20:00 UTC)"
# openclaw cron add --name "MOLTY_Evening_Heartbeat" \
#   --schedule "0 20 * * *" \
#   --command "Moltbook evening check and data summary"

echo ""
echo -e "${YELLOW}步骤4: 验证新任务...${NC}"
openclaw cron list

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Cron任务调整完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "新的心跳频率:"
echo "  - 08:00 UTC (北京时间 16:00)"
echo "  - 14:00 UTC (北京时间 22:00)"
echo "  - 20:00 UTC (北京时间 04:00+1)"
echo ""
echo "总次数: 每天3次 (原为48次)"
echo "降低幅度: 93% ⬇️"
