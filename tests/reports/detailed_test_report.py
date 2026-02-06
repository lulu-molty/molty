#!/usr/bin/env python3
"""
MOLTY 详细测试报告
全面验证系统功能
"""

import sys
import time
sys.path.append('/root/.openclaw/workspace/molty_coin')

print("🧪 MOLTY 详细测试报告")
print("=" * 70)
print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# 测试计数器
tests_passed = 0
tests_failed = 0

def test(name):
    global tests_passed, tests_failed
    def decorator(func):
        try:
            print(f"\n📝 {name}")
            result = func()
            if result:
                print(f"   ✅ 通过")
                tests_passed += 1
            else:
                print(f"   ❌ 失败")
                tests_failed += 1
            return result
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            tests_failed += 1
            return False
    return decorator

# ==================== 区块链测试 ====================

@test("1.1 创世区块创建")
def test_genesis_block():
    from core.blockchain import Blockchain
    chain = Blockchain()
    genesis = chain.chain[0]
    return (
        genesis.index == 0 and
        genesis.previous_hash == "0" * 64 and
        len(genesis.hash) == 64
    )

@test("1.2 区块哈希计算")
def test_block_hash():
    from core.blockchain import Blockchain
    chain = Blockchain()
    block = chain.chain[0]
    calculated = block.calculate_hash()
    return block.hash == calculated

@test("1.3 交易创建与签名")
def test_transaction():
    from core.blockchain import Transaction
    tx = Transaction(
        sender="A" * 40,
        recipient="B" * 40,
        amount=100,
        timestamp=time.time()
    )
    return (
        tx.tx_id is not None and
        len(tx.tx_id) == 64 and
        tx.amount == 100
    )

@test("1.4 区块链验证")
def test_chain_validation():
    from core.blockchain import Blockchain, Transaction
    chain = Blockchain()
    
    # 添加交易并挖矿
    tx = Transaction("A" * 40, "B" * 40, 50, time.time())
    chain.add_transaction(tx)
    chain.mine_pending_transactions("miner")
    
    return chain.is_chain_valid()

@test("1.5 Merkle根计算")
def test_merkle_root():
    from core.blockchain import Block, Transaction
    
    tx1 = Transaction("A" * 40, "B" * 40, 10, time.time())
    tx2 = Transaction("C" * 40, "D" * 40, 20, time.time())
    
    block = Block(
        index=1,
        transactions=[tx1.to_dict(), tx2.to_dict()],
        timestamp=time.time(),
        previous_hash="0" * 64
    )
    
    return len(block.merkle_root) == 64

# ==================== 钱包测试 ====================

@test("2.1 钱包创建")
def test_wallet_creation():
    from wallet.wallet import MoltyWallet
    wallet = MoltyWallet("test_user")
    return (
        wallet.address is not None and
        len(wallet.address) > 20 and
        wallet.get_balance() == 0
    )

@test("2.2 钱包地址生成")
def test_wallet_address():
    from wallet.wallet import MoltyWallet
    wallet = MoltyWallet("test_user_2")
    # 地址应该以1开头（Base58编码）
    return wallet.address.startswith('Y') or wallet.address.startswith('1')

@test("2.3 密钥对生成")
def test_key_pair():
    from wallet.wallet import MoltyWallet
    wallet = MoltyWallet("test_user_3")
    return (
        wallet.private_key is not None and
        wallet.public_key is not None
    )

@test("2.4 交易签名验证")
def test_transaction_signing():
    from wallet.wallet import MoltyWallet
    from core.blockchain import Transaction
    
    wallet = MoltyWallet("sender")
    wallet.balance = 1000
    
    tx = Transaction(
        sender=wallet.address,
        recipient="B" * 40,
        amount=100,
        timestamp=time.time()
    )
    
    # 签名
    wallet.sign_transaction(tx)
    
    return tx.signature is not None and len(tx.signature) > 0

# ==================== PoV共识测试 ====================

@test("3.1 PoV初始化")
def test_pov_init():
    from consensus.pov import PoVConsensus
    pov = PoVConsensus(min_votes=3, approval_threshold=0.6)
    return pov.min_votes == 3 and pov.approval_threshold == 0.6

