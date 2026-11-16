#!/usr/bin/env python3
"""生成 tools/credentials.local.json（本地凭据文件，已被 .gitignore 忽略）。

用法：
    python scripts/init_credentials.py            # 交互式填写
    python scripts/init_credentials.py --force    # 覆盖已存在的文件
"""
from __future__ import annotations

import argparse
import getpass
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
EXAMPLE_FILE = TOOLS_DIR / "credentials.example.json"
LOCAL_FILE = TOOLS_DIR / "credentials.local.json"

PLACEHOLDER = "REPLACE_ME"


def prompt_value(label, current):
    """交互式读取一个值。密码用 getpass 避免回显。"""
    default = "" if current == PLACEHOLDER else current
    is_secret = "pwd" in label or "password" in label
    tip = f" [回车保持当前值]" if default else ""
    while True:
        if is_secret:
            value = getpass.getpass(f"{label}{tip}: ").strip()
        else:
            value = input(f"{label}{tip}: ").strip()
        if value:
            return value
        if default:
            return default
        print("  该项不能为空，请重新输入")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="覆盖已存在的凭据文件")
    args = parser.parse_args()

    if not EXAMPLE_FILE.is_file():
        print(f"[错误] 找不到模板文件: {EXAMPLE_FILE}", file=sys.stderr)
        return 1

    if LOCAL_FILE.exists() and not args.force:
        print(f"[错误] {LOCAL_FILE} 已存在。加 --force 覆盖。", file=sys.stderr)
        return 1

    try:
        template = json.loads(EXAMPLE_FILE.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"[错误] 模板文件解析失败: {e}", file=sys.stderr)
        return 1

    profiles = template.get("profiles", {})
    if not profiles:
        print("[错误] 模板里没有 profiles", file=sys.stderr)
        return 1

    print(f"填写设备凭据，写入 {LOCAL_FILE}")
    print("（直接回车 = 保持模板里的占位值，请确保已替换为真实口令）\n")

    result = {}
    for platform, fields in profiles.items():
        print(f"--- 平台 {platform} ---")
        result[platform] = {}
        for key, value in fields.items():
            result[platform][key] = prompt_value(key, value)
        print()

    LOCAL_FILE.write_text(
        json.dumps({"profiles": result}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"已写入 {LOCAL_FILE}")
    print("提醒：该文件已被 .gitignore 忽略，不会提交到仓库。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
