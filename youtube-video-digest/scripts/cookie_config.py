#!/usr/bin/env python3
"""Discover YouTube cookie files from the private user configuration."""

from __future__ import annotations

import os
from pathlib import Path

from user_config import config_path, load_config, save_config


def _absolute(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def configured_dirs(extra: list[str | Path] | None = None) -> list[Path]:
    values: list[str | Path] = []
    if extra:
        values.extend(extra)
    values.extend(value for value in os.environ.get("YOUTUBE_COOKIE_DIRS", "").split(os.pathsep) if value)
    values.extend(load_config().get("cookie_dirs", []))
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
            # Automatic discovery is limited to clearly YouTube-named files.
            if not ("youtube" in name and "cookie" in name and path.suffix.lower() in {".txt", ".cookies"}):
                continue
            result.append(path)
            seen.add(path)
    return sorted(result, key=lambda path: (-path.stat().st_mtime_ns, str(path)))


def add_dir(directory: str | Path) -> Path:
    path = _absolute(directory)
    if not path.is_dir():
        raise ValueError(f"Cookie 目录不存在或不是目录：{path}")
    data = load_config()
    directories = configured_dirs()
    if path not in directories:
        directories.append(path)
        data["cookie_dirs"] = [str(item) for item in directories]
        save_config(data)
    return path


def remove_dir(directory: str | Path) -> Path:
    path = _absolute(directory)
    data = load_config()
    data["cookie_dirs"] = [item for item in data.get("cookie_dirs", []) if _absolute(item) != path]
    save_config(data)
    return path
