# Agent Skills

公开维护的 Codex skills，当前包含视频字幕提取、中文笔记整理和 Telegram 推送工具。

## Skills

### `bilibili-video-digest`

处理 B 站视频链接：获取字幕和元数据，生成带时间戳的中文笔记，并按要求发送到 Telegram。支持显式提供 Netscape 格式 Cookie 或登记 Cookie 目录、`1-3,7-9` 形式的多分集批量处理，以及按登录态区分的失败原因与退出码。

### `youtube-video-digest`

处理 YouTube 视频链接：获取人工或自动字幕，优先选择中文字幕，生成带时间戳的中文笔记，并按要求发送到 Telegram。支持登录 Cookie 或登记 Cookie 目录、单视频模式，以及按失败原因区分的退出码。

两个 skill 都不会把 Cookie、Bot token、Telegram 配置或视频下载产物放进仓库。

## 安装到 Codex

```bash
git clone https://github.com/liuzhouquan/agent-skills.git
cp -a agent-skills/bilibili-video-digest ~/.codex/skills/
cp -a agent-skills/youtube-video-digest ~/.codex/skills/
```

使用时直接告诉 Codex：

```text
使用 youtube-video-digest 总结这个视频并发到 Telegram：<YouTube URL>
```

Telegram 配置默认读取 `~/.config/bilibili-video-digest/telegram.env`，两个 skill 可以共用同一个 Bot 和目标聊天。

两个 skill 的笔记目录和 Cookie 目录都保存在本机私有配置中，不受 skill 安装位置影响：

```bash
# B 站
python3 ~/.agents/skills/bilibili-video-digest/scripts/configure_cookies.py --init
python3 ~/.agents/skills/bilibili-video-digest/scripts/configure_cookies.py --set-notes-dir "/absolute/path/to/bilibili-notes"
python3 ~/.agents/skills/bilibili-video-digest/scripts/configure_cookies.py --add-dir "/absolute/path/to/cookies"
python3 ~/.agents/skills/bilibili-video-digest/scripts/configure_cookies.py --check

# YouTube
python3 ~/.agents/skills/youtube-video-digest/scripts/configure_cookies.py --init
python3 ~/.agents/skills/youtube-video-digest/scripts/configure_cookies.py --set-notes-dir "/absolute/path/to/youtube-notes"
python3 ~/.agents/skills/youtube-video-digest/scripts/configure_cookies.py --add-dir "/absolute/path/to/youtube-cookies"
python3 ~/.agents/skills/youtube-video-digest/scripts/configure_cookies.py --list
```

配置文件默认是 `~/.config/bilibili-video-digest/config.json` 与 `~/.config/youtube-video-digest/config.json`（可用 `BILIBILI_DIGEST_CONFIG` / `YOUTUBE_DIGEST_CONFIG` 覆盖），不会提交到 GitHub。首次运行时如果文件不存在，skill 会自动生成不含隐私信息的模板，并在发现其它同名笔记目录时提示改用哪一个。

Cookie 目录与笔记目录也能用环境变量临时覆盖：`BILIBILI_COOKIE_DIRS` / `YOUTUBE_COOKIE_DIRS`（用 `os.pathsep` 分隔）、`BILIBILI_NOTES_DIR` / `YOUTUBE_NOTES_DIR`。`--check`（仅 B 站，YouTube 没有离线登录态接口）会用登录态接口验证 Cookie 是否仍有效，避免把失效 Cookie 误判成「视频没有字幕」。

## 本地验证

每个 skill 都包含结构校验所需的 `SKILL.md`，以及不访问真实视频或 Telegram 的离线测试。
