from logging import raiseExceptions
from playwright.sync_api import sync_playwright, Page, expect
import time
import re
import os
import random
import sys

# 设备 WebUI 账号口令不写进版本库，从本地凭据文件读取
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from common.credentials import require_profile

_CRED = require_profile("9606")

mobile_net_setting = False

class LoginPage:
    """登录页面对象"""
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.locator('input[name="username"], input#username, input[type="text"]')
        self.password_input = page.locator('input[name="password"], input#password, input[type="password"]')
        self.login_button = page.locator('button[type="submit"], button:has-text("登录"), .login-btn')

    def login(self, username: str = None, password: str = None):
        """执行登录操作。缺省用凭据文件里的 WebUI 账号口令。"""
        if username is None:
            username = _CRED.get("webui_user", "admin")
        if password is None:
            password = _CRED["webui_password"]
        # 等待页面加载
        self.page.wait_for_load_state("networkidle")
        
        # 输入用户名和密码
        if self.username_input.count() > 0:
            self.username_input.fill(username)
        if self.password_input.count() > 0:
            self.password_input.fill(password)
        
        # 点击登录按钮
        self.login_button.click()
        
        # 等待登录完成，可能需要等待跳转或页面元素出现
        self.page.wait_for_load_state("networkidle")
        
        self.page.wait_for_timeout(3000)
        
class BaseInfoPage:
    """基本信息页面对象"""
    def __init__(self, page: Page):
        self.page = page

    def navigate_to_base_info(self):
        """导航到基本信息页面"""
        print("导航到基本信息页面...")
        global mobile_net_setting
        # 根据调试发现，页面使用Element UI，需要查找侧边栏菜单
        # 尝试多种可能的导航方式
        
        # 首先尝试查找包含'网络'的菜单项
        network_selectors = [
            'text="基本信息"',
            '.el-sub-menu:has-text("基本信息")',
            '[class*="menu"]:has-text("基本信息")'
        ]
        
        navigated = False
        for selector in network_selectors:
            try:
                element = self.page.locator(selector)
                if element.count() > 0:
                    print(f"找到基本信息相关菜单: {selector}")
                    element.first.click()
                    navigated = True
                    break
            except:
                continue
        
        if not navigated:
            raise Exception("警告: 未找到基本信息导航菜单项")
        
        # 等待页面加载
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)
        mobile_net_setting = False

    def navigate_to_info_settings(self):
        """导航到信息设置页面"""
        print("导航到信息设置页面...")
        
        # 尝试多种可能的PIN设置导航方式
        pin_selectors = [
            'text="信息"',
            'text="INFO"',
            '.el-menu-item:has-text("信息")',
            '.el-sub-menu:has-text("INFO")'
        ]
        
        navigated = False
        for selector in pin_selectors:
            try:
                element = self.page.locator(selector)
                if element.count() > 0:
                    print(f"找到信息设置菜单: {selector}")
                    element.first.click()
                    navigated = True
                    break
            except:
                continue
        
        if not navigated:
            raise Exception("警告: 未找到信息设置菜单")
        
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

