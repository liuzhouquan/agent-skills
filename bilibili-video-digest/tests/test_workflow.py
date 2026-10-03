"""Behavioral checks; fake Telegram/yt-dlp I/O, no messages or real credentials."""

import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import telegram_common as common
import setup_telegram as setup
import send_telegram as sender
import subtitle_to_text as subtitle
import fetch_bilibili as fetch
import configure_cookies
import cookie_config
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


class CredentialTests(TemporaryFiles):
    def test_previous_export_format_remains_compatible(self):
        path = self.write("config", "# old config\nexport TELEGRAM_BOT_TOKEN='123:FAKE'\nexport TELEGRAM_CHAT_ID='42'\n")
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(common.credentials(path), ("123:FAKE", "42"))

    def test_partial_environment_does_not_mix_bots(self):
        path = self.write("config", "TELEGRAM_BOT_TOKEN=123:OLD\nTELEGRAM_CHAT_ID=42\n")
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "456:NEW"}, clear=True):
            with self.assertRaises(common.TelegramError):
                common.credentials(path)

    def test_save_replaces_existing_file_privately(self):
        path = self.write("config", "old")
        path.chmod(0o644)
        common.save_config("123:FAKE", "42", path)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(common.read_config(path)["TELEGRAM_CHAT_ID"], "42")
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["config"])

    def test_failed_replace_preserves_old_configuration(self):
        path = self.write("config", "old")
        with patch.object(common.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                common.save_config("123:FAKE", "42", path)
        self.assertEqual(path.read_text(), "old")
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["config"])


