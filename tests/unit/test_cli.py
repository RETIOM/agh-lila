import shutil
import subprocess
import sys
from pathlib import Path

import pytest

lli_available = pytest.mark.skipif(
    shutil.which("lli") is None, reason="lli not on PATH"
)
clang_available = pytest.mark.skipif(
    shutil.which("clang") is None, reason="clang not on PATH"
)


def run_cli(*args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "lila.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_cli_emits_tokens(tmp_path: Path):
    src = tmp_path / "p.lila"
    src.write_text("fn main() -> int { return 0; }")
    r = run_cli(
        str(src),
        "--tokens",
        "-o",
        "-",
        cwd=str(Path(__file__).resolve().parent.parent.parent),
    )
    assert r.returncode == 0
    assert "FN" in r.stdout and "TYPE_INT" in r.stdout


def test_cli_emits_ast(tmp_path: Path):
    src = tmp_path / "p.lila"
    src.write_text("fn main() -> int { return 7; }")
    r = run_cli(
        str(src),
        "--ast",
        "-o",
        "-",
        cwd=str(Path(__file__).resolve().parent.parent.parent),
    )
    assert r.returncode == 0
    assert "Program" in r.stdout
    assert "FnDecl" in r.stdout


def test_cli_emits_ir(tmp_path: Path):
    src = tmp_path / "p.lila"
    src.write_text("fn main() -> int { return 0; }")
    out = tmp_path / "p.ll"
    r = run_cli(
        str(src),
        "--ir",
        "-o",
        str(out),
        cwd=str(Path(__file__).resolve().parent.parent.parent),
    )
    assert r.returncode == 0
    text = out.read_text()
    assert "define i32 @main" in text


@lli_available
def test_cli_run_executes_program(tmp_path: Path):
    src = tmp_path / "p.lila"
    src.write_text('fn main() -> int { println("hi"); return 0; }')
    r = run_cli(
        str(src), "--run", cwd=str(Path(__file__).resolve().parent.parent.parent)
    )
    assert r.returncode == 0
    assert r.stdout.strip() == "hi"


@clang_available
def test_cli_emit_exe_runs(tmp_path: Path):
    src = tmp_path / "p.lila"
    src.write_text("fn main() -> int { println(42); return 0; }")
    out = tmp_path / "p"
    r = run_cli(
        str(src),
        "--exe",
        "-o",
        str(out),
        cwd=str(Path(__file__).resolve().parent.parent.parent),
    )
    assert r.returncode == 0
    r2 = subprocess.run([str(out)], capture_output=True, text=True)
    assert r2.stdout.strip() == "42"


def test_cli_reports_syntax_error_with_location(tmp_path: Path):
    src = tmp_path / "bad.lila"
    src.write_text("fn main() -> int { return }")
    r = run_cli(str(src), cwd=str(Path(__file__).resolve().parent.parent.parent))
    assert r.returncode != 0
    assert "syntax error" in r.stderr.lower()
    assert "bad.lila" in r.stderr


def test_cli_reports_illegal_char(tmp_path: Path):
    src = tmp_path / "bad.lila"
    src.write_text("fn main() -> int {\n    @\n    return 0;\n}")
    r = run_cli(str(src), cwd=str(Path(__file__).resolve().parent.parent.parent))
    assert r.returncode != 0
    assert "illegal character" in r.stderr
    assert "'@'" in r.stderr
    assert "bad.lila" in r.stderr