class MobileNetworkPage:
    """移动网络设置页面对象"""
    def __init__(self, page: Page):
        self.page = page

    def navigate_to_mobile_network(self):
        """导航到移动网络设置页面"""
        print("导航到移动网络设置页面...")
        global mobile_net_setting
        if mobile_net_setting:
            return
        
        # 根据调试发现，页面使用Element UI，需要查找侧边栏菜单
        # 尝试多种可能的导航方式
        
        # 首先尝试查找包含'网络'的菜单项
        network_selectors = [
            'text="移动网络设置"',
            '.el-sub-menu:has-text("网络")',
            '[class*="menu"]:has-text("网络")'
        ]
        
        navigated = False
        for selector in network_selectors:
            try:
                element = self.page.locator(selector)
                if element.count() > 0:
                    print(f"找到网络相关菜单: {selector}")
                    element.first.click()
                    navigated = True
                    break
            except:
                continue
        
        if not navigated:
            print("未找到网络相关菜单，尝试查找所有菜单项")
            # 如果没找到网络菜单，尝试查找其他可能的导航项
            all_menu_items = self.page.locator('.el-menu-item, .el-sub-menu, [role="menuitem"], a')
            for i in range(all_menu_items.count()):
                try:
                    menu_item = all_menu_items.nth(i)
                    text = menu_item.text_content().strip()
                    if text and any(keyword in text for keyword in ["设置", "配置", "系统"]):
                        print(f"尝试点击菜单项: {text}")
                        menu_item.click()
                        navigated = True
                        break
                except:
                    continue
        
        if not navigated:
            raise Exception("警告: 未找到合适的导航菜单项")
        
        # 等待页面加载
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)
        mobile_net_setting = True

    def navigate_to_connection_settings(self):
        """导航到连接设置页面"""
        print("导航到连接设置页面...")
        
        # 尝试多种可能的连接设置导航方式
        connection_selectors = [
            'text="连接设置"',
            'text="APN设置"',
            'text="连接"',
            '.el-menu-item:has-text("连接")',
            '.el-sub-menu:has-text("连接")',
            '.el-menu-item:has-text("APN")',
            '.el-sub-menu:has-text("APN")'
        ]
        
        navigated = False
        for selector in connection_selectors:
            try:
                element = self.page.locator(selector)
                if element.count() > 0:
                    print(f"找到连接设置菜单: {selector}")
                    element.first.click()
                    navigated = True
                    break
            except:
                continue
        
        if not navigated:
            raise Exception("警告: 未找到连接设置菜单")
        
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

    def navigate_to_sim_esim_settings(self):
        """导航到SIM/eSIM设置页面"""
        print("导航到SIM/eSIM设置页面...")
        
        # 尝试多种可能的SIM/eSIM设置导航方式
        sim_selectors = [
            'text="SIM1/SIM2/eSIM设置"',
            'text="eSIM设置"',
            'text="SIM"',
            'text="eSIM"',
            '.el-menu-item:has-text("SIM")',
            '.el-sub-menu:has-text("SIM")',
            '.el-menu-item:has-text("eSIM")',
            '.el-sub-menu:has-text("eSIM")'
        ]
        
        navigated = False
        for selector in sim_selectors:
            try:
                element = self.page.locator(selector)
                if element.count() > 0:
                    print(f"找到SIM/eSIM设置菜单: {selector}")
                    element.first.click()
                    navigated = True
                    break
            except:
                continue
        
        if not navigated:
            raise Exception("警告: 未找到SIM/eSIM设置菜单")
        
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

    def navigate_to_band_settings(self):
        """导航到Band设置页面"""
        print("导航到Band设置页面...")
        
        # 尝试多种可能的Band设置导航方式
        band_selectors = [
            'text="Band设置"',
            'text="Band"',
            '.el-menu-item:has-text("Band")',
            '.el-sub-menu:has-text("Band")'
        ]
        
        navigated = False
        for selector in band_selectors:
            try:
                element = self.page.locator(selector)
                if element.count() > 0:
                    print(f"找到Band设置菜单: {selector}")
                    element.first.click()
                    navigated = True
                    break
            except:
                continue
        
        if not navigated:
            raise Exception("警告: 未找到Band设置菜单")
        
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)
    def navigate_to_pin_settings(self):
        """导航到PIN设置页面"""
        print("导航到PIN设置页面...")
        
        # 尝试多种可能的PIN设置导航方式
        pin_selectors = [
            'text="PIN设置"',
            'text="PIN"',
            '.el-menu-item:has-text("PIN")',
            '.el-sub-menu:has-text("PIN")'
        ]
        
        navigated = False
        for selector in pin_selectors:
            try:
                element = self.page.locator(selector)
                if element.count() > 0:
                    print(f"找到PIN设置菜单: {selector}")
                    element.first.click()
                    navigated = True
                    break
            except:
                continue
        
        if not navigated:
            raise Exception("警告: 未找到PIN设置菜单")
        
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

    def navigate_to_mtu_settings(self):
        """导航到MTU设置页面"""
        print("导航到MTU设置页面...")
        
        # 尝试多种可能的MTU设置导航方式
        mtu_selectors = [
            'text="MTU设置"',
            'text="MTU"',
            '.el-menu-item:has-text("MTU")',
            '.el-sub-menu:has-text("MTU")'
        ]
        
        navigated = False
        for selector in mtu_selectors:
            try:
                element = self.page.locator(selector)
                if element.count() > 0:
                    print(f"找到MTU设置菜单: {selector}")
                    element.first.click()
                    navigated = True
                    break
            except:
                continue
        
        if not navigated:
            raise Exception("警告: 未找到MTU设置菜单")
        
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

