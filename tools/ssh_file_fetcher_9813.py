# -*- coding: utf-8 -*-
# 9813 平台 SSH 文件下载器（标准认证模式）
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.ssh_fetcher import download_files
from common.credentials import require_profile

_CRED = require_profile("9813")

CONFIG = dict(
    host="192.168.1.1",
    port=22,
    username="root",
    password=_CRED["ssh_password"],
    remote_path="/tmp",
    file_pattern="all*",
    mode="standard",
    debug_list_dir=True,  # 9813 找不到文件时打印 /tmp 列表便于排查
)

if __name__ == "__main__":
    download_files(**CONFIG)
