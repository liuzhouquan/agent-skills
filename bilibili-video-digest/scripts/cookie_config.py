#!/usr/bin/env python3
"""Private persistent directories used to discover Netscape cookie files."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


DEFAULT_CONFIG = Path.home() / ".config/bilibili-video-digest/cookie-dirs.txt"


def config_path() -> Path:
    return Path(os.environ.get("BILIBILI_COOKIE_DIRS_FILE", str(DEFAULT_CONFIG))).expanduser()


def _absolute(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def configured_dirs(extra: list[str | Path] | None = None) -> list[Path]:
    values: list[str | Path] = []
    if extra:
        values.extend(extra)
    values.extend(value for value in os.environ.get("BILIBILI_COOKIE_DIRS", "").split(os.pathsep) if value)
    path = config_path()
    if path.is_file():
        values.extend(
            line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    result = []
    seen = set()
    for value in values:
        directory = _absolute(value)
        if directory not in seen:
            result.append(directory)
            seen.add(directory)
    return result


def cookie_files(extra: list[str | Path] | None = None) -> list[Path]:
    result = []
    seen = set()
    for directory in configured_dirs(extra):
        if not directory.is_dir():
            continue
        try:
            children = directory.iterdir()
        except OSError:
            continue
        for path in children:
            name = path.name.lower()
            if not path.is_file() or path in seen:
                continue
            # Automatic discovery is deliberately limited to clearly Bilibili-named files.
            # Other sites must be passed explicitly with --cookies.
            if not (
                "bilibili" in name
                and "cookie" in name
                and path.suffix.lower() in {".txt", ".cookies"}
            ):
                continue
            result.append(path)
            seen.add(path)
    return sorted(result, key=lambda path: (-path.stat().st_mtime_ns, str(path)))


def save_dirs(directories: list[Path]) -> None:
    path = config_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("Cookie 目录配置路径不能是符号链接。")
    fd, temporary = tempfile.mkstemp(prefix=".cookie-dirs-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write("# Managed locally; one absolute Cookie directory per line.\n")
            stream.writelines(f"{directory}\n" for directory in directories)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def add_dir(directory: str | Path) -> Path:
    path = _absolute(directory)
    if not path.is_dir():
        raise ValueError(f"Cookie 目录不存在或不是目录：{path}")
    directories = configured_dirs()
    if path not in directories:
        directories.append(path)
        save_dirs(directories)
    return path


def remove_dir(directory: str | Path) -> Path:
    path = _absolute(directory)
    directories = [item for item in configured_dirs() if item != path]
    save_dirs(directories)
    return path