class APNPage:
    """APN设置页面对象"""
    def __init__(self, page: Page):
        self.page = page
        self.add_button = page.locator('button:has-text("添加"), .add-apn-btn, [data-action="add"]')
        self.save_button = page.locator('button:has-text("保存"), .save-btn, [data-action="save"]')
        self.delete_button = page.locator('button:has-text("删除"), .delete-btn, [data-action="delete"]')
        self.apn_rows = page.locator('.apn-row, .apn-item, tr.apn')

    def create_apn(self, config_name: str, username: str, password: str, apn: str, auth_type: str = "PAP", ip_type: str = "IPv4"):
        """创建APN"""
        print(f"开始创建APN: {config_name}")
        
        # 等待页面加载完成
        self.page.wait_for_load_state("networkidle")
        
        # 等待添加按钮可点击
        try:
            self.page.wait_for_selector('button:has-text("添加"), .add-apn-btn, [data-action="add"]', state="visible", timeout=5000)
            self.add_button.click()
            print("已点击添加按钮")
        except:
            print("警告: 添加按钮未找到或不可点击，尝试其他方式")
            # 尝试查找其他可能的添加按钮
            alt_add_btns = self.page.locator('button:has-text("新建"), button:has-text("新增"), [class*="add" i]')
            if alt_add_btns.count() > 0:
                alt_add_btns.first.click()
                print("点击了备用添加按钮")
            else:
                print("错误: 未找到任何添加按钮")
                return False
        
        # 等待表单字段加载
        self.page.wait_for_timeout(2000)
        
        # 填写表单
        try:
            # APN名称
            self.page.get_by_label("配置名称").fill(config_name)
            # 用户名
            self.page.get_by_label("用户名").fill(username)
            # 密码
            self.page.get_by_label("密码").fill(password)
            # APN
            self.page.get_by_label("APN").fill(apn)
            self.page.wait_for_timeout(2000)
        except Exception as e:
            print(f"填写APN表单时出错: {e}")
            
        # 选择认证类型
        try:
            self.page.locator("#app").get_by_text("CHAP").click()
            self.page.get_by_role("option", name=auth_type).click()
        except Exception as e:
            print(f"选择认证类型时出错: {e}")
            
        # 选择IP类型
        try:
            self.page.locator("div").filter(has_text=re.compile(r"^IPv4/v6$")).nth(4).click()
            self.page.get_by_role("option", name=ip_type, exact=True).click()
        except Exception as e:
            print(f"选择IP类型时出错: {e}")
        
        time.sleep(1)
        # 点击保存
        try:
            if self.save_button.count() > 0:
                self.save_button.click()
                print("已点击保存按钮")
            else:
                print("警告: 未找到保存按钮")
                # 尝试其他可能的保存按钮
                alt_save_btns = self.page.locator('button:has-text("确定"), [data-action="save"], .save-btn')
                if alt_save_btns.count() > 0:
                    alt_save_btns.click()
                    print("点击了备用保存按钮")
        except Exception as e:
            print(f"点击保存按钮时出错: {e}")
            
        # 等待保存完成
        self.page.wait_for_timeout(8000)
        print(f"APN {config_name} 创建完成")
        return True

    def delete_apn(self, apn_name: str = None):
        """删除APN"""
        print(f"正在删除APN: {apn_name}")
        # 从"设置默认APN"下拉菜单中选择APN
        self.page.locator("form").get_by_role("img").first.click()
        self.page.get_by_role("option", name=apn_name).last.click()
        
        # 删除APN
        if self.delete_button.count() > 0:
            self.delete_button.first.click()
        else:
            # 如果没有直接的删除按钮，尝试通过行操作删除
            apn_rows = self.page.locator('.apn-row, .apn-item, tr.apn')
            if apn_rows.count() > 0:
                # 点击第一行的删除操作
                delete_btn = apn_rows.first.locator('button:has-text("删除"), .delete-btn, [data-action="delete"]')
                if delete_btn.count() > 0:
                    delete_btn.first.click()

        self.page.wait_for_timeout(2000)

    def set_default_apn(self, apn_name: str):
        """设置默认APN"""
        # 从下拉菜单选择APN
        print(f"正在设置默认APN: {apn_name}")
        self.page.locator("form").get_by_role("img").first.click()
        self.page.get_by_role("option", name=apn_name).last.click()
        
        # 点击保存
        try:
            if self.save_button.count() > 0:
                self.save_button.click()
                print("已点击保存按钮")
            else:
                print("警告: 未找到保存按钮")
                # 尝试其他可能的保存按钮
                alt_save_btns = self.page.locator('button:has-text("确定"), [data-action="save"], .save-btn')
                if alt_save_btns.count() > 0:
                    alt_save_btns.click()
                    print("点击了备用保存按钮")
        except Exception as e:
            print(f"点击保存按钮时出错: {e}")
        
        self.page.wait_for_timeout(1000)


