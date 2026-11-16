# -*- coding: utf-8 -*-
"""设备凭据读取。

设备口令不写进版本库。按以下顺序查找凭据文件：

1. 环境变量 ``DEVTOOLS_CREDENTIALS`` 指定的文件
2. 打包成 exe 时：exe 同级目录下的 ``credentials.local.json``
3. 源码运行时：``tools/credentials.local.json``

文件格式见 ``tools/credentials.example.json``，
也可用 ``python scripts/init_credentials.py`` 生成。
"""
import json
import os
import sys
from pathlib import Path

CREDENTIALS_FILENAME = "credentials.local.json"

_cache = None


class CredentialsError(RuntimeError):
    """凭据文件缺失或格式不正确。"""


def _executable_dirs():
    """返回 exe 所在目录的候选列表（兼容 PyInstaller 与 Nuitka）。

    - PyInstaller：sys.frozen 为 True，sys.executable 就是 exe 本身
    - Nuitka onefile：sys.executable 指向临时解压目录里的 python.exe，
      真正的 exe 路径在 sys.argv[0] / __compiled__.original_argv0
    """
    dirs = []

    if getattr(sys, "frozen", False):
        dirs.append(Path(sys.executable).resolve().parent)

    if sys.argv and sys.argv[0]:
        dirs.append(Path(sys.argv[0]).resolve().parent)

    compiled = globals().get("__compiled__")
    for attr in ("original_argv0", "process_exe"):
        value = getattr(compiled, attr, None)
        if value:
            dirs.append(Path(value).resolve().parent)

    seen = set()
    unique = []
    for d in dirs:
        if d not in seen:
            seen.add(d)
            unique.append(d)
    return unique


def _candidate_paths():
    env_path = os.environ.get("DEVTOOLS_CREDENTIALS")
    if env_path:
        yield Path(env_path)

    # 打包成 exe：找 exe 同级目录
    for d in _executable_dirs():
        yield d / CREDENTIALS_FILENAME

    # 源码运行：tools/common/credentials.py -> tools/
    yield Path(__file__).resolve().parent.parent / CREDENTIALS_FILENAME
    yield Path(__file__).resolve().parent / CREDENTIALS_FILENAME


def _missing_message(tried):
    return (
        "[错误] 未找到设备凭据文件 {name}\n"
        "已尝试的路径:\n  {tried}\n"
        "处理方法:\n"
        "  1) 源码运行：复制 tools/credentials.example.json 为 tools/credentials.local.json，填入设备口令\n"
        "  2) 使用 exe：把 credentials.local.json 放到 exe 同级目录下\n"
        "  3) 或用环境变量 DEVTOOLS_CREDENTIALS 指定凭据文件的完整路径"
    ).format(name=CREDENTIALS_FILENAME, tried="\n  ".join(tried))


def load_credentials():
    """读取并返回凭据字典。文件缺失或格式错误时抛出 CredentialsError。"""
    global _cache
    if _cache is not None:
        return _cache

    tried = []
    for path in _candidate_paths():
        tried.append(str(path))
        if not path.is_file():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            raise CredentialsError(f"凭据文件解析失败: {path}\n{e}") from e
        if not isinstance(data, dict):
            raise CredentialsError(f"凭据文件格式错误（顶层应为 JSON 对象）: {path}")
        _cache = data
        return data

    raise CredentialsError(_missing_message(tried))


def get_profile(name):
    """取某个平台（如 '9606'）的凭据字典。"""
    data = load_credentials()
    profiles = data.get("profiles", {})
    profile = profiles.get(name)
    if not isinstance(profile, dict):
        available = ", ".join(sorted(profiles)) or "(空)"
        raise CredentialsError(
            f"凭据文件里缺少平台 '{name}' 的配置。\n"
            f"可用的平台: {available}"
        )
    return profile


def require_profile(name):
    """取平台凭据；缺失时打印清晰提示并以退出码 1 结束。"""
    try:
        return get_profile(name)
    except CredentialsError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


def get_password(name, key):
    """取某平台的某个口令。"""
    profile = get_profile(name)
    value = profile.get(key)
    if not value:
        raise CredentialsError(f"凭据文件里平台 '{name}' 缺少 '{key}'")
    return value
