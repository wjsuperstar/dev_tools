import paramiko
import os
import sys
from scp import SCPClient

# Configuration
HOSTNAME = "192.168.200.1"
PORT = 22
USERNAME = "root"
PASSWORD = None

def get_ssh_client():
    """建立并返回 SSH 客户端连接"""
    try:
        # === 关键修复：使用 Transport 对象手动认证 ===
        transport = paramiko.Transport((HOSTNAME, PORT))
        transport.connect(username=USERNAME, password=PASSWORD)  # 这里 password=None 是安全的
        # 强制使用 none 认证（跳过 Paramiko 的自动选择）
        transport.auth_none(USERNAME)
        
        # 创建 SSHClient
        client = paramiko.SSHClient()
        client._transport = transport
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client
    except Exception as e:
        # 让调用者处理异常
        raise e

def execute_shell_command(command):
    """
    执行 Shell 命令并返回结果
    :param command: Shell 命令字符串
    :return: (stdout_content, stderr_content)
    """
    client = None
    try:
        client = get_ssh_client()
        stdin, stdout, stderr = client.exec_command(command)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        return out, err
    except Exception as e:
        return None, str(e)
    finally:
        if client:
            client.close()

def download_files_with_scp():
    remote_path = "/2ndfile/log"
    local_dir = "./download"
    os.makedirs(local_dir, exist_ok=True)

    client = None
    try:
        client = get_ssh_client()
        print("连接成功!")

        # === 后续文件操作保持不变 ===
        print("正在查找文件...")
        stdin, stdout, stderr = client.exec_command(f"find {remote_path} -name 'dev*' -type f")
        files_output = stdout.read().decode().strip()
        error = stderr.read().decode()
        if error and "No such file" not in error:
            print(f"查找文件时出错: {error}")
            return
        if not files_output:
            print("未找到以 'dev' 开头的文件")
            return

        file_list = [f.strip() for f in files_output.split('\n') if f.strip()]
        print(f"找到 {len(file_list)} 个匹配的文件:")
        for file_path in file_list:
            print(f" - {file_path}")

        print("开始下载文件...")
        with SCPClient(client.get_transport()) as scp:
            for remote_file_path in file_list:
                filename = os.path.basename(remote_file_path)
                local_file_path = os.path.join(local_dir, filename)
                try:
                    print(f"正在下载: {filename}")
                    scp.get(remote_file_path, local_file_path)
                    print(f"已下载: {filename}")
                except Exception as e:
                    print(f"下载文件 {filename} 时出错: {e}")

        print("所有文件下载完成！")
        print(f"文件保存在: {os.path.abspath(local_dir)}")

    except paramiko.AuthenticationException as e:
        print(f"❌ 认证失败: {e}")
        print("重要提示: 设备需要 'none' 认证 (password=None), 请确认脚本中 password=None")
    except paramiko.SSHException as e:
        print(f"❌ SSH 连接错误: {e}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 如果有命令行参数，则执行命令
        cmd = " ".join(sys.argv[1:])
        # print(f"Executing command: {cmd}") 
        # 用户可能只想要输出结果，不想要额外的log，这里可以斟酌。但为了调试还是保留print cmd比较好，或者打印在stderr。
        
        out, err = execute_shell_command(cmd)
        if out:
            print(out)
        if err:
            print(f"Error: {err}", file=sys.stderr)
    else:
        # 否则执行默认的文件下载任务
        download_files_with_scp()
