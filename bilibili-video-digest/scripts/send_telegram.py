#!/usr/bin/env python3
"""Send a UTF-8 note through Telegram using saved credentials."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from telegram_common import TelegramError, api_call, credentials


def chunks(text: str, size: int = 3800):
    """Split without breaking code points; count UTF-16 units conservatively."""
    if size < 2:
        raise ValueError("chunk size must be at least 2")
    current = []
    units = 0
    for character in text:
        width = 2 if ord(character) > 0xFFFF else 1
        if units + width > size:
            yield "".join(current)
            current, units = [], 0
        current.append(character)
        units += width
    if current:
        yield "".join(current)


def send_note(token: str, chat_id: str, text: str) -> int:
    sent = 0
    for part in chunks(text):
        try:
            api_call(token, "sendMessage", {
                "chat_id": chat_id,
                "text": part,
                "link_preview_options": json.dumps({"is_disabled": True}),
            })
        except TelegramError as error:
            raise TelegramError(
                f"已有 {sent} 段确认发送；当前段失败或状态未知。{error} "
                "为避免重复消息，未自动重发。"
            ) from None
        sent += 1
    return sent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("note", type=Path)
    parser.add_argument("--title", default="B站视频笔记")
    parser.add_argument("--dry-run", action="store_true", help="validate note and chunk sizes without sending")
    args = parser.parse_args()
    try:
        text = args.note.read_text(encoding="utf-8").strip()
        if not text:
            raise TelegramError("笔记为空。")
        content = f"{args.title}\n\n{text}"
        if args.dry_run:
            print(f"可发送，共 {len(list(chunks(content)))} 段；未发送。")
        else:
            token, chat_id = credentials()
            print(f"已发送 {send_note(token, chat_id, content)} 段。")
        return 0
    except (TelegramError, OSError, UnicodeError) as error:
        print(f"发送失败：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
