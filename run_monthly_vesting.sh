#!/bin/bash
# MOLTY Monthly Vesting Executor

echo "$(date): Starting monthly vesting..." >> /var/log/molty_vesting.log

cd /root/.openclaw/workspace/molty_coin
python3 monthly_vesting.py >> /var/log/molty_vesting.log 2>&1

echo "$(date): Monthly vesting completed" >> /var/log/molty_vesting.log
echo "---" >> /var/log/molty_vesting.log
