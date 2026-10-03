#!/usr/bin/env python3
"""Private, non-secret configuration for the Bilibili digest skill."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


DEFAULT_CONFIG = {
    "notes_dir": "~/bilibili-notes",
    "cookie_dirs": [],
}


def config_path() -> Path:
    return Path(os.environ.get(
        "BILIBILI_DIGEST_CONFIG",
        str(Path.home() / ".config/bilibili-video-digest/config.json"),
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
