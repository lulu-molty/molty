"""
MOLTY Circuit Breaker - 熔断机制
防止异常资金流出
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass, field
import json
import os

# 告警配置
ALERT_WEBHOOK = os.getenv('MOLTBOOK_WEBHOOK', '')  # 告警webhook
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')


@dataclass
class CircuitBreakerConfig:
    """熔断配置"""
    # 10分钟内超过500 MOLTY触发熔断
    time_window_minutes: int = 10
    amount_threshold: float = 500.0
    
    # 连续失败次数触发熔断
    failure_threshold: int = 5
    
    # 熔断后冷却时间（分钟）
    cooldown_minutes: int = 30
    
    # 每小时最大交易数
    max_transactions_per_hour: int = 1000


@dataclass
class TransactionWindow:
    """交易时间窗口"""
    start_time: datetime
    end_time: datetime
    total_amount: float = 0.0
    transaction_count: int = 0
    transactions: list = field(default_factory=list)


class CircuitBreaker:
    """
    熔断器 - 防止异常资金流出
    
    触发条件:
    1. 10分钟内流出超过500 MOLTY
    2. 连续失败超过5次
    3. 每小时交易数超过1000
    """
    
    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.is_open = False  # 熔断状态
        self.opened_at: Optional[datetime] = None
        self.failure_count = 0
        self.windows: Dict[str, TransactionWindow] = {}  # 按地址的窗口
        self.global_window = TransactionWindow(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=self.config.time_window_minutes)
        )
        self.lock = threading.Lock()
        
        # 加载历史状态
        self._load_state()
    
    def _load_state(self):
        """加载熔断器状态"""
        state_file = '/root/.openclaw/workspace/molty_coin/data/circuit_breaker_state.json'
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.is_open = state.get('is_open', False)
                    if self.is_open:
                        self.opened_at = datetime.fromisoformat(state['opened_at'])
                        # 检查是否应该恢复
                        self._try_reset()
            except:
                pass
    
    def _save_state(self):
        """保存熔断器状态"""
        state_file = '/root/.openclaw/workspace/molty_coin/data/circuit_breaker_state.json'
        try:
            with open(state_file, 'w') as f:
                json.dump({
                    'is_open': self.is_open,
                    'opened_at': self.opened_at.isoformat() if self.opened_at else None,
                    'failure_count': self.failure_count
                }, f)
        except:
            pass
    
    def _try_reset(self):
        """尝试重置熔断器"""
        if not self.is_open or not self.opened_at:
            return
        
        cooldown = timedelta(minutes=self.config.cooldown_minutes)
        if datetime.now() - self.opened_at > cooldown:
            print("🔄 熔断器冷却时间结束，自动恢复")
            self.is_open = False
            self.opened_at = None
            self.failure_count = 0
            self._save_state()
    
    def can_execute(self, from_address: str, amount: float) -> bool:
        """
        检查是否允许执行交易
        
        Args:
            from_address: 发送方地址
            amount: 交易金额
            
        Returns:
            bool: 是否允许执行
        """
        with self.lock:
            # 1. 检查熔断状态
            if self.is_open:
                self._try_reset()
                if self.is_open:
                    print(f"🚫 熔断器开启中，拒绝交易: {from_address} -> {amount} MOLTY")
                    return False
            
            # 2. 检查全局窗口
            now = datetime.now()
            if now > self.global_window.end_time:
                # 重置全局窗口
                self.global_window = TransactionWindow(
                    start_time=now,
                    end_time=now + timedelta(minutes=self.config.time_window_minutes)
                )
            
            # 3. 检查金额阈值
            if self.global_window.total_amount + amount > self.config.amount_threshold:
                self._trip_circuit("10分钟内总流出超过阈值")
                return False
            
            # 4. 检查交易频率
            if self.global_window.transaction_count >= self.config.max_transactions_per_hour:
                self._trip_circuit("交易频率过高")
                return False
            
            # 5. 检查单个地址窗口
            if from_address not in self.windows:
                self.windows[from_address] = TransactionWindow(
                    start_time=now,
                    end_time=now + timedelta(minutes=self.config.time_window_minutes)
                )
            
            addr_window = self.windows[from_address]
            if now > addr_window.end_time:
                # 重置地址窗口
                self.windows[from_address] = TransactionWindow(
                    start_time=now,
                    end_time=now + timedelta(minutes=self.config.time_window_minutes)
                )
                addr_window = self.windows[from_address]
            
            # 检查地址阈值（单个地址10分钟内不超过200）
            if addr_window.total_amount + amount > 200:
                print(f"⚠️ 地址 {from_address} 超过个人限额")
                return False
            
            return True
    
    def record_success(self, from_address: str, amount: float, tx_id: str):
        """记录成功交易"""
        with self.lock:
            now = datetime.now()
            
            # 更新全局窗口
            self.global_window.total_amount += amount
            self.global_window.transaction_count += 1
            self.global_window.transactions.append({
                'tx_id': tx_id,
                'from': from_address,
                'amount': amount,
                'time': now.isoformat()
            })
            
            # 更新地址窗口
            if from_address in self.windows:
                self.windows[from_address].total_amount += amount
                self.windows[from_address].transaction_count += 1
            
            # 重置失败计数
            self.failure_count = 0
    
    def record_failure(self, error: str):
        """记录失败"""
        with self.lock:
            self.failure_count += 1
            print(f"⚠️ 交易失败 ({self.failure_count}/{self.config.failure_threshold}): {error}")
            
            if self.failure_count >= self.config.failure_threshold:
                self._trip_circuit(f"连续失败{self.failure_count}次")
    
    def _trip_circuit(self, reason: str):
        """触发熔断"""
        self.is_open = True
        self.opened_at = datetime.now()
        self._save_state()
        
        alert_message = f"""
