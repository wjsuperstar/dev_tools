#!/usr/bin/env python3
"""Auto-generate requirements.txt from imports in tools/*.py."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
import sysconfig

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
REQUIREMENTS_FILE = REPO_ROOT / "requirements.txt"

# import module -> pip package name
PACKAGE_MAP = {
    "Crypto": "pycryptodome",
    "scp": "scp",
    "paramiko": "paramiko",
    "watchdog": "watchdog",
    "tftpy": "tftpy",
}

# Keep build tool dependencies required by CI packaging.
BUILD_DEPENDENCIES = ["nuitka", "pyinstaller"]

# Minimum versions currently used in this repo.
MIN_VERSIONS = {
    "paramiko": ">=2.7.2",
    "scp": ">=0.13.2",
    "pycryptodome": ">=3.10.1",
    "watchdog": ">=4.0.0",
    "tftpy": ">=0.8.6",
    "nuitka": ">=0.6.12",
    "pyinstaller": ">=4.0",
}


def get_local_modules() -> set[str]:
    modules: set[str] = set()
    for file in TOOLS_DIR.glob("*.py"):
        if file.name == "__init__.py":
            continue
        modules.add(file.stem)
    return modules


def extract_top_level_imports(py_file: Path) -> set[str]:
    content = py_file.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(py_file))
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                modules.add(node.module.split(".")[0])

    return modules


def to_requirements_line(pkg: str) -> str:
    version = MIN_VERSIONS.get(pkg)
    if version:
        return f"{pkg}{version}"
    return pkg


def is_stdlib_module(module: str) -> bool:
    if module in sys.builtin_module_names:
        return True

    paths = sysconfig.get_paths()
    stdlib_path = Path(paths["stdlib"]).resolve()
    purelib_path = Path(paths["purelib"]).resolve()
    platlib_path = Path(paths["platlib"]).resolve()
    spec = importlib.util.find_spec(module)
    if spec is None:
        return False
    if spec.origin in (None, "built-in", "frozen"):
        return True

    try:
        origin_path = Path(spec.origin).resolve()
    except OSError:
        return False

    if str(origin_path).startswith(str(purelib_path)) or str(origin_path).startswith(str(platlib_path)):
        return False

    return str(origin_path).startswith(str(stdlib_path))


def main() -> int:
    if not TOOLS_DIR.exists():
        print(f"tools directory not found: {TOOLS_DIR}", file=sys.stderr)
        return 1

    local_modules = get_local_modules()
    imported: set[str] = set()

    for py_file in sorted(TOOLS_DIR.glob("*.py")):
        imported.update(extract_top_level_imports(py_file))

    resolved_packages: set[str] = set()
    for module in imported:
        if module in local_modules:
            continue
        if is_stdlib_module(module):
            continue

        package = PACKAGE_MAP.get(module)
        if package:
            resolved_packages.add(package)

    resolved_packages.update(BUILD_DEPENDENCIES)

    lines = [to_requirements_line(pkg) for pkg in sorted(resolved_packages)]
    content = "\n".join(lines) + "\n"
    REQUIREMENTS_FILE.write_text(content, encoding="utf-8")

    print(f"Updated {REQUIREMENTS_FILE}")
    for line in lines:
        print(f"  - {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
