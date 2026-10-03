"""Behavioral checks for the YouTube workflow; no real downloads or messages."""

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_youtube as fetch
import configure_cookies
import cookie_config
import send_telegram as sender
import subtitle_to_text as subtitle
import user_config


class TemporaryFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path


class URLTests(unittest.TestCase):
    def test_supported_video_hosts(self):
        for url in (
            "https://www.youtube.com/watch?v=abc",
            "https://youtu.be/abc",
            "https://m.youtube.com/shorts/abc",
            "https://music.youtube.com/watch?v=abc",
        ):
            self.assertTrue(fetch.is_youtube_url(url))

    def test_rejects_credentials_and_other_hosts(self):
        self.assertFalse(fetch.is_youtube_url("https://user:pass@youtube.com/watch?v=abc"))
        self.assertFalse(fetch.is_youtube_url("https://example.com/watch?v=abc"))


class SubtitleTests(TemporaryFiles):
    def test_vtt_is_converted(self):
        path = self.write("video.en.vtt", "WEBVTT\n\n00:01.500 --> 00:03.000\n<b>Learning</b> &amp; practice\n")
        self.assertEqual(subtitle.convert(path), "[00:00:01] Learning & practice\n")

    def test_empty_subtitle_does_not_create_transcript(self):
        path = self.write("empty.vtt", "WEBVTT\n")
        output = self.root / "transcript.txt"
        with self.assertRaises(ValueError):
            subtitle.convert(path, output)
        self.assertFalse(output.exists())


