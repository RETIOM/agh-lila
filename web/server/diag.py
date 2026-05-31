from __future__ import annotations

from lila.diagnostics import CompileError


def make(stage: str, message: str, line: int = 0, col: int = 0) -> dict:
    return {
        "stage": stage,
        "line": line,
        "col": col,
        "message": message,
        "severity": "error",
    }


def from_compile_error(stage: str, err: CompileError) -> dict:
    return make(stage, err.message, line=err.lineno, col=err.col)


def from_syntax_error(err: SyntaxError) -> dict:
    line = getattr(err, "lineno", 0) or 0
    col = getattr(err, "col", 0) or 0
    message = err.args[0] if err.args else "syntax error"
    return make("parser", message, line=line, col=col)
