# -*- coding: utf-8 -*-
# auth: wujian 20241231
# python -m nuitka --lto=no --standalone --onefile xx
# 导入程序运行必须模块 
import sys, os
import json
import time
import telnetlib

class RunCmd():
    def __init__(self):
        self.host = "192.168.200.1"
        self.port = 5504
        self.pwd1 = 'bRysj,hHrhl'
        self.pwd2 = 'yQqlm,gSycl'
        self.unlock = 'AT!UNLOCK=10'
        self.at_ack = b'OK'
        self.tn = None

    def login(self):
        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=5)
            time.sleep(0.5)
            self.tn.write(self.pwd1.encode('ascii') + b'\r')
            time.sleep(0.5)
            self.tn.write(self.pwd2.encode('ascii') + b'\r')
            time.sleep(0.5)
            result = self.tn.read_until(self.at_ack, 2)
            if self.unlock:
                self.tn.write(self.unlock.encode('ascii') + b'\r')
                time.sleep(0.5)
                result = self.tn.read_until(self.at_ack, 2)
            #print('login...')
            return True
        except Exception as e:
            print("telnet login error: ", e)
            time.sleep(5)
            sys.exit(0)
            return False

    def run_cmd(self, cmd):
        if self.tn is None:
            if not self.login():
                return False
        try:
            self.tn.write(cmd.encode('ascii') + b'\r')
            result = self.tn.read_until(self.at_ack, 10)
            print('recv:', result.decode('ascii'))
            if result is None:
                print("run cmd fail\n")
            return True
        except Exception as e:
            print("telnet rw error: ", e)
            return False

    def logout(self):
        if self.tn is not None:
            self.tn.close()

def main():
    cmd_list = []
    far_level = input("配置远离事件对应的射频等级: 值域0~20, 如果输入99表示查询(第一个是远离，第二个是靠近)：")
    if far_level == "99":
        cmd_list = [{"type": "shell_echo", "cmd": "uci get mm.rf_state.far_level"}, {"type": "shell_echo", "cmd": "uci get mm.rf_state.near_level"}]
    else:
        near_level = input("配置靠近事件对应的射频等级, 值域0~20, 输入:")
        near_level = int(near_level)
        far_level = int(far_level)
        if far_level in range(0,21) and near_level in range(0,21):
            cmd_list = [{"type": "shell", "cmd": f"uci set mm.rf_state.far_level={far_level};uci set mm.rf_state.near_level={near_level};uci commit mm"}]
        else:
            print(f"参数错误, far_level={far_level}, near_level={near_level}")
            time.sleep(1)
            exit(0)
    
    obj = RunCmd()
    for item in cmd_list:
        #print(f'run: {item["cmd"]}')
        if item["type"] == "std_at":
            obj.run_cmd('AT+MODEM=' + item['cmd'] + '\r')
        elif item["type"] == "ext_at":
            obj.run_cmd(item['cmd'] + '\r')
        elif item["type"] == "shell":
            obj.run_cmd('AT+SYSTEM=' + item['cmd'] + '\r')
        elif item["type"] == "shell_echo":
            obj.run_cmd('AT+SYSTEMECHO=' + item['cmd'] + '\r')
        else:
            print("cmd type error\n")
    obj.logout()

if __name__ == "__main__":
    main()
    time.sleep(2)
    # input("Press Enter to exit...")