class SIMESimPage:
    """SIM/eSIM设置页面对象"""
    def __init__(self, page: Page):
        self.page = page
        self.slot_name_list = ["SIM1", "SIM2", "eSIM"]

    def test_get_dropbox_list(self):
        """测试获取下拉框"""
        # 获取下拉框元素
        dropdown_list = []
        options = self.page.locator('.el-select-dropdown__item')
        count = options.count()
        print(f"下拉元素个数: {count}")
        for i in range(count):
            option = options.nth(i)
            text = option.text_content()
            print(f"  下拉选项 {i+1}: {text}")
            dropdown_list.append(text)
        return dropdown_list
    
    def test_get_current_dropbox_option(self):
        # 获取当前选中的值
        selected_item = self.page.locator('.el-select__selected-item').last
        selected_text = selected_item.text_content() if  selected_item.count() > 0 else None
        print(f"获取当前选中的APN: {selected_text}")
        return selected_text
    
    def test_get_current_sim_slot(self):
        """测试获取当前SIM槽"""
        slot_idx_list = []
        radios = self.page.locator('input[type="radio"]')
        count = radios.count()
        # 遍历检查哪个被选中
        for i in range(count):
            radio = radios.nth(i)
            is_checked = radio.is_checked()
            # 获取更多信息
            value = radio.get_attribute('value')
            if is_checked:
                return self.slot_name_list[int(value)]
        return None
    
    def test_get_sim_slot_list(self):
        """测试获取SIM槽列表"""
        slot_idx_list = []
        radios = self.page.locator('input[type="radio"]')
        count = radios.count()
        print(f"找到 {count} 个单选框")
        # 遍历检查哪个被选中
        for i in range(count):
            radio = radios.nth(i)
            is_checked = radio.is_checked()
            # 获取更多信息
            value = radio.get_attribute('value')
            name = radio.get_attribute('name')
            id_attr = radio.get_attribute('id')
            
            print(f"第 {i+1} 个单选框被选中:")
            print(f"  - value: {value}")
            print(f"  - name: {name}")
            print(f"  - id: {id_attr}")
            print(f"  - 选中状态: {is_checked}")
            if not is_checked:
                slot_idx_list.append(self.slot_name_list[int(value)])
        print(f"找到 {len(slot_idx_list)} 个未选中的SIM槽: {slot_idx_list}")
        return slot_idx_list

    def test_sim_esim_settings(self):
        """测试SIM/eSIM设置功能"""
        print("开始SIM/eSIM设置测试...")
        
        # 获取可切换的SIM槽列表
        sim_slot_list = self.test_get_sim_slot_list()
        for slot_name in sim_slot_list:
            # 切换卡槽
            print(f"------------------>切换到卡槽: [{slot_name}]")
            self.page.get_by_text(slot_name.strip(), exact=True).click()
            self.page.wait_for_timeout(3000)
            time.sleep(2);
            save_button = self.page.locator('button:has-text("保存"), .save-btn, [data-action="save"]')
            if save_button.is_visible():
                # 选择APN：
                print(f"选择APN:")
                dropdown_list = self.test_get_dropbox_list()
                dropdown_list_idx = random.randint(1, len(dropdown_list) - 2)
                print(f"得到APN: {dropdown_list[dropdown_list_idx]}")
                self.page.locator("form").get_by_role("img").last.click()
                self.page.wait_for_timeout(1000)
                self.page.get_by_role("option", name=dropdown_list[dropdown_list_idx]).last.click()
                self.page.wait_for_timeout(1000)
                # 点击保存
                print("点击保存按钮")
                save_button.click()
                self.page.wait_for_timeout(5000)

                # 检查切换卡槽是否成功
                current_slot = self.test_get_current_sim_slot()
                print(f"切换后的SIM槽: {current_slot}")
                if current_slot != slot_name:
                    raise Exception(f"切换到卡槽: {slot_name} 失败")
                
                # 检查APN是否切换成功
                current_apn = self.test_get_current_dropbox_option()
                print(f"切换后的APN: {current_apn}")
                if current_apn != dropdown_list[dropdown_list_idx]:
                    raise Exception(f"切换到APN: {dropdown_list[dropdown_list_idx]} 失败")
                print(f"切换到卡槽 {slot_name} 成功")
                time.sleep(1);
            else:
                print(f"------------------>跳过: {slot_name}")
        print("SIM/eSIM设置测试完成")

