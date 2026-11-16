# dev_tools

用 Python 写的一些操作设备（9606 / 9811 / 9813 / 9916 平台）的工具脚本。

- `tools/` —— 面向设备的工具，会被 GitHub Actions 打包成 Windows 单文件 exe 发布
- `scripts/` —— 仓库维护脚本（生成依赖清单、初始化本地凭据）
- `test_9606_by_webui.py` —— 基于 Playwright 的 WebUI 测试脚本，直接跑源码

## 目录结构

```
.
├── tools/                              # 设备工具（会被打包成 exe）
│   ├── common/                         # 公共实现
│   │   ├── at_runner.py                #   AT / Telnet 命令执行器
│   │   ├── credentials.py              #   设备凭据读取（不写进版本库）
│   │   ├── ssh_fetcher.py              #   SSH / SCP 下载器
│   │   └── tftp_fetcher.py             #   TFTP 导入导出服务
│   ├── credentials.example.json        # 凭据文件模板（提交进仓库）
│   ├── credentials.local.json          # 本地凭据文件（已 gitignore，不提交）
│   ├── enable_multiport_ssh_9606.py    # 9606 开启多端口 + dropbear ssh
│   ├── enable_multiport_ssh_9811.py    # 9811 开启多端口 + dropbear ssh
│   ├── enable_multiport_ssh_9813.py    # 9813 开启多端口 + dropbear ssh
│   ├── enable_multiport_telnet_9606.py # 9606 开启多端口 + telnetd
│   ├── enable_multiport_telnet_9916.py # 9916 开启多端口 + telnetd
│   ├── sim_lock_reset_mifi_9813.py     # 9813 清除 SIM 锁文件
│   ├── ssh_file_fetcher_9606.py        # 9606 SSH 下载文件 / 执行远程命令
│   ├── ssh_file_fetcher_9813.py        # 9813 SSH 下载文件
│   ├── tftp_fetcher_9606.py            # 9606 TFTP 导入导出服务
│   └── tftp_fetcher_9916.py            # 9916 TFTP 导入导出服务
├── scripts/
│   ├── init_credentials.py             # 生成 credentials.local.json
│   └── update_requirements.py          # 依据 tools/ 的 import 生成 requirements.txt
├── test_9606_by_webui.py               # Playwright WebUI 测试（需额外安装 playwright）
├── .github/workflows/
│   └── build-windows-executable.yml
└── requirements.txt
```

## 设备凭据

**设备口令不写进版本库。** 运行时从 `credentials.local.json` 读取，按以下顺序查找：

1. 环境变量 `DEVTOOLS_CREDENTIALS` 指定的文件
2. 打包成 exe 时：exe 同级目录下的 `credentials.local.json`
3. 源码运行时：`tools/credentials.local.json`

首次使用：

```bash
# 交互式填写，生成 tools/credentials.local.json
python scripts/init_credentials.py

# 已有文件想重填
python scripts/init_credentials.py --force
```

也可以手工创建：

```bash
cp tools/credentials.example.json tools/credentials.local.json
# 然后把里面的 REPLACE_ME 换成真实设备口令
```

`tools/credentials.local.json` 已在 `.gitignore` 中，不会被提交。

凭据文件格式（`tools/credentials.example.json`）：

```json
{
  "profiles": {
    "9606": {
      "telnet_pwd1": "REPLACE_ME",
      "telnet_pwd2": "REPLACE_ME",
      "ssh_password": "REPLACE_ME"
    },
    "9811": { "telnet_pwd1": "REPLACE_ME", "telnet_pwd2": "REPLACE_ME" },
    "9813": {
      "telnet_pwd1": "REPLACE_ME",
      "telnet_pwd2": "REPLACE_ME",
      "ssh_password": "REPLACE_ME"
    },
    "9916": { "telnet_pwd1": "REPLACE_ME", "telnet_pwd2": "REPLACE_ME" }
  }
}
```

