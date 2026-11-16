# -*- coding: utf-8 -*-
# 9813 平台：清除 SIM 锁文件
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.at_runner import main as run_at
from common.credentials import require_profile

CMD_LIST = [
    {"type": "shell", "cmd": "rm -f /data/.mm_sl_iccid /data/.mm_sl_m;sync"},
    {"type": "shell_echo", "cmd": "ls /data/.mm*"},
]

_CRED = require_profile("9813")

CONFIG = dict(
    host="192.168.1.1",
    port=5504,
    pwd1=_CRED["telnet_pwd1"],
    pwd2=_CRED["telnet_pwd2"],
    unlock='',  # 9813 不需要 unlock
)

if __name__ == "__main__":
    run_at(CONFIG, CMD_LIST)
