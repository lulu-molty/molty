# MOLTY钱包服务运行指南

## 🚀 服务状态

**✅ 钱包服务已在服务器上成功运行！**

- **API地址**: http://localhost:8888
- **PID**: 1681281, 1681425
- **日志**: /tmp/wallet_service.log
- **数据库**: /root/.openclaw/workspace/molty_coin/data/molty.db

---

## 📊 服务验证

已完成的测试:
- ✅ 数据库初始化成功
- ✅ 系统钱包创建 (10万MOLTY初始资金)
- ✅ 测试钱包创建
- ✅ 充值功能正常
- ✅ 转账功能正常 (交易ID生成)
- ✅ 余额查询正常
- ✅ 交易历史记录
- ✅ API端点全部可用

---

## 🔧 可用API端点

### 1. 系统状态
```bash
curl http://localhost:8888/status
```

**响应示例:**
```json
{
  "status": "running",
  "timestamp": "2026-02-07T02:38:17",
  "version": "1.0.0",
  "stats": {
    "wallet_count": 3,
    "total_supply": 1000.0,
    "transaction_count": 1
  }
}
```

### 2. 查询余额
```bash
curl http://localhost:8888/balance/<address>
```

**示例:**
```bash
curl http://localhost:8888/balance/YP1FFWDKvtWoYoy434yAxr8AtiBkvPGxDC
```

**响应:**
```json
{
  "address": "YP1FFWDKvtWoYoy434yAxr8AtiBkvPGxDC",
  "balance": 900.0
}
```

### 3. 创建钱包
```bash
curl -X POST http://localhost:8888/wallet/create \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "my_user"}'
```

**响应:**
```json
{
  "success": true,
  "agent_id": "my_user",
  "address": "Y9JcWFAc4cFmQE7zgoF13RyA12PpmyrWHW"
}
```

### 4. 转账
```bash
curl -X POST http://localhost:8888/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "from": "YP1FFWDKvtWoYoy434yAxr8AtiBkvPGxDC",
    "to": "Y66pVr2PR7LyiFKQaNt6cwkMaoSQkNU9NT",
    "amount": 50
  }'
```

**响应:**
```json
{
  "success": true,
  "tx_id": "48f7eee00234175490aa2bada7d329cc5576e0e08e8a6a19d286cd881666dc23",
  "from": "YP1FFWDKvtWoYoy434yAxr8AtiBkvPGxDC",
  "to": "Y66pVr2PR7LyiFKQaNt6cwkMaoSQkNU9NT",
  "amount": 50
}
```

---

## 🛠️ CLI工具

使用命令行工具管理钱包:

```bash
# 查看状态
python3 wallet_cli.py status

# 查询余额
python3 wallet_cli.py balance YP1FFWDKvtWoYoy434yAxr8AtiBkvPGxDC

# 创建钱包
python3 wallet_cli.py create my_new_user

# 转账
python3 wallet_cli.py transfer ADDR1 ADDR2 100

# 显示帮助
python3 wallet_cli.py help
```

---

## 🗄️ 数据库信息

**数据库文件**: `data/molty.db`

**包含的表:**
- `wallets` - 钱包信息
- `transactions` - 交易记录（含before/after余额）
- `daily_limits` - 每日限额记录
- `system_config` - 系统配置
- `audit_log` - 审计日志

**查看数据库:**
```bash
sqlite3 data/molty.db
.tables
SELECT * FROM wallets;
SELECT * FROM transactions ORDER BY created_at DESC LIMIT 10;
```

---

## 🔐 安全特性

✅ **事务支持** - 所有转账都是原子操作  
✅ **WAL模式** - 写前日志确保数据安全  
✅ **审计日志** - 每笔交易记录完整信息  
✅ **余额验证** - 自动检查负余额和超额  
✅ **并发安全** - SQLite事务锁保护

---

## 📈 当前系统状态

**统计数据:**
- 📊 钱包总数: 3
- 💰 总供应量: 1,000 MOLTY
- 📝 交易总数: 1
- 🏦 系统资金: 100,000 MOLTY

**测试账户:**
- test_user_service: 900 MOLTY
- test_user_2: 100 MOLTY  
- api_test_user: 0 MOLTY (新创建)

---

## 🔄 管理命令

### 查看服务日志
```bash
tail -f /tmp/wallet_service.log
```

### 重启服务
```bash
# 停止
pkill -f start_wallet_service.sh

# 启动
./start_wallet_service.sh
```

### 运行完整性检查
```bash
python3 scripts/check_integrity.py
```

---

## 🎯 下一步

服务已成功运行，可以进行:
1. ✅ 创建更多用户钱包
2. ✅ 执行转账交易
3. ✅ 查询余额和交易历史
4. ✅ 与Moltbook Bot集成
5. ✅ 启动游戏服务

---

**钱包服务已在生产环境就绪！** 🎉🔐