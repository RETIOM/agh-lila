from lila.diagnostics import CompileError
from web.server import diag
from web.server import compiler


def test_tokenize_offsets_and_fields():
    toks, errors = compiler._tokenize("int x = 42;")
    assert errors == []
    got = [(t.type, t.value, t.start, t.end, t.line, t.col) for t in toks]
    assert got == [
        ("TYPE_INT", "int", 0, 3, 1, 1),
        ("ID", "x", 4, 5, 1, 5),
        ("ASSIGN", "=", 6, 7, 1, 7),
        ("INTEGER_LITERAL", "42", 8, 10, 1, 9),
        ("SEMI", ";", 10, 11, 1, 11),
    ]


def test_tokenize_collects_illegal_char():
    toks, errors = compiler._tokenize("int @ x")
    types = [t.type for t in toks]
    assert "TYPE_INT" in types and "ID" in types
    assert len(errors) == 1
    assert "illegal character" in errors[0].message


def test_from_compile_error():
    err = CompileError("boom", lineno=4, col=2)
    assert diag.from_compile_error("semantic", err) == {
        "stage": "semantic", "line": 4, "col": 2,
        "message": "boom", "severity": "error",
    }


def test_from_syntax_error():
    err = SyntaxError("syntax error at '}'")
    err.lineno = 3
    err.col = 5
    assert diag.from_syntax_error(err) == {
        "stage": "parser", "line": 3, "col": 5,
        "message": "syntax error at '}'", "severity": "error",
    }


def test_generic_builder():
    assert diag.make("codegen", "oops", line=1, col=1) == {
        "stage": "codegen", "line": 1, "col": 1,
        "message": "oops", "severity": "error",
    }


def _spans(source):
    return compiler.highlight(source)


def test_highlight_basic_token_spans():
    spans = _spans("int x;")
    assert {"start": 0, "end": 3, "type": "TYPE_INT"} in spans
    assert {"start": 4, "end": 5, "type": "ID"} in spans
    # spans are sorted by start
    starts = [s["start"] for s in spans]
    assert starts == sorted(starts)


def test_highlight_includes_comment_span():
    spans = _spans("int x;\n// hi\nint y;")
    assert {"start": 7, "end": 12, "type": "COMMENT"} in spans


def test_highlight_ignores_comment_markers_inside_strings():
    # the // lives inside a string literal, so it must NOT become a comment span
    spans = _spans('println("a//b");')
    assert all(s["type"] != "COMMENT" for s in spans)


def test_highlight_maps_utf16_offsets():
    # 😀 is U+1F600 — one code point but two UTF-16 units
    spans = _spans("// 😀\nint x;")
    comment = next(s for s in spans if s["type"] == "COMMENT")
    assert comment == {"start": 0, "end": 5, "type": "COMMENT"}
    int_tok = next(s for s in spans if s["type"] == "TYPE_INT")
    assert int_tok == {"start": 6, "end": 9, "type": "TYPE_INT"}


from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _example(rel: str) -> str:
    return (ROOT / "examples" / rel).read_text()


def test_compile_valid_program():
    out = compiler.compile_stages("fn main() -> int { return 0; }")
    assert out["diagnostics"] == []
    assert "define i32 @main" in out["ir"]
    assert "Program" in out["ast"] and "FnDecl" in out["ast"]
    assert any(t["type"] == "FN" for t in out["tokens"])


def test_compile_reports_lexer_error():
    out = compiler.compile_stages(_example("errs/illegal_char.lila"))
    assert any(d["stage"] == "lexer" for d in out["diagnostics"])
    assert any("illegal character" in d["message"] for d in out["diagnostics"])


def test_compile_reports_parser_error():
    out = compiler.compile_stages(_example("errs/syntax_err.lila"))
    assert any(d["stage"] == "parser" for d in out["diagnostics"])
    assert out["ir"] is None


def test_compile_reports_semantic_error():
    out = compiler.compile_stages(_example("errs/compile_err.lila"))
    assert any(d["stage"] == "semantic" for d in out["diagnostics"])
    assert any("break" in d["message"] for d in out["diagnostics"])
    # AST still available even though semantics failed
    assert out["ast"] is not None


import shutil
import pytest

lli_available = pytest.mark.skipif(shutil.which("lli") is None, reason="lli not on PATH")


def test_run_returns_diagnostics_on_compile_error():
    out = compiler.run_program("fn main() -> int { break; }", "")
    assert out["diagnostics"]
    assert out["exit_code"] is None
    assert out["timed_out"] is False


@lli_available
def test_run_executes_and_captures_stdout():
    out = compiler.run_program('fn main() -> int { println("hi"); return 0; }', "")
    assert out["exit_code"] == 0
    assert out["stdout"] == "hi\n"
    assert out["timed_out"] is False
    assert out["diagnostics"] == []


@lli_available
def test_run_pipes_stdin():
    src = "fn main() -> int { int x = read_i32(); println(x); return 0; }"
    out = compiler.run_program(src, "7\n")
    assert out["stdout"] == "7\n"


@lli_available
def test_run_times_out_on_infinite_loop():
    src = "fn main() -> int { while true { } return 0; }"
    out = compiler.run_program(src, "", timeout=2)
    assert out["timed_out"] is True
    assert out["exit_code"] is None
