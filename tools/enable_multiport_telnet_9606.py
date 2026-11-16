# -*- coding: utf-8 -*-
# 9606 平台：开启多端口，开启 telnetd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.at_runner import main as run_at
from common.credentials import require_profile

CMD_LIST = [
    {"type": "shell", "cmd": "lc_usb_switch 0x03"},
    {"type": "shell", "cmd": "telnetd -l /bin/sh"},
]

_CRED = require_profile("9606")

CONFIG = dict(
    host="192.168.200.1",
    port=5504,
    pwd1=_CRED["telnet_pwd1"],
    pwd2=_CRED["telnet_pwd2"],
    unlock='AT!UNLOCK=10',
)

def main():
    run_at(CONFIG, CMD_LIST)


if __name__ == "__main__":
    main()
