# -*- coding: utf-8 -*-
# 9606 平台：开启 dropbear ssh
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.at_runner import main as run_at
from common.credentials import require_profile

CMD_LIST = [
    {"type": "shell", "cmd": "lc_usb_switch 0x03"},
    {"type": "shell", "cmd": "uci set dropbear.@dropbear[0].enable=1;uci commit"},
    {"type": "shell", "cmd": "/etc/init.d/dropbear start"},
]

_CRED = require_profile("9606")

CONFIG = dict(
    host="192.168.200.1",
    port=5504,
    pwd1=_CRED["telnet_pwd1"],
    pwd2=_CRED["telnet_pwd2"],
    unlock='AT!UNLOCK=10',
)

if __name__ == "__main__":
    run_at(CONFIG, CMD_LIST)