找不到凭据文件时，脚本会打印明确的提示并以退出码 1 结束，不会带着空口令去连设备。

## 依赖

```bash
pip install -r requirements.txt
```

`requirements.txt` 由 `scripts/update_requirements.py` 依据 `tools/` 的实际 import 自动生成，
不要手工维护。改完代码后跑一次并提交：

```bash
python scripts/update_requirements.py
```

CI 会校验 `requirements.txt` 是否与代码一致，不一致直接失败。

`test_9606_by_webui.py` 需要额外依赖：

```bash
pip install playwright
playwright install chromium
```

## 使用方法

### 直接运行源码

```bash
# 工具脚本都在 tools/ 下，需要在该目录下运行（脚本用相对路径导入 common 包）
cd tools
python enable_multiport_ssh_9606.py
python ssh_file_fetcher_9813.py
```

`test_9606_by_webui.py` 在仓库根目录运行。

### 运行 Windows 可执行程序

从 [Releases](https://github.com/wjsuperstar/dev_tools/releases) 下载 exe，运行前把
`credentials.local.json` 放到 exe 同级目录。

## 本地构建

```powershell
# PyInstaller（默认后端）
pyinstaller --onefile --noconfirm --clean `
  --name ssh_file_fetcher_9813_pyinstaller `
  --distpath . --workpath build --specpath build `
  tools\ssh_file_fetcher_9813.py

# Nuitka（可选后端，产物更大、构建更慢）
python -m nuitka --lto=no --onefile --assume-yes-for-downloads `
  --include-dir=tools --include-package=common `
  --output-filename=ssh_file_fetcher_9813_nuitka.exe `
  tools\ssh_file_fetcher_9813.py
```

`--include-dir=tools --include-package=common` 是必需的：`tools/` 下的脚本通过
`sys.path.insert` 导入 `common` 包，打包时要显式告诉打包器带上这个包。

## GitHub Actions

`.github/workflows/build-windows-executable.yml` 在以下时机运行：

- push 到 `main` / `master`，或 push 到 `v*` 标签
- 向 `main` / `master` 提 PR
- 手动触发（workflow_dispatch）

**打包后端默认只构建 PyInstaller**，Nuitka 需要手动触发时勾选：

| 触发方式 | PyInstaller | Nuitka |
| --- | --- | --- |
| push / PR | ✅ | ❌ |
| 手动触发（默认） | ✅ | ❌ |
| 手动触发（勾选 Nuitka） | 按勾选 | ✅ |

流程：校验 `requirements.txt` -> 安装依赖 -> 逐个脚本打包 -> 汇总校验 -> 上传 artifact。

- **只有推 `v*` 标签时才会创建 Release**；普通 push / PR 只会上传
  [Actions artifact](https://github.com/wjsuperstar/dev_tools/actions)。
- 同一个脚本只要有一种启用的打包方式成功就算通过；所有启用的方式都失败才会让流水线失败。

创建 Release：

```bash
git tag v1.0.0 && git push origin v1.0.0
```

## 设备连接方式

| 方式 | 端口 | 说明 |
| --- | --- | --- |
| AT / Telnet | 5504 | 登录后执行 `AT+SYSTEM=...` / `AT+SYSTEMECHO=...` 等命令 |
| SSH | 22 | 9606 走 none 认证，9813 走标准口令认证 |
| TFTP | 69 | 研发主机作为 TFTP server，设备用 `tftp -g/-p` 拉/推文件 |

9606 的 SSH 需要 none 认证，`common/ssh_fetcher.py` 的 `transport_none` 模式会先按
none 认证连接，设备若要求口令认证则自动回退重试。

## 注意事项

- 脚本里的设备地址、端口是按开发环境写死的，换设备需要改 `tools/` 下各脚本顶部的
  `CONFIG` 字典。
- `tftp_fetcher_*.exe` 需要**以管理员身份运行**：TFTP 走 UDP 69 端口，
  Windows 上绑定 69 端口需要管理员权限，否则脚本会直接报错退出。
