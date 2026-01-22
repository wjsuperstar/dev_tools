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
                return None
        try:
            self.tn.write(cmd.encode('ascii') + b'\r')
            result = self.tn.read_until(self.at_ack, 10)
            print('recv:', result.decode('ascii'))
            if result is None:
                print("run cmd fail\n")
            return result.decode('ascii')
        except Exception as e:
            print("telnet rw error: ", e)
            return None

    def logout(self):
        if self.tn is not None:
            self.tn.close()

def main():
    action = input("强制设置SAR的射频等级，值域0~20，输入: ")
    param_list = list(range(0, 21))
    action = int(action)
    if action not in param_list:
        print(f"参数错误, param={action}")
        time.sleep(1)
        exit(0)
    
    obj = RunCmd()
    cmd_set = f"AT+SYSTEM=trc_mm_test --sar-rf {action}"
    cmd_get = f"AT+SYSTEMECHO=trc_mm_test --sar-rf 99"
    reslut = obj.run_cmd(cmd_set + '\r')
    reslut = obj.run_cmd(cmd_get + '\r')
    if reslut:
        first_line = reslut.split('\n')[2]
        value = int(first_line.split('=')[1])
        print("value=", value)
        if value == -999:
            print("错误: SAR功能未打开，请先打开SAR！")
        elif value == action:
            print(f"成功: 配置射频等级{action}成功！")
        else:
            print("错误: 配置失败！")
    obj.logout()

if __name__ == "__main__":
    main()
    time.sleep(3)
    # input("Press Enter to exit...")
