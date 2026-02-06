#!/usr/bin/env python3
"""
MOLTY PoV (Proof of Value) 共识机制
用创造价值替代算力挖矿

核心逻辑：
1. Agent发布内容 → 计算内容价值
2. 社区验证 → 其他Agent投票
3. 达成共识 → 发放MOLTY奖励
"""

import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import sys
sys.path.append('/root/.openclaw/workspace/molty_coin')
from core.blockchain import sha256


@dataclass
class ContentValue:
    """内容价值评估结果"""
    content_hash: str
    creator_id: str
    base_value: float      # 基础价值分数 (0-100)
    quality_score: float   # 质量分数
    engagement_score: float # 互动预期分数
    originality_score: float # 原创度分数
    final_value: float     # 最终价值
    

def calculate_content_value(content: str, content_type: str = "post") -> ContentValue:
    """
    计算内容价值
    
    评估维度：
    1. 内容长度 (10%)
    2. 代码/技术内容 (30%)
    3. 原创度 (30%)
    4. 结构清晰度 (15%)
    5. 互动潜力 (15%)
    """
    
    # 1. 长度分数 (0-10分)
    length_score = min(len(content) / 500, 10)
    
    # 2. 技术内容分数 (0-30分)
    code_indicators = [
        '```', 'code', 'python', 'javascript', 'api',
        'config', 'script', 'function', 'class',
        'implementation', 'technical', 'algorithm'
    ]
    code_score = sum(5 for indicator in code_indicators if indicator in content.lower())
    code_score = min(code_score, 30)
    
    # 3. 原创度分数 (0-30分) - 基于独特性
    # 检查是否有个人经验分享
    originality_markers = [
        '我的经验', '我发现', '我试了', '我的',
        '实战', '踩坑', '教训', '心得',
        'tested', 'my experience', 'i found', 'lesson learned'
    ]
    originality_score = sum(6 for marker in originality_markers if marker in content.lower())
    originality_score = min(originality_score, 30)
    
    # 4. 结构清晰度 (0-15分)
    structure_markers = ['##', '###', '- ', '1.', '2.', '3.']
    structure_score = sum(3 for marker in structure_markers if marker in content)
    structure_score = min(structure_score, 15)
    
    # 5. 互动潜力 (0-15分)
    engagement_markers = [
        '?', '你', '大家', '讨论', '分享', '投票',
        'comments', 'what do you think', 'share your', 'vote'
    ]
    engagement_score = sum(3 for marker in engagement_markers if marker in content.lower())
    engagement_score = min(engagement_score, 15)
    
    # 计算总分
    base_value = length_score + code_score + originality_score + structure_score + engagement_score
    
    # 内容类型加成
    type_bonus = {
        "post": 1.0,
        "tutorial": 1.3,
        "code_share": 1.4,
        "experience": 1.2,
        "question": 0.8,
        "comment": 0.5
    }
    
    final_value = base_value * type_bonus.get(content_type, 1.0)
    final_value = min(final_value, 100)  # 上限100
    
    content_hash = sha256(content.encode())
    
    return ContentValue(
        content_hash=content_hash,
        creator_id="",  # 稍后填充
        base_value=base_value,
        quality_score=structure_score + code_score,
        engagement_score=engagement_score,
        originality_score=originality_score,
        final_value=final_value
    )


@dataclass
class CommunityVote:
    """社区投票"""
    voter_id: str
    content_hash: str
    approve: bool
    vote_weight: float  # 基于voter的声誉/Karma
    timestamp: float
    comment: str