class CookieConfigTests(TemporaryFiles):
    def test_discovery_only_accepts_bilibili_cookie_names(self):
        directory = self.root / "cookies"
        directory.mkdir()
        (directory / "www.bilibili.com_cookies.txt").write_text("# Netscape\n", encoding="utf-8")
        (directory / "youtube_cookies.txt").write_text("# Netscape\n", encoding="utf-8")
        (directory / "random.txt").write_text("# Netscape\n", encoding="utf-8")
        config = self.root / "config.json"
        with patch.dict(os.environ, {"BILIBILI_COOKIE_DIRS": str(directory), "BILIBILI_DIGEST_CONFIG": str(config)}, clear=False):
            self.assertEqual([p.name for p in cookie_config.cookie_files()], ["www.bilibili.com_cookies.txt"])

    def test_directory_registration_is_persistent(self):
        directory = self.root / "cookies"
        directory.mkdir()
        config = self.root / "nested" / "config.json"
        with patch.dict(os.environ, {"BILIBILI_DIGEST_CONFIG": str(config), "BILIBILI_COOKIE_DIRS": ""}, clear=False):
            self.assertEqual(cookie_config.add_dir(directory), directory.resolve())
            self.assertEqual(cookie_config.configured_dirs(), [directory.resolve()])
        self.assertEqual(config.stat().st_mode & 0o777, 0o600)

    def test_missing_config_creates_non_secret_template(self):
        config = self.root / "config.json"
        with patch.dict(os.environ, {"BILIBILI_DIGEST_CONFIG": str(config)}, clear=False):
            data, created = user_config.ensure_config()
        self.assertTrue(created)
        self.assertEqual(data["cookie_dirs"], [])
        self.assertEqual(config.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("TOKEN", config.read_text())

    def test_notes_directory_can_be_changed(self):
        config = self.root / "config.json"
        notes = self.root / "notes"
        with patch.dict(os.environ, {"BILIBILI_DIGEST_CONFIG": str(config)}, clear=False):
            user_config.ensure_config()
            self.assertEqual(user_config.set_notes_dir(notes), notes.resolve())
            self.assertEqual(user_config.load_config()["notes_dir"], str(notes.resolve()))

    def test_httponly_prefixed_cookie_line_is_used(self):
        path = self.write(
            "bilibili.cookies.txt",
            "# Netscape HTTP Cookie File\n"
            "#HttpOnly_.bilibili.com\tTRUE\t/\tFALSE\t0\tSESSDATA\tvalue\n",
        )
        self.assertIn("SESSDATA=value", fetch.cookie_header(path))

    def test_expired_cookie_line_is_ignored(self):
        path = self.write(
            "bilibili.cookies.txt",
            "# Netscape HTTP Cookie File\n.bilibili.com\tTRUE\t/\tFALSE\t1\tSESSDATA\tstale\n",
        )
        self.assertEqual(fetch.cookie_header(path), "")

    def test_existing_notes_directories_are_reported(self):
        archive = self.root / "projects" / "bilibili-notes"
        archive.mkdir(parents=True)
        configured = self.root / "bilibili-notes"
        found = user_config.existing_notes_dirs(configured, bases=[self.root])
        self.assertEqual(found, [archive.resolve()])
        hint = user_config.notes_dir_hint({"notes_dir": str(configured)}, bases=[self.root])
        self.assertIn(str(archive.resolve()), hint)
        self.assertIn("--set-notes-dir", hint)

    def test_configured_notes_directory_is_not_reported_as_other(self):
        configured = self.root / "bilibili-notes"
        configured.mkdir()
        self.assertEqual(user_config.existing_notes_dirs(configured, bases=[self.root]), [])


class ConfigureTests(TemporaryFiles):
    def setUp(self):
        super().setUp()
        self.directory = self.root / "cookies"
        self.directory.mkdir()
        (self.directory / "www.bilibili.com_cookies.txt").write_text(
            "# Netscape HTTP Cookie File\n.bilibili.com\tTRUE\t/\tFALSE\t0\tSESSDATA\tvalue\n", encoding="utf-8"
        )
        self.environment = patch.dict(
            os.environ,
            {"BILIBILI_DIGEST_CONFIG": str(self.root / "config.json"), "BILIBILI_COOKIE_DIRS": str(self.directory)},
            clear=False,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def run_configure(self, *arguments):
        with patch.object(sys, "argv", ["configure", *arguments]), contextlib.redirect_stdout(io.StringIO()) as out:
            code = configure_cookies.main()
        return code, out.getvalue()

    def test_list_reports_directories_and_cookie_files(self):
        code, text = self.run_configure("--list")
        self.assertEqual(code, 0)
        self.assertIn(str(self.directory), text)
        self.assertIn("www.bilibili.com_cookies.txt", text)

    def test_check_reports_login_state_without_downloading(self):
        response = io.BytesIO(b'{"code":-101,"data":{"isLogin":false}}')
        with patch.object(fetch.urlrequest, "urlopen", return_value=response) as urlopen:
            code, text = self.run_configure("--check")
        self.assertEqual(code, 0)
        self.assertIn("已失效", text)
        self.assertEqual(urlopen.call_count, 1)


class TelegramTests(unittest.TestCase):
    def message(self, update_id, chat_id, text, chat_type="private"):
        return {"update_id": update_id, "message": {
            "chat": {"id": chat_id, "type": chat_type}, "text": text,
        }}

    def test_binding_ignores_old_and_other_users_messages(self):
        replies = [
            {}, [self.message(1, 111, "/start"), self.message(2, 222, "hello")],
            [self.message(3, 333, "/start code", "group"), self.message(4, 444, "/start code")],
        ]
        with patch.object(setup.secrets, "token_urlsafe", return_value="code"), \
                patch.object(setup, "api_call", side_effect=replies) as api, \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(setup.discover_chat("123:FAKE", "test_bot", 10)["id"], 444)
        self.assertEqual(api.call_args_list[2].args[2]["offset"], 3)
        self.assertNotIn("allowed_updates", api.call_args_list[1].args[2])

    def test_webhook_is_preserved(self):
        with patch.object(setup, "api_call", return_value={"url": "https://example.com/hook"}) as api:
            with self.assertRaises(common.TelegramError):
                setup.discover_chat("123:FAKE", "test_bot", 10)
        self.assertEqual(api.call_count, 1)

    def test_json_ok_false_is_a_failure(self):
        response = io.BytesIO(json.dumps({"ok": False, "error_code": 403, "description": "Forbidden"}).encode())
        with patch.object(common.urllib.request, "urlopen", return_value=response):
            with self.assertRaisesRegex(common.TelegramError, "403"):
                common.api_call("123:FAKE", "sendMessage")

    def test_http_error_redacts_token(self):
        token = "123:FAKE"
        body = io.BytesIO(json.dumps({"ok": False, "error_code": 401, "description": token}).encode())
        error = HTTPError("https://api.telegram.org/bot" + token, 401, "", {}, body)
        with patch.object(common.urllib.request, "urlopen", side_effect=error):
            with self.assertRaises(common.TelegramError) as result:
                common.api_call(token, "getMe")
        self.assertNotIn(token, str(result.exception))

    def test_unicode_long_note_is_preserved_and_within_limit(self):
        text = "课程😀笔记\n" * 1800
        parts = list(sender.chunks(text))
        self.assertEqual("".join(parts), text)
        self.assertTrue(all(0 < len(part.encode("utf-16-le")) // 2 <= 3800 for part in parts))

    def test_failed_send_stops_without_resending_previous_parts(self):
        with patch.object(sender, "api_call", side_effect=[{}, common.TelegramError("timeout")]) as api:
            with self.assertRaisesRegex(common.TelegramError, "已有 1 段"):
                sender.send_note("123:FAKE", "42", "x" * 9000)
        self.assertEqual(api.call_count, 2)

    def test_existing_config_never_prompts_or_overwrites(self):
        with patch.object(setup, "read_config", return_value={"TELEGRAM_BOT_TOKEN": "123:FAKE", "TELEGRAM_CHAT_ID": "42"}), \
                patch.object(setup.getpass, "getpass") as prompt, \
                patch.object(setup, "save_config") as save, \
                patch.object(sys, "argv", ["setup"]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(setup.main(), 0)
        prompt.assert_not_called()
        save.assert_not_called()


class SubtitleTests(TemporaryFiles):
    def test_vtt_short_timestamps_and_markup(self):
        path = self.write("test.vtt", "WEBVTT\n\n00:01.500 --> 00:03.000 align:start\n<b>学习</b> &amp; 练习\n\n01:02.000 --> 01:03.000\n下一句\n")
        self.assertEqual(subtitle.convert(path), "[00:00:01] 学习 & 练习\n[00:01:02] 下一句\n")

    def test_ass_dialogue_commas_and_tags(self):
        path = self.write("test.ass", "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:01:05.00,0:01:07.00,Default,,0,0,0,,{\\b1}第一句,例子\\N第二句\n")
        self.assertEqual(subtitle.convert(path), "[00:01:05] 第一句,例子 第二句\n")

    def test_srt_multiline_crlf(self):
        path = self.write("test.srt", "1\r\n00:00:01,500 --> 00:00:02,500\r\n第一行\r\n第二行\r\n\r\n")
        self.assertEqual(subtitle.convert(path), "[00:00:01] 第一行 第二行\n")

    def test_empty_subtitle_fails_without_output(self):
        path = self.write("empty.vtt", "WEBVTT\n")
        output = self.root / "transcript.txt"
        with self.assertRaises(ValueError):
            subtitle.convert(path, output)
        self.assertFalse(output.exists())

    def test_metadata_json_is_not_subtitle(self):
        with self.assertRaises(ValueError):
            subtitle.convert(self.write("test.json", '{"title":"video"}'))


class FetchTests(TemporaryFiles):
    def setUp(self):
        super().setUp()
        self.config_patch = patch.dict(
            os.environ, {"BILIBILI_DIGEST_CONFIG": str(self.root / "config.json"), "BILIBILI_COOKIE_DIRS": ""}, clear=False
        )
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def test_cookie_login_probe_distinguishes_valid_and_invalid(self):
        cookie = self.write(
            "bilibili.cookies.txt",
            "# Netscape HTTP Cookie File\n.bilibili.com\tTRUE\t/\tFALSE\t0\tSESSDATA\tvalue\n",
        )
        valid = io.BytesIO(b'{"code":0,"data":{"isLogin":true}}')
        invalid = io.BytesIO(b'{"code":-101,"data":{"isLogin":false}}')
        with patch.object(fetch.urlrequest, "urlopen", return_value=valid):
            self.assertEqual(fetch.check_cookie_login(["--cookies", str(cookie)]), "valid")
        with patch.object(fetch.urlrequest, "urlopen", return_value=invalid):
            self.assertEqual(fetch.check_cookie_login(["--cookies", str(cookie)]), "invalid")

    def test_no_subtitle_manifest_records_reason_and_tracks(self):
        info = {"id": "BVno-track", "title": "课程", "subtitles": {"danmaku": [{"ext": "xml"}]}}
        manifest, missing = fetch.process_info(
            info, "https://www.bilibili.com/video/BVno-track", self.root,
            "no-subtitle-track", "valid",
        )
        self.assertTrue(missing)
        self.assertEqual(manifest["status"], "no-accessible-subtitle")
        self.assertEqual(manifest["reason"], "no-subtitle-track")
        self.assertEqual(manifest["auth_status"], "valid")
        self.assertEqual(manifest["available_subtitle_tracks"], ["danmaku"])

    def test_failure_message_names_the_concrete_reason(self):
        self.assertIn("已失效", fetch.subtitle_failure_message("BV1", "cookie-invalid"))
        self.assertIn("没有可用的字幕轨", fetch.subtitle_failure_message("BV1", "no-subtitle-track"))
        self.assertIn("未配置", fetch.subtitle_failure_message("BV1", "no-cookie-or-login-required"))
        self.assertNotIn("可能", fetch.subtitle_failure_message("BV1", "cookie-invalid"))

    def test_invalid_cookie_has_distinct_exit_code(self):
        fake = subprocess.CompletedProcess(
            [], 0, json.dumps({"id": "BVbad-cookie", "title": "课程", "subtitles": {"danmaku": [{}]}}), ""
        )
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch, "cookie_options", return_value=[["--cookies", "/tmp/fake.cookies"]]), \
                patch.object(fetch, "auth_status", return_value="invalid"), \
                patch.object(fetch.subprocess, "run", return_value=fake), \
                patch.object(sys, "argv", ["fetch", "https://www.bilibili.com/video/BVbad-cookie", "--output", str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(), fetch.EXIT_COOKIE_INVALID)

    def test_parts_expression_supports_ranges_and_discrete_parts(self):
        self.assertEqual(fetch.parse_parts("1~3,7,8,9"), [1, 2, 3, 7, 8, 9])

    def test_parts_expression_rejects_reversed_range(self):
        with self.assertRaises(ValueError):
            fetch.parse_parts("3-1")

    def test_multipart_url_without_part_stops_before_download(self):
        playlist = json.dumps({
            "_type": "playlist", "id": "BVseries", "title": "课程", "playlist_count": 23,
            "entries": [{"_type": "url", "url": "https://www.bilibili.com/video/BVseries?p=1"}],
        })
        fake = subprocess.CompletedProcess([], 0, playlist, "")
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch.subprocess, "run", return_value=fake) as run, \
                patch.object(sys, "argv", ["fetch", "https://www.bilibili.com/video/BVseries", "--output", str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(), 5)
        self.assertEqual(run.call_count, 1)
        self.assertFalse((self.root / "BVseries").exists())

    def test_batch_parts_downloads_and_combines_selected_transcripts(self):
        playlist = subprocess.CompletedProcess([], 0, json.dumps({
            "_type": "playlist", "id": "BVseries", "title": "课程", "playlist_count": 4,
            "entries": [],
        }), "")
        results = [playlist]
        for part in (1, 2, 4):
            folder = self.root / f"BVseries_p{part}"
            folder.mkdir()
            (folder / f"BVseries_p{part}.zh-Hans.srt").write_text(
                f"1\n00:00:01,000 --> 00:00:02,000\n第{part}集内容\n", encoding="utf-8"
            )
            results.append(subprocess.CompletedProcess(
                [], 0, json.dumps({"id": f"BVseries_p{part}", "title": f"课程 p{part:02d}"}), ""
            ))
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch.subprocess, "run", side_effect=results) as run, \
                patch.object(sys, "argv", ["fetch", "https://www.bilibili.com/video/BVseries", "--parts", "1-2,4", "--output", str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(), 0)
        self.assertEqual(run.call_count, 4)
        combined = self.root / "BVseries" / "combined-transcript.txt"
        content = combined.read_text(encoding="utf-8")
        self.assertIn("第1集内容", content)
        self.assertIn("第2集内容", content)
        self.assertIn("第4集内容", content)
        self.assertNotIn("第3集内容", content)
        series_manifest = json.loads((self.root / "BVseries" / "series-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(series_manifest["status"], "transcript-ready")

    def test_explicit_part_skips_probe_and_processes_selected_part(self):
        folder = self.root / "BVseries_p2"
        folder.mkdir()
        (folder / "BVseries_p2.zh-Hans.srt").write_text("1\n00:00:01,000 --> 00:00:02,000\n第二集\n", encoding="utf-8")
        fake = subprocess.CompletedProcess([], 0, json.dumps({"id": "BVseries_p2", "title": "课程 p02"}), "")
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch.subprocess, "run", return_value=fake) as run, \
                patch.object(sys, "argv", ["fetch", "https://www.bilibili.com/video/BVseries?p=2", "--output", str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(), 0)
        self.assertEqual(run.call_count, 1)
        self.assertIn("第二集", (folder / "transcript.txt").read_text(encoding="utf-8"))

    def test_cached_subtitle_is_success_and_generates_transcript(self):
        folder = self.root / "BVexample"
        folder.mkdir()
        (folder / "BVexample.zh-Hans.srt").write_text("1\n00:00:01,000 --> 00:00:02,000\n学习内容\n", encoding="utf-8")
        (folder / "BVexample.info.json").write_text('{"title":"metadata"}')
        fake = subprocess.CompletedProcess([], 0, json.dumps({"id": "BVexample", "title": "课程"}), "")
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch.subprocess, "run", return_value=fake), \
                patch.object(sys, "argv", ["fetch", "https://www.bilibili.com/video/BVexample", "--output", str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(), 0)
        self.assertIn("学习内容", (folder / "transcript.txt").read_text())
        self.assertEqual(json.loads((folder / "manifest.json").read_text())["status"], "transcript-ready")

    def test_configured_notes_directory_is_used_without_output_override(self):
        notes = self.root / "configured-notes"
        user_config.set_notes_dir(notes)
        folder = notes / "BVexample"
        folder.mkdir(parents=True)
        (folder / "BVexample.zh-Hans.srt").write_text(
            "1\n00:00:01,000 --> 00:00:02,000\n配置目录内容\n", encoding="utf-8"
        )
        (folder / "BVexample.info.json").write_text('{"title":"metadata"}')
        fake = subprocess.CompletedProcess([], 0, json.dumps({"id": "BVexample", "title": "课程"}), "")
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch.subprocess, "run", return_value=fake), \
                patch.object(sys, "argv", ["fetch", "https://www.bilibili.com/video/BVexample"]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(), 0)
        self.assertIn("配置目录内容", (folder / "transcript.txt").read_text())

    def test_downloader_failure_does_not_report_cached_success(self):
        fake = subprocess.CompletedProcess([], 1, '{"id":"BVexample"}', "access denied")
        with patch.object(fetch, "yt_dlp_command", return_value="/fake/yt-dlp"), \
                patch.object(fetch.subprocess, "run", return_value=fake), \
                patch.object(sys, "argv", ["fetch", "https://www.bilibili.com/video/BVexample", "--output", str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertNotEqual(fetch.main(), 0)


if __name__ == "__main__":
    unittest.main()
