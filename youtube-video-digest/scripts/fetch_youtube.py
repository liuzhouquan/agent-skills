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

from cookie_config import cookie_files
from subtitle_to_text import convert
from user_config import config_path, ensure_config, notes_dir_hint

EXIT_NO_SUBTITLE = 4
EXIT_LOGIN_REQUIRED = 6

# yt-dlp messages that mean the request was rejected for authentication reasons.
LOGIN_HINTS = (
    "sign in to confirm",
    "login required",
    "private video",
    "members-only",
    "members only",
    "this video is available to this channel's members",
    "confirm you’re not a bot",
    "confirm you're not a bot",
)


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


def safe_video_id(video_id: str) -> bool:
    return video_id not in {".", ".."} and not any(char in video_id for char in "/\\")


def subtitle_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
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


def cookie_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> list[list[str]]:
    if args.cookies:
        path = args.cookies.expanduser().resolve()
        if not path.is_file():
            parser.error("cookies file does not exist")
        return [["--cookies", str(path)]]
    if args.cookies_from_browser:
        return [["--cookies-from-browser", args.cookies_from_browser]]
    files = cookie_files(args.cookie_dir)
    if not files:
        return [[]]
    return [["--cookies", str(path)] for path in files] + [[]]


def cookies_configured(options: list[list[str]]) -> bool:
    return any("--cookies" in item or "--cookies-from-browser" in item for item in options)


def login_hint(output: str) -> bool:
    """Whether yt-dlp output reports an authentication rejection rather than an empty video."""
    lowered = output.lower()
    return any(hint in lowered for hint in LOGIN_HINTS)


def available_subtitle_tracks(info: dict) -> set[str]:
    tracks = set()
    for key in ("subtitles", "automatic_captions"):
        values = info.get(key)
        if isinstance(values, dict):
            tracks.update(str(name) for name in values)
    return tracks


def failure_reason(info: dict, output: str, cookie_configured: bool) -> str:
    if login_hint(output):
        return "cookie-invalid" if cookie_configured else "login-required"
    tracks = {name for name in available_subtitle_tracks(info) if name.lower() != "live_chat"}
    if not tracks:
        return "no-subtitle-track"
    return "subtitle-download-failed"


def failure_message(video_id: str, reason: str) -> str:
    """Explain one concrete missing-subtitle reason instead of guessing."""
    messages = {
        "cookie-invalid": "登录或人机校验失败；请更新 Cookie 后重试。",
        "login-required": "需要登录才能取得字幕；请配置 Cookie 后重试。",
        "no-subtitle-track": "该视频没有可用的字幕轨（只有直播聊天等）。",
        "subtitle-download-failed": "存在字幕轨但未下载成功；可重试或检查 yt-dlp。",
    }
    detail = messages.get(reason, "原因未知；请重试或检查 yt-dlp 输出。")
    return f"{video_id} 未获得字幕：{detail}"


def build_command(executable: str, url: str, output: Path, sub_langs: str, cookies: list[str]) -> list[str]:
    return [
        executable, "--ignore-config", "--no-playlist", "--skip-download",
        "--write-subs", "--write-auto-subs", "--write-info-json",
        "--print-json", "--no-simulate", "--no-progress", "--socket-timeout", "20",
        "--retries", "2", "--sub-langs", sub_langs,
        "--sub-format", "srt/vtt/best",
        "-o", str(output / "%(id)s" / "%(id)s.%(ext)s"),
        *cookies, "--", url,
    ]


def has_subtitles(metadata: list[dict], output: Path) -> bool:
    return any(
        subtitle_files(output / info["id"]) for info in metadata
        if isinstance(info.get("id"), str) and safe_video_id(info["id"])
    )


def run_with_cookie_options(
    executable: str, args: argparse.Namespace, output: Path, options: list[list[str]]
) -> tuple[subprocess.CompletedProcess | None, list[dict], int]:
    """Try each Cookie candidate newest first, and stop at the first usable transcript."""
    last_result = None
    last_metadata: list[dict] = []
    attempts = 0
    for cookies in options:
        attempts += 1
        command = build_command(executable, args.url, output, args.sub_langs, cookies)
        result = subprocess.run(command, text=True, capture_output=True, timeout=180, check=False)
        metadata = parse_metadata(result.stdout)
        last_result, last_metadata = result, metadata
        if has_subtitles(metadata, output):
            return result, metadata, attempts
    return last_result, last_metadata, attempts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--output", type=Path, help="override the configured note directory")
    parser.add_argument("--sub-langs", default="all,-live_chat")
    parser.add_argument("--cookie-dir", action="append", help="search this YouTube Cookie directory; may be repeated")
    cookies = parser.add_mutually_exclusive_group()
    cookies.add_argument("--cookies-from-browser", metavar="BROWSER")
    cookies.add_argument("--cookies", type=Path, help="local Netscape-format cookies file")
    args = parser.parse_args()
    if not is_youtube_url(args.url):
        parser.error("provide a YouTube video URL from youtube.com, music.youtube.com, or youtu.be")

    try:
        config, created = ensure_config()
    except (OSError, ValueError) as error:
        print(f"无法读取 YouTube digest 配置：{error}", file=sys.stderr)
        return 2
    if created:
        print(f"已创建配置模板：{config_path()}")
        hint = notes_dir_hint(config)
        if hint:
            print(hint, file=sys.stderr)

    executable = yt_dlp_command()
    if executable is None:
        print("未找到 yt-dlp。请安装 yt-dlp，或设置 YOUTUBE_YT_DLP。", file=sys.stderr)
        return 2

    notes_dir = args.output or Path(os.environ.get("YOUTUBE_NOTES_DIR", config["notes_dir"])).expanduser()
    output = notes_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    cookie_sets = cookie_options(args, parser)
    cookie_configured = cookies_configured(cookie_sets)
    if cookie_configured:
        print("YouTube 无离线登录态接口；Cookie 是否有效只能由 yt-dlp 的结果判断。", file=sys.stderr)

    try:
        result, metadata, attempts = run_with_cookie_options(executable, args, output, cookie_sets)
    except (OSError, subprocess.TimeoutExpired):
        print("yt-dlp 启动失败或超过 180 秒；请检查 WSL 网络和可执行文件。", file=sys.stderr)
        return 2
    if result is None:
        print("没有可用的 Cookie 或 yt-dlp 没有返回结果。", file=sys.stderr)
        return 3
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if attempts > 1:
        print(f"已尝试 {attempts} 个 Cookie 配置。", file=sys.stderr)
    if not metadata:
        print("yt-dlp 未返回视频元数据。", file=sys.stderr)
        return 3

    missing = False
    auth_failure = False
    for info in metadata:
        video_id = info["id"]
        if not safe_video_id(video_id):
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
            reason = failure_reason(info, result.stderr or "", cookie_configured)
            manifest["status"] = "no-accessible-subtitle"
            manifest["reason"] = reason
            manifest["auth_status"] = "unknown" if cookie_configured else "not-configured"
            manifest["available_subtitle_tracks"] = sorted(available_subtitle_tracks(info))
            print(failure_message(video_id, reason), file=sys.stderr)
            missing = True
            if reason in {"login-required", "cookie-invalid"}:
                auth_failure = True
        (folder / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
    if result.returncode and not missing:
        print(f"下载未完成（yt-dlp 退出码 {result.returncode}）。", file=sys.stderr)
        return 3
    if auth_failure:
        return EXIT_LOGIN_REQUIRED
    return EXIT_NO_SUBTITLE if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
