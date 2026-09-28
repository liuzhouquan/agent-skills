#!/usr/bin/env python3
"""Bind a Telegram private chat once, check it, or send an explicit test."""

from __future__ import annotations

import argparse
import getpass
import math
import secrets
import sys
import time

from telegram_common import TelegramError, api_call, config_path, credentials, read_config, save_config


def matching_chat(update: dict, code: str) -> dict | None:
    message = update.get("message", {})
    chat = message.get("chat", {})
    text = message.get("text", "").strip()
    if chat.get("type") == "private" and text == f"/start {code}" and "id" in chat:
        return chat
    return None


def discover_chat(token: str, username: str, timeout_seconds: int) -> dict:
    webhook = api_call(token, "getWebhookInfo")
    if webhook.get("url"):
        raise TelegramError(
            "这个 Bot 已有 webhook，无法同时轮询绑定。请使用一个专用 Bot，"
            "或先在原服务处理 webhook；本脚本不会自动移除它。"
        )
    code = secrets.token_urlsafe(12)
    print("打开以下链接，在 Telegram 私聊中点击 Start / 开始：", flush=True)
    print(f"https://t.me/{username}?start={code}", flush=True)
    print(f"若链接没有带上绑定码，可发送：/start {code}", flush=True)
    print(f"正在等待绑定（最多 {timeout_seconds} 秒）……", flush=True)
    offset = None
    deadline = time.monotonic() + timeout_seconds
    while (remaining := deadline - time.monotonic()) > 0:
        poll = min(10, max(1, math.ceil(remaining)))
        params = {"timeout": poll, "limit": 100}
        if offset is not None:
            params["offset"] = offset
        updates = api_call(token, "getUpdates", params, timeout=min(poll + 5, remaining + 1))
        for update in updates:
            offset = max(offset or 0, int(update["update_id"]) + 1)
            chat = matching_chat(update, code)
            if chat:
                return chat
    raise TelegramError("绑定超时。请重新运行，再打开新链接并点击 Start。")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=180, help="binding wait in seconds")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--reconfigure", action="store_true", help="bind again, reusing a saved token if desired")
    mode.add_argument("--check", action="store_true", help="verify saved credentials without sending")
    mode.add_argument("--test", action="store_true", help="send one test message to the saved chat")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    try:
        if args.check or args.test:
            token, chat_id = credentials()
            bot = api_call(token, "getMe")
            chat = api_call(token, "getChat", {"chat_id": chat_id})
            print(f"配置有效：@{bot['username']} → {chat.get('first_name') or chat.get('title') or chat_id}")
            if args.test:
                api_call(token, "sendMessage", {
                    "chat_id": chat_id, "text": "YouTube 视频笔记：Telegram 推送测试成功。"
                })
                print("测试消息已发送。")
            return 0

        saved = read_config()
        if saved.get("TELEGRAM_BOT_TOKEN") and saved.get("TELEGRAM_CHAT_ID") and not args.reconfigure:
            print(f"已有长期配置：{config_path()}")
            print("无需重复输入。使用 --check 检查，--test 测试发送，--reconfigure 重新绑定。")
            return 0
        existing_token = saved.get("TELEGRAM_BOT_TOKEN", "")
        prompt = "Bot Token（直接回车复用已保存的 token）: " if existing_token else "Telegram Bot Token: "
        token = getpass.getpass(prompt).strip() or existing_token
        if not token:
            raise TelegramError("需要 Bot Token。")
        bot = api_call(token, "getMe")
        print(f"已验证 Bot：@{bot['username']}")
        chat = discover_chat(token, bot["username"], args.timeout)
        save_config(token, str(chat["id"]))
        print(f"绑定成功：{chat.get('first_name') or chat['id']}")
        print(f"已长期保存到 {config_path()}（权限 600）。以后自动读取。")
        return 0
    except (TelegramError, OSError) as error:
        print(f"配置失败：{error}", file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print("\n已取消，未更改配置。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
