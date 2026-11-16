# -*- coding: utf-8 -*-
# 9606 平台 TFTP 文件监控/上传下载器
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.tftp_fetcher import run_service
from enable_multiport_telnet_9606 import main as enable_telnetd

MONITOR_PATH = "Z:\\test\\"
IMPORT_PATH = "E:\\tftp\\import\\"
EXPORT_CONTROL_PATH = "E:\\tftp\\export\\"
TFTP_ROOT_PATH = "E:\\tftp\\tftp_root\\"
DEVICE_IP = "192.168.200.1"

if __name__ == "__main__":
    run_service(
        device_ip=DEVICE_IP,
        monitor_path=MONITOR_PATH,
        import_path=IMPORT_PATH,
        export_control_path=EXPORT_CONTROL_PATH,
        tftp_root_path=TFTP_ROOT_PATH,
        enable_telnetd_fn=enable_telnetd,
    )
