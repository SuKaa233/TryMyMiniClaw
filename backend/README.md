# Mini-OpenClaw Backend

这是 Mini-OpenClaw 的后端部分，基于 Python FastAPI 和 LangChain 构建。

## 前置要求

- Python 3.10+
- OpenAI API Key

## 快速开始

1. 创建虚拟环境 (推荐):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
2. 安装依赖:
   ```bash
   pip install -r requirements.txt
   playwright install  # 安装浏览器驱动
   ```
3. 配置环境变量:
   确保项目根目录有 `.env` 文件，并包含 `OPENAI_API_KEY`。
4. 启动服务:
   ```bash
   uvicorn app:app --reload --port 8002
   ```
   或者运行：
   ```bash
   python app.py
   ```
   API 将运行在 `http://localhost:8002`。

## 目录说明

- `app.py`: FastAPI 应用入口
- `graph/`: Agent 逻辑定义 (LangGraph)
- `tools/`: 自定义工具集
- `skills/`: Agent 技能文件 (Markdown)
- `workspace/`: 系统提示词与配置 (SOUL, IDENTITY, etc.)
- `memory/`: 记忆存储

