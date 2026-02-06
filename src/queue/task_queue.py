"""
MOLTY Async Task Queue - Redis + Celery
解决并发竞争问题
"""

import redis
import json
import time
import threading
from typing import Callable, Dict, Any
from queue import Queue, Empty
from dataclasses import dataclass
from datetime import datetime
import os

# Redis配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# 任务队列名称
TASK_QUEUE = 'molty:tasks'
RESULT_QUEUE = 'molty:results'
DLQ_QUEUE = 'molty:dlq'  # Dead Letter Queue


@dataclass
class Task:
    """任务数据结构"""
    task_id: str
    task_type: str  # transfer, game, reward, genesis
    payload: Dict[str, Any]
    priority: int = 5  # 1-10, 1最高
    created_at: str = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'payload': self.payload,
            'priority': self.priority,
            'created_at': self.created_at,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        return cls(**data)


class AsyncTaskQueue:
    """
    异步任务队列 - 基于Redis
    解决并发竞争问题
    """
    
    def __init__(self):
        self.redis_client = None
        self.running = False
        self.worker_thread = None
        self.handlers: Dict[str, Callable] = {}
        self._connect_redis()
    
    def _connect_redis(self):
        """连接Redis"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            self.redis_client.ping()
            print("✅ Redis连接成功")
        except Exception as e:
            print(f"⚠️ Redis连接失败，使用内存队列: {e}")
            self.redis_client = None
            self.memory_queue = Queue()
    
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.handlers[task_type] = handler
        print(f"✅ 注册处理器: {task_type}")
    
    def submit_task(self, task: Task) -> bool:
        """
        提交任务到队列
        
        Args:
            task: 任务对象
            
        Returns:
            bool: 是否成功提交
        """
        try:
            task_dict = task.to_dict()
            
            if self.redis_client:
                # 使用Redis队列（优先级队列）
                # 使用sorted set，score为优先级
                self.redis_client.zadd(
                    TASK_QUEUE,
                    {json.dumps(task_dict): task.priority}
                )
            else:
                # 使用内存队列
                self.memory_queue.put(task_dict)
            
            print(f"✅ 任务提交成功: {task.task_id} (类型: {task.task_type})")
            return True
            
        except Exception as e:
            print(f"❌ 任务提交失败: {e}")
            return False
    
    def get_task(self) -> Optional[Task]:
        """从队列获取任务（优先级最高）"""
        try:
            if self.redis_client:
                # 从sorted set获取优先级最高的任务
                result = self.redis_client.zrange(
                    TASK_QUEUE, 0, 0, withscores=True
                )
                if result:
                    task_json, priority = result[0]
                    task = Task.from_dict(json.loads(task_json))
                    # 从队列移除
                    self.redis_client.zrem(TASK_QUEUE, task_json)
                    return task
            else:
                # 从内存队列获取
                try:
                    task_dict = self.memory_queue.get(timeout=1)
                    return Task.from_dict(task_dict)
                except Empty:
                    return None
                    
        except Exception as e:
            print(f"❌ 获取任务失败: {e}")
            return None
        
        return None
    
    def process_task(self, task: Task) -> Dict[str, Any]:
        """处理单个任务"""
        print(f"\n🔄 处理任务: {task.task_id} (类型: {task.task_type})")
        
        handler = self.handlers.get(task.task_type)
        if not handler:
            raise ValueError(f"未知任务类型: {task.task_type}")
        
        try:
            # 执行任务
            result = handler(task.payload)
            print(f"✅ 任务完成: {task.task_id}")
            return {
                'success': True,
                'task_id': task.task_id,
                'result': result
            }
            
        except Exception as e:
            print(f"❌ 任务失败: {task.task_id} - {e}")
            
            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                print(f"🔄 重新提交任务 (重试 {task.retry_count}/{task.max_retries})")
                self.submit_task(task)
                return {
                    'success': False,
                    'task_id': task.task_id,
                    'error': str(e),
                    'will_retry': True
                }
            else:
                # 进入死信队列
                self._move_to_dlq(task, str(e))
                return {
                    'success': False,
                    'task_id': task.task_id,
                    'error': str(e),
                    'will_retry': False
                }
    
    def _move_to_dlq(self, task: Task, error: str):
        """移动到死信队列"""
        dlq_entry = {
            'task': task.to_dict(),
            'error': error,
            'failed_at': datetime.now().isoformat()
        }
        
        if self.redis_client:
            self.redis_client.lpush(DLQ_QUEUE, json.dumps(dlq_entry))
        
        print(f"📦 任务进入死信队列: {task.task_id}")
    
    def start_worker(self):
        """启动工作线程"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        print("✅ 任务队列工作线程已启动")
    
    def stop_worker(self):
        """停止工作线程"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        print("✅ 任务队列工作线程已停止")
    
    def _worker_loop(self):
        """工作线程主循环"""
        while self.running:
            try:
                task = self.get_task()
                if task:
                    self.process_task(task)
                else:
                    # 没有任务，休眠一段时间
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"❌ 工作线程错误: {e}")
                time.sleep(1)
    
    def get_queue_status(self) -> Dict[str, int]:
        """获取队列状态"""
        if self.redis_client:
            return {
                'pending': self.redis_client.zcard(TASK_QUEUE),
                'dlq': self.redis_client.llen(DLQ_QUEUE)
            }
        else:
            return {
                'pending': self.memory_queue.qsize(),
                'dlq': 0
            }


# ==================== 任务处理器 ====================

class TaskHandlers:
    """任务处理器集合"""
    
    @staticmethod
    def handle_transfer(payload: dict) -> dict:
        """处理转账任务"""
        from src.database.db_manager import db_manager
        
        from_address = payload['from_address']
        to_address = payload['to_address']
        amount = payload['amount']
        fee = payload.get('fee', 0.0)
        tx_type = payload.get('tx_type', 'transfer')
        metadata = payload.get('metadata')
        
        # 执行转账（数据库层已包含事务保护）
        tx_id = db_manager.transfer(
            from_address, to_address, amount, fee, tx_type, metadata
        )
        
        if not tx_id:
            raise Exception("转账失败：余额不足或地址不存在")
        
        return {
            'tx_id': tx_id,
            'from': from_address,
            'to': to_address,
            'amount': amount
        }
    
    @staticmethod
    def handle_game(payload: dict) -> dict:
        """处理游戏任务"""
        from src.casino.arcade import casino
        from src.database.db_manager import db_manager
        
        user_id = payload['user_id']
        game_type = payload['game_type']  # slot, dice
        bet = payload['bet']
        
        # 检查每日限额
        limits = db_manager.check_daily_limit(user_id)
        if limits['game_spent'] + bet > 100:  # 日限额100
            raise Exception("超过每日游戏限额")
        
        # 执行游戏
        if game_type == 'slot':
            result = casino.play_slot_machine(user_id, bet)
        elif game_type == 'dice':
            prediction = payload.get('prediction', 'high')
            result = casino.play_dice(user_id, bet, prediction)
        else:
            raise ValueError(f"未知游戏类型: {game_type}")
        
        # 更新限额记录
        db_manager.update_daily_limit(user_id, game_spent=bet)
        if result.get('winnings', 0) > 0:
            db_manager.update_daily_limit(user_id, game_won=result['winnings'])
        
        return result
    
    @staticmethod
    def handle_reward(payload: dict) -> dict:
        """处理奖励任务"""
        from src.database.db_manager import db_manager
        
        to_address = payload['to_address']
        amount = payload['amount']
        reward_type = payload.get('reward_type', 'general')
        
        # 系统发放奖励
        tx_id = db_manager.transfer(
            'SYSTEM', to_address, amount, 0.0, 
            f'reward:{reward_type}', {'type': reward_type}
        )
        
        if not tx_id:
            raise Exception("奖励发放失败")
        
        return {
            'tx_id': tx_id,
            'to': to_address,
            'amount': amount,
            'type': reward_type
        }


# 全局任务队列实例
task_queue = AsyncTaskQueue()

# 注册处理器
task_queue.register_handler('transfer', TaskHandlers.handle_transfer)
task_queue.register_handler('game', TaskHandlers.handle_game)
task_queue.register_handler('reward', TaskHandlers.handle_reward)


# 使用示例
if __name__ == "__main__":
    import uuid
    
    print("🚀 测试异步任务队列...")
    
    # 启动工作线程
    task_queue.start_worker()
    
    # 提交测试任务
    for i in range(5):
        task = Task(
            task_id=str(uuid.uuid4()),
            task_type='reward',
            payload={
                'to_address': f'USER_{i}',
                'amount': 10.0,
                'reward_type': 'test'
            },
            priority=i
        )
        task_queue.submit_task(task)
    
    # 等待处理
    time.sleep(3)
    
    # 查看状态
    status = task_queue.get_queue_status()
    print(f"\n📊 队列状态: {status}")
    
    # 停止
    task_queue.stop_worker()
    print("✅ 测试完成")