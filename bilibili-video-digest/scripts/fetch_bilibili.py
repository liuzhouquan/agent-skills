#!/usr/bin/env python3
"""Download Bilibili subtitles and create a timestamped transcript."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from subtitle_to_text import convert


def yt_dlp_command() -> str | None:
    candidates = [
        os.environ.get("BILIBILI_YT_DLP"),
        str(Path.home() / ".local/share/bilibili-video-digest/venv/bin/yt-dlp"),
        shutil.which("yt-dlp"),
        shutil.which("yt-dlp_linux"),
    ]
    return next((path for path in candidates if path and Path(path).is_file() and os.access(path, os.X_OK)), None)


def subtitle_files(folder: Path) -> list[Path]:
    # Include cached subtitles on reruns; metadata JSON is never a transcript.
    return sorted(
        path for path in folder.iterdir()
        if path.is_file() and path.stat().st_size
        and path.suffix.lower() in {".srt", ".vtt", ".ass", ".json"}
        and not path.name.endswith((".info.json", "manifest.json"))
    )


def preferred_subtitle(paths: list[Path]) -> Path:
    def rank(path: Path):
        name = path.name.lower()
        chinese = any(tag in name for tag in (".zh", ".ai-zh"))
        automatic = ".ai-" in name
        return (not chinese, automatic, path.name)
    return min(paths, key=rank)


def metadata_from_output(output: str) -> list[dict]:
    metadata = []
    for line in output.splitlines():
        try:
            info = json.loads(line)
        except ValueError:
            continue
        if isinstance(info, dict) and isinstance(info.get("id"), str):
            metadata.append(info)
    return metadata


def cookie_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> list[str]:
    if args.cookies:
        path = args.cookies.expanduser().resolve()
        if not path.is_file():
            parser.error("cookies file does not exist")
        return ["--cookies", str(path)]
    if args.cookies_from_browser:
        return ["--cookies-from-browser", args.cookies_from_browser]
    return []


def selected_part(url: str) -> int | None:
    values = parse_qs(urlparse(url).query).get("p", [])
    if not values:
        return None
    if len(values) != 1 or not values[0].isdigit() or int(values[0]) < 1:
        raise ValueError("URL 中的 p 参数必须是正整数，例如 ?p=2")
    return int(values[0])


def probe_metadata(executable: str, url: str, cookies: list[str]) -> dict | None:
    command = [
        executable, "--ignore-config", "--flat-playlist", "--dump-single-json", "--skip-download",
        "--no-warnings", "--socket-timeout", "20", "--retries", "2",
        *cookies, "--", url,
    ]
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=90, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    values = metadata_from_output(result.stdout)
    return values[0] if values else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--output", type=Path, default=Path("bilibili-notes"))
    parser.add_argument("--sub-langs", default="all,-danmaku")
    cookies = parser.add_mutually_exclusive_group()
    cookies.add_argument("--cookies-from-browser", metavar="BROWSER")
    cookies.add_argument("--cookies", type=Path, help="local Netscape-format cookies file")
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "www.bilibili.com", "bilibili.com", "m.bilibili.com", "b23.tv",
    } or parsed.username or parsed.password:
        parser.error("provide a Bilibili video URL or b23.tv share URL")

    executable = yt_dlp_command()
    if executable is None:
        print("未找到 yt-dlp。请在隔离 Python 环境安装，或设置 BILIBILI_YT_DLP。", file=sys.stderr)
        return 2
    try:
        part = selected_part(args.url)
    except ValueError as error:
        parser.error(str(error))
    cookies = cookie_args(args, parser)
    if part is None:
        probe = probe_metadata(executable, args.url, cookies)
        if probe is None:
            print("无法判断该链接是否包含多分集内容；为避免默认处理第 1 集，已停止。", file=sys.stderr)
            return 3
        if probe.get("_type") == "playlist":
            count = probe.get("playlist_count") or len(probe.get("entries") or [])
            if count and int(count) > 1:
                title = probe.get("title") or probe.get("id") or "该视频"
                print(
                    f"检测到“{title}”包含 {count} 个分集。请在链接后指定 ?p=1、?p=2 等分集；"
                    "本次未下载字幕。",
                    file=sys.stderr,
                )
                return 5
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
    command.extend(cookies)
    command.extend(["--", args.url])
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=180, check=False)
    except (OSError, subprocess.TimeoutExpired):
        print("yt-dlp 启动失败或超过 180 秒；请检查 WSL 网络和可执行文件。", file=sys.stderr)
        return 2
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    metadata = metadata_from_output(result.stdout)
    if not metadata:
        print("yt-dlp 未返回视频元数据。", file=sys.stderr)
        return 3
    download_failed = bool(result.returncode)
    if download_failed:
        print(f"下载未完成（yt-dlp 退出码 {result.returncode}），继续检查已保存的字幕。", file=sys.stderr)

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
            "id": video_id, "title": info.get("title"), "uploader": info.get("uploader"),
            "upload_date": info.get("upload_date"), "duration": info.get("duration"),
            "source_url": args.url, "webpage_url": info.get("webpage_url"),
            "subtitles": [str(path) for path in paths],
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
    if download_failed and not missing:
        return 3
    return 4 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