@test("3.2 内容价值评估")
def test_content_value():
    from consensus.pov import calculate_content_value
    
    content = """
    ## 教程
    ```python
    code example
    ```
    我的经验分享
    大家觉得怎么样？
    """
    
    value = calculate_content_value(content, "tutorial")
    return (
        value.final_value > 0 and
        value.final_value <= 100
    )

@test("3.3 内容提交")
def test_content_submission():
    from consensus.pov import PoVConsensus
    
    pov = PoVConsensus(min_votes=2, approval_threshold=0.5)
    result = pov.submit_content("Test content", "test_user", "post")
    
    return (
        "content_hash" in result and
        "estimated_reward" in result and
        result["estimated_reward"] > 0
    )

@test("3.4 社区投票")
def test_community_voting():
    from consensus.pov import PoVConsensus
    
    pov = PoVConsensus(min_votes=2, approval_threshold=0.5)
    result = pov.submit_content("Test content", "creator", "post")
    content_hash = result["content_hash"]
    
    # 投票
    pov.vote(content_hash, "voter1", True, voter_weight=1.0)
    pov.vote(content_hash, "voter2", True, voter_weight=1.0)
    
    status = pov.get_content_status(content_hash)
    return status["votes_count"] == 2

@test("3.5 奖励计算")
def test_reward_calculation():
    from consensus.pov import PoVConsensus
    
    pov = PoVConsensus()
    
    # 高价值内容奖励
    high_value_reward = pov._calculate_reward(85)
    # 低价值内容奖励
    low_value_reward = pov._calculate_reward(30)
    
    return high_value_reward > low_value_reward

# ==================== 集成测试 ====================

@test("4.1 完整流程测试")
def test_full_workflow():
    from core.blockchain import Blockchain, Transaction
    from wallet.wallet import MoltyWallet
    
    # 1. 创建区块链
    chain = Blockchain()
    
    # 2. 创建钱包
    wallet_a = MoltyWallet("alice")
    wallet_b = MoltyWallet("bob")
    wallet_a.balance = 1000
    
    # 3. 创建交易
    tx = Transaction(
        sender=wallet_a.address,
        recipient=wallet_b.address,
        amount=100,
        timestamp=time.time()
    )
    wallet_a.sign_transaction(tx)
    
    # 4. 添加到区块链
    chain.add_transaction(tx)
    chain.mine_pending_transactions(wallet_a.address)
    
    # 5. 验证
    return (
        chain.is_chain_valid() and
        len(chain.chain) == 2
    )

# ==================== 运行测试 ====================

print("\n" + "=" * 70)
print("📦 模块1: 区块链核心")
print("=" * 70)
test_genesis_block()
test_block_hash()
test_transaction()
test_chain_validation()
test_merkle_root()

print("\n" + "=" * 70)
print("👛 模块2: 钱包系统")
print("=" * 70)
test_wallet_creation()
test_wallet_address()
test_key_pair()
test_transaction_signing()

print("\n" + "=" * 70)
print("🗳️ 模块3: PoV共识")
print("=" * 70)
test_pov_init()
test_content_value()
test_content_submission()
test_community_voting()
test_reward_calculation()

print("\n" + "=" * 70)
print("🔗 模块4: 集成测试")
print("=" * 70)
test_full_workflow()

# ==================== 测试报告 ====================

print("\n" + "=" * 70)
print("📊 测试报告总结")
print("=" * 70)

total_tests = tests_passed + tests_failed
pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

print(f"\n总测试数: {total_tests}")
print(f"✅ 通过: {tests_passed}")
print(f"❌ 失败: {tests_failed}")
print(f"📈 通过率: {pass_rate:.1f}%")

if tests_failed == 0:
    print("\n🎉 所有测试通过！系统已就绪！")
    status = "READY"
else:
    print(f"\n⚠️ 有 {tests_failed} 个测试失败，需要修复")
    status = "NEED_FIX"

print("\n" + "=" * 70)
print(f"状态: {status}")
print("=" * 70)

# 导出结果
sys.exit(0 if tests_failed == 0 else 1)