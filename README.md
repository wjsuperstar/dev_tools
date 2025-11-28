# SSH File Fetcher

通过SSH协议从远程服务器获取指定文件的Python脚本，可编译为Windows可执行程序。

## 功能

- 通过SSH连接到指定服务器
- 从服务器的/tmp目录下获取所有以"all"开头的文件
- 将文件下载到本地目录

## 项目结构

```
├── tools/
│   ├── enable_multiport_ssh_9606.py
│   ├── enable_multiport_ssh_9811.py
│   ├── enable_multiport_ssh_9813.py
│   ├── sim_lock.py
│   └── ssh_file_fetcher.py
├── .github/workflows/
│   └── build-windows-executable.yml
├── README.md
└── requirements.txt
```

## 使用方法

### 直接运行Python脚本

```bash
cd tools
python ssh_file_fetcher.py
python sim_lock.py
```

### 运行Windows可执行程序

下载release中的exe文件，双击运行即可。每个脚本会生成两个版本的可执行程序：
- `*_nuitka.exe` - 使用Nuitka打包的版本
- `*_pyinstaller.exe` - 使用PyInstaller打包的版本

如果一个版本在某些系统上运行失败，可以尝试另一个版本。

## 构建

### 使用Nuitka构建Windows可执行程序

```bash
# 构建单个脚本
python -m nuitka --lto=no --onefile tools/ssh_file_fetcher.py

# 构建所有脚本（Nuitka版本）
Get-ChildItem -Path "tools" -Filter "*.py" | ForEach-Object {
  python -m nuitka --lto=no --onefile $_.FullName
}
```

### 使用PyInstaller构建Windows可执行程序

```bash
# 构建单个脚本
pyinstaller --onefile tools/ssh_file_fetcher.py

# 构建所有脚本（PyInstaller版本）
Get-ChildItem -Path "tools" -Filter "*.py" | ForEach-Object {
  pyinstaller --onefile $_.FullName
}
```

## GitHub Actions

每次提交到main或master分支时，GitHub Actions会自动构建tools目录下所有Python脚本的Windows可执行程序并创建release。每个脚本会生成两个版本：
1. Nuitka版本 - 文件名格式为 `{脚本名}_nuitka.exe`
2. PyInstaller版本 - 文件名格式为 `{脚本名}_pyinstaller.exe`

## 依赖

- paramiko
- scp
- nuitka (用于构建可执行程序)
- pyinstaller (用于构建可执行程序)
- pycryptodome