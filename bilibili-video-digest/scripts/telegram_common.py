#!/usr/bin/env python3
"""Shared credential storage and checked Telegram Bot API requests."""

from __future__ import annotations

import json
import os
import re
import shlex
import socket
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class TelegramError(RuntimeError):
    """A user-facing error that never includes the Bot API URL."""


def config_path() -> Path:
    return Path(os.environ.get(
        "BILIBILI_TELEGRAM_ENV",
        str(Path.home() / ".config/bilibili-video-digest/telegram.env"),
    )).expanduser()


def read_config(path: Path | None = None) -> dict[str, str]:
    path = path if path is not None else config_path()
    if not path.exists():
        return {}
    values = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        key, separator, raw = line.partition("=")
        key = key.strip()
        if key not in {"TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"}:
            continue
        try:
            parts = shlex.split(raw, comments=True)
        except ValueError:
            raise TelegramError(f"配置文件第 {number} 行引号不匹配。") from None
        if not separator or len(parts) > 1:
            raise TelegramError(f"配置文件第 {number} 行格式错误。")
        values[key] = parts[0] if parts else ""
    return values


def credentials(path: Path | None = None) -> tuple[str, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if token or chat:
        if not (token and chat):
            raise TelegramError("环境变量覆盖需要同时设置 token 和 chat_id，避免混用两个 Bot 的配置。")
    else:
        values = read_config(path)
        token, chat = values.get("TELEGRAM_BOT_TOKEN", ""), values.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        raise TelegramError("尚未完成 Telegram 配置；请先运行 scripts/setup_telegram.py。")
    return token, chat


def save_config(token: str, chat_id: str, path: Path | None = None) -> None:
    path = path if path is not None else config_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink():
        raise TelegramError("配置路径是符号链接；请改用普通配置文件。")
    fd, temporary = tempfile.mkstemp(prefix=".telegram-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(
                "# Managed by bilibili-video-digest; keep private.\n"
                f"TELEGRAM_BOT_TOKEN={shlex.quote(token)}\n"
                f"TELEGRAM_CHAT_ID={shlex.quote(chat_id)}\n"
            )
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def api_call(token: str, method: str, params: dict | None = None, *, timeout: float = 30):
    if not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", token):
        raise TelegramError("Bot Token 格式错误；请复制 BotFather 提供的完整 token。")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=urllib.parse.urlencode(params or {}).encode("utf-8"),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        try:
            payload = json.load(error)
        except (ValueError, OSError):
            raise TelegramError(f"Telegram HTTP {error.code}。") from None
    except (urllib.error.URLError, OSError, socket.timeout):
        raise TelegramError(
            "无法连接 Telegram（连接失败或超时）。WSL 需能访问 api.telegram.org；"
            "如使用 HTTP 代理，请为当前终端设置 HTTPS_PROXY。"
        ) from None
    except ValueError:
        raise TelegramError("Telegram 返回了非 JSON 响应，请检查代理。") from None
    if not isinstance(payload, dict):
        raise TelegramError("Telegram 返回了无效响应。")
    if not payload.get("ok"):
        code = payload.get("error_code")
        description = str(payload.get("description", "请求失败")).replace(token, "[redacted]")
        hint = {
            401: "token 已失效或复制错误。",
            403: "Bot 被屏蔽或没有目标聊天的发送权限。",
            409: "Bot 正被其他轮询程序或 webhook 使用；先检查现有服务。",
        }.get(code, "")
        raise TelegramError(f"Telegram {code}: {description} {hint}".strip())
    if "result" not in payload:
        raise TelegramError("Telegram 响应缺少 result。")
    return payload["result"]
