"""
MOLTY Database Layer - SQLite with Transaction Support
解决并发竞争和数据持久化问题
"""

import sqlite3
import json
import threading
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, List, Dict
import os

# 数据库文件路径
DB_PATH = os.getenv('MOLTY_DB_PATH', '/root/.openclaw/workspace/molty_coin/data/molty.db')

# 线程本地存储
_local = threading.local()

class DatabaseManager:
    """
    数据库管理器 - 支持事务和并发安全
    """
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接（线程安全）"""
        if not hasattr(_local, 'connection'):
            _local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # 手动控制事务
            )
            _local.connection.row_factory = sqlite3.Row
            # 启用WAL模式（写前日志）
            _local.connection.execute("PRAGMA journal_mode=WAL")
            _local.connection.execute("PRAGMA synchronous=NORMAL")
        return _local.connection
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        使用: with db.transaction(): ...
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")  # 立即获取写锁
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self.transaction() as cursor:
            # 钱包表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT UNIQUE NOT NULL,
                    address TEXT UNIQUE NOT NULL,
                    public_key TEXT NOT NULL,
                    private_key_encrypted TEXT NOT NULL,
                    balance REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active',  -- active, frozen, pending
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 交易记录表（审计日志）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tx_id TEXT UNIQUE NOT NULL,
                    from_address TEXT NOT NULL,
                    to_address TEXT NOT NULL,
                    amount REAL NOT NULL,
                    fee REAL DEFAULT 0.0,
                    type TEXT NOT NULL,  -- transfer, reward, game, genesis
                    status TEXT DEFAULT 'pending',  -- pending, confirmed, failed
                    balance_before_from REAL,
                    balance_after_from REAL,
                    balance_before_to REAL,
                    balance_after_to REAL,
                    metadata TEXT,  -- JSON格式存储额外信息
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    FOREIGN KEY (from_address) REFERENCES wallets(address),
                    FOREIGN KEY (to_address) REFERENCES wallets(address)
                )
            """)
            
            # 每日限额记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT NOT NULL,
                    date TEXT NOT NULL,
                    game_spent REAL DEFAULT 0.0,
                    game_won REAL DEFAULT 0.0,
                    transfer_sent REAL DEFAULT 0.0,
                    transfer_received REAL DEFAULT 0.0,
                    UNIQUE(address, date)
                )
            """)
            
            # 系统配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 审计日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    address TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions(from_address)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_to ON transactions(to_address)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_created ON transactions(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wallet_address ON wallets(address)")
            
            # 插入初始配置
            cursor.execute("""
                INSERT OR IGNORE INTO system_config (key, value) VALUES
                ('total_supply', '1000000'),
                ('daily_emission_limit', '100'),
                ('game_daily_limit', '100'),
                ('game_win_limit', '500'),
                ('version', '1.0.0')
            """)
    
    # ==================== 钱包操作 ====================
    
    def create_wallet(self, agent_id: str, address: str, public_key: str, 
                     private_key_encrypted: str) -> bool:
        """创建新钱包（事务保护）"""
        try:
            with self.transaction() as cursor:
                cursor.execute("""
                    INSERT INTO wallets (agent_id, address, public_key, private_key_encrypted)
                    VALUES (?, ?, ?, ?)
                """, (agent_id, address, public_key, private_key_encrypted))
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_wallet(self, address: str) -> Optional[Dict]:
        """获取钱包信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM wallets WHERE address = ?", 
            (address,)
        )
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None
    
    def get_balance(self, address: str) -> float:
        """获取余额（原子操作）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT balance FROM wallets WHERE address = ?",
            (address,)
        )
        row = cursor.fetchone()
        cursor.close()
        return row['balance'] if row else 0.0
    
    def update_balance(self, address: str, new_balance: float) -> bool:
        """更新余额（事务保护）"""
        try:
            with self.transaction() as cursor:
                cursor.execute("""
                    UPDATE wallets 
                    SET balance = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE address = ?
                """, (new_balance, address))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ 更新余额失败: {e}")
            return False
    
    # ==================== 转账操作（核心 - 事务保护） ====================
    
    def transfer(self, from_address: str, to_address: str, amount: float,
                fee: float = 0.0, tx_type: str = 'transfer',
                metadata: dict = None) -> Optional[str]:
        """
        执行转账（原子操作）
        
        Returns:
            tx_id: 交易成功返回交易ID
            None: 交易失败（余额不足或其他错误）
        """
        import hashlib
        import time
        
        # 生成交易ID
        tx_id = hashlib.sha256(
            f"{from_address}{to_address}{amount}{time.time()}".encode()
        ).hexdigest()
        
        try:
            with self.transaction() as cursor:
                # 1. 获取发送方余额（加锁）
                cursor.execute(
                    "SELECT balance FROM wallets WHERE address = ?",
                    (from_address,)
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"发送方地址不存在: {from_address}")
                
                balance_before_from = row['balance']
                
                # 2. 检查余额充足
                total_deduction = amount + fee
                if balance_before_from < total_deduction:
                    raise ValueError(f"余额不足: {balance_before_from} < {total_deduction}")
                
                # 3. 获取接收方余额
                cursor.execute(
                    "SELECT balance FROM wallets WHERE address = ?",
                    (to_address,)
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"接收方地址不存在: {to_address}")
                
                balance_before_to = row['balance']
                
                # 4. 计算新余额
                balance_after_from = balance_before_from - total_deduction
                balance_after_to = balance_before_to + amount
                
                # 5. 更新发送方余额
                cursor.execute("""
                    UPDATE wallets 
                    SET balance = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE address = ?
                """, (balance_after_from, from_address))
                
                # 6. 更新接收方余额
                cursor.execute("""
                    UPDATE wallets 
                    SET balance = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE address = ?
                """, (balance_after_to, to_address))
                
                # 7. 记录交易（审计日志）
                cursor.execute("""
                    INSERT INTO transactions (
                        tx_id, from_address, to_address, amount, fee, type,
                        status, balance_before_from, balance_after_from,
                        balance_before_to, balance_after_to, metadata, confirmed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'confirmed', ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    tx_id, from_address, to_address, amount, fee, tx_type,
                    balance_before_from, balance_after_from,
                    balance_before_to, balance_after_to,
                    json.dumps(metadata) if metadata else None
                ))
                
                return tx_id
                
        except Exception as e:
            print(f"❌ 转账失败: {e}")
            return None
    
    # ==================== 限额管理 ====================
    
    def check_daily_limit(self, address: str, limit_type: str = 'game') -> dict:
        """检查每日限额"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM daily_limits 
            WHERE address = ? AND date = ?
        """, (address, today))
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return {
                'game_spent': 0.0,
                'game_won': 0.0,
                'transfer_sent': 0.0,
                'transfer_received': 0.0
            }
        
        return dict(row)
    
    def update_daily_limit(self, address: str, **kwargs) -> bool:
        """更新每日限额"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with self.transaction() as cursor:
                # 检查记录是否存在
                cursor.execute("""
                    SELECT id FROM daily_limits 
                    WHERE address = ? AND date = ?
                """, (address, today))
                
                if cursor.fetchone():
                    # 更新
                    updates = []
                    values = []
                    for key, value in kwargs.items():
                        updates.append(f"{key} = {key} + ?")
                        values.append(value)
                    values.extend([address, today])
                    
                    cursor.execute(f"""
                        UPDATE daily_limits 
                        SET {', '.join(updates)}
                        WHERE address = ? AND date = ?
                    """, values)
                else:
                    # 插入
                    cursor.execute("""
                        INSERT INTO daily_limits (address, date, game_spent, game_won)
                        VALUES (?, ?, 0.0, 0.0)
                    """, (address, today))
                    
                    # 然后更新
                    updates = []
                    values = []
                    for key, value in kwargs.items():
                        updates.append(f"{key} = ?")
                        values.append(value)
                    values.extend([address, today])
                    
                    cursor.execute(f"""
                        UPDATE daily_limits 
                        SET {', '.join(updates)}
                        WHERE address = ? AND date = ?
                    """, values)
                
                return True
        except Exception as e:
            print(f"❌ 更新限额失败: {e}")
            return False
    
    # ==================== 审计和统计 ====================
    
    def log_audit(self, action: str, address: str = None, details: str = None,
                 ip_address: str = None, user_agent: str = None):
        """记录审计日志"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_log (action, address, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            """, (action, address, details, ip_address, user_agent))
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"❌ 审计日志记录失败: {e}")
    
    def get_transaction_history(self, address: str, limit: int = 50) -> List[Dict]:
        """获取交易历史"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM transactions 
            WHERE from_address = ? OR to_address = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (address, address, limit))
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows]
    
    def get_system_stats(self) -> Dict:
        """获取系统统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 总供应量
        cursor.execute("SELECT SUM(balance) as total FROM wallets")
        total_supply = cursor.fetchone()['total'] or 0.0
        
        # 钱包数量
        cursor.execute("SELECT COUNT(*) as count FROM wallets")
        wallet_count = cursor.fetchone()['count']
        
        # 交易数量
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE status = 'confirmed'")
        tx_count = cursor.fetchone()['count']
        
        # 今日交易
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) as count FROM transactions 
            WHERE DATE(created_at) = ? AND status = 'confirmed'
        """, (today,))
        today_tx_count = cursor.fetchone()['count']
        
        cursor.close()
        
        return {
            'total_supply': total_supply,
            'wallet_count': wallet_count,
            'transaction_count': tx_count,
            'today_transaction_count': today_tx_count
        }


# 全局单例
db_manager = DatabaseManager()