🚨 **MOLTY熔断器已触发** 🚨

**原因**: {reason}
**时间**: {self.opened_at.isoformat()}
**冷却时间**: {self.config.cooldown_minutes}分钟

**当前统计**:
- 10分钟总流出: {self.global_window.total_amount:.2f} MOLTY
- 交易次数: {self.global_window.transaction_count}

**系统已自动暂停转账功能**
请联系管理员检查系统状态。
        """
        
        print(alert_message)
        self._send_alert(alert_message)
    
    def _send_alert(self, message: str):
        """发送告警"""
        # 这里可以实现webhook告警
        if ALERT_WEBHOOK:
            try:
                import requests
                requests.post(ALERT_WEBHOOK, json={'text': message})
            except:
                pass
    
    def get_status(self) -> dict:
        """获取熔断器状态"""
        return {
            'is_open': self.is_open,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'failure_count': self.failure_count,
            'global_window': {
                'total_amount': self.global_window.total_amount,
                'transaction_count': self.global_window.transaction_count,
                'start_time': self.global_window.start_time.isoformat(),
                'end_time': self.global_window.end_time.isoformat()
            },
            'config': {
                'time_window_minutes': self.config.time_window_minutes,
                'amount_threshold': self.config.amount_threshold,
                'cooldown_minutes': self.config.cooldown_minutes
            }
        }
    
    def manual_reset(self, admin_key: str) -> bool:
        """手动重置熔断器（需要管理员密钥）"""
        expected_key = os.getenv('CIRCUIT_BREAKER_RESET_KEY', '')
        if admin_key != expected_key:
            print("❌ 管理员密钥错误")
            return False
        
        with self.lock:
            self.is_open = False
            self.opened_at = None
            self.failure_count = 0
            self.global_window = TransactionWindow(
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(minutes=self.config.time_window_minutes)
            )
            self._save_state()
            print("✅ 熔断器已手动重置")
            return True


# 全局熔断器实例
circuit_breaker = CircuitBreaker()


# 装饰器：保护函数
def circuit_breaker_protected(func):
    """
    熔断保护装饰器
    
    使用:
    @circuit_breaker_protected
    def transfer(from_addr, to_addr, amount):
        ...
    """
    def wrapper(from_address: str, to_address: str, amount: float, *args, **kwargs):
        # 检查熔断器
        if not circuit_breaker.can_execute(from_address, amount):
            raise Exception("熔断器开启中，交易被拒绝")
        
        try:
            # 执行函数
            result = func(from_address, to_address, amount, *args, **kwargs)
            
            # 记录成功
            if isinstance(result, dict) and 'tx_id' in result:
                circuit_breaker.record_success(from_address, amount, result['tx_id'])
            
            return result
            
        except Exception as e:
            # 记录失败
            circuit_breaker.record_failure(str(e))
            raise
    
    return wrapper


# 测试
if __name__ == "__main__":
    print("🧪 测试熔断器...")
    
    cb = CircuitBreaker()
    
    # 测试正常交易
    for i in range(3):
        can_do = cb.can_execute('USER_1', 100)
        print(f"交易 {i+1}: {'✅ 允许' if can_do else '❌ 拒绝'}")
        if can_do:
            cb.record_success('USER_1', 100, f'TX_{i}')
    
    # 测试触发熔断
    print("\n测试触发熔断...")
    can_do = cb.can_execute('USER_1', 300)
    print(f"大额交易: {'✅ 允许' if can_do else '❌ 拒绝'}")
    
    print(f"\n熔断器状态: {cb.get_status()}")
    
    print("✅ 测试完成")