class BandPage:
    """Band设置页面对象"""
    def __init__(self, page: Page):
        self.page = page

    def test_get_checkbox_list(self):
        # 获取复选框组 (el-checkbox-group) 下的所有选项
        band_list = []
        groups = self.page.locator(".el-checkbox-group").all()
        for group in groups:
            checkboxes = group.locator(".el-checkbox")
            count = checkboxes.count()
            print(f"找到 {count} 个复选框")
            band_dict = {}
            for i in range(count):
                box = checkboxes.nth(i)
                label_text = box.text_content().strip()
                
                # 判断是否选中：检查 class 属性中是否包含 'is-checked'
                # 注意：is-checked 通常在 .el-checkbox__input 上，但也可能在 .el-checkbox 上
                # 最稳妥的方法是检查整个组件内部是否有 .is-checked 类
                class_str = box.get_attribute("class")
                is_checked = "is-checked" in class_str
                # print(f"选项 '{label_text}' : {is_checked}")
                band_dict[label_text] = is_checked
            band_list.append(band_dict)

        return band_list
    
    def test_set_checkbox_list(self, band_dict_list):
        print(f"enter...")
        groups = self.page.locator(".el-checkbox-group").all()
        for group in groups:
            i = groups.index(group)
            for key, value in band_dict_list[i].items():
                if not value:
                    pattern = re.compile(rf"^\s*{key}\s*$")
                    print(f"正在选择: {key}")
                    target_box = group.locator(".el-checkbox").filter(has_text=pattern)
                    target_box.click()
                    self.page.wait_for_timeout(2000)
    
    def test_save_band_list(self):
        save_button = self.page.locator('button:has-text("保存"), .save-btn, [data-action="save"]')
        save_button.click()
        self.page.wait_for_timeout(2000)


class PINPage:
    """PIN设置页面对象"""
    def __init__(self, page: Page):
        self.page = page

    def test_get_pin_state(self):
        # --- 获取 "PIN状态" ---
        # 逻辑：找到文本完全匹配 "PIN状态" 的元素，取它后面紧邻的第一个兄弟元素
        # xpath=following-sibling::* 表示“之后的所有同级元素”，.first 取第一个
        pin_status = self.page.get_by_text("PIN状态", exact=True).locator("xpath=following-sibling::*").first.text_content()
        print(f"PIN状态: {pin_status}")

        # --- 获取 "3" (PIN剩余尝试次数) ---
        pin_attempts = self.page.get_by_text("PIN剩余尝试次数").locator("xpath=following-sibling::*").first.text_content()
        print(f"PIN剩余次数: {pin_attempts}")

        # --- 获取 "10" (PUK剩余尝试次数) ---
        puk_attempts = self.page.get_by_text("PUK剩余尝试次数").locator("xpath=following-sibling::*").first.text_content()
        print(f"PUK剩余次数: {puk_attempts}")
        return pin_status,pin_attempts,puk_attempts
    
    def test_click_pin_opt(self, opt):
        self.page.locator("label").filter(has_text=opt).first.click()
        self.page.wait_for_timeout(2000)
    
    def test_click_auto_pin_opt(self, opt):
        self.page.locator("label").filter(has_text=opt).last.click()
        self.page.wait_for_timeout(2000)

    def test_input_pin_passwd(self, passwd):
        self.page.get_by_label("PIN码", exact=True).fill(passwd)
        self.page.wait_for_timeout(2000)
    
    def test_modify_pin_passwd(self, old, new):
        self.page.get_by_label("PIN码", exact=True).fill(old)
        self.page.get_by_label("新PIN码", exact=True).fill(new)
        self.page.get_by_label("确认PIN码", exact=True).fill(new)
        self.page.wait_for_timeout(2000)

    def test_save_pin_pwd(self):
        save_button = self.page.locator('button:has-text("保存"), .save-btn, [data-action="save"]').first
        save_button.click()
        self.page.wait_for_timeout(2000)

    def test_save_auto_pin(self):
        save_button = self.page.locator('button:has-text("保存"), .save-btn, [data-action="save"]').last
        save_button.click()
        self.page.wait_for_timeout(2000)


class MTUPage:
    """MTU设置页面对象"""
    def __init__(self, page: Page):
        self.page = page

    def test_input_mtu_value(self, value):
        print(f"输入MTU值: {value}")
        self.page.get_by_label("MTU值", exact=True).fill(f"{value}")
        self.page.wait_for_timeout(2000)
    
    def test_get_mtu_value(self):
        ret = self.page.get_by_label("MTU值", exact=True).input_value()
        print(f"获取MTU值: {ret}")
        return int(ret.strip())

    def test_save_mtu_value(self):
        save_button = self.page.locator('button:has-text("保存"), .save-btn, [data-action="save"]').first
        save_button.click()
        self.page.wait_for_timeout(2000)

