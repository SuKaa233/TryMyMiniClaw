# AGENTS PROTOCOL

## Meta-Instructions

1.  **Skill Loading**: You do not have pre-loaded functions for skills. You have a list of available skills in `SKILLS_SNAPSHOT.md`.
2.  **Skill Execution**: To use a skill, you MUST first read its definition file using `read_file`. Then follow the instructions in that file.
3.  **Memory Management**:
    *   You can read your long-term memory from `backend/memory/MEMORY.md`.
    *   You can update your memory by rewriting the file, but be careful not to lose important information. Append new information when possible.
4.  **Tool Usage**:
    *   Use `terminal` for system commands (sandboxed).
    *   Use `python_repl` for calculations and data processing.
    *   Use `fetch_url` for web access.
    *   Use `read_file` for reading skills and memory.
    *   Use `search_knowledge_base` for retrieving information from your knowledge base.

## Safety
- Do not execute dangerous commands (e.g., `rm -rf`).
- Do not access files outside the project root.
