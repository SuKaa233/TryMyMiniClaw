# Mini-OpenClaw

Mini-OpenClaw 是一个轻量级、本地优先的 AI Agent 系统，基于 Python (FastAPI + LangChain) 和 Next.js 构建。

## 前置要求

- Python 3.10+
- Node.js 18+
- OpenAI API Key (或兼容的 API Key)

## 快速开始 (推荐)

项目包含一个启动脚本，可以一键启动后端和前端服务。

1.  **安装依赖**:
    首次运行前，请确保已安装后端和前端的依赖：
    ```bash
    # 后端
    pip install -r backend/requirements.txt
    playwright install  # 安装浏览器驱动

    # 前端
    cd frontend
    npm install
    cd ..
    ```

2.  **配置环境变量**:
    在项目根目录创建一个 `.env` 文件，并添加你的 API Key：
    ```env
    OPENAI_API_KEY=sk-your-key-here
    ```

3.  **启动服务**:
    在根目录下运行：
    ```bash
    python start_services.py
    ```
    脚本会自动清理占用端口，启动后端 (8002) 和前端 (3000)，并自动打开浏览器访问 `http://localhost:3000`。

## 手动部署与启动

如果你更喜欢手动控制每个服务，或者在服务器上部署，请参考以下步骤。

### 后端 (Backend)

1.  进入项目根目录。
2.  创建虚拟环境 (可选但推荐):
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```
3.  安装依赖:
    ```bash
    pip install -r backend/requirements.txt
    playwright install
    ```
4.  确保 `.env` 文件已配置 `OPENAI_API_KEY`。
5.  启动后端服务:
    ```bash
    # 开发模式 (热重载)
    uvicorn backend.app:app --reload --port 8002

    # 生产模式
    uvicorn backend.app:app --host 0.0.0.0 --port 8002
    ```
    API 地址: `http://localhost:8002`

### 前端 (Frontend)

1.  进入 `frontend` 目录:
    ```bash
    cd frontend
    ```
2.  安装依赖:
    ```bash
    npm install
    ```
3.  启动开发服务器:
    ```bash
    npm run dev
    ```
    访问地址: `http://localhost:3000`

### 生产环境构建 (Production Build)

如果你需要部署到生产环境，建议构建前端静态资源。

1.  在 `frontend` 目录下运行构建命令:
    ```bash
    npm run build
    ```
2.  启动生产服务器:
    ```bash
    npm start
    ```
    或者使用 PM2 等进程管理工具来运行 Next.js 服务。

## 功能特性

- **文件优先记忆**: 所有的记忆和技能都作为 Markdown 文件存储在 `backend/workspace` 和 `backend/skills` 中。
- **技能系统**: 通过在 `backend/skills` 中创建文件夹和 `SKILL.md` 文件来添加新技能。
- **透明代理**: 实时查看 Agent 的思考过程和工具使用情况。
- **本地执行**: 所有代码都在你的机器上运行，数据安全可控。
- **MCP 支持**: 支持通过 Model Context Protocol 连接外部工具。

## 目录结构

- `backend/`: Python 后端代码。
    - `app.py`: FastAPI 应用程序入口。
    - `graph/`: LangGraph Agent 定义。
    - `tools/`: 核心工具 (Terminal, Python, Fetch, Browser 等)。
    - `workspace/`: 系统提示词和配置。
    - `skills/`: Agent 技能定义。
- `frontend/`: Next.js 前端代码。
    - `src/app/page.tsx`: 主应用 UI。
    - `src/lib/api.ts`: API 客户端。
- `start_services.py`: 一键启动脚本。