class InfoPage:
    """INFO页面对象"""
    def __init__(self, page: Page):
        self.page = page

    def test_get_wan_state(self):
        wan_ip = self.page.get_by_text("WAN IP地址").locator("xpath=following-sibling::*").first.text_content()
        print(f"WAN IP地址: {wan_ip}")
        return wan_ip

def run_apn_test(page: Page):
    """运行APN测试"""
    print("开始APN测试...")
    
    # 导航到移动网络设置
    mobile_page = MobileNetworkPage(page)
    mobile_page.navigate_to_mobile_network()
    mobile_page.navigate_to_connection_settings()
    
    # 创建APN页面对象
    apn_page = APNPage(page)
    
    # 创建4个APN
    apn_configs = [
        {"name": "APN_Test_0", "username": "user1", "password": "1234", "apn": "test", "auth": "PAP", "ip": "IPv4/v6"},
        {"name": "APN_Test_1", "username": "user1", "password": "pass1", "apn": "", "auth": "PAP", "ip": "IPv4"},
        {"name": "APN_Test_2", "username": "user2", "password": "pass2", "apn": "internet2", "auth": "CHAP", "ip": "IPv6"},
        {"name": "APN_Test_3", "username": "user3", "password": "pass3", "apn": "internet3", "auth": "PAP", "ip": "IPv4/v6"}
    ]
  
    for config in apn_configs:
        print(f"创建APN: {config['name']}")
        apn_page.create_apn(
            config_name=config["name"],
            username=config["username"],
            password=config["password"],
            apn=config["apn"],
            auth_type=config["auth"],
            ip_type=config["ip"])
        time.sleep(1)  # 等待创建完成
    print("所有APN创建完成")
    
    # 按要求执行删除操作：先从设置默认APN下拉菜单选择一个非当前APN，再删除
    print("删除一个APN（先选择非当前APN，再删除）...")
    apn_idx = random.randint(1, len(apn_configs) - 2)
    apn_page.delete_apn(apn_configs[apn_idx]["name"])
    
    # 设置默认APN为另一个APN
    print("设置第一个APN为默认APN...")
    # 重新获取APN选项并设置默认APN
    apn_page.set_default_apn(apn_configs[0]["name"])
    print("APN测试完成")

def run_sim_esim_test(page: Page):
    """运行SIM/eSIM设置测试"""
    print("开始SIM/eSIM设置测试...")
    
    # 导航到SIM/eSIM设置
    mobile_page = MobileNetworkPage(page)
    mobile_page.navigate_to_mobile_network()
    mobile_page.navigate_to_sim_esim_settings()
    page.wait_for_timeout(2000)
    time.sleep(2)
    # 创建SIM/eSIM页面对象并执行测试
    sim_esim_page = SIMESimPage(page)
    sim_esim_page.test_sim_esim_settings()


def run_band_test(page: Page):
    """运行Band设置测试"""
    print("开始Band设置测试...")
    # 导航到Band设置
    mobile_page = MobileNetworkPage(page)
    mobile_page.navigate_to_mobile_network()
    mobile_page.navigate_to_band_settings()
    
    # 创建Band页面对象并执行测试
    band_page = BandPage(page)
    print("检查默认选项...")
    band_lists = band_page.test_get_checkbox_list()
    print(f'band_lists = {band_lists}')
    for band_dict in band_lists:
        sel_band_dict = {k:v for k,v in band_dict.items() if v}
        if ('B' in list(band_dict.keys())[0] or 'b' in list(band_dict.keys())[0]) and len(sel_band_dict) == 11:
            print("检查默认lte band list成功")
        elif ('n' in list(band_dict.keys())[0] or 'N' in list(band_dict.keys())[0]) and len(sel_band_dict) == 10:
            print("检查默认nr5g band list成功")
        else:
            raise Exception("默认band list选项数量错误", band_dict)
    # 设置band list
    print("设置band list...")
    record_random_band_list = []
    for band_dict in band_lists:
        random_list = random.sample(list(band_dict.keys()), 2)
        print(f'random_list = {random_list}')
        record_random_band_list.append(random_list)
        if 'B' in list(band_dict.keys())[0] or 'b' in list(band_dict.keys())[0]:
            band_dict[random_list[0]] = False
            band_dict[random_list[1]] = False
        elif 'n' in list(band_dict.keys())[0] or 'N' in list(band_dict.keys())[0]:
            band_dict[random_list[0]] = False
            band_dict[random_list[1]] = False
        
    band_page.test_set_checkbox_list(band_lists)
    print("保存设置...")
    band_page.test_save_band_list()

    time.sleep(2)
    print("检查保存是否成功:")
    band_lists = band_page.test_get_checkbox_list()
    #print(f'band_lists2 = {band_lists}, record_random_band_list={record_random_band_list}')
    for band_dict in band_lists:
        i = band_lists.index(band_dict)
        sel_key1 = record_random_band_list[i][0]
        sel_key2 = record_random_band_list[i][1]
        #print(f'i={i}, sel_key1 = {sel_key1}, sel_key2={sel_key2}')
        if band_dict[sel_key1] or band_dict[sel_key2]:
            raise Exception("保存的band list错误", band_dict)
        else:
            print("保存的band list成功")
    time.sleep(2)
    print("恢复默认设置...")
    band_page.test_set_checkbox_list(band_lists)
    band_page.test_save_band_list()

