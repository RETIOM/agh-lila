from dataclasses import dataclass


@dataclass
class CompileError(Exception):
    message: str
    lineno: int = 0
    col: int = 0
    path: str | None = None

    def __str__(self) -> str:
        return format_error(self)


def format_error(err: CompileError) -> str:
    path = err.path or "<input>"
    return f"{path}:{err.lineno}:{err.col}: error: {err.message}"
