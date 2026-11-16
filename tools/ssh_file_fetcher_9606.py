# -*- coding: utf-8 -*-
# 9606 平台 SSH 文件下载器（transport_none 认证模式）
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.ssh_fetcher import run_cli
from common.credentials import require_profile

_CRED = require_profile("9606")

CONFIG = dict(
    host="192.168.200.1",
    port=22,
    username="root",
    password=_CRED["ssh_password"],
    mode="transport_none",  # 9606 设备需要跳过 paramiko 默认认证
)

if __name__ == "__main__":
    run_cli(**CONFIG)
