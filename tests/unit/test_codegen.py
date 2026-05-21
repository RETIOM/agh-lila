import subprocess
from lila.syntax.scanner import LILALexer
from lila.syntax.parser import build_parser
from lila.sema.semantic import analyze
from lila.codegen.module import emit_ir


def compile_to_ir(source: str) -> str:
    lx = LILALexer(); lx.build()
    parser = build_parser()
    ast = parser.parse(source, lexer=lx.lexer)
    program, _ = analyze(ast)
    return emit_ir(program)


def assert_valid_ir(ir: str) -> None:
    result = subprocess.run(
        ["llc", "-filetype=null", "-"],
        input=ir, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"llc rejected IR:\n{result.stderr}\n---\n{ir}"


def test_empty_main_returning_zero():
    ir = compile_to_ir("fn main() -> int { return 0; }")
    assert "define i32 @main" in ir
    assert "ret i32 0" in ir
    assert_valid_ir(ir)


def test_main_returning_literal_i64():
    ir = compile_to_ir("fn main() -> long { return 7; }")
    assert "ret i64 7" in ir
    assert_valid_ir(ir)


def test_module_preamble_declares_printf_and_scanf():
    ir = compile_to_ir("fn main() -> int { return 0; }")
    assert "declare i32 @printf" in ir
    assert "declare i32 @scanf" in ir


def test_arith_signed_div_emitted():
    ir = compile_to_ir("fn main() -> int { return 10 / 3; }")
    assert "sdiv i32" in ir
    assert_valid_ir(ir)


def test_arith_unsigned_div_emitted():
    ir = compile_to_ir("fn main() -> uint { uint a = 10; uint b = 3; return a / b; }")
    assert "udiv i32" in ir
    assert_valid_ir(ir)


def test_float_add():
    ir = compile_to_ir("fn main() -> double { return 1.5 + 2.5; }")
    assert "fadd double" in ir
    assert_valid_ir(ir)


def test_relational_signed_vs_unsigned():
    ir_signed = compile_to_ir("fn main() -> bool { int a = 1; return a < 2; }")
    assert "icmp slt" in ir_signed
    ir_unsigned = compile_to_ir("fn main() -> bool { uint a = 1; return a < 2; }")
    assert "icmp ult" in ir_unsigned


def test_short_circuit_logical_and():
    ir = compile_to_ir("fn main() -> bool { return true && false; }")
    assert "br i1" in ir
    assert_valid_ir(ir)


def test_array_index_load():
    ir = compile_to_ir(
        "fn main() -> int { int xs[3]; xs[0] = 7; return xs[0]; }"
    )
    assert "getelementptr inbounds" in ir
    assert "[3 x i32]" in ir
    assert_valid_ir(ir)


def test_if_else_emits_branches():
    ir = compile_to_ir(
        "fn main() -> int { if true { return 1; } else { return 0; } }"
    )
    assert "br i1" in ir
    assert "ret i32 1" in ir and "ret i32 0" in ir
    assert_valid_ir(ir)


def test_while_loop_executes_in_lli():
    ir = compile_to_ir(
        "fn main() -> int { int i = 0; while i < 3 { i = i + 1; } return i; }"
    )
    assert_valid_ir(ir)
    result = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert result.returncode == 3, f"exit={result.returncode} stderr={result.stderr}"


def test_for_in_range_sums_to_45():
    ir = compile_to_ir(
        "fn main() -> int { int s = 0; for int i in 0..10 { s = s + i; } return s; }"
    )
    assert_valid_ir(ir)
    result = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert result.returncode == 45


def test_do_while_runs_at_least_once():
    ir = compile_to_ir(
        "fn main() -> int { int i = 5; do { i = i - 1; } while i > 0; return i; }"
    )
    assert_valid_ir(ir)
    result = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert result.returncode == 0


def test_break_exits_loop():
    ir = compile_to_ir(
        "fn main() -> int { int i = 0; while true { if i >= 5 { break; } i = i + 1; } return i; }"
    )
    assert_valid_ir(ir)
    r = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert r.returncode == 5


def test_continue_skips_iteration():
    # Sum even numbers 0+2+4+6+8 = 20
    ir = compile_to_ir(
        "fn main() -> int {\n"
        "  int s = 0;\n"
        "  for int i in 0..10 {\n"
        "    if i % 2 != 0 { continue; }\n"
        "    s = s + i;\n"
        "  }\n"
        "  return s;\n"
        "}\n"
    )
    assert_valid_ir(ir)
    r = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert r.returncode == 20


def test_println_int_outputs_value():
    ir = compile_to_ir("fn main() -> int { println(42); return 0; }")
    assert "@printf" in ir
    r = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert r.returncode == 0
    assert r.stdout.strip() == "42"


def test_println_string():
    ir = compile_to_ir('fn main() -> int { println("hello"); return 0; }')
    r = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert r.stdout.strip() == "hello"


def test_read_i32_then_println():
    import tempfile, os
    ir = compile_to_ir(
        "fn main() -> int { int x = read_i32(); println(x); return 0; }"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".ll", delete=False) as f:
        f.write(ir)
        path = f.name
    try:
        r = subprocess.run(["lli", path], input="7\n", capture_output=True, text=True)
        assert r.stdout.strip() == "7"
    finally:
        os.unlink(path)


def test_print_char():
    ir = compile_to_ir("fn main() -> int { print('A'); println(\"\"); return 0; }")
    r = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert r.stdout.startswith("A")


def test_print_f64():
    ir = compile_to_ir("fn main() -> int { println(3.5); return 0; }")
    r = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert r.stdout.strip() == "3.5"


def test_compound_assignment_operators():
    src = (
        "fn main() -> int {\n"
        "  int x = 10;\n"
        "  x += 3;\n"
        "  x -= 1;\n"
        "  x *= 4;\n"
        "  x /= 3;\n"
        "  x %= 5;\n"
        "  return x;\n"
        "}\n"
    )
    # 10+3=13, 13-1=12, 12*4=48, 48/3=16, 16%5=1
    ir = compile_to_ir(src)
    assert_valid_ir(ir)
    r = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert r.returncode == 1


def test_recursive_array_sum():
    ir = compile_to_ir(
        "fn sum(int xs[5], int i, int n) -> int {\n"
        "  if i >= n { return 0; }\n"
        "  return xs[i] + sum(xs, i + 1, n);\n"
        "}\n"
        "fn main() -> int {\n"
        "  int xs[5];\n"
        "  xs[0] = 1; xs[1] = 2; xs[2] = 3; xs[3] = 4; xs[4] = 5;\n"
        "  return sum(xs, 0, 5);\n"
        "}\n"
    )
    assert_valid_ir(ir)
    r = subprocess.run(["lli", "-"], input=ir, capture_output=True, text=True)
    assert r.returncode == 15
