# -*- coding: utf-8 -*-
"""通用 TFTP 文件监控/上传下载器。

两个 handler 类（导入监控 / 导出指令）此前在每个 fetcher 中都各自重写了
exec_cmd_by_telnet / get_rndis_ip / _retry / _on_telnet_fail 等方法。
此处抽到 TelnetMixin，handler 只需关心业务回调。
"""
import os
import re
import socket
import subprocess
import time
import shutil
import telnetlib
import threading

import tftpy
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _lookup_rndis_ip(prefix):
    """从 ipconfig 输出中找出属于 prefix 网段的 IPv4 地址。

    直接解析 ipconfig 原始输出，不依赖 findstr 的 "IPv4 地址" 文案，
    因此在英文/其他语言版本的 Windows 上同样可用。
    """
    if not prefix:
        return None
    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=10,
        )
    except Exception as e:
        print(f"[错误] 执行 ipconfig 失败: {e}")
        return None

    for line in result.stdout.splitlines():
        if prefix not in line:
            continue
        for match in _IPV4_RE.finditer(line):
            ip = match.group(0)
            if ip.startswith(prefix):
                return ip
    return None


# ---------- 共享 mixin ----------

class TelnetMixin:
    """封装 telnet 命令执行、IP 查询、连接重试等通用方法。

    子类需在 self 上提供：
      - device_ip            : str  设备 IP
      - tftp_root_path       : str  本地 TFTP 根目录
      - enable_telnetd_fn    : 可调用对象，触发设备打开 telnetd；可为 None
      - telnetd_flg          : bool 是否已尝试过打开 telnetd
    """

    # ---- IP / 命令执行 ----

    def get_rndis_ip(self):
        prefix = self.device_ip[:11] if self.device_ip else ""
        ip_address = _lookup_rndis_ip(prefix)
        if not ip_address:
            print(f"错误：未找到 {prefix} 网段的 IP，请检查 RNDIS 连接")
            return None
        return ip_address

    def exec_cmd_by_telnet(self, tn, cmd):
        tn.write(cmd.encode('ascii'))
        print(f"[指令] 开始执行: {cmd}")
        print("[输出]:")
        for _ in range(10):
            output = tn.read_very_eager().decode('utf-8', errors='ignore')
            if output:
                print(output, end="")
            if "#" in output:
                print("\n[指令] 执行成功！")
                return True
            time.sleep(1)
        return False

    # ---- 连接辅助 ----

    def _telnet_connect(self):
        tn = telnetlib.Telnet(self.device_ip, timeout=5)
        time.sleep(0.5)
        tn.read_very_eager().decode("utf-8", errors="ignore").strip()
        print(f"[系统] 连接telnet服务成功")
        return tn

    def _on_telnet_fail(self):
        if not self.telnetd_flg and self.enable_telnetd_fn:
            print("[系统] 尝试打开telnetd服务:")
            time.sleep(2)
            try:
                self.enable_telnetd_fn()
            except Exception as e:
                print(f"[系统] 打开telnetd失败: {e}")
            self.telnetd_flg = True

    def _retry(self, action, *args):
        for _ in range(10):
            if action(*args):
                return
            time.sleep(2)
            print("[系统] 重连telnet服务：")


# ---------- 导入监控 handler ----------

class NewFileHandler(TelnetMixin, FileSystemEventHandler):
    """监控目录有新文件时：拷贝到 TFTP 根目录 → tftp -g 推到设备 → opkg install。"""

    def __init__(self, tftp_root_path, device_ip, enable_telnetd_fn=None):
        FileSystemEventHandler.__init__(self)
        self.tftp_root_path = tftp_root_path
        self.device_ip = device_ip
        self.enable_telnetd_fn = enable_telnetd_fn
        self.telnetd_flg = False

    def on_created(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)
        if filename.startswith("~") or filename.endswith(".tmp"):
            return
        print(f"\n[监控] 检测到新文件: {filename}")
        self._retry(self._download_and_install, event.src_path, filename)

    # ---- 业务步骤 ----

    def _stage_to_tftp_root(self, src_path, filename):
        try:
            os.makedirs(self.tftp_root_path, exist_ok=True)
            dst = os.path.join(self.tftp_root_path, filename)
            shutil.copy2(src_path, dst)
            print(f"[系统] 已同步文件到 TFTP 目录: {dst}")
            return True
        except Exception as e:
            print(f"[错误] 同步文件到 TFTP 目录失败: {e}")
            return False

    def _download_and_install(self, src_path, filename):
        try:
            if not self._stage_to_tftp_root(src_path, filename):
                return False

            tn = self._telnet_connect()
            ip_address = self.get_rndis_ip()
            if not ip_address:
                tn.close()
                return False

            self.exec_cmd_by_telnet(tn,
                f"tftp -g -r {filename} -l /2ndfile/{filename} {ip_address}\n")
            self.exec_cmd_by_telnet(tn, "mount -o remount rw /\n")
            self.exec_cmd_by_telnet(tn,
                f"opkg install --force-reinstall /2ndfile/{filename}\n")
            tn.close()
            return True
        except Exception as e:
            print(f"[错误] Telnet 连接失败: {e}")
            self._on_telnet_fail()
            return False


# ---------- 导出指令 handler ----------

