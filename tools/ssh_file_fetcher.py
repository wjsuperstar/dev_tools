import paramiko
import os
import sys
from scp import SCPClient

def download_files_with_scp():
    # SSH 连接参数
    hostname = "192.168.1.1"
    port = 22
    username = "root"
    password = "jS5d@50X@1X@1z@4hN"
    remote_path = "/tmp"
    
    # 本地保存目录
    local_dir = "./download"
    os.makedirs(local_dir, exist_ok=True)
    
    try:
        # 创建 SSH 客户端
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print("正在连接到服务器...")
        # 建立 SSH 连接
        client.connect(hostname, port, username, password, timeout=10)
        print("连接成功!")
        
        # 查找以 'all' 开头的文件
        print("正在查找文件...")
        stdin, stdout, stderr = client.exec_command(f"find {remote_path} -name 'all*' -type f")
        files_output = stdout.read().decode().strip()
        error = stderr.read().decode()
        
        if error and "No such file" not in error:
            print(f"查找文件时出错: {error}")
        
        if not files_output:
            print("未找到以 'all' 开头的文件")
            # 列出 /tmp 中的所有文件以便调试
            stdin, stdout, stderr = client.exec_command(f"ls -la {remote_path}")
            print(f"调试信息 - /tmp 目录完整列表:\n{stdout.read().decode()}")
            return
        
        # 解析文件列表
        file_list = [f.strip() for f in files_output.split('\n') if f.strip()]
        
        print(f"找到 {len(file_list)} 个匹配的文件:")
        for file_path in file_list:
            print(f"  - {file_path}")
        
        # 使用 SCP 下载文件
        print("开始下载文件...")
        with SCPClient(client.get_transport()) as scp:
            for remote_file_path in file_list:
                filename = os.path.basename(remote_file_path)
                local_file_path = os.path.join(local_dir, filename)
                
                try:
                    print(f"正在下载: {filename}")
                    scp.get(remote_file_path, local_file_path)
                    print(f"已下载: {filename}")
                    
                    # 检查文件大小
                    file_size = os.path.getsize(local_file_path)
                    print(f"文件大小: {file_size} 字节")
                    
                except Exception as e:
                    print(f"下载文件 {filename} 时出错: {e}")
        
        print("所有文件下载完成！")
        print(f"文件保存在: {os.path.abspath(local_dir)}")
        
    except paramiko.AuthenticationException:
        print("认证失败，请检查用户名和密码")
    except paramiko.SSHException as e:
        print(f"SSH 连接错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 关闭连接
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    download_files_with_scp()