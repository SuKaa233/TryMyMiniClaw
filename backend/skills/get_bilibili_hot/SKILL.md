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