def run_pin_test(page: Page):
    """运行PIN设置测试"""
    print("开始PIN设置测试...")
    default_pwd = "1234"
    modify_pwd = "5678"
    
    # 导航到PIN设置
    mobile_page = MobileNetworkPage(page)
    mobile_page.navigate_to_mobile_network()
    mobile_page.navigate_to_pin_settings()
    
    pin_page = PINPage(page)
    pin_status,pin_attempts,puk_attempts = pin_page.test_get_pin_state()
    if pin_status == "PIN已停用":
        pin_page.test_click_pin_opt("锁定")
        pin_page.test_input_pin_passwd(default_pwd)
        pin_page.test_save_pin_pwd()
        page.wait_for_timeout(3000)
        pin_status,pin_attempts,puk_attempts = pin_page.test_get_pin_state()
        if pin_status == "PIN已启用":
            print("PIN已启用")
        else:
            raise Exception("PIN设置失败: ", pin_status)
    elif pin_status == "PIN已锁定":
        pin_page.test_click_pin_opt("解锁")
        pin_page.test_input_pin_passwd(default_pwd)
        pin_page.test_save_pin_pwd()
        page.wait_for_timeout(3000)
        pin_status,pin_attempts,puk_attempts = pin_page.test_get_pin_state()
        if pin_status == "PIN已启用":
            print("PIN解锁成功")
        else:
            raise Exception("PIN解锁失败: ", pin_status)

    time.sleep(1)
    # modify pin
    pin_page.test_click_pin_opt("修改")
    pin_page.test_modify_pin_passwd(default_pwd, modify_pwd)
    pin_page.test_save_pin_pwd()
    page.wait_for_timeout(3000)
    pin_status,pin_attempts,puk_attempts = pin_page.test_get_pin_state()
    if pin_attempts == "3":
        print("PIN修改成功")
    else:
        raise Exception("PIN修改失败", pin_status)
    
    time.sleep(1)
    # modify pin again
    pin_page.test_click_pin_opt("修改")
    pin_page.test_modify_pin_passwd(modify_pwd, default_pwd)
    pin_page.test_save_pin_pwd()
    pin_status,pin_attempts,puk_attempts = pin_page.test_get_pin_state()
    if pin_attempts == "3":
        print("PIN修改成功2")
    else:
        raise Exception("PIN修改失败2", pin_status)
    
    # Auto PIN
    pin_page.test_click_auto_pin_opt("启用")
    pin_page.test_save_auto_pin()

    time.sleep(1)
    # disable pin
    pin_page.test_click_pin_opt("禁用")
    pin_page.test_input_pin_passwd(default_pwd)
    pin_page.test_save_pin_pwd()
    time.sleep(1)
    pin_status,pin_attempts,puk_attempts = pin_page.test_get_pin_state()
    if pin_status == "PIN已停用":
        print("PIN已停用")
    else:
        raise Exception("PIN停用失败", pin_status)

