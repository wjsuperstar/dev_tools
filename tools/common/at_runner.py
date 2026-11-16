# -*- coding: utf-8 -*-
"""通用 AT/Telnet 命令执行器。

各产品平台（9606/9811/9813/9916）的 RunCmd 实现此前分散在多个脚本中，
差异仅在 host/port/密码/是否需要 unlock。统一收敛到此处。
"""
import sys
import time
import telnetlib


class RunCmd:
    """AT/Telnet 命令执行器。

    设备走 telnet 登录后接受 AT+SYSTEM=... / AT+MODEM=... 等 AT 命令。
    """

    def __init__(self, host, port=5504, pwd1='', pwd2='',
                 unlock='AT!UNLOCK=10', at_ack=b'OK', timeout=5):
        self.host = host
        self.port = port
        self.pwd1 = pwd1
        self.pwd2 = pwd2
        self.unlock = unlock  # 空字符串表示跳过 unlock 步骤
        self.at_ack = at_ack
        self.timeout = timeout
        self.tn = None

    def login(self):
        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)
            time.sleep(0.5)
            self.tn.write(self.pwd1.encode('ascii') + b'\r')
            time.sleep(0.5)
            self.tn.write(self.pwd2.encode('ascii') + b'\r')
            time.sleep(0.5)
            self.tn.read_until(self.at_ack, 2)
            if self.unlock:
                self.tn.write(self.unlock.encode('ascii') + b'\r')
                time.sleep(0.5)
                self.tn.read_until(self.at_ack, 2)
            return True
        except Exception as e:
            print("telnet login error: ", e)
            time.sleep(5)
            # 登录失败属于异常退出，用非 0 退出码，便于脚本/CI 感知
            sys.exit(1)

    def run_cmd(self, cmd):
        if self.tn is None:
            if not self.login():
                return False
        try:
            self.tn.write(cmd.encode('ascii') + b'\r')
            result = self.tn.read_until(self.at_ack, 10)
            print('recv:', result.decode('ascii', errors='ignore'))
            return True
        except Exception as e:
            print("telnet rw error: ", e)
            return False

    def logout(self):
        if self.tn is not None:
            self.tn.close()

    def run(self, cmd_list):
        """执行一组命令，cmd_list 每项形如 {"type": ..., "cmd": ...}。

        支持 type:
          - std_at:      'AT+MODEM=<cmd>'
          - ext_at:      原样发送
          - shell:       'AT+SYSTEM=<cmd>'
          - shell_echo:  'AT+SYSTEMECHO=<cmd>'
        """
        for item in cmd_list:
            ctype = item.get("type")
            cmd = item.get("cmd")
            # 结尾的 \r 由 run_cmd() 统一追加，这里不要再加，否则会发出双 CR
            if ctype == "std_at":
                self.run_cmd('AT+MODEM=' + cmd)
            elif ctype == "ext_at":
                self.run_cmd(cmd)
            elif ctype == "shell":
                self.run_cmd('AT+SYSTEM=' + cmd)
            elif ctype == "shell_echo":
                self.run_cmd('AT+SYSTEMECHO=' + cmd)
            else:
                print(f"cmd type error: {ctype!r}")


def main(config, cmd_list, sleep_after=5):
    """便捷入口：执行命令列表后休眠退出。"""
    obj = RunCmd(**config)
    obj.run(cmd_list)
    obj.logout()
    time.sleep(sleep_after)
