import random
import string
import time
import sys
import os
import traceback

# 尝试导入 SSH 执行接口
# 假设 ssh_file_fetcher_9606.py 在同一目录下
try:
    from ssh_file_fetcher_9606 import execute_shell_command
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from ssh_file_fetcher_9606 import execute_shell_command

# ==========================================
# 测试框架核心类
# ==========================================

class TestResult:
    def __init__(self, name, success, message=""):
        self.name = name
        self.success = success
        self.message = message

class TestFramework:
    def __init__(self):
        self.tests = []

    def register_test(self, test_func):
        """注册一个测试函数"""
        self.tests.append(test_func)

    def run(self):
        """运行所有注册的测试"""
        results = []
        print(f"=== 开始运行测试套件 (共 {len(self.tests)} 个测试) ===")
        print("="*60)
        
        for test in self.tests:
            test_name = test.__name__
            print(f"正在运行测试: {test_name} ...")
            start_time = time.time()
            try:
                # 测试函数应该返回 (bool, str) 或者只是 bool
                # True 表示通过, False 表示失败
                res = test()
                
                success = False
                msg = ""
                
                if isinstance(res, tuple):
                    success = res[0]
                    if len(res) > 1:
                        msg = res[1]
                elif isinstance(res, bool):
                    success = res
                
                duration = time.time() - start_time
                status = "PASS" if success else "FAIL"
                results.append(TestResult(test_name, success, msg))
                print(f"[{status}] {test_name} (耗时: {duration:.2f}s)")
                if msg:
                    print(f"       详情: {msg}")
            except Exception as e:
                duration = time.time() - start_time
                err_msg = str(e)
                traceback.print_exc()
                results.append(TestResult(test_name, False, f"异常: {err_msg}"))
                print(f"[ERROR] {test_name} 发生异常 (耗时: {duration:.2f}s)")
            print("-" * 60)

        self._print_summary(results)

    def _print_summary(self, results):
        print("\n=== 测试执行汇总 ===")
        passed = sum(1 for r in results if r.success)
        total = len(results)
        
        for r in results:
            status = "PASS" if r.success else "FAIL"
            print(f"[{status}] {r.name}: {r.message}")
            
        print(f"\n总计: {total}, 通过: {passed}, 失败: {total - passed}")
        
        if passed < total:
            sys.exit(1)
        else:
            sys.exit(0)

# ==========================================
# 辅助函数
# ==========================================

def generate_random_iccid():
    """生成随机的 ICCID (20位数字)"""
    prefix = "89860"
    suffix = ''.join(random.choices(string.digits, k=15))
    return prefix + suffix

