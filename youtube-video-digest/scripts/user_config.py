#!/usr/bin/env python3
"""Private, non-secret configuration for the YouTube digest skill."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


NOTES_DIR_NAME = "youtube-notes"
DEFAULT_CONFIG = {
    "notes_dir": f"~/{NOTES_DIR_NAME}",
    "cookie_dirs": [],
}


def config_path() -> Path:
    return Path(os.environ.get(
        "YOUTUBE_DIGEST_CONFIG",
        str(Path.home() / ".config/youtube-video-digest/config.json"),
    )).expanduser()


def _normalise(data: dict) -> dict:
    result = dict(DEFAULT_CONFIG)
    if isinstance(data.get("notes_dir"), str) and data["notes_dir"].strip():
        result["notes_dir"] = data["notes_dir"].strip()
    if isinstance(data.get("cookie_dirs"), list):
        result["cookie_dirs"] = [value.strip() for value in data["cookie_dirs"] if isinstance(value, str) and value.strip()]
    return result


def save_config(data: dict) -> Path:
    path = config_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("配置路径不能是符号链接。")
    fd, temporary = tempfile.mkstemp(prefix=".config-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(_normalise(data), stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        return _normalise({})
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"配置文件无法读取：{path}（{error}）") from None
    if not isinstance(data, dict):
        raise ValueError(f"配置文件必须是 JSON 对象：{path}")
    return _normalise(data)


def ensure_config() -> tuple[dict, bool]:
    path = config_path()
    if path.exists():
        return load_config(), False
    data = _normalise({})
    save_config(data)
    return data, True


def set_notes_dir(directory: str | Path) -> Path:
    path = Path(directory).expanduser().resolve()
    data = load_config()
    data["notes_dir"] = str(path)
    save_config(data)
    return path


def existing_notes_dirs(configured: str | Path, bases: list[Path] | None = None) -> list[Path]:
    """Return existing note directories that differ from the configured one.

    Each base is searched for `<base>/youtube-notes` and `<base>/*/youtube-notes`, so an
    archive kept next to a project (for example `~/projects/youtube-notes`) is found
    without hard-coding that layout.
    """
    try:
        configured_path = Path(configured).expanduser().resolve()
    except OSError:
        configured_path = Path(configured).expanduser()
    if bases is None:
        bases = [Path.cwd(), Path.home()]
    candidates = []
    for base in bases:
        candidates.append(base / NOTES_DIR_NAME)
        try:
            children = sorted(child for child in base.iterdir() if child.is_dir() and not child.name.startswith("."))
        except OSError:
            children = []
        candidates.extend(child / NOTES_DIR_NAME for child in children)
    found: list[Path] = []
    seen = {configured_path}
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.is_dir():
            continue
        seen.add(resolved)
        found.append(resolved)
    return found


def notes_dir_hint(data: dict, bases: list[Path] | None = None) -> str | None:
    """Explain that other note directories already exist when the template is created."""
    others = existing_notes_dirs(data.get("notes_dir", DEFAULT_CONFIG["notes_dir"]), bases)
    if not others:
        return None
    lines = ["检测到已有的笔记目录，默认目录可能不是你想继续用的那一个："]
    lines.extend(f"  - {path}" for path in others)
    lines.append(
        '如需改用其中之一：python3 <skill-dir>/scripts/configure_cookies.py '
        f'--set-notes-dir "{others[0]}"'
    )
    return "\n".join(lines)