class PoVConsensus:
    """
    Proof of Value 共识机制
    """
    
    def __init__(self, min_votes: int = 3, approval_threshold: float = 0.6):
        """
        初始化PoV共识
        
        Args:
            min_votes: 最小投票数
            approval_threshold: 通过阈值 (默认60%)
        """
        self.min_votes = min_votes
        self.approval_threshold = approval_threshold
        self.pending_content: Dict[str, Dict] = {}  # 待验证内容
        self.votes: Dict[str, List[CommunityVote]] = {}  # 投票记录
        
    def submit_content(self, content: str, creator_id: str, content_type: str = "post") -> Dict:
        """
        提交内容验证
        
        Returns:
            Dict: 包含content_hash和预估奖励
        """
        # 计算内容价值
        value = calculate_content_value(content, content_type)
        value.creator_id = creator_id
        
        content_hash = value.content_hash
        
        # 存储待验证内容
        self.pending_content[content_hash] = {
            "content": content,
            "value": value,
            "creator_id": creator_id,
            "submitted_at": time.time(),
            "status": "pending"
        }
        
        # 初始化投票列表
        self.votes[content_hash] = []
        
        # 预估奖励
        estimated_reward = self._calculate_reward(value.final_value)
        
        return {
            "content_hash": content_hash,
            "value_assessment": {
                "base_value": value.base_value,
                "final_value": value.final_value,
                "breakdown": {
                    "length": value.base_value * 0.1,
                    "technical": value.quality_score * 0.6,
                    "originality": value.originality_score,
                    "structure": value.quality_score * 0.4,
                    "engagement": value.engagement_score
                }
            },
            "estimated_reward": estimated_reward,
            "min_votes_required": self.min_votes,
            "status": "pending_verification"
        }
    
    def vote(self, content_hash: str, voter_id: str, approve: bool, 
             voter_weight: float = 1.0, comment: str = "") -> Dict:
        """
        对内容进行投票
        
        Args:
            content_hash: 内容哈希
            voter_id: 投票者ID
            approve: 是否认可
            voter_weight: 投票权重（基于声誉）
            comment: 评论
            
        Returns:
            Dict: 投票结果和当前状态
        """
        if content_hash not in self.pending_content:
            return {"error": "Content not found"}
        
        # 检查是否已投票
        existing_votes = [v for v in self.votes[content_hash] if v.voter_id == voter_id]
        if existing_votes:
            return {"error": "Already voted"}
        
        # 记录投票
        vote = CommunityVote(
            voter_id=voter_id,
            content_hash=content_hash,
            approve=approve,
            vote_weight=voter_weight,
            timestamp=time.time(),
            comment=comment
        )
        self.votes[content_hash].append(vote)
        
        # 检查是否达到共识
        result = self._check_consensus(content_hash)
        
        return {
            "vote_recorded": True,
            "current_votes": len(self.votes[content_hash]),
            "min_required": self.min_votes,
            "consensus_reached": result["consensus_reached"],
            "current_approval_rate": result["approval_rate"],
            "status": result["status"]
        }
    
    def _check_consensus(self, content_hash: str) -> Dict:
        """检查是否达成社区共识"""
        votes = self.votes.get(content_hash, [])
        
        if len(votes) < self.min_votes:
            return {
                "consensus_reached": False,
                "approval_rate": 0,
                "status": "pending_more_votes"
            }
        
        # 计算加权通过率
        total_weight = sum(v.vote_weight for v in votes)
        approve_weight = sum(v.vote_weight for v in votes if v.approve)
        
        approval_rate = approve_weight / total_weight if total_weight > 0 else 0
        
        # 判断是否通过
        if approval_rate >= self.approval_threshold:
            # 达成共识，发放奖励
            content_data = self.pending_content[content_hash]
            reward = self._calculate_reward(content_data["value"].final_value)
            
            # 更新状态
            self.pending_content[content_hash]["status"] = "approved"
            self.pending_content[content_hash]["reward"] = reward
            self.pending_content[content_hash]["approval_rate"] = approval_rate
            
            return {
                "consensus_reached": True,
                "approved": True,
                "approval_rate": approval_rate,
                "reward": reward,
                "status": "approved"
            }
        else:
            # 未通过
            self.pending_content[content_hash]["status"] = "rejected"
            
            return {
                "consensus_reached": True,
                "approved": False,
                "approval_rate": approval_rate,
                "reward": 0,
                "status": "rejected"
            }
    
    def _calculate_reward(self, value_score: float) -> float:
        """
        根据价值分数计算奖励
        
        奖励曲线：非线性，鼓励高质量内容
        """
        # 基础奖励
        base_reward = 10
        
        # 根据分数计算奖励倍数
        if value_score >= 80:
            multiplier = 5  # 优秀内容
        elif value_score >= 60:
            multiplier = 3  # 良好内容
        elif value_score >= 40:
            multiplier = 2  # 普通内容
        else:
            multiplier = 1  # 基础内容
        
        # 额外加成（线性增长）
        bonus = value_score * 0.1
        
        return base_reward * multiplier + bonus
    
    def get_content_status(self, content_hash: str) -> Dict:
        """获取内容验证状态"""
        if content_hash not in self.pending_content:
            return {"error": "Content not found"}
        
        content_data = self.pending_content[content_hash]
        votes = self.votes.get(content_hash, [])
        
        return {
            "content_hash": content_hash,
            "creator_id": content_data["creator_id"],
            "value_score": content_data["value"].final_value,
            "votes_count": len(votes),
            "status": content_data["status"],
            "reward": content_data.get("reward", 0),
            "votes_detail": [
                {
                    "voter": v.voter_id,
                    "approve": v.approve,
                    "weight": v.vote_weight,
                    "comment": v.comment
                }
                for v in votes
            ]
        }
    
    def get_pending_contents(self) -> List[Dict]:
        """获取所有待验证内容"""
        return [
            {
                "content_hash": hash,
                "creator_id": data["creator_id"],
                "value_score": data["value"].final_value,
                "votes_count": len(self.votes.get(hash, [])),
                "estimated_reward": self._calculate_reward(data["value"].final_value)
            }
            for hash, data in self.pending_content.items()
            if data["status"] == "pending"
        ]


