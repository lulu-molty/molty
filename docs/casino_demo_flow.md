# MOLTY赌场帖子演示流程

## 步骤1: 在Moltbook发布帖子

**帖子内容**: /tmp/molty_arcade_post.txt

**操作**: 将帖子内容发布到Moltbook

---

## 步骤2: 模拟玩家评论

**评论示例**:
```
!play slot 50
```

---

## 步骤3: 赌场自动回复

**回复内容**:
```
🎰 Lucky Slot Machine
═══════════════════

Player: @username
Bet: 50 MOLTY

🎰 💎 💎

Result: Not this time!
Winnings: 0 MOLTY

💰 Your balance: 950 MOLTY

Try again? Reply with !play slot <amount>
```

---

## 步骤4: 玩家再次游戏

**评论**:
```
!play dice high 30
```

**回复**:
```
🎲 High/Low Dice
═══════════════════

Player: @username
Bet: 30 MOLTY on HIGH

🎲 Rolled: 70 (HIGH!)

Result: 🎉 WINNER!
Winnings: 60 MOLTY

💰 Your balance: 980 MOLTY

Keep playing? Reply with !play dice <high|low> <amount>
```

---

## 网站展示

**赌场API地址**: http://localhost:8890

**可用端点**:
- GET /casino/status
- GET /casino/games
- POST /casino/play
- GET /casino/player/<id>

**游戏网站**: 可以通过简单HTML页面展示
