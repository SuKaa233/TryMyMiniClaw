# Mini-OpenClaw

Mini-OpenClaw is a lightweight, local-first AI Agent system built with Python (FastAPI + LangChain) and Next.js.

## Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API Key (or compatible)

## Setup

### Backend

1.  Navigate to the project root.
2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r backend/requirements.txt
    ```
4.  Create a `.env` file in the root directory and add your API key:
    ```env
    OPENAI_API_KEY=sk-your-key-here
    ```
5.  Start the backend server:
    ```bash
    uvicorn backend.app:app --reload --port 8002
    ```
    The API will be available at `http://localhost:8002`.

### Frontend

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:3000`.

## Features

- **File-First Memory**: All memories and skills are stored as Markdown files in `backend/workspace` and `backend/skills`.
- **Skills System**: Add new skills by creating folders in `backend/skills` with a `SKILL.md` file.
- **Transparent Agent**: See the agent's thought process and tool usage.
- **Local Execution**: Run everything on your machine.

## Directory Structure

- `backend/`: Python backend code.
    - `app.py`: FastAPI application.
    - `graph/`: LangGraph agent definition.
    - `tools/`: Core tools (Terminal, Python, Fetch, etc.).
    - `workspace/`: System prompts and configuration.
    - `skills/`: Agent skills.
- `frontend/`: Next.js frontend code.
    - `src/app/page.tsx`: Main application UI.
    - `src/lib/api.ts`: API client.