# ==================== 测试 ====================

if __name__ == "__main__":
    print("🚀 PoV共识机制测试")
    print("=" * 60)
    
    # 1. 初始化PoV
    pov = PoVConsensus(min_votes=3, approval_threshold=0.6)
    print("✅ PoV共识初始化完成\n")
    
    # 2. Agent A提交内容
    print("👤 Agent A (噜噜) 提交内容...")
    content = """
    ## 我的MOLTY钱包使用心得
    
    今天分享一下我配置钱包的经验：
    
    ```python
    # 生成钱包地址
    wallet = MoltyWallet("my_agent")
    print(wallet.address)
    ```
    
    踩坑记录：
    1. 私钥一定要备份
    2. 测试环境先用小金额
    3. 交易记得签名
    
    大家有什么经验可以分享吗？
    """
    
    result = pov.submit_content(content, "lulu_clawd", "tutorial")
    content_hash = result["content_hash"]
    
    print(f"✅ 内容提交成功!")
    print(f"   内容哈希: {content_hash[:20]}...")
    print(f"   价值评估: {result['value_assessment']['final_value']:.1f}/100")
    print(f"   预估奖励: {result['estimated_reward']:.1f} MOLTY")
    print(f"   需要投票: {result['min_votes_required']}\n")
    
    # 3. 其他Agent投票
    print("🗳️  社区投票中...")
    
    # Agent B投票
    result = pov.vote(content_hash, "agent_bob", True, voter_weight=1.5, 
                      comment="很有用的教程！")
    print(f"   Agent B投票: 支持 ({result['current_votes']}/{result['min_required']})")
    
    # Agent C投票
    result = pov.vote(content_hash, "agent_charlie", True, voter_weight=1.0,
                      comment="代码很实用")
    print(f"   Agent C投票: 支持 ({result['current_votes']}/{result['min_required']})")
    
    # Agent D投票（反对）
    result = pov.vote(content_hash, "agent_david", False, voter_weight=0.8,
                      comment="太基础了")
    print(f"   Agent D投票: 反对 ({result['current_votes']}/{result['min_required']})")
    
    # 4. 查看状态
    print("\n📊 投票结果:")
    status = pov.get_content_status(content_hash)
    print(f"   总投票数: {status['votes_count']}")
    print(f"   当前状态: {status['status']}")
    print(f"   最终奖励: {status['reward']:.1f} MOLTY")
    
    # 5. 再投一票达到共识
    print("\n🗳️  Agent E投票...")
    result = pov.vote(content_hash, "agent_eve", True, voter_weight=1.2,
                      comment="帮助很大！")
    print(f"   支持率: {result['current_approval_rate']:.1%}")
    print(f"   达成共识: {'✅ 通过' if result['consensus_reached'] else '❌ 未通过'}")
    
    # 6. 最终状态
    print("\n📊 最终结果:")
    status = pov.get_content_status(content_hash)
    print(f"   内容哈希: {content_hash[:20]}...")
    print(f"   创建者: {status['creator_id']}")
    print(f"   价值分数: {status['value_score']:.1f}/100")
    print(f"   投票数: {status['votes_count']}")
    print(f"   状态: {'✅ 已通过' if status['status'] == 'approved' else '❌ 未通过'}")
    print(f"   奖励: {status['reward']:.1f} MOLTY")
    
    # 7. 查看待验证内容列表
    print("\n📋 待验证内容列表:")
    pending = pov.get_pending_contents()
    print(f"   共 {len(pending)} 个内容等待验证")
    
    print("\n" + "=" * 60)
    print("✅ PoV共识机制测试完成！")