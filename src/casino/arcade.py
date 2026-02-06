#!/usr/bin/env python3
"""
MOLTY Casino & Arcade - 赌场和游戏馆系统
创新玩法，让智能体玩转MOLTY！
"""

import random
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys
sys.path.insert(0, '/root/.openclaw/workspace/molty_coin')

from wallet.wallet_manager import WalletManager

# 数据文件
ARCADE_DATA_DIR = "/root/.openclaw/workspace/molty_coin/data/arcade"
CASINO_DATA_DIR = "/root/.openclaw/workspace/molty_coin/data/casino"

import os
os.makedirs(ARCADE_DATA_DIR, exist_ok=True)
os.makedirs(CASINO_DATA_DIR, exist_ok=True)


@dataclass
class GameSession:
    """游戏会话"""
    session_id: str
    game_type: str
    player_id: str
    bet_amount: float
    result: str
    payout: float
    timestamp: str
    details: Dict


@dataclass
class LeaderboardEntry:
    """排行榜条目"""
    agent_id: str
    game_type: str
    score: int
    wins: int
    total_games: int
    molty_earned: float
    rank: int
    last_updated: str


class MOLTYArcade:
    """MOLTY游戏馆 - 技能型游戏"""
    
    def __init__(self):
        self.wallet_manager = WalletManager()
        self.sessions: List[GameSession] = []
        self.leaderboard: Dict[str, List[LeaderboardEntry]] = {}
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        # 加载游戏会话
        sessions_file = os.path.join(ARCADE_DATA_DIR, "sessions.json")
        if os.path.exists(sessions_file):
            with open(sessions_file, 'r') as f:
                data = json.load(f)
                self.sessions = [GameSession(**s) for s in data]
        
        # 加载排行榜
        lb_file = os.path.join(ARCADE_DATA_DIR, "leaderboard.json")
        if os.path.exists(lb_file):
            with open(lb_file, 'r') as f:
                self.leaderboard = json.load(f)
    
    def _save_sessions(self):
        """保存游戏会话"""
        sessions_file = os.path.join(ARCADE_DATA_DIR, "sessions.json")
        with open(sessions_file, 'w') as f:
            json.dump([asdict(s) for s in self.sessions], f, indent=2)
    
    def _save_leaderboard(self):
        """保存排行榜"""
        lb_file = os.path.join(ARCADE_DATA_DIR, "leaderboard.json")
        with open(lb_file, 'w') as f:
            json.dump(self.leaderboard, f, indent=2)
    
    def play_text_rpg(self, player_id: str, bet: float = 10) -> Dict:
        """
        文本冒险RPG游戏
        智能体做选择，不同选择不同结局
        """
        # 检查余额
        balance = self.wallet_manager.get_balance(player_id)
        if balance < bet:
            return {"error": "Insufficient balance", "required": bet, "current": balance}
        
        # 扣除下注
        self.wallet_manager.transfer(player_id, "arcade_house", bet, "Text RPG entry fee")
        
        # 生成随机剧情和结果
        scenarios = [
            {"name": "神秘洞穴", "difficulty": 3, "reward_mult": 2.5},
            {"name": "失落城堡", "difficulty": 2, "reward_mult": 2.0},
            {"name": "魔法森林", "difficulty": 1, "reward_mult": 1.5},
        ]
        
        scenario = random.choice(scenarios)
        
        # 根据难度计算胜率
        win_chance = max(0.3, 1.0 - (scenario["difficulty"] * 0.2))
        win = random.random() < win_chance
        
        if win:
            reward = bet * scenario["reward_mult"]
            self.wallet_manager.transfer("arcade_house", player_id, reward, f"Text RPG win: {scenario['name']}")
            result = "win"
            message = f"🎉 恭喜你！你在{scenario['name']}中获得了胜利！"
        else:
            result = "loss"
            message = f"😢 很遗憾，你在{scenario['name']}中遭遇了失败..."
        
        # 记录会话
        session = GameSession(
            session_id=f"rpg_{int(time.time())}_{player_id}",
            game_type="text_rpg",
            player_id=player_id,
            bet_amount=bet,
            result=result,
            payout=reward if win else 0,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            details={"scenario": scenario["name"], "difficulty": scenario["difficulty"]}
        )
        self.sessions.append(session)
        self._save_sessions()
        
        return {
            "game": "Text RPG Adventure",
            "scenario": scenario["name"],
            "result": result,
            "message": message,
            "bet": bet,
            "payout": reward if win else 0,
            "new_balance": self.wallet_manager.get_balance(player_id)
        }
    
    def play_trivia(self, player_id: str, bet: float = 5) -> Dict:
        """
        知识问答游戏
        5道题，答对越多奖励越高
        """
        # 检查余额
        balance = self.wallet_manager.get_balance(player_id)
        if balance < bet:
            return {"error": "Insufficient balance"}
        
        # 扣除下注
        self.wallet_manager.transfer(player_id, "arcade_house", bet, "Trivia entry fee")
        
        # 生成5道随机题目
        questions = [
            {"q": "比特币的创世区块诞生于哪一年？", "a": ["2008", "2009", "2010"], "correct": 1},
            {"q": "AI中的'LLM'代表什么？", "a": ["Large Language Model", "Long Learning Model", "Logical Learning Model"], "correct": 0},
            {"q": "以太坊的创始人是谁？", "a": ["Satoshi", "Vitalik", "Elon"], "correct": 1},
            {"q": "哪个不是编程语言？", "a": ["Python", "Java", "Photoshop"], "correct": 2},
            {"q": "MOLTY的共识机制是什么？", "a": ["PoW", "PoS", "PoV"], "correct": 2},
        ]
        
        # 随机选择5道（这里简化为全部答对随机数）
        correct_answers = random.randint(1, 5)
        
        # 根据答对题数计算奖励
        reward_mult = {1: 0.5, 2: 0.8, 3: 1.2, 4: 1.8, 5: 3.0}
        reward = bet * reward_mult[correct_answers]
        
        if correct_answers >= 3:
            self.wallet_manager.transfer("arcade_house", player_id, reward, f"Trivia win: {correct_answers}/5")
            result = "win"
            message = f"🎉 答对{correct_answers}/5题！获得{reward:.1f} MOLTY！"
        else:
            result = "loss"
            message = f"😢 只答对{correct_answers}/5题...再接再厉！"
        
        # 记录会话
        session = GameSession(
            session_id=f"trivia_{int(time.time())}_{player_id}",
            game_type="trivia",
            player_id=player_id,
            bet_amount=bet,
            result=result,
            payout=reward if correct_answers >= 3 else 0,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            details={"correct_answers": correct_answers}
        )
        self.sessions.append(session)
        self._save_sessions()
        
        return {
            "game": "Knowledge Trivia",
            "correct": correct_answers,
            "total": 5,
            "result": result,
            "message": message,
            "bet": bet,
            "payout": reward if correct_answers >= 3 else 0,
            "new_balance": self.wallet_manager.get_balance(player_id)
        }
    
    def get_leaderboard(self, game_type: str = None) -> List[Dict]:
        """获取排行榜"""
        # 计算排行榜（简化版，实际应该根据会话统计）
        players = {}
        
        for session in self.sessions:
            if game_type and session.game_type != game_type:
                continue
            
            if session.player_id not in players:
                players[session.player_id] = {
                    "agent_id": session.player_id,
                    "score": 0,
                    "wins": 0,
                    "total_games": 0,
                    "molty_earned": 0
                }
            
            players[session.player_id]["total_games"] += 1
            if session.result == "win":
                players[session.player_id]["wins"] += 1
                players[session.player_id]["score"] += 10
            players[session.player_id]["molty_earned"] += session.payout - session.bet_amount
        
        # 排序
        leaderboard = sorted(players.values(), key=lambda x: x["score"], reverse=True)
        
        # 添加排名
        for i, entry in enumerate(leaderboard, 1):
            entry["rank"] = i
        
        return leaderboard[:10]  # Top 10


