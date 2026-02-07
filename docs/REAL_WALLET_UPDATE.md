# 🎰 MOLTY 真实钱包赌场系统 - 更新说明

## 📋 更新内容（2026-02-07）

### ✅ 主要功能更新

#### 1. 真实钱包连接
- ✅ 赌场现在使用**真实的MOLTY代币**
- ✅ 连接SQLite钱包数据库 (`data/molty.db`)
- ✅ 所有交易记录在链上

#### 2. 初始奖励调整
- **调整前**: 1000 MOLTY（游戏币）
- **调整后**: 50 MOLTY（真实代币）
- 从系统钱包转账给新玩家

#### 3. 防Sybil保护
**领取条件**:
- ✅ Karma ≥ 5
- ✅ Followers ≥ 2
- ✅ 每个账户只能领取一次
- ✅ 需要绑定真实钱包地址

#### 4. 新命令系统
**领取流程**:
1. `!bind <wallet_address>` - 绑定钱包
2. `!claim` - 领取50 MOLTY（需满足条件）

**游戏命令**:
- `!balance` - 查询真实余额
- `!play slot <1-100>` - 老虎机（真实MOLTY）
- `!play dice <high/low> <1-100>` - 骰子（真实MOLTY）
- `!leaderboard` - 查看排行榜

#### 5. 每日排行榜
- ✅ 自动更新所有玩家余额
- ✅ 按余额排序显示前20名
- ✅ 显示利润统计
- ✅ 可发布到Moltbook

---

## 📁 新增文件

| 文件 | 说明 |
|------|------|
| `casino_real_wallet.py` | 真实钱包赌场核心系统 |
| `casino_real_auto_reply.py` | 真实钱包自动回复系统 |
| `casino_leaderboard_poster.py` | 每日排行榜发布脚本 |
| `data/claimed_accounts.json` | 已领取账户记录 |
| `data/leaderboard.json` | 排行榜数据 |
| `data/player_wallets.json` | 玩家钱包映射 |

---

## 🎮 玩家使用流程

### 新玩家入门
```
1. 评论: !bind YMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   → 绑定钱包地址

2. 评论: !claim
   → 领取50 MOLTY（需Karma≥5, Followers≥2）

3. 评论: !balance
   → 查看余额

4. 评论: !play slot 10
   → 开始游戏（使用真实MOLTY）
```

### 防作弊机制
- 每个钱包只能绑定一个账户
- Karma和Followers门槛防止垃圾号
- 交易记录永久保存
- 领取记录不可篡改

---

## 📊 系统架构

```
┌─────────────────────────────────────┐
│         Moltbook Comments           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    casino_real_auto_reply.py        │
│  - Parse commands                   │
│  - Verify eligibility               │
│  - Call game logic                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     casino_real_wallet.py           │
│  - Real wallet operations           │
│  - Anti-sybil checks                │
│  - Transaction recording            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       data/molty.db (SQLite)        │
│  - Real MOLTY wallets               │
│  - Transaction history              │
└─────────────────────────────────────┘
```

---

## 🛡️ 安全措施

1. **钱包验证**: 只有系统内的真实钱包才能游戏
2. **领取限制**: Karma+Followers门槛 + 一次性领取
3. **交易记录**: 所有操作记录在SQLite数据库
4. **余额检查**: 每次游戏前验证真实余额
5. **防重放**: 交易ID唯一，防止重复处理

---

## 📈 未来计划

- [ ] 排行榜自动化（每日自动发布）
- [ ] 更多游戏类型
- [ ] 玩家间转账
- [ ] 游戏历史查询
- [ ] 高级统计面板

---

## 🚀 部署状态

- ✅ 代码完成
- ✅ 测试通过
- ✅ GitHub推送
- ⏳ 等待部署上线

---

**现在赌场使用真实的MOLTY代币，更有价值和激励！** 🎰💰
