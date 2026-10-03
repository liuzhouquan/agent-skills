#!/usr/bin/env python3
"""Download one or more Bilibili subtitles and create timestamped transcripts."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import parse_qs, parse_qsl, urlencode, urlparse, urlunparse

from cookie_config import cookie_files
from subtitle_to_text import convert
from user_config import config_path, ensure_config


EXIT_NO_SUBTITLE = 4
EXIT_COOKIE_INVALID = 6


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
    if not folder.is_dir():
        return []
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


def cookie_file(options: list[str]) -> Path | None:
    try:
        return Path(options[options.index("--cookies") + 1])
    except (ValueError, IndexError):
        return None


def cookie_header(path: Path) -> str:
    values = {}
    now = int(time.time())
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 7 or "bilibili.com" not in fields[0].lower():
            continue
        if fields[4].isdigit() and int(fields[4]) not in {0} and int(fields[4]) <= now:
            continue
        values[fields[5]] = fields[6]
    return "; ".join(f"{name}={value}" for name, value in values.items())


def check_cookie_login(options: list[str]) -> str:
    """Return valid, invalid, unknown, or not-configured without exposing Cookie values."""
    path = cookie_file(options)
    if path is None:
        return "unknown" if "--cookies-from-browser" in options else "not-configured"
    try:
        header = cookie_header(path)
        if not header:
            return "invalid"
        request = urlrequest.Request(
            "https://api.bilibili.com/x/web-interface/nav",
            headers={"Cookie": header, "User-Agent": "Mozilla/5.0"},
        )
        with urlrequest.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, UnicodeError, ValueError, urlerror.URLError, urlerror.HTTPError, TimeoutError):
        return "unknown"
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict) and data.get("isLogin") is True and payload.get("code") == 0:
        return "valid"
    if payload.get("code") == -101 or (isinstance(data, dict) and data.get("isLogin") is False):
        return "invalid"
    return "unknown"


def auth_status(options: list[list[str]]) -> str:
    states = [check_cookie_login(item) for item in options]
    if "valid" in states:
        return "valid"
    if "invalid" in states:
        return "invalid"
    if "unknown" in states:
        return "unknown"
    return "not-configured"


def available_subtitle_tracks(info: dict) -> set[str]:
    tracks = set()
    for key in ("subtitles", "automatic_captions"):
        values = info.get(key)
        if isinstance(values, dict):
            tracks.update(str(name) for name in values)
    return tracks


def subtitle_failure_reason(info: dict, login_status: str) -> str:
    tracks = available_subtitle_tracks(info)
    non_danmaku = {name for name in tracks if name.lower() != "danmaku"}
    if login_status == "invalid":
        return "cookie-invalid"
    if login_status == "unknown":
        return "cookie-status-unverified"
    if login_status == "not-configured":
        return "no-cookie-or-login-required"
    if not non_danmaku:
        return "no-subtitle-track"
    return "subtitle-download-failed"


def selected_part(url: str) -> int | None:
    values = parse_qs(urlparse(url).query).get("p", [])
    if not values:
        return None
    if len(values) != 1 or not values[0].isdigit() or int(values[0]) < 1:
        raise ValueError("URL 中的 p 参数必须是正整数，例如 ?p=2")
    return int(values[0])


def parse_parts(spec: str) -> list[int]:
    """Parse 1-3,7-9 / 1~3,7,8,9 into sorted unique positive part numbers."""
    normalized = spec.translate(str.maketrans("～—–", "~~~"))
    parts: set[int] = set()
    for token in re.split(r"[\s,，;；]+", normalized.strip()):
        if not token:
            continue
        match = re.fullmatch(r"(\d+)\s*[-~]\s*(\d+)", token)
        if match:
            start, end = map(int, match.groups())
            if start < 1 or end < start or end - start > 100:
                raise ValueError(f"无效的分集范围：{token}")
            parts.update(range(start, end + 1))
        elif token.isdigit() and int(token) > 0:
            parts.add(int(token))
        else:
            raise ValueError(f"无法解析分集：{token}。示例：1-3,7-9")
    if not parts:
        raise ValueError("至少指定一个分集")
    if len(parts) > 100:
        raise ValueError("一次最多处理 100 个分集")
    return sorted(parts)


def part_url(url: str, part: int) -> str:
    parsed = urlparse(url)
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key != "p"]
    query.append(("p", str(part)))
    return urlunparse(parsed._replace(query=urlencode(query)))


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


def run_download(executable: str, url: str, output: Path, sub_langs: str, cookies: list[str]):
    command = [
        executable, "--ignore-config", "--no-playlist", "--skip-download",
        "--write-subs", "--write-auto-subs", "--write-info-json",
        "--print-json", "--no-simulate", "--no-progress", "--socket-timeout", "20",
        "--retries", "2", "--sub-langs", sub_langs,
        "--sub-format", "srt/vtt/best",
        "-o", str(output / "%(id)s" / "%(id)s.%(ext)s"),
        *cookies, "--", url,
    ]
    return subprocess.run(command, text=True, capture_output=True, timeout=180, check=False)


def safe_video_id(video_id: str) -> bool:
    return video_id not in {".", ".."} and not any(char in video_id for char in "/\\")


def has_subtitles(metadata: list[dict], output: Path) -> bool:
    return any(subtitle_files(output / info["id"]) for info in metadata if safe_video_id(info["id"]))


def run_with_cookie_options(
    executable: str, url: str, output: Path, sub_langs: str, options: list[list[str]]
):
    last_result = None
    last_metadata: list[dict] = []
    attempts = 0
    for cookies in options:
        attempts += 1
        result = run_download(executable, url, output, sub_langs, cookies)
        metadata = metadata_from_output(result.stdout)
        last_result, last_metadata = result, metadata
        if metadata and has_subtitles(metadata, output):
            return result, metadata, attempts
    return last_result, last_metadata, attempts


def process_info(
    info: dict, source_url: str, output: Path, failure_reason: str | None = None, login_status: str | None = None
) -> tuple[dict, bool]:
    video_id = info["id"]
    if not safe_video_id(video_id):
        raise ValueError("视频 ID 格式错误。")
    folder = output / video_id
    folder.mkdir(parents=True, exist_ok=True)
    paths = subtitle_files(folder)
    manifest = {
        "id": video_id, "title": info.get("title"), "uploader": info.get("uploader"),
        "upload_date": info.get("upload_date"), "duration": info.get("duration"),
        "source_url": source_url, "webpage_url": info.get("webpage_url"),
        "subtitles": [str(path) for path in paths],
    }
    if not paths:
        manifest["status"] = "no-accessible-subtitle"
        manifest["reason"] = failure_reason or subtitle_failure_reason(info, login_status or "unknown")
        manifest["auth_status"] = login_status or "unknown"
        manifest["available_subtitle_tracks"] = sorted(available_subtitle_tracks(info))
        return manifest, True
    selected = preferred_subtitle(paths)
    transcript = folder / "transcript.txt"
    convert(selected, transcript)
    manifest.update(status="transcript-ready", selected_subtitle=str(selected), transcript=str(transcript))
    return manifest, False


def series_id(video_id: str) -> str:
    return re.sub(r"_p\d+$", "", video_id)


def write_series_transcript(output: Path, source_url: str, records: list[dict], requested_parts: list[int]) -> Path:
    base_id = series_id(records[0]["id"])
    folder = output / base_id
    folder.mkdir(parents=True, exist_ok=True)
    chunks = []
    included = 0
    for record in records:
        transcript_path = record.get("transcript")
        if not transcript_path or not Path(transcript_path).is_file():
            continue
        part = record.get("part")
        label = f"第 {part} 集" if part else record["id"]
        chunks.append(f"\n===== {label}：{record.get('title') or ''} =====\n")
        chunks.append(Path(transcript_path).read_text(encoding="utf-8"))
        included += 1
    transcript = folder / "combined-transcript.txt"
    transcript.write_text("".join(chunks).lstrip(), encoding="utf-8")
    (folder / "series-manifest.json").write_text(
        json.dumps({
            "id": base_id, "source_url": source_url, "requested_parts": requested_parts,
            "parts": records, "status": "transcript-ready" if included == len(records) else "partial",
            "combined_transcript": str(transcript),
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return transcript


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--output", type=Path, help="override the configured note directory")
    parser.add_argument("--sub-langs", default="all,-danmaku")
    parser.add_argument("--parts", help="batch parts, e.g. 1-3,7-9; requires a multi-part URL without ?p=")
    parser.add_argument("--cookie-dir", action="append", help="search this Bilibili Cookie directory; may be repeated")
    cookies = parser.add_mutually_exclusive_group()
    cookies.add_argument("--cookies-from-browser", metavar="BROWSER")
    cookies.add_argument("--cookies", type=Path, help="local Netscape-format cookies file")
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "www.bilibili.com", "bilibili.com", "m.bilibili.com", "b23.tv",
    } or parsed.username or parsed.password:
        parser.error("provide a Bilibili video URL or b23.tv share URL")
    try:
        explicit_part = selected_part(args.url)
        requested_parts = parse_parts(args.parts) if args.parts else None
    except ValueError as error:
        parser.error(str(error))
    if explicit_part is not None and requested_parts is not None:
        parser.error("URL 已指定 ?p= 时不能再使用 --parts")

    try:
        config, created = ensure_config()
    except (OSError, ValueError) as error:
        print(f"无法读取 Bilibili digest 配置：{error}", file=sys.stderr)
        return 2
    if created:
        print(f"已创建配置模板：{config_path()}")
    executable = yt_dlp_command()
    if executable is None:
        print("未找到 yt-dlp。请在隔离 Python 环境安装，或设置 BILIBILI_YT_DLP。", file=sys.stderr)
        return 2
    notes_dir = args.output or Path(os.environ.get("BILIBILI_NOTES_DIR", config["notes_dir"])).expanduser()
    output = notes_dir.resolve()
    cookie_sets = cookie_options(args, parser)
    login_status = auth_status(cookie_sets)
    if login_status == "invalid":
        print("Cookie 登录态无效：将继续尝试公开字幕；如果字幕缺失，请更新 Cookie。", file=sys.stderr)
    elif login_status == "unknown":
        print("无法确认 Cookie 登录态；如果没有字幕，请先检查网络或更新 Cookie。", file=sys.stderr)
    elif login_status == "not-configured":
        print("未配置可验证的 B 站 Cookie；字幕缺失时无法区分登录限制和视频无字幕。", file=sys.stderr)
    if explicit_part is not None:
        targets = [(explicit_part, args.url)]
    else:
        probe = None
        for cookies in cookie_sets:
            probe = probe_metadata(executable, args.url, cookies)
            if probe is not None:
                break
        if probe is None:
            print("无法判断该链接是否包含多分集内容；为避免默认处理第 1 集，已停止。", file=sys.stderr)
            return 3
        is_playlist = probe.get("_type") == "playlist"
        count = int(probe.get("playlist_count") or len(probe.get("entries") or [])) if is_playlist else 1
        if is_playlist and count > 1:
            if not requested_parts:
                print(
                    f"检测到“{probe.get('title') or probe.get('id') or '该视频'}”包含 {count} 个分集。"
                    "请在链接后指定 ?p=1，或使用 --parts 1-3,7-9；本次未下载字幕。",
                    file=sys.stderr,
                )
                return 5
            if any(part > count for part in requested_parts):
                print(f"请求的分集超出范围；该视频共有 {count} 集。", file=sys.stderr)
                return 5
            targets = [(part, part_url(args.url, part)) for part in requested_parts]
        else:
            if requested_parts and requested_parts != [1]:
                print("该链接不是多分集视频，不能请求多个分集。", file=sys.stderr)
                return 5
            targets = [(None, args.url)]

    output.mkdir(parents=True, exist_ok=True)
    records = []
    missing = False
    failed = False
    for part, target in targets:
        try:
            result, metadata, attempts = run_with_cookie_options(
                executable, target, output, args.sub_langs, cookie_sets
            )
        except (OSError, subprocess.TimeoutExpired):
            print(f"{target}：yt-dlp 启动失败或超过 180 秒。", file=sys.stderr)
            failed = True
            continue
        if result is None:
            print(f"{target}：没有可用的 Cookie 或 yt-dlp 没有返回结果。", file=sys.stderr)
            failed = True
            continue
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        if attempts > 1:
            print(f"{target}：已尝试 {attempts} 个 Cookie 配置。", file=sys.stderr)
        if not metadata:
            print(f"{target}：yt-dlp 未返回视频元数据。", file=sys.stderr)
            failed = True
            continue
        if result.returncode:
            print(f"{target}：下载未完成（退出码 {result.returncode}），继续检查已保存的字幕。", file=sys.stderr)
            failed = True
        for info in metadata:
            try:
                manifest, no_subtitle = process_info(
                    info, target, output, subtitle_failure_reason(info, login_status), login_status
                )
            except (OSError, ValueError, TypeError) as error:
                print(f"字幕解析失败：{error}", file=sys.stderr)
                failed = True
                continue
            if part is not None:
                manifest["part"] = part
            (output / info["id"] / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
            )
            records.append(manifest)
            if no_subtitle:
                print(f"{info['id']} 未获得字幕。可能需要登录 Cookie，或只有画面内字幕。", file=sys.stderr)
                missing = True
            else:
                print(f"已提取：{info.get('title', info['id'])}\n文字稿：{manifest['transcript']}")

    if len(targets) > 1 and records:
        combined = write_series_transcript(output, args.url, records, [part for part, _ in targets if part is not None])
        print(f"合并文字稿：{combined}")
    if not records:
        return 3
    if login_status == "invalid" and missing:
        return EXIT_COOKIE_INVALID
    if failed or missing:
        return EXIT_NO_SUBTITLE
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