class MOLTYCasino:
    """MOLTY赌场 - 概率游戏"""
    
    def __init__(self):
        self.wallet_manager = WalletManager()
        self.house_edge = 0.15  # 15% 赌场优势
        self.sessions: List[GameSession] = []
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        sessions_file = os.path.join(CASINO_DATA_DIR, "sessions.json")
        if os.path.exists(sessions_file):
            with open(sessions_file, 'r') as f:
                data = json.load(f)
                self.sessions = [GameSession(**s) for s in data]
    
    def _save_sessions(self):
        """保存会话"""
        sessions_file = os.path.join(CASINO_DATA_DIR, "sessions.json")
        with open(sessions_file, 'w') as f:
            json.dump([asdict(s) for s in self.sessions], f, indent=2)
    
    def play_slot_machine(self, player_id: str, bet: float = 10) -> Dict:
        """
        老虎机游戏
        3个转轮，匹配图案获胜
        """
        # 检查余额
        balance = self.wallet_manager.get_balance(player_id)
        if balance < bet:
            return {"error": "Insufficient balance"}
        
        # 扣除下注
        self.wallet_manager.transfer(player_id, "casino_house", bet, "Slot machine bet")
        
        # 转轮图案
        symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣", "🎰"]
        
        # 生成结果
        reel1 = random.choice(symbols)
        reel2 = random.choice(symbols)
        reel3 = random.choice(symbols)
        
        # 计算奖励
        if reel1 == reel2 == reel3 == "🎰":
            multiplier = 50  # Jackpot!
            result = "jackpot"
        elif reel1 == reel2 == reel3 == "7️⃣":
            multiplier = 20
            result = "big_win"
        elif reel1 == reel2 == reel3 == "💎":
            multiplier = 10
            result = "win"
        elif reel1 == reel2 == reel3:
            multiplier = 5
            result = "win"
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
            multiplier = 2
            result = "small_win"
        else:
            multiplier = 0
            result = "loss"
        
        payout = bet * multiplier
        
        if payout > 0:
            # 扣除抽成
            house_cut = payout * self.house_edge
            player_payout = payout - house_cut
            self.wallet_manager.transfer("casino_house", player_id, player_payout, "Slot machine win")
        else:
            player_payout = 0
        
        # 记录会话
        session = GameSession(
            session_id=f"slot_{int(time.time())}_{player_id}",
            game_type="slot_machine",
            player_id=player_id,
            bet_amount=bet,
            result=result,
            payout=player_payout,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            details={"reels": [reel1, reel2, reel3], "multiplier": multiplier}
        )
        self.sessions.append(session)
        self._save_sessions()
        
        return {
            "game": "🎰 Slot Machine",
            "reels": [reel1, reel2, reel3],
            "result": result,
            "bet": bet,
            "payout": player_payout,
            "house_cut": payout * self.house_edge if payout > 0 else 0,
            "message": f"{'🎉 JACKPOT!' if result == 'jackpot' else '🎉 WIN!' if payout > 0 else '😢 Try again!'}" ,
            "new_balance": self.wallet_manager.get_balance(player_id)
        }
    
    def play_dice(self, player_id: str, bet: float = 10, prediction: str = "high") -> Dict:
        """
        骰子游戏
        猜大小
        """
        # 检查余额
        balance = self.wallet_manager.get_balance(player_id)
        if balance < bet:
            return {"error": "Insufficient balance"}
        
        # 扣除下注
        self.wallet_manager.transfer(player_id, "casino_house", bet, "Dice game bet")
        
        # 掷骰子
        dice = random.randint(1, 6)
        
        # 判断结果
        is_high = dice >= 4
        player_win = (prediction == "high" and is_high) or (prediction == "low" and not is_high)
        
        if player_win:
            # 扣除抽成后赔付
            payout = bet * 1.8  # 1.8x (抽成10%)
            house_cut = bet * 0.2
            player_payout = payout
            self.wallet_manager.transfer("casino_house", player_id, player_payout, "Dice win")
            result = "win"
            message = f"🎉 骰子点数{dice}，你赢了{player_payout:.1f} MOLTY！"
        else:
            player_payout = 0
            result = "loss"
            message = f"😢 骰子点数{dice}，你输了..."
        
        # 记录会话
        session = GameSession(
            session_id=f"dice_{int(time.time())}_{player_id}",
            game_type="dice",
            player_id=player_id,
            bet_amount=bet,
            result=result,
            payout=player_payout,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            details={"dice": dice, "prediction": prediction}
        )
        self.sessions.append(session)
        self._save_sessions()
        
        return {
            "game": "🎲 Dice",
            "dice": dice,
            "prediction": prediction,
            "result": result,
            "message": message,
            "bet": bet,
            "payout": player_payout,
            "new_balance": self.wallet_manager.get_balance(player_id)
        }
    
    def get_house_stats(self) -> Dict:
        """获取赌场统计"""
        total_bets = sum(s.bet_amount for s in self.sessions)
        total_payouts = sum(s.payout for s in self.sessions)
        total_games = len(self.sessions)
        house_profit = total_bets - total_payouts
        
        return {
            "total_games": total_games,
            "total_bets": total_bets,
            "total_payouts": total_payouts,
            "house_profit": house_profit,
            "house_edge": self.house_edge
        }


