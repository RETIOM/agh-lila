from __future__ import annotations
import argparse
import os
import sys
import subprocess
import tempfile
from pathlib import Path

from lila.syntax.scanner import LILALexer
from lila.syntax.parser import build_parser
from lila.sema.semantic import analyze
from lila.codegen.module import emit_ir
from lila.diagnostics import CompileError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lila", description="LILA compiler")
    parser.add_argument("input", help="path to .lila source")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tokens", action="store_true", help="emit token stream")
    group.add_argument("--ast", action="store_true", help="emit AST")
    group.add_argument("--ir", action="store_true", help="emit LLVM IR (default)")
    group.add_argument("--obj", action="store_true", help="emit object file")
    group.add_argument("--exe", action="store_true", help="emit executable")
    parser.add_argument(
        "-o", "--output", default=None, help="output path; `-` for stdout"
    )
    parser.add_argument(
        "--run", action="store_true", help="JIT-run via lli instead of writing output"
    )
    parser.add_argument("--keep-temps", action="store_true")
    args = parser.parse_args(argv)

    src_path = Path(args.input)
    try:
        source = src_path.read_text()
    except OSError as e:
        print(f"lila: {e}", file=sys.stderr)
        return 2

    try:
        if args.tokens:
            return _emit_tokens(source, src_path, args.output)
        ast_node = _parse(source, src_path)
        if args.ast:
            return _emit_ast(ast_node, args.output, src_path)
        program, _ = analyze(ast_node)
        ir = emit_ir(program)
        if args.run:
            return _run(ir)
        if args.obj:
            return _emit_obj(ir, args.output, src_path)
        if args.exe:
            return _emit_exe(ir, args.output, src_path, args.keep_temps)
        return _write(ir, args.output, default_ext=".ll", src_path=src_path)
    except CompileError as e:
        if not e.path:
            e.path = str(src_path)
        print(str(e), file=sys.stderr)
        return 1
    except SyntaxError as e:
        lineno = getattr(e, 'lineno', 0) or 0
        col = getattr(e, 'col', 0) or 0
        print(f"{src_path}:{lineno}:{col}: error: {e.args[0]}", file=sys.stderr)
        return 1
    return 0


def _parse(source: str, src_path: Path):
    lx = LILALexer()
    lx.build()
    parser = build_parser()
    ast = parser.parse(source, lexer=lx.lexer)
    if ast is None:
        raise SyntaxError("empty program or parse failure")
    return ast


def _write(text: str, output: str | None, default_ext: str, src_path: Path) -> int:
    if output == "-":
        sys.stdout.write(text)
        return 0
    out = output or src_path.with_suffix(default_ext).name
    Path(out).write_text(text)
    return 0


def _emit_tokens(source: str, src_path: Path, output: str | None) -> int:
    lx = LILALexer()
    lx.build()
    lx.lexer.input(source)
    lines = []
    for tok in iter(lx.lexer.token, None):
        lines.append(f"{tok.type}\t{tok.value!r}\tline={tok.lineno}")
    return _write("\n".join(lines) + "\n", output, ".tok", src_path)


def _emit_ast(ast, output: str | None, src_path: Path) -> int:
    return _write(_format_ast(ast, 0), output, ".ast", src_path)


def _format_ast(node, indent: int) -> str:
    pad = "  " * indent
    if hasattr(node, "__dataclass_fields__"):
        cls = node.__class__.__name__
        out = [f"{pad}{cls}"]
        for f in node.__dataclass_fields__:
            v = getattr(node, f)
            if f in ("lineno", "col", "type"):
                continue
            out.append(f"{pad}  {f}:")
            out.append(_format_ast(v, indent + 2))
        return "\n".join(out)
    if isinstance(node, list):
        return "\n".join(_format_ast(x, indent) for x in node) if node else f"{pad}[]"
    return f"{pad}{node!r}"


def _emit_obj(ir: str, output: str | None, src_path: Path) -> int:
    out = output or src_path.with_suffix(".o").name
    r = subprocess.run(
        ["llc", "-filetype=obj", "-o", out, "-"],
        input=ir,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        return r.returncode
    return 0


def _emit_exe(ir: str, output: str | None, src_path: Path, keep: bool) -> int:
    out = output or src_path.with_suffix("").name
    with tempfile.NamedTemporaryFile("w", suffix=".ll", delete=not keep) as f:
        f.write(ir)
        f.flush()
        ll_path = f.name
        r = subprocess.run(
            ["clang", ll_path, "-o", out], capture_output=True, text=True
        )
        if r.returncode != 0:
            sys.stderr.write(r.stderr)
            return r.returncode
    return 0


def _run(ir: str) -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".ll", delete=False) as f:
        f.write(ir)
        f.flush()
        path = f.name
    try:
        r = subprocess.run(["lli", path])
        return r.returncode
    finally:
        os.unlink(path)


if __name__ == "__main__":
    sys.exit(main())
