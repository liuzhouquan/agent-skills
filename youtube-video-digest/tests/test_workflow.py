"""Behavioral checks for the YouTube workflow; no real downloads or messages."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_youtube as fetch
import send_telegram as sender
import subtitle_to_text as subtitle


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
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(), 4)
        manifest = json.loads((self.root / "abc123" / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "no-accessible-subtitle")


class TelegramTests(unittest.TestCase):
    def test_unicode_chunks_preserve_text_and_limit(self):
        content = "YouTube😀笔记\n" * 1800
        parts = list(sender.chunks(content))
        self.assertEqual("".join(parts), content)
        self.assertTrue(all(0 < len(part.encode("utf-16-le")) // 2 <= 3800 for part in parts))


if __name__ == "__main__":
    unittest.main()