def generate_random_name():
    """生成随机名称"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"test_name_{suffix}"

# ==========================================
# 测试用例实现
# ==========================================

def test_add_multiple_iccids():
    """
    功能测试 1: 批量添加 ICCID 并查询验证
    """
    count = 3  # 一次性添加 3 个
    added_items = []
    
    print(f"步骤 1: 准备添加 {count} 个随机 ICCID...")
    # 删除之前的iccid列表
    prev_cout, stderr = execute_shell_command("uci get iccidlist.global.count")
    if stderr:
        return False, f"查询 ICCID 列表索引时出错: {stderr}"
    print(f"当前 ICCID 列表个数: {prev_cout}")
    for index in range(int(prev_cout)):
        delete_cmd = f"trc_mm_test --del-iccidlist 0" 
        stdout, stderr = execute_shell_command(delete_cmd)
        if stderr:
            return False, f"删除 ICCID 列表时出错: {stderr}"
    
    # 循环添加
    for i in range(count):
        name = generate_random_name()
        iccid = generate_random_iccid()
        
        cmd = f'trc_mm_test --add-iccidlist "{name} {iccid}"'
        print(f"  [{i+1}/{count}] 执行命令: {cmd}")
        
        stdout, stderr = execute_shell_command(cmd)
        if stderr:
            print(f"  [警告] 标准错误输出: {stderr}")
            
        # 记录已添加的数据以便后续验证
        added_items.append({'name': name, 'iccid': iccid})
    
    print("步骤 2: 查询 ICCID 列表进行验证...")
    list_cmd = "trc_mm_test --list-iccidlist"
    stdout_list, stderr_list = execute_shell_command(list_cmd)
    
    if not stdout_list:
        return False, "查询列表命令返回为空"

    print("步骤 3: 验证所有添加项是否存在...")
    missing_items = []
    for item in added_items:
        # 构造期望的匹配字符串
        # 格式示例: name=test_name_123, iccid=89860...
        expected_substr = f"name={item['name']}, iccid={item['iccid']}"
        
        if expected_substr in stdout_list:
            print(f"  [√] 找到: {expected_substr}")
        else:
            print(f"  [x] 未找到: {expected_substr}")
            missing_items.append(item)
    
    if missing_items:
        return False, f"验证失败，有 {len(missing_items)} 个项未在列表中找到"
    
    return True, "所有 ICCID 添加并验证成功"

def test_active_iccid_lock():
    """
    功能测试 2: 激活 ICCID 锁并验证
    """
    cmd = "trc_mm_test --iccid-lock 1"
    stdout, stderr = execute_shell_command(cmd)
    if stderr:
        return False, f"激活 ICCID 锁时出错: {stderr}"
    
    query = "trc_mm_test -k 2 |grep lock_enable"
    stdout, stderr = execute_shell_command(query)
    if stderr:
        return False, f"查询 ICCID 锁状态时出错: {stderr}"
    if "lock_enable=1" not in stdout:
        return False, "激活 ICCID 锁失败"
    
    cmd = "trc_mm_test --iccid-lock 0"
    stdout, stderr = execute_shell_command(cmd)
    if stderr:
        return False, f"去激活 ICCID 锁时出错: {stderr}"
    
    query = "trc_mm_test -k 2 |grep lock_enable"
    stdout, stderr = execute_shell_command(query)
    if stderr:
        return False, f"查询 ICCID 锁状态时出错: {stderr}"
    if "lock_enable=0" not in stdout:
        return False, "去激活 ICCID 锁失败"

    return True, "ICCID 激活测试成功"

def test_net_mode():
    """
    功能测试 3: 测试网络制式切换
    """
    net_mode_list = [3, 4, 5, 6, 0]
    for net_mode in net_mode_list:
        cmd = f"trc_mm_test -m {net_mode}"
        print(f"  执行命令: {cmd}")
        stdout, stderr = execute_shell_command(cmd)
        if stderr:
            return False, f"切换网络制式 {net_mode} 时出错: {stderr}"
        query = "trc_mm_test -m 99 |grep curr_net_mode"
        print(f"  查询命令: {query}")
        stdout, stderr = execute_shell_command(query)
        if stderr:
            return False, f"查询网络制式时出错: {stderr}"
        if f"curr_net_mode={net_mode}" not in stdout:
            return False, f"切换网络制式 {net_mode} 失败"
    
    return True, "网络制式切换测试成功"

carrier_list = [
    {"name": "CMCC", "mcc": "460", "mnc": "02"},
    {"name": "CMCC", "mcc": "460", "mnc": "07"},
    {"name": "UNICOM", "mcc": "460", "mnc": "01"},
    {"name": "UNICOM", "mcc": "454", "mnc": "07"},
    {"name": "CTNET", "mcc": "460", "mnc": "11"}
]
apn_configs = [
    {"carrier": "CMCC", "name": "cmcc_profile1", "username": "user1", "password": "1234", "apn": "cmcc", "auth": "2", "ip": "2"},
    {"carrier": "UNICOM", "name": "uni_profile1", "username": "user1", "password": "pass1", "apn": "3gnet", "auth": "2", "ip": "2"},
    {"carrier": "CTNET", "name": "ctnet_profile1", "username": "user2", "password": "pass2", "apn": "ctnet", "auth": "2", "ip": "2"},
]
def init_auto_apn_result():
    # 检查是有需求增加运营商列表和apnlist
    add_apnlist_flag = True
    stdout, stderr = execute_shell_command("uci show apnlist |grep CMCC")
    if stderr:
        return False, f"查询运营商列表时出错: {stderr}"
    if "CMCC" in stdout:
        add_apnlist_flag = False
    
    if add_apnlist_flag:
        for carrier in carrier_list:
            carrier_cmd = f'''
            uci add apnlist carrier_info;
            uci set apnlist.@carrier_info[-1].carrier="{carrier["name"]}";
            uci set apnlist.@carrier_info[-1].mcc="{carrier["mcc"]}";
            uci set apnlist.@carrier_info[-1].mnc="{carrier["mnc"]}";
            uci set apnlist.carrier_info.count=$(($(uci get apnlist.carrier_info.count)+1));
            '''
            stdout, stderr = execute_shell_command(carrier_cmd)
            if stderr:
                return False, f"增加运营商列表时出错: {stderr}"

        for apn in apn_configs:
            apn_cmd = f'''
            uci add apnlist apn;
            uci set apnlist.@apn[-1].carrier="{apn["carrier"]}";
            uci set apnlist.@apn[-1].profile_name="{apn["name"]}";
            uci set apnlist.@apn[-1].name="{apn["apn"]}";
            uci set apnlist.@apn[-1].user="{apn["username"]}";
            uci set apnlist.@apn[-1].passwd="{apn["password"]}";
            uci set apnlist.@apn[-1].auth="{apn["auth"]}";
            uci set apnlist.@apn[-1].ipmode="{apn["ip"]}";
            uci set apnlist.@apn[-1].profile_prop="0";
            uci set apnlist.apn.count=$(($(uci get apnlist.apn.count)+1));
            '''
            print(f"  执行命令: {apn_cmd}")
            stdout, stderr = execute_shell_command(apn_cmd)
            if stderr:
                return False, f"增加 APN 时出错: {stderr}" 

def check_auto_apn_result():
    # 验证是否触发了自动匹配
    apn_status = "uci tmpget mmtmp.auto_apn.status"
    for i in range(30):
        print(f"  查询命令: {apn_status}")
        stdout, stderr = execute_shell_command(apn_status)
        if stderr:
            return False, f"查询自动匹配APN状态时出错: {stderr}"
        print(f"  查询结果: {stdout.strip()}")
        if "2" in stdout:
            print(f"自动匹配成功")
            break
        elif "3" in stdout:
            return False, "自动匹配APN失败"
        time.sleep(2)

    mcc, stderr = execute_shell_command("uci tmpget mmtmp.netinfo.uim_mcc")
    mnc, stderr = execute_shell_command("uci tmpget mmtmp.netinfo.uim_mnc")
    for carrier in carrier_list:
        if carrier["mcc"] == mcc.strip() and carrier["mnc"] == mnc.strip():
            print(f"当前运营商: {carrier['name']}")
            for apn in apn_configs:
                if apn["carrier"] == carrier["name"]:
                    profile_name = apn["name"]
                    print(f"当前profile name: {profile_name}")
            break
    
    auto_apn_cmd = "trc_mm_test --list-apn | head -1"
    auto_apn_result, stderr = execute_shell_command(auto_apn_cmd)
    if stderr:
        return False, f"获取APN时出错: {stderr}"
    
    print(f"期望profile name: {profile_name}, 当前自动匹配APN: {auto_apn_result.strip()}")
    if profile_name in auto_apn_result:
        print(f"当前profile name: {profile_name} 已匹配")
    else:
        return False, f"当前profile name: {profile_name} 未匹配"

    return True, "APN自动匹配测试成功"

def test_auto_apn():
    """
    功能测试 4: 测试自动配置 APN
    """
    init_auto_apn_result()
    # list apn list
    list_apn_cmd = "trc_mm_test --list-apn"
    stdout, stderr = execute_shell_command(list_apn_cmd)
    if stderr:
        return False, f"查询APN列表时出错: {stderr}"
    print(f"当前APN列表: \n{stdout.strip()}\n")

    # 切换一个手动的APN，验证是否会触发自动匹配
    get_one_apn_id = "trc_mm_test --list-apn | head -1 | awk -F'apn_id=' '{print $2}' | awk '{print $1}'"
    stdout, stderr = execute_shell_command(get_one_apn_id)
    if stderr:
        return False, f"获取APN时出错: {stderr}"
    manual_apn = stdout.strip()
    
    cmd = f"trc_mm_test --active-apn {manual_apn}"
    print(f"  执行命令: {cmd}")
    stdout, stderr = execute_shell_command(cmd)
    if stderr:
        return False, f"切换手动APN时出错: {stderr}"
    
    cmd = f"trc_mm_test --active-apn 0"
    print(f"  执行命令: {cmd}")
    stdout, stderr = execute_shell_command(cmd)
    if stderr:
        return False, f"切换自动匹配APN时出错: {stderr}"
    
    # 检查自动匹配的APN是否正确
    return check_auto_apn_result()

def test_auto_apn_by_switch_card():
    """
    功能测试 4: 测试自动配置 APN
    """
    init_auto_apn_result()
    # list apn list
    list_apn_cmd = "trc_mm_test --list-apn"
    stdout, stderr = execute_shell_command(list_apn_cmd)
    if stderr:
        return False, f"查询APN列表时出错: {stderr}"
    print(f"当前APN列表: \n{stdout.strip()}\n")

    # 查询当前卡slot
    cmd = f"trc_mm_test --set-cardslot 99"
    stdout, stderr = execute_shell_command(cmd)
    if stderr:
        return False, f"查询当前卡slot时出错: {stderr}"
    print(f"当前卡slot: {stdout.strip()}")
    simslot = 0
    if "simslot=0" in stdout.strip():
        simslot = 1
    elif "simslot=1" in stdout.strip():
        simslot = 0
    #切卡
    cmd = f"trc_mm_test --set-cardslot {simslot}"
    print(f"  执行命令: {cmd}")
    stdout, stderr = execute_shell_command(cmd)
    if stderr:
        return False, f"切换手动APN时出错: {stderr}"
    
    cmd = f"trc_mm_test --active-apn 0"
    print(f"  执行命令: {cmd}")
    stdout, stderr = execute_shell_command(cmd)
    if stderr:
        return False, f"切换自动匹配APN时出错: {stderr}"
    
    # 检查自动匹配的APN是否正确
    return check_auto_apn_result()

# ==========================================
# 主程序入口
# ==========================================

if __name__ == "__main__":
    # 实例化测试框架
    runner = TestFramework()
    
    # 注册测试用例
    runner.register_test(test_add_multiple_iccids)
    runner.register_test(test_active_iccid_lock)
    runner.register_test(test_net_mode)
    runner.register_test(test_auto_apn)
    runner.register_test(test_auto_apn_by_switch_card)
    
    # 可以在这里继续添加其他功能的测试函数
    # runner.register_test(test_other_feature)
    
    # 运行
    runner.run()
