#!/usr/bin/env python3
"""Download YouTube subtitles and create a timestamped transcript."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from subtitle_to_text import convert


def yt_dlp_command() -> str | None:
    candidates = [
        os.environ.get("YOUTUBE_YT_DLP"),
        str(Path.home() / ".local/share/bilibili-video-digest/venv/bin/yt-dlp"),
        shutil.which("yt-dlp"),
        shutil.which("yt-dlp_linux"),
    ]
    return next((path for path in candidates if path and Path(path).is_file() and os.access(path, os.X_OK)), None)


def is_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    valid_hosts = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}
    return (
        parsed.scheme in {"http", "https"}
        and host in valid_hosts
        and not parsed.username
        and not parsed.password
    )


def subtitle_files(folder: Path) -> list[Path]:
    return sorted(
        path for path in folder.iterdir()
        if path.is_file() and path.stat().st_size
        and path.suffix.lower() in {".srt", ".vtt", ".ass", ".ssa"}
        and not path.name.endswith((".info.json", "manifest.json"))
    )


def preferred_subtitle(paths: list[Path]) -> Path:
    def rank(path: Path):
        name = path.name.lower()
        chinese = any(tag in name for tag in (".zh", ".chi", ".zho", ".cmn"))
        english = ".en" in name or ".eng" in name
        automatic = any(tag in name for tag in (".auto.", ".ai-", ".asr."))
        # Prefer human Chinese, then human English, then auto captions in those languages.
        return (not chinese, not english, automatic, path.name)

    return min(paths, key=rank)


def parse_metadata(stdout: str) -> list[dict]:
    metadata = []
    for line in stdout.splitlines():
        try:
            info = json.loads(line)
        except ValueError:
            continue
        if isinstance(info, dict) and isinstance(info.get("id"), str):
            metadata.append(info)
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--output", type=Path, default=Path("youtube-notes"))
    parser.add_argument("--sub-langs", default="all,-live_chat")
    cookies = parser.add_mutually_exclusive_group()
    cookies.add_argument("--cookies-from-browser", metavar="BROWSER")
    cookies.add_argument("--cookies", type=Path, help="local Netscape-format cookies file")
    args = parser.parse_args()
    if not is_youtube_url(args.url):
        parser.error("provide a YouTube video URL from youtube.com, music.youtube.com, or youtu.be")

    executable = yt_dlp_command()
    if executable is None:
        print("未找到 yt-dlp。请安装 yt-dlp，或设置 YOUTUBE_YT_DLP。", file=sys.stderr)
        return 2
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    command = [
        executable, "--ignore-config", "--no-playlist", "--skip-download",
        "--write-subs", "--write-auto-subs", "--write-info-json",
        "--print-json", "--no-simulate", "--no-progress", "--socket-timeout", "20",
        "--retries", "2", "--sub-langs", args.sub_langs,
        "--sub-format", "srt/vtt/best",
        "-o", str(output / "%(id)s" / "%(id)s.%(ext)s"),
    ]
    if args.cookies:
        path = args.cookies.expanduser().resolve()
        if not path.is_file():
            parser.error("cookies file does not exist")
        command.extend(["--cookies", str(path)])
    elif args.cookies_from_browser:
        command.extend(["--cookies-from-browser", args.cookies_from_browser])
    command.extend(["--", args.url])
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=180, check=False)
    except (OSError, subprocess.TimeoutExpired):
        print("yt-dlp 启动失败或超过 180 秒；请检查 WSL 网络和可执行文件。", file=sys.stderr)
        return 2
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    metadata = parse_metadata(result.stdout)
    if not metadata:
        print("yt-dlp 未返回视频元数据。", file=sys.stderr)
        return 3

    missing = False
    for info in metadata:
        video_id = info["id"]
        if video_id in {".", ".."} or any(char in video_id for char in "/\\"):
            print("视频 ID 格式错误。", file=sys.stderr)
            return 3
        folder = output / video_id
        folder.mkdir(parents=True, exist_ok=True)
        paths = subtitle_files(folder)
        manifest = {
            "id": video_id, "title": info.get("title"), "channel": info.get("channel") or info.get("uploader"),
            "uploader": info.get("uploader"), "upload_date": info.get("upload_date"),
            "duration": info.get("duration"), "source_url": args.url,
            "webpage_url": info.get("webpage_url"), "subtitles": [str(path) for path in paths],
        }
        if paths:
            selected = preferred_subtitle(paths)
            try:
                transcript = folder / "transcript.txt"
                convert(selected, transcript)
            except (OSError, ValueError, TypeError) as error:
                print(f"字幕解析失败：{error}", file=sys.stderr)
                return 4
            manifest.update(status="transcript-ready", selected_subtitle=str(selected), transcript=str(transcript))
            print(f"已提取：{info.get('title', video_id)}\n文字稿：{transcript}")
        else:
            manifest["status"] = "no-accessible-subtitle"
            print(f"{video_id} 未获得字幕。可能需要登录 Cookie，或只有画面内字幕。", file=sys.stderr)
            missing = True
        (folder / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
    if result.returncode and not missing:
        print(f"下载未完成（yt-dlp 退出码 {result.returncode}）。", file=sys.stderr)
        return 3
    return 4 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