class FetchTests(TemporaryFiles):
    def setUp(self):
        super().setUp()
        self.config_patch = patch.dict(
            os.environ,
            {"YOUTUBE_DIGEST_CONFIG": str(self.root / "config.json"), "YOUTUBE_COOKIE_DIRS": ""},
            clear=False,
        )
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def test_cached_chinese_subtitle_is_success(self):
        folder = self.root / "abc123"
        folder.mkdir()
        (folder / "abc123.en.vtt").write_text("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nEnglish\n", encoding="utf-8")
        (folder / "abc123.zh-Hans.vtt").write_text("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n中文\n", encoding="utf-8")
        fake = subprocess.CompletedProcess([], 0, json.dumps({"id": "abc123", "title": "课程", "channel": "频道"}), "")
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch.subprocess, "run", return_value=fake), \
                patch.object(sys, "argv", ["fetch", "https://youtu.be/abc123", "--output", str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(fetch.main(), 0)
        self.assertEqual((folder / "transcript.txt").read_text(encoding="utf-8").strip(), "[00:00:01] 中文")
        self.assertEqual(json.loads((folder / "manifest.json").read_text())['status'], "transcript-ready")

    def test_metadata_is_preserved_when_subtitles_are_missing(self):
        fake = subprocess.CompletedProcess([], 1, json.dumps({"id": "abc123", "title": "登录视频"}), "access denied")
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch.subprocess, "run", return_value=fake), \
                patch.object(sys, "argv", ["fetch", "https://www.youtube.com/watch?v=abc123", "--output", str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(), fetch.EXIT_NO_SUBTITLE)
        manifest = json.loads((self.root / "abc123" / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "no-accessible-subtitle")
        self.assertEqual(manifest["reason"], "no-subtitle-track")
        self.assertEqual(manifest["auth_status"], "not-configured")
        self.assertEqual(manifest["available_subtitle_tracks"], [])

    def test_login_requirement_without_cookie_is_distinct_from_no_subtitle(self):
        stderr = "ERROR: [youtube] abc123: Private video. Sign in if you've been granted access"
        fake = subprocess.CompletedProcess([], 1, json.dumps({"id": "abc123", "title": "私有视频"}), stderr)
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch, "cookie_options", return_value=[[]]), \
                patch.object(fetch.subprocess, "run", return_value=fake), \
                patch.object(sys, "argv", ["fetch", "https://www.youtube.com/watch?v=abc123", "--output", str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(), fetch.EXIT_LOGIN_REQUIRED)
        manifest = json.loads((self.root / "abc123" / "manifest.json").read_text())
        self.assertEqual(manifest["reason"], "login-required")
        self.assertEqual(manifest["auth_status"], "not-configured")

    def test_rejected_cookie_is_reported_as_cookie_invalid(self):
        stderr = "ERROR: [youtube] abc123: Sign in to confirm you’re not a bot."
        fake = subprocess.CompletedProcess([], 1, json.dumps({"id": "abc123", "title": "登录视频"}), stderr)
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch, "cookie_options", return_value=[["--cookies", "/tmp/fake.cookies"]]), \
                patch.object(fetch.subprocess, "run", return_value=fake), \
                patch.object(sys, "argv", ["fetch", "https://www.youtube.com/watch?v=abc123", "--output", str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(fetch.main(), fetch.EXIT_LOGIN_REQUIRED)
        manifest = json.loads((self.root / "abc123" / "manifest.json").read_text())
        self.assertEqual(manifest["reason"], "cookie-invalid")
        self.assertEqual(manifest["auth_status"], "unknown")
        self.assertIn("Cookie", errors.getvalue())

    def test_configured_notes_directory_is_used_without_output_override(self):
        notes = self.root / "configured-notes"
        user_config.set_notes_dir(notes)
        folder = notes / "abc123"
        folder.mkdir(parents=True)
        (folder / "abc123.zh-Hans.vtt").write_text(
            "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n配置目录内容\n", encoding="utf-8"
        )
        fake = subprocess.CompletedProcess([], 0, json.dumps({"id": "abc123", "title": "课程"}), "")
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch.subprocess, "run", return_value=fake), \
                patch.object(sys, "argv", ["fetch", "https://youtu.be/abc123"]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(), 0)
        self.assertIn("配置目录内容", (folder / "transcript.txt").read_text(encoding="utf-8"))

    def test_failure_message_names_the_concrete_reason(self):
        self.assertIn("需要登录", fetch.failure_message("abc", "login-required"))
        self.assertIn("没有可用的字幕轨", fetch.failure_message("abc", "no-subtitle-track"))
        self.assertNotIn("可能", fetch.failure_message("abc", "login-required"))


class CookieConfigTests(TemporaryFiles):
    def environment(self, directory):
        return patch.dict(
            os.environ,
            {"YOUTUBE_DIGEST_CONFIG": str(self.root / "config.json"), "YOUTUBE_COOKIE_DIRS": str(directory)},
            clear=False,
        )

    def test_discovery_only_accepts_youtube_cookie_names(self):
        directory = self.root / "cookies"
        directory.mkdir()
        (directory / "www.youtube.com_cookies.txt").write_text("# Netscape\n", encoding="utf-8")
        (directory / "bilibili_cookies.txt").write_text("# Netscape\n", encoding="utf-8")
        (directory / "cookies.txt").write_text("# Netscape\n", encoding="utf-8")
        with self.environment(directory):
            self.assertEqual([path.name for path in cookie_config.cookie_files()], ["www.youtube.com_cookies.txt"])

    def test_cookie_options_keep_a_no_cookie_fallback(self):
        directory = self.root / "cookies"
        directory.mkdir()
        (directory / "youtube_cookies.txt").write_text("# Netscape\n", encoding="utf-8")
        arguments = argparse.Namespace(cookies=None, cookies_from_browser=None, cookie_dir=None)
        with self.environment(directory):
            options = fetch.cookie_options(arguments, argparse.ArgumentParser())
        self.assertEqual(len(options), 2)
        self.assertEqual(options[-1], [])
        self.assertTrue(fetch.cookies_configured(options))

    def test_existing_notes_directories_are_reported(self):
        archive = self.root / "projects" / "youtube-notes"
        archive.mkdir(parents=True)
        configured = self.root / "youtube-notes"
        self.assertEqual(user_config.existing_notes_dirs(configured, bases=[self.root]), [archive.resolve()])
        hint = user_config.notes_dir_hint({"notes_dir": str(configured)}, bases=[self.root])
        self.assertIn(str(archive.resolve()), hint)
        self.assertIn("--set-notes-dir", hint)


class ConfigureTests(TemporaryFiles):
    def test_list_reports_directories_and_cookie_files(self):
        directory = self.root / "cookies"
        directory.mkdir()
        (directory / "www.youtube.com_cookies.txt").write_text("# Netscape\n", encoding="utf-8")
        environment = patch.dict(
            os.environ,
            {"YOUTUBE_DIGEST_CONFIG": str(self.root / "config.json"), "YOUTUBE_COOKIE_DIRS": str(directory)},
            clear=False,
        )
        with environment, patch.object(sys, "argv", ["configure", "--list"]), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(configure_cookies.main(), 0)
        text = out.getvalue()
        self.assertIn(str(directory), text)
        self.assertIn("www.youtube.com_cookies.txt", text)


class TelegramTests(unittest.TestCase):
    def test_unicode_chunks_preserve_text_and_limit(self):
        content = "YouTube😀笔记\n" * 1800
        parts = list(sender.chunks(content))
        self.assertEqual("".join(parts), content)
        self.assertTrue(all(0 < len(part.encode("utf-16-le")) // 2 <= 3800 for part in parts))


if __name__ == "__main__":
    unittest.main()