class ExportFileHandler(TelnetMixin, FileSystemEventHandler):
    """监控导出指令文件变更：从文件读取远端路径列表 → tftp -p 拉回本地。"""

    def __init__(self, tftp_root_path, export_out_dir, device_ip,
                 enable_telnetd_fn=None):
        FileSystemEventHandler.__init__(self)
        self.tftp_root_path = tftp_root_path
        self.export_out_dir = export_out_dir
        self.device_ip = device_ip
        self.enable_telnetd_fn = enable_telnetd_fn
        self.telnetd_flg = False
        self.processed_mtime = {}

    def on_created(self, event):
        self._handle(event)

    def on_modified(self, event):
        self._handle(event)

    def _handle(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)
        if filename.startswith("~") or filename.endswith(".tmp"):
            return
        src_abs = os.path.abspath(event.src_path)
        out_abs = os.path.abspath(self.export_out_dir)
        try:
            is_export_output = os.path.commonpath([src_abs, out_abs]) == out_abs
        except ValueError:
            is_export_output = False
        if is_export_output:
            return

        try:
            mtime = os.path.getmtime(src_abs)
        except OSError:
            return
        if self.processed_mtime.get(src_abs) == mtime:
            return
        self.processed_mtime[src_abs] = mtime

        print(f"\n[导出] 检测到导出指令文件变更: {src_abs}")
        self._retry(self._export, src_abs)

    @staticmethod
    def _normalize_remote_name(device_path):
        safe_name = device_path.strip().lstrip("/").replace("/", "__")
        return safe_name if safe_name else "root_file"

    @staticmethod
    def _read_export_list(list_file):
        items = []
        try:
            with open(list_file, "r", encoding="utf-8", errors="ignore") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if not line.startswith("/"):
                        print(f"[导出] 已跳过非绝对路径: {line}")
                        continue
                    items.append(line)
        except Exception as e:
            print(f"[错误] 读取导出列表失败: {e}")
        return items

    def _export(self, list_file):
        try:
            export_items = self._read_export_list(list_file)
            if not export_items:
                print("[导出] 导出列表为空，跳过")
                return True

            ip_address = self.get_rndis_ip()
            if not ip_address:
                return False

            tn = self._telnet_connect()

            for device_file in export_items:
                remote_name = self._normalize_remote_name(device_file)
                self.exec_cmd_by_telnet(tn,
                    f"tftp -p -l {device_file} -r {remote_name} {ip_address}\n")

                src_file = os.path.join(self.tftp_root_path, remote_name)
                dst_file = os.path.join(self.export_out_dir, remote_name)
                for _ in range(10):
                    if os.path.exists(src_file):
                        shutil.copy2(src_file, dst_file)
                        print(f"[导出] 已保存: {dst_file}")
                        break
                    time.sleep(0.3)
                else:
                    print(f"[导出] 未在本地 TFTP 目录检测到导出文件: {remote_name}")

            tn.close()
            return True
        except Exception as e:
            print(f"[错误] 导出失败: {e}")
            self._on_telnet_fail()
            return False


# ---------- TFTP server + 主入口 ----------

def check_tftp_port(bind_ip, port=69):
    """预检 UDP 端口能否绑定。

    TFTP 走 UDP，Windows 下绑定 69 端口需要管理员权限。若不预检，
    端口占用/权限不足只会让后台线程静默退出，表现为"导入导出全部失败"。
    """
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.bind((bind_ip, port))
    except OSError as e:
        raise RuntimeError(
            f"TFTP 端口 {port} 无法绑定（Windows 下绑定 69 端口需要以管理员身份运行）：{e}"
        ) from e
    finally:
        probe.close()


def start_tftp_server(bind_ip, tftp_root_path):
    print(f"[TFTP] Server 启动，监听 {bind_ip}:69, 工作目录: {tftp_root_path}")
    server = tftpy.TftpServer(tftp_root_path)
    try:
        server.listen(bind_ip, 69)
    except Exception as e:
        print(f"[错误] TFTP 端口占用或权限不足: {e}")


def run_service(device_ip, monitor_path, import_path, export_control_path,
                tftp_root_path, enable_telnetd_fn=None):
    """组装并启动监控服务。供各产品平台入口脚本调用。"""
    if not os.path.isdir(monitor_path):
        raise Exception(f"[错误] 研发主机往外导出目录：{monitor_path} 不存在")

    os.makedirs(tftp_root_path, exist_ok=True)
    os.makedirs(import_path, exist_ok=True)
    os.makedirs(export_control_path, exist_ok=True)

    export_out_dir = os.path.join(export_control_path, "export_out")
    os.makedirs(export_out_dir, exist_ok=True)

    # TFTP server：先在主线程预检端口，避免后台线程静默失败
    check_tftp_port("0.0.0.0", 69)
    threading.Thread(
        target=start_tftp_server,
        args=("0.0.0.0", tftp_root_path),
        daemon=True,
    ).start()

    # 监控
    observer = Observer()
    observer.schedule(NewFileHandler(tftp_root_path, device_ip, enable_telnetd_fn),
                      monitor_path, recursive=False)
    observer.schedule(NewFileHandler(tftp_root_path, device_ip, enable_telnetd_fn),
                      import_path, recursive=False)
    observer.schedule(ExportFileHandler(tftp_root_path, export_out_dir,
                                        device_ip, enable_telnetd_fn),
                      export_control_path, recursive=False)
    observer.start()

    print(f"[系统] 正在监控导入目录: {monitor_path}, {import_path}")
    print(f"[系统] 正在监控导出指令目录: {export_control_path}")
    print(f"[系统] TFTP 工作目录(可写): {tftp_root_path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
