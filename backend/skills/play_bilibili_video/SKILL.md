# Skill: Play Bilibili Video
name: play_bilibili_video
description: 在Bilibili上搜索并播放指定的视频，支持通过关键词搜索或直接通过BV号播放。

## Capabilities
- 通过关键词搜索并播放最相关的视频。
- 通过BV号直接播放视频。
- 优先尝试使用 MCP 控制用户的现有浏览器。
- 如果 MCP 不可用，使用内置浏览器打开。

## Tools Used
- `mcp_new_tab` / `mcp_switch_tab` / `mcp_type` / `mcp_click` (Preferred)
- `browser_open`
- `browser_type`
- `browser_click`
- `browser_smart_click`

## Usage
当用户要求“播放视频”、“看视频”、“打开B站视频”时使用此技能。

### Scenario 1: Play by BV ID
User: "播放视频 BV1xx411c7mD"
Agent:
1.  Check if MCP tools are available.
2.  If MCP available:
    -   `mcp_new_tab(url="https://www.bilibili.com/video/BV1xx411c7mD")`
3.  If MCP not available:
    -   `browser_open(url="https://www.bilibili.com/video/BV1xx411c7mD")`

### Scenario 2: Play by Keyword
User: "我想看关于 Python 教程的视频"
Agent:
1.  Check if MCP tools are available.
2.  If MCP available:
    -   `mcp_new_tab(url="https://search.bilibili.com/all?keyword=Python教程")`
    -   Wait for load.
    -   `mcp_click(selector=".video-list .bili-video-card__info--right a")` (Click first result)
3.  If MCP not available:
    -   `browser_open(url="https://search.bilibili.com/all?keyword=Python教程")`
    -   `browser_smart_click(description="视频标题或封面")` (Try to click the first video)

## Notes
- Bilibili search URL pattern: `https://search.bilibili.com/all?keyword={keyword}`
- Direct video URL pattern: `https://www.bilibili.com/video/{bvid}`
- Always prefer MCP tools to respect user's "control my browser" preference.
- If using built-in browser (`browser_open`), ensure the window is visible.
