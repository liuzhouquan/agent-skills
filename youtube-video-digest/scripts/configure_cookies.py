#!/usr/bin/env python3
"""Remember private directories that contain YouTube Netscape cookie files.

YouTube offers no offline login-status endpoint, so this helper only reports which
Cookie files would be used; the fetch helper classifies failures from yt-dlp output.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cookie_config import add_dir, configured_dirs, config_path, cookie_files, remove_dir
from user_config import ensure_config, set_notes_dir


def directory_line(directory: Path) -> str:
    return f"Cookie 目录：{directory}" + ("" if directory.is_dir() else "（目录不存在）")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--add-dir", action="append", metavar="DIR", help="remember a Cookie directory")
    parser.add_argument("--remove-dir", action="append", metavar="DIR", help="forget a Cookie directory")
    parser.add_argument("--set-notes-dir", metavar="DIR", help="set the persistent note output directory")
    parser.add_argument("--init", action="store_true", help="create the template config if it does not exist")
    parser.add_argument("--list", action="store_true", help="list directories and discovered Cookie files")
    args = parser.parse_args()
    if not any([args.add_dir, args.remove_dir, args.set_notes_dir, args.init, args.list]):
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
            print(f"笔记目录：{config['notes_dir']}")
            directories = configured_dirs()
            if directories:
                for directory in directories:
                    print(directory_line(directory))
            else:
                print("Cookie 目录：未配置，可用 --add-dir 记录")
            files = cookie_files()
            if not files:
                print("Cookie 文件：未发现（文件名需同时含 youtube 和 cookie，后缀 .txt 或 .cookies）")
            for path in files:
                print(f"Cookie 文件：{path}")
        return 0
    except (OSError, ValueError) as error:
        print(f"Cookie 目录配置失败：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
