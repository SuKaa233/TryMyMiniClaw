<available_skills>

<!-- Skill: get_bilibili_hot -->
name: get_bilibili_video_stats
description: 获取指定B站（Bilibili）视频的播放量、弹幕数、点赞数等热度信息
Bilibili Video Stats Skill
This skill allows you to fetch popularity statistics and engagement metrics for a specific Bilibili video.

Steps
Identify Video ID: Extract the video's BV number (Bvid) or AV number from the user's request or URL.

Fetch Video Data: Use the fetch_url tool to get video statistics from the official Bilibili web interface API.

URL format: https://api.bilibili.com/x/web-interface/view?bvid={bvid}

Example: https://api.bilibili.com/x/web-interface/view?bvid=BV1xx411c7mD

Parse Response: The response will be a JSON object. Navigate to the data.stat object to extract the necessary metrics (e.g., view for views, danmaku for danmakus, like for likes, coin for coins, favorite for favorites).

Return: Present the organized video statistics to the user in a clear format.

Example
User: "帮我查一下B站视频 BV1xx411c7mD 的热度数据。"
Agent:

Reads backend/skills/get_bilibili_video_stats/SKILL.md.

Calls fetch_url("https://api.bilibili.com/x/web-interface/view?bvid=BV1xx411c7mD").

Parses the JSON response to extract the metrics from data.stat.

Returns: "该视频的当前热度如下：播放量为...，点赞数为...，投币数为...，收藏数为..."


<!-- Skill: get_bilibili_ranking -->
# Skill: Get Bilibili Ranking
This skill allows the agent to fetch the current top popular videos from Bilibili using a specialized tool that bypasses anti-scraping measures.

## Capabilities
- Get top 10 popular videos across all categories.
- Get top 10 popular videos for specific categories: origin (原创), bangumi (番剧), cinema (影视), rookie (新人).

## Tools Used
- `get_bilibili_ranking`: The primary tool for this skill.

## Usage
When a user asks for "B站热度排行榜", "Bilibili popular videos", or similar requests, invoke the `get_bilibili_ranking` tool.

Example:
User: "What are the top 10 videos on Bilibili right now?"
Agent: Calls `get_bilibili_ranking(category="all")`

User: "Show me popular anime on Bilibili."
Agent: Calls `get_bilibili_ranking(category="bangumi")`



<!-- Skill: get_weather -->
---
name: get_weather
description: 获取指定城市的实时天气信息
---

# Weather Skill

This skill allows you to fetch weather information for a specific city.

## Steps

1.  **Identify City**: Extract the city name from the user's request.
2.  **Fetch Weather Data**: Use the `fetch_url` tool to get weather data from `wttr.in`.
    *   URL format: `https://wttr.in/{city}?format=3`
    *   Example: `https://wttr.in/Beijing?format=3`
3.  **Parse Response**: The response will be a simple string.
4.  **Return**: Present the weather information to the user.

## Example

User: "What's the weather in London?"
Agent:
1.  Reads `backend/skills/get_weather/SKILL.md`.
2.  Calls `fetch_url("https://wttr.in/London?format=3")`.
3.  Returns: "The weather in London is..."


<!-- Skill: play_bilibili_video -->
name: play_bilibili_video
description: 在Bilibili上搜索并播放指定的视频，支持通过关键词搜索或直接通过BV号播放。
Skill: Play Bilibili Video
This skill allows the agent to search for and play specific videos on Bilibili, prioritizing MCP tools to control the user's existing browser.

Capabilities
- Search and play videos by keyword.
- Play videos directly by BV ID.
- Prioritize MCP tools (mcp_new_tab, etc.) over built-in browser tools.

Tools Used
- mcp_new_tab / mcp_switch_tab / mcp_type / mcp_click (Preferred)
- browser_open / browser_type / browser_click (Fallback)

Usage
When the user asks to "play video", "watch video", "open Bilibili video", use this skill.

Example
User: "播放关于 Python 的视频"
Agent:
1. Reads backend/skills/play_bilibili_video/SKILL.md.
2. Checks MCP availability (if tool available) or tries MCP tools first.
3. If MCP available, calls mcp_new_tab("https://search.bilibili.com/all?keyword=Python").
4. If MCP unavailable, calls browser_open("https://search.bilibili.com/all?keyword=Python").

</available_skills>