# ==================== 测试 ====================

if __name__ == "__main__":
    print("🎰 MOLTY Casino & Arcade 测试")
    print("=" * 60)
    
    # 初始化系统
    arcade = MOLTYArcade()
    casino = MOLTYCasino()
    
    # 创建测试玩家
    test_player = "casino_test_player"
    arcade.wallet_manager.create_wallet(test_player)
    arcade.wallet_manager.add_balance(test_player, 1000, "Test balance")
    
    print(f"✅ 测试玩家创建成功，余额: 1000 MOLTY\n")
    
    # 测试游戏馆
    print("🎮 测试游戏馆...")
    result = arcade.play_text_rpg(test_player, bet=20)
    print(f"   文本RPG: {result.get('message', result.get('error'))}")
    
    result = arcade.play_trivia(test_player, bet=10)
    print(f"   知识问答: {result.get('message', result.get('error'))}")
    print()
    
    # 测试赌场
    print("🎰 测试赌场...")
    result = casino.play_slot_machine(test_player, bet=20)
    print(f"   老虎机: {result.get('message', result.get('error'))}")
    print(f"   转轮: {result.get('reels', [])}")
    
    result = casino.play_dice(test_player, bet=15, prediction="high")
    print(f"   骰子: {result.get('message', result.get('error'))}")
    print()
    
    # 显示排行榜
    print("🏆 游戏馆排行榜:")
    lb = arcade.get_leaderboard()
    for i, entry in enumerate(lb[:3], 1):
        print(f"   #{i} {entry['agent_id']}: {entry['score']}分, {entry['wins']}胜")
    print()
    
    # 显示赌场统计
    print("📊 赌场统计:")
    stats = casino.get_house_stats()
    print(f"   总局数: {stats['total_games']}")
    print(f"   总投注: {stats['total_bets']:.1f} MOLTY")
    print(f"   总赔付: {stats['total_payouts']:.1f} MOLTY")
    print(f"   赌场盈利: {stats['house_profit']:.1f} MOLTY")
    print(f"   抽成比例: {stats['house_edge']*100:.0f}%")
    print()
    
    print("=" * 60)
    print("✅ Casino & Arcade 测试完成！")