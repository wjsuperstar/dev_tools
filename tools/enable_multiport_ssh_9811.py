# -*- coding: utf-8 -*-
# auth: wujian 20241231
# python -m nuitka --lto=no --standalone --onefile xx
# 导入程序运行必须模块
import sys, os
import json
import time
import telnetlib

cmd_list = [{"type": "shell", "cmd": "lc_usb_switch 0x03"},
            {"type": "shell", "cmd": "uci set dropbear.@dropbear[0].enable=1;uci commit"},
            {"type": "shell", "cmd": "/etc/init.d/dropbear start"}]

class RunCmd():
    def __init__(self):
        self.host = "192.168.10.1"
        self.port = 5504
        self.pwd1 = 'bRysj,hHrhl'
        self.pwd2 = 'yQqlm,gSycl'
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
    input("Press Enter to exit...")
