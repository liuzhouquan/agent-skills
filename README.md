# Agent Skills

公开维护的 Codex skills，当前包含视频字幕提取、中文笔记整理和 Telegram 推送工具。

## Skills

### `bilibili-video-digest`

处理 B 站视频链接：获取字幕和元数据，生成带时间戳的中文笔记，并按要求发送到 Telegram。支持显式提供 Netscape 格式 Cookie，以及 `1-3,7-9` 形式的多分集批量处理。

### `youtube-video-digest`

处理 YouTube 视频链接：获取人工或自动字幕，优先选择中文字幕，生成带时间戳的中文笔记，并按要求发送到 Telegram。支持登录 Cookie 和单视频模式。

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

B 站的笔记目录和 Cookie 目录保存在本机私有配置中，不受 skill 安装位置影响：

```bash
python3 ~/.agents/skills/bilibili-video-digest/scripts/configure_cookies.py --init
python3 ~/.agents/skills/bilibili-video-digest/scripts/configure_cookies.py --set-notes-dir "/absolute/path/to/bilibili-notes"
python3 ~/.agents/skills/bilibili-video-digest/scripts/configure_cookies.py --add-dir "/absolute/path/to/cookies"
```

配置文件默认是 `~/.config/bilibili-video-digest/config.json`，不会提交到 GitHub。首次运行时如果文件不存在，skill 会自动生成不含隐私信息的模板。

## 本地验证

每个 skill 都包含结构校验所需的 `SKILL.md`，以及不访问真实视频或 Telegram 的离线测试。
