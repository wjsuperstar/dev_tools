import time
import os
import shutil
import telnetlib
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tftpy
from enable_multiport_telnet_9606 import main as enable_telnetd


# --- 配置区 ---
MONITOR_PATH = "Z:\\test\\"
IMPORT_PATH = "E:\\tftp\\import\\"
EXPORT_CONTROL_PATH = "E:\\tftp\\export\\"
TFTP_ROOT_PATH = "E:\\tftp\\tftp_root\\"
DEVICE_IP = "192.168.200.1"
# --------------

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, source_path):
        super().__init__()
        self.source_path = os.path.abspath(source_path)
        self.telnetd_flg = False

    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            if filename.startswith("~") or filename.endswith(".tmp"):
                return
            print(f"\n[监控] 检测到新文件: {filename}")
            self.trigger_device_download_ext(event.src_path, filename)
    
    def exec_cmd_by_telnet(self, tn, cmd):
        tn.write(cmd.encode('ascii'))
        print(f"[指令] 开始执行: {cmd}")
        print("[输出]:")
        for _ in range(10):  # 稍微延长等待时间
            output = tn.read_very_eager().decode('utf-8', errors='ignore')
            if output:
                print(output, end="")
            if "#" in output:
                print(f"\n[指令] 执行成功！")
                break
            time.sleep(1)
        
    def trigger_device_download_ext(self, src_path, filename):
        for _ in range(10):
            if self.trigger_device_download(src_path, filename):
                break
            time.sleep(2)
            print(f"[系统] 重连telnet服务：")

    def get_rndis_ip(self):
        src_ipaddress_cmd = f"ipconfig | findstr.exe \"IPv4 地址\" | findstr {DEVICE_IP[0:11]}"
        raw_output = os.popen(src_ipaddress_cmd).read()
        if not raw_output:
            print("错误：未找到 192.168.200 网段的 IP，请检查 RNDIS 连接")
            return None
        return raw_output.split(":")[-1].strip()

    def stage_file_to_tftp_root(self, src_path, filename):
        src_abs = os.path.abspath(src_path)
        tftp_root_abs = os.path.abspath(TFTP_ROOT_PATH)

        try:
            os.makedirs(tftp_root_abs, exist_ok=True)
            dst_file = os.path.join(tftp_root_abs, filename)
            shutil.copy2(src_abs, dst_file)
            print(f"[系统] 已同步文件到 TFTP 目录: {dst_file}")
            return True
        except Exception as e:
            print(f"[错误] 同步文件到 TFTP 目录失败: {e}")
            return False

    def trigger_device_download(self, src_path, filename):
        ret = True
        try:
            if not self.stage_file_to_tftp_root(src_path, filename):
                return False

            tn = telnetlib.Telnet(DEVICE_IP, timeout=5)
            time.sleep(0.5)
            banner = tn.read_very_eager().decode("utf-8", errors="ignore").strip()
            #print("banner=", banner)
            print(f"[系统] 连接telnet服务成功")
            
            # --- 登录逻辑 (如果需要密码请取消注释) ---
            # tn.read_until(b"login: ", timeout=2)
            # tn.write(b"root\n")
            # ---------------------------------------
            
            ip_address = self.get_rndis_ip()
            if not ip_address:
                tn.close()
                return False
            #print(f"RNDIS口IP地址: {ip_address}")
            
            cmd = f"tftp -g -r {filename} -l /2ndfile/{filename} {ip_address}\n"
            self.exec_cmd_by_telnet(tn, cmd);
            
            self.exec_cmd_by_telnet(tn, "mount -o remount rw /\n");
            self.exec_cmd_by_telnet(tn, f"opkg install --force-reinstall /2ndfile/{filename}\n");
            
            #print("exit start");
            #tn.write(b"exit\n")
            tn.close()
        except Exception as e:
            print(f"[错误] Telnet 连接失败: {e}")
            ret = False
            if not self.telnetd_flg:
                print(f"[系统] 尝试打开telnetd服务:")
                time.sleep(2)
                enable_telnetd()
                self.telnetd_flg = True
        return ret


class ExportFileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.telnetd_flg = False
        self.processed_mtime = {}
        self.export_out_dir = os.path.join(EXPORT_CONTROL_PATH, "export_out")
        os.makedirs(self.export_out_dir, exist_ok=True)

    def on_created(self, event):
        self.handle_event(event)

    def on_modified(self, event):
        self.handle_event(event)

    def handle_event(self, event):
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
        self.trigger_export_ext(src_abs)

    def get_rndis_ip(self):
        src_ipaddress_cmd = f"ipconfig | findstr.exe \"IPv4 地址\" | findstr {DEVICE_IP[0:11]}"
        raw_output = os.popen(src_ipaddress_cmd).read()
        if not raw_output:
            print("错误：未找到 192.168.200 网段的 IP，请检查 RNDIS 连接")
            return None
        return raw_output.split(":")[-1].strip()

    def exec_cmd_by_telnet(self, tn, cmd):
        tn.write(cmd.encode('ascii'))
        print(f"[指令] 开始执行: {cmd}")
        print("[输出]:")
        for _ in range(10):
            output = tn.read_very_eager().decode('utf-8', errors='ignore')
            if output:
                print(output, end="")
            if "#" in output:
                print(f"\n[指令] 执行成功！")
                break
            time.sleep(1)

    def normalize_remote_name(self, device_path):
        safe_name = device_path.strip().lstrip("/").replace("/", "__")
        return safe_name if safe_name else "root_file"

    def read_export_list(self, list_file):
        export_items = []
        try:
            with open(list_file, "r", encoding="utf-8", errors="ignore") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if not line.startswith("/"):
                        print(f"[导出] 已跳过非绝对路径: {line}")
                        continue
                    export_items.append(line)
        except Exception as e:
            print(f"[错误] 读取导出列表失败: {e}")
        return export_items

    def trigger_export_ext(self, list_file):
        for _ in range(10):
            if self.trigger_export(list_file):
                break
            time.sleep(2)
            print(f"[系统] 重连telnet服务：")

    def trigger_export(self, list_file):
        ret = True
        try:
            export_items = self.read_export_list(list_file)
            if not export_items:
                print("[导出] 导出列表为空，跳过")
                return True

            ip_address = self.get_rndis_ip()
            if not ip_address:
                return False

            tn = telnetlib.Telnet(DEVICE_IP, timeout=5)
            time.sleep(0.5)
            tn.read_very_eager().decode("utf-8", errors="ignore").strip()
            print(f"[系统] 连接telnet服务成功")

            for device_file in export_items:
                remote_name = self.normalize_remote_name(device_file)
                cmd = f"tftp -p -l {device_file} -r {remote_name} {ip_address}\n"
                self.exec_cmd_by_telnet(tn, cmd)

                src_file = os.path.join(TFTP_ROOT_PATH, remote_name)
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
        except Exception as e:
            print(f"[错误] 导出失败: {e}")
            ret = False
            if not self.telnetd_flg:
                print(f"[系统] 尝试打开telnetd服务:")
                time.sleep(2)
                enable_telnetd()
                self.telnetd_flg = True
        return ret

def start_tftp_server(bind_ip, monitor_path):
    print(f"[TFTP] Server 启动，监听 {bind_ip}:69, 工作目录: {monitor_path}")
    server = tftpy.TftpServer(monitor_path)
    try:
        server.listen(bind_ip, 69)
    except Exception as e:
        print(f"[错误] TFTP 端口占用或权限不足: {e}")

if __name__ == "__main__":
    if not os.path.isdir(MONITOR_PATH):
        raise Exception(f"[错误] 研发主机往外导出目录：{MONITOR_PATH} 不存在")
    
    os.makedirs(TFTP_ROOT_PATH, exist_ok=True)
    os.makedirs(IMPORT_PATH, exist_ok=True)
    os.makedirs(EXPORT_CONTROL_PATH, exist_ok=True)

    # 启动 TFTP 线程
    tftp_thread = threading.Thread(
        target=start_tftp_server, 
        args=("0.0.0.0", TFTP_ROOT_PATH), 
        daemon=True
    )
    tftp_thread.start()

    # 启动导入监控（两个目录）
    event_handler_main = NewFileHandler(MONITOR_PATH)
    event_handler_import = NewFileHandler(IMPORT_PATH)
    export_handler = ExportFileHandler()
    observer = Observer()
    observer.schedule(event_handler_main, MONITOR_PATH, recursive=False)
    observer.schedule(event_handler_import, IMPORT_PATH, recursive=False)
    observer.schedule(export_handler, EXPORT_CONTROL_PATH, recursive=False)
    observer.start()

    print(f"[系统] 正在监控导入目录: {MONITOR_PATH}, {IMPORT_PATH}")
    print(f"[系统] 正在监控导出指令目录: {EXPORT_CONTROL_PATH}")
    print(f"[系统] TFTP 工作目录(可写): {TFTP_ROOT_PATH}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
