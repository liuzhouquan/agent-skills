#!/usr/bin/env python3
"""Remember private directories that contain Bilibili Netscape cookie files."""

from __future__ import annotations

import argparse
import sys

from cookie_config import add_dir, configured_dirs, config_path, remove_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--add-dir", action="append", metavar="DIR", help="remember a Cookie directory")
    parser.add_argument("--remove-dir", action="append", metavar="DIR", help="forget a Cookie directory")
    parser.add_argument("--list", action="store_true", help="list remembered and environment directories")
    args = parser.parse_args()
    if not args.add_dir and not args.remove_dir and not args.list:
        parser.error("choose --add-dir, --remove-dir, or --list")
    try:
        for directory in args.add_dir or []:
            print(f"已记录 Cookie 目录：{add_dir(directory)}")
        for directory in args.remove_dir or []:
            print(f"已移除 Cookie 目录：{remove_dir(directory)}")
        if args.list:
            print(f"配置文件：{config_path()}")
            for directory in configured_dirs():
                print(directory)
        return 0
    except (OSError, ValueError) as error:
        print(f"Cookie 目录配置失败：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
