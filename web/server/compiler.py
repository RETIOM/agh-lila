from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass

from lila.syntax.scanner import LILALexer
from lila.syntax.parser import build_parser
from lila.sema.semantic import analyze
from lila.codegen.module import emit_ir
from lila.cli import _format_ast
from lila.diagnostics import CompileError

from web.server import diag


@dataclass
class Tok:
    type: str
    value: str
    start: int
    end: int
    line: int
    col: int


def _tokenize(source: str) -> tuple[list[Tok], list[CompileError]]:
    lx = LILALexer()
    lx.build()
    lx.lexer.input(source)
    toks: list[Tok] = []
    while True:
        t = lx.lexer.token()
        if t is None:
            break
        start = t.lexpos
        end = lx.lexer.lexpos  # PLY advances lexpos to just past the matched text
        col = start - source.rfind("\n", 0, start)
        toks.append(Tok(t.type, str(t.value), start, end, t.lineno, col))
    return toks, lx.errors


def _comment_spans(source: str, token_spans: list[tuple[int, int]]) -> list[tuple[int, int, str]]:
    """Any non-whitespace in the gaps between tokens must be a comment:
    the lexer only ever skips whitespace and comments."""
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for ts, te in token_spans + [(len(source), len(source))]:
        gap = source[cursor:ts]
        if gap.strip():
            left = cursor + (len(gap) - len(gap.lstrip()))
            right = ts - (len(gap) - len(gap.rstrip()))
            spans.append((left, right, "COMMENT"))
        cursor = max(cursor, te)
    return spans


def _utf16_offsets(source: str) -> list[int]:
    """Map each code-point index (0..len) to its UTF-16 code-unit index."""
    offsets = [0] * (len(source) + 1)
    u = 0
    for i, ch in enumerate(source):
        offsets[i] = u
        u += 2 if ord(ch) > 0xFFFF else 1
    offsets[len(source)] = u
    return offsets


def highlight(source: str) -> list[dict]:
    toks, _errors = _tokenize(source)
    token_spans = [(t.start, t.end) for t in toks]
    raw: list[tuple[int, int, str]] = [(t.start, t.end, t.type) for t in toks]
    raw += _comment_spans(source, token_spans)
    raw.sort(key=lambda s: s[0])
    u16 = _utf16_offsets(source)
    return [
        {"start": u16[s], "end": u16[e], "type": ty}
        for (s, e, ty) in raw
        if s < e
    ]


def _tokens_payload(toks: list[Tok]) -> list[dict]:
    return [
        {"type": t.type, "value": t.value, "line": t.line, "col": t.col}
        for t in toks
    ]


def compile_stages(source: str) -> dict:
    diagnostics: list[dict] = []
    toks, lex_errors = _tokenize(source)
    tokens = _tokens_payload(toks)

    for err in lex_errors:
        diagnostics.append(diag.from_compile_error("lexer", err))
    if diagnostics:
        return {"tokens": tokens, "ast": None, "ir": None, "diagnostics": diagnostics}

    # parse (fresh lexer; the tokenizing one above is exhausted)
    lx = LILALexer()
    lx.build()
    parser = build_parser()
    try:
        ast = parser.parse(source, lexer=lx.lexer)
    except SyntaxError as e:
        diagnostics.append(diag.from_syntax_error(e))
        return {"tokens": tokens, "ast": None, "ir": None, "diagnostics": diagnostics}
    if lx.errors:
        diagnostics.append(diag.from_compile_error("lexer", lx.errors[0]))
        return {"tokens": tokens, "ast": None, "ir": None, "diagnostics": diagnostics}
    if ast is None:
        diagnostics.append(diag.make("parser", "empty program or parse failure", line=1, col=1))
        return {"tokens": tokens, "ast": None, "ir": None, "diagnostics": diagnostics}

    ast_str = _format_ast(ast, 0)  # capture parse tree before analyze() mutates it

    try:
        program, _ = analyze(ast)
    except CompileError as e:
        diagnostics.append(diag.from_compile_error("semantic", e))
        return {"tokens": tokens, "ast": ast_str, "ir": None, "diagnostics": diagnostics}

    try:
        ir = emit_ir(program)
    except Exception as e:  # codegen safety net
        diagnostics.append(diag.make("codegen", str(e)))
        return {"tokens": tokens, "ast": ast_str, "ir": None, "diagnostics": diagnostics}

    return {"tokens": tokens, "ast": ast_str, "ir": ir, "diagnostics": []}


def _decode_output(b) -> str:
    if b is None:
        return ""
    return b.decode(errors="replace") if isinstance(b, bytes) else b


def run_program(source: str, stdin: str = "", timeout: float = 5.0) -> dict:
    stages = compile_stages(source)
    if stages["diagnostics"]:
        return {
            "stdout": "", "stderr": "", "exit_code": None,
            "timed_out": False, "diagnostics": stages["diagnostics"],
        }

    with tempfile.NamedTemporaryFile("w", suffix=".ll", delete=False) as f:
        f.write(stages["ir"])
        path = f.name
    try:
        proc = subprocess.run(
            ["lli", path], input=stdin, capture_output=True, text=True, timeout=timeout
        )
        return {
            "stdout": proc.stdout, "stderr": proc.stderr,
            "exit_code": proc.returncode, "timed_out": False, "diagnostics": [],
        }
    except subprocess.TimeoutExpired as e:
        return {
            "stdout": _decode_output(e.stdout),
            "stderr": _decode_output(e.stderr),
            "exit_code": None, "timed_out": True, "diagnostics": [],
        }
    except FileNotFoundError:
        return {
            "stdout": "", "stderr": "lli not found on PATH", "exit_code": None,
            "timed_out": False,
            "diagnostics": [diag.make("runtime", "lli not found on PATH")],
        }
    finally:
        os.unlink(path)
