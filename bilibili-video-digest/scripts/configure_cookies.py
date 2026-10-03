#!/usr/bin/env python3
"""Remember private directories that contain Bilibili Netscape cookie files."""

from __future__ import annotations

import argparse
import sys

from cookie_config import add_dir, configured_dirs, config_path, remove_dir
from user_config import ensure_config, set_notes_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--add-dir", action="append", metavar="DIR", help="remember a Cookie directory")
    parser.add_argument("--remove-dir", action="append", metavar="DIR", help="forget a Cookie directory")
    parser.add_argument("--set-notes-dir", metavar="DIR", help="set the persistent note output directory")
    parser.add_argument("--init", action="store_true", help="create the template config if it does not exist")
    parser.add_argument("--list", action="store_true", help="list remembered and environment directories")
    args = parser.parse_args()
    if not args.add_dir and not args.remove_dir and not args.set_notes_dir and not args.init and not args.list:
        parser.error("choose --add-dir, --remove-dir, --set-notes-dir, --init, or --list")
    try:
        config, created = ensure_config()
        if args.init:
            print(f"{'已创建' if created else '已存在'}配置文件：{config_path()}")
        for directory in args.add_dir or []:
            print(f"已记录 Cookie 目录：{add_dir(directory)}")
        for directory in args.remove_dir or []:
            print(f"已移除 Cookie 目录：{remove_dir(directory)}")
        if args.set_notes_dir:
            print(f"已设置笔记目录：{set_notes_dir(args.set_notes_dir)}")
        if args.list:
            print(f"配置文件：{config_path()}")
            print(f"笔记目录：{ensure_config()[0]['notes_dir']}")
            for directory in configured_dirs():
                print(directory)
        return 0
    except (OSError, ValueError) as error:
        print(f"Cookie 目录配置失败：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
