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
