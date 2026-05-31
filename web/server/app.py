from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from web.server import compiler

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = (REPO_ROOT / "examples").resolve()

app = FastAPI(title="LILA Web Playground")


class SourceReq(BaseModel):
    source: str


class RunReq(BaseModel):
    source: str
    stdin: str = ""


@app.post("/api/highlight")
def highlight_endpoint(req: SourceReq) -> dict:
    return {"spans": compiler.highlight(req.source)}


@app.post("/api/compile")
def compile_endpoint(req: SourceReq) -> dict:
    return compiler.compile_stages(req.source)


@app.post("/api/run")
def run_endpoint(req: RunReq) -> dict:
    return compiler.run_program(req.source, req.stdin)


@app.get("/api/examples")
def list_examples() -> list[dict]:
    items = []
    for path in sorted(EXAMPLES_DIR.rglob("*.lila")):
        rel = path.relative_to(EXAMPLES_DIR)
        category = rel.parts[0] if len(rel.parts) > 1 else ""
        items.append(
            {"id": rel.with_suffix("").as_posix(), "category": category, "name": path.stem}
        )
    return items


@app.get("/api/examples/{example_id:path}")
def get_example(example_id: str) -> dict:
    target = (EXAMPLES_DIR / f"{example_id}.lila").resolve()
    if not target.is_relative_to(EXAMPLES_DIR) or not target.is_file():
        raise HTTPException(status_code=404, detail="example not found")
    return {"source": target.read_text()}


_DIST = REPO_ROOT / "web" / "client" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="client")


def main() -> None:
    import uvicorn

    uvicorn.run("web.server.app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
