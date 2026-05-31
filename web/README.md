# LILA Web Playground

Local web app demoing the LILA compiler: real-lexer syntax highlighting,
tokens/AST/LLVM IR views, and run via `lli`.

## Requirements
- Python 3.14 + `uv`, with the compiler installed (`uv sync --extra web`)
- Node.js 18+ (for the frontend)
- LLVM `lli` on PATH (only needed for Run)

## Develop (two terminals)
Backend:
    uv run uvicorn web.server.app:app --reload --port 8000
Frontend (proxies /api to the backend):
    cd web/client && npm install && npm run dev
Open the URL Vite prints (default http://localhost:5173).

## Demo (single process)
    cd web/client && npm run build
    uv run python -m web.server.app
Open http://localhost:8000.
