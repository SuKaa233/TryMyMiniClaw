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
