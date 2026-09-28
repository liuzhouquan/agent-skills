#!/usr/bin/env python3
"""Convert SRT, VTT, ASS/SSA and Bilibili JSON to timestamped text."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from pathlib import Path


TIME_RE = re.compile(r"(?:(\d+):)?(\d{2}):(\d{2})(?:[,.](\d+))?")
TAG_RE = re.compile(r"<[^>]+>")
ASS_TAG_RE = re.compile(r"\{[^}]*\}")


def clean(value: str) -> str:
    value = html.unescape(TAG_RE.sub("", value)).replace("\\N", " ").replace("\\n", " ").replace("\\h", " ")
    return re.sub(r"\s+", " ", value).strip()


def stamp(seconds: float) -> str:
    total = max(0, int(seconds))
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def parse_seconds(value: str) -> float:
    match = TIME_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"无效字幕时间：{value}")
    hours, minutes, seconds, fraction = match.groups()
    if int(minutes) >= 60 or int(seconds) >= 60:
        raise ValueError(f"无效字幕时间：{value}")
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds) + float(f"0.{fraction or '0'}")


def parse_json(path: Path) -> list[tuple[float, str]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    entries = data.get("body") if isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise ValueError("JSON 中没有 B 站 body 字幕列表。")
    result = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("content"), str):
            continue
        seconds = float(entry.get("from", 0))
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("字幕时间必须是非负有限数值。")
        text = clean(entry["content"])
        if text:
            result.append((seconds, text))
    return result


def parse_text(path: Path) -> list[tuple[float, str]]:
    raw = path.read_text(encoding="utf-8-sig")
    result = []
    for block in re.split(r"\n\s*\n", raw.replace("\r\n", "\n").replace("\r", "\n")):
        lines = block.splitlines()
        for index, line in enumerate(lines):
            if "-->" not in line:
                continue
            start = parse_seconds(line.split("-->", 1)[0])
            text = clean(" ".join(lines[index + 1:]))
            if text:
                result.append((start, text))
            break
    return result


def parse_ass(path: Path) -> list[tuple[float, str]]:
    result = []
    fields = []
    in_events = False
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if line.startswith("["):
            in_events = line.lower() == "[events]"
        elif in_events and line.lower().startswith("format:"):
            fields = [value.strip().lower() for value in line.split(":", 1)[1].split(",")]
        elif in_events and line.lower().startswith("dialogue:"):
            # ASS and SSA both put Text last; commas inside the text are literal.
            if not fields or fields[-1] != "text" or "start" not in fields:
                raise ValueError("ASS/SSA Events Format 无效。")
            parts = line.split(":", 1)[1].lstrip().split(",", len(fields) - 1)
            if len(parts) != len(fields):
                raise ValueError("ASS/SSA Dialogue 列数错误。")
            entry = dict(zip(fields, parts))
            text = clean(ASS_TAG_RE.sub("", entry["text"]))
            if text:
                result.append((parse_seconds(entry["start"]), text))
    return result


def convert(subtitle: Path, output: Path | None = None) -> str:
    if subtitle.suffix.lower() == ".json":
        entries = parse_json(subtitle)
    elif subtitle.suffix.lower() in {".ass", ".ssa"}:
        entries = parse_ass(subtitle)
    elif subtitle.suffix.lower() in {".srt", ".vtt"}:
        entries = parse_text(subtitle)
    else:
        raise ValueError("只支持 SRT、VTT、ASS/SSA 和 B站 JSON 字幕。")
    if not entries:
        raise ValueError("字幕中没有可解析正文；未生成空文字稿。")
    content = "\n".join(f"[{stamp(seconds)}] {text}" for seconds, text in sorted(entries)) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subtitle", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        content = convert(args.subtitle, args.output)
    except (OSError, ValueError, TypeError) as error:
        print(f"转换失败：{error}", file=sys.stderr)
        return 2
    if not args.output:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
