# -*- coding: utf-8 -*-
"""通用 SSH/SCP 文件下载器。

支持两种认证模式：
  - standard: 标准 SSHClient + connect（9813 等）
  - transport_none: 手工构造 Transport 后 connect（9606 等设备需要跳过 paramiko 默认认证）
"""
import os
import socket
import sys
import paramiko
from scp import SCPClient


def _connect_transport_none(host, port, username, password, timeout=10):
    """9606 系列：设备通常只接受 none 认证（无密码）。

    先按 none 认证建连（paramiko 在不传 password 时会走 auth_none）；
    设备若要求密码认证，则换一条新连接用密码重试一次。
    """
    def _open(with_password):
        sock = socket.create_connection((host, port), timeout=timeout)
        transport = paramiko.Transport(sock)
        if with_password:
            transport.connect(username=username, password=password)
        else:
            transport.connect(username=username)
        return transport

    try:
        transport = _open(with_password=False)
    except (paramiko.BadAuthenticationType, paramiko.AuthenticationException):
        transport = _open(with_password=True)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client._transport = transport
    return client


def _get_client(host, port, username, password, mode, timeout=10):
    """建立 SSH 客户端。"""
    if mode == "transport_none":
        return _connect_transport_none(host, port, username, password, timeout)

    # default: 标准 connect
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port, username, password, timeout=timeout)
    return client


def execute_shell_command(host, port, username, password, command,
                           mode="standard"):
    """执行一条 shell 命令，返回 (stdout, stderr)。"""
    client = None
    try:
        client = _get_client(host, port, username, password, mode)
        stdin, stdout, stderr = client.exec_command(command)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except Exception as e:
        return None, str(e)
    finally:
        if client:
            client.close()


def download_files(host, port, username, password,
                   remote_path, file_pattern,
                   local_dir="./download",
                   mode="standard",
                   debug_list_dir=False):
    """从 remote_path 下 find '*file_pattern*' 的文件并 scp 到 local_dir。

    file_pattern: find -name 接受的 glob，例如 'dev*'、'all*'。
    """
    os.makedirs(local_dir, exist_ok=True)
    client = None
    try:
        client = _get_client(host, port, username, password, mode)
        print("连接成功!")

        print(f"正在查找 {remote_path} 下匹配 {file_pattern!r} 的文件...")
        stdin, stdout, stderr = client.exec_command(
            f"find {remote_path} -name '{file_pattern}' -type f"
        )
        files_output = stdout.read().decode().strip()
        error = stderr.read().decode()
        if error and "No such file" not in error:
            print(f"查找文件时出错: {error}")
            return
        if not files_output:
            print(f"未找到匹配 {file_pattern!r} 的文件")
            if debug_list_dir:
                stdin, stdout, stderr = client.exec_command(f"ls -la {remote_path}")
                print(f"调试 - {remote_path} 目录列表:\n{stdout.read().decode()}")
            return

        file_list = [f.strip() for f in files_output.split('\n') if f.strip()]
        print(f"找到 {len(file_list)} 个匹配的文件:")
        for fp in file_list:
            print(f"  - {fp}")

        print("开始下载文件...")
        with SCPClient(client.get_transport()) as scp:
            for fp in file_list:
                filename = os.path.basename(fp)
                local_file = os.path.join(local_dir, filename)
                try:
                    print(f"正在下载: {filename}")
                    scp.get(fp, local_file)
                    print(f"已下载: {filename}")
                except Exception as e:
                    print(f"下载文件 {filename} 时出错: {e}")

        print("所有文件下载完成！")
        print(f"文件保存在: {os.path.abspath(local_dir)}")
    except paramiko.AuthenticationException as e:
        if mode == "transport_none":
            print(f"❌ 认证失败: {e}")
            print("提示: 设备可能需要 none 认证，请确认脚本中 password 是否正确")
        else:
            print("认证失败，请检查用户名和密码")
    except paramiko.SSHException as e:
        print(f"❌ SSH 连接错误: {e}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        if client:
            client.close()


def run_cli(host, port, username, password, mode="standard"):
    """CLI 入口：有命令行参数则执行命令，无参数则下载默认文件。"""
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        out, err = execute_shell_command(host, port, username, password, cmd, mode)
        if out:
            print(out)
        if err:
            print(f"Error: {err}", file=sys.stderr)
    else:
        # 默认从 /2ndfile/log 找 dev* 文件
        download_files(host, port, username, password,
                       remote_path="/2ndfile/log",
                       file_pattern="dev*",
                       mode=mode)