def run_mtu_test(page: Page):
    """运行MTU设置测试"""
    print("开始MTU设置测试...")
    modify_mtu_value = 1428

    # 导航到MTU设置
    mobile_page = MobileNetworkPage(page)
    mobile_page.navigate_to_mobile_network()
    mobile_page.navigate_to_mtu_settings()
    
    mtu_page = MTUPage(page)
    mtu_page.test_input_mtu_value(modify_mtu_value)
    mtu_page.test_save_mtu_value()

    # 按F5刷新页面
    # page.reload(timeout=3000)
    # page.wait_for_load_state("networkidle")
    
    # 获取MTU值
    mtu_value = mtu_page.test_get_mtu_value()
    print(f"当前MTU值: {mtu_value}")
    if mtu_value == modify_mtu_value:
        print("MTU值修改成功")
    else:
        raise Exception("MTU值修改失败", mtu_value)

    base_info_page = BaseInfoPage(page)
    base_info_page.navigate_to_base_info()
    base_info_page.navigate_to_info_settings()
    info_page = InfoPage(page)
    wan_ip = info_page.test_get_wan_state()
    is_connected = False
    # 检查IP长度大于0
    if len(wan_ip) > 0:
        is_connected = True
        print("WAN IP地址获取成功")

    if is_connected:
    # 通过PING测试检查MTU值是否生效
        # 首先获取PIN命令的源IP地址，通过在window上cmd执行ipconfig |findstr 192.168.200
        # C:\Users\wujian>ipconfig |findstr 192.168.200
        # IPv4 地址 . . . . . . . . . . . . : 192.168.200.139
        src_ipaddress_cmd = "ipconfig |findstr.exe \"IPv4 地址\" |findstr 192.168.200"
        ip_address = os.popen(src_ipaddress_cmd).read().split(":")[-1].strip()
        print(f"RNDIS口IP地址: {ip_address}")
        
        # 检查PING是否成功
        icmp_pack_size = modify_mtu_value - 28
        ping_command = f"ping 8.8.4.4 -S {ip_address} -l {icmp_pack_size} -f"  
        print(f"执行ping命令: {ping_command}")
        ping_result = os.popen(ping_command).read()
        if ("100% 丢失" not in ping_result):
            print(f'检查MTU={icmp_pack_size} 成功')
        else:
            raise Exception("检查MTU失败", ping_result)
        
        time.sleep(2)
        icmp_pack_size = modify_mtu_value - 27
        ping_command = f"ping 8.8.4.4 -S {ip_address} -l {icmp_pack_size} -f"  
        print(f"执行ping命令: {ping_command}")
        ping_result = os.popen(ping_command).read()
        if ("需要拆分数据包但是设置 DF" in ping_result):
            print(f'检查MTU={icmp_pack_size} 成功')
        else:
            raise Exception("检查MTU失败", ping_result)

def main():
    """主测试函数"""
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-dev-shm-usage'])  # 设为False以便观察测试过程
        page = browser.new_page()
        
        try:
            # 设置页面超时时间
            page.set_default_timeout(30000)  # 30秒超时
            
            # 访问网站
            print("访问网站: http://192.168.200.1/")
            page.goto("http://192.168.200.1/")
            
            # 创建登录页面对象并登录
            login_page = LoginPage(page)
            print("执行登录...")
            login_page.login()  # 账号口令取自本地凭据文件
            
            # 等待登录完成
            page.wait_for_load_state("networkidle")

            popup_locator = page.get_by_text("SIM/eSIM卡已锁定")
            # 定义处理函数：点击关闭按钮
            def on_popup():
                print("检测到弹窗，正在执行关闭操作...")
                # 在这个函数里，定位并点击关闭按钮
                # 注意：有时候 locator 本身就是关闭按钮，有时候是弹窗容器
                page.get_by_role("button", name="取消").click() 
                # 或者 locator.locator(".close-btn").click()
                popup_locator.wait_for(state="hidden", timeout=3000)
                print("弹窗已关闭成功")

            # 注册 Handler
            # 只要 popup_locator 出现并干扰了操作，就会触发 on_popup
            page.add_locator_handler(popup_locator, on_popup)

            print("\n=== 开始APN测试 ===")
            run_apn_test(page)
            print("\n=== 开始SIM/eSIM设置测试 ===")
            run_sim_esim_test(page)
            print("\n=== 开始Band设置测试 ===")
            run_band_test(page)
            print("\n=== 开始PIN设置测试 ===")
            run_pin_test(page)
            #print("\n=== 开始MTU设置测试 ===")
            #run_mtu_test(page)
            print("\n所有测试完成！")
            
        except Exception as e:
            print(f"\n测试过程中出现错误: {str(e)}")
            # 截图以便调试
            try:
                page.screenshot(path="error_screenshot.png")
                print("已保存错误截图: error_screenshot.png")
            except:
                print("保存截图失败")
            
        finally:
            # 关闭浏览器
            browser.close()


if __name__ == "__main__":
    main()