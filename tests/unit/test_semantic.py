import pytest
from lila.syntax.scanner import LILALexer
from lila.syntax.parser import build_parser
from lila.sema.semantic import analyze, SymbolTable
from lila.diagnostics import CompileError
from lila.tree import types as T


def compile_to_typed_ast(source: str):
    lx = LILALexer()
    lx.build()
    parser = build_parser()
    ast = parser.parse(source, lexer=lx.lexer)
    return analyze(ast)


def test_signatures_collected():
    program, symtab = compile_to_typed_ast(
        "fn add(int a, int b) -> int { return a + b; }"
    )
    sym = symtab.lookup("add")
    assert sym.kind == "fn"
    assert sym.type.return_type == T.i32
    assert sym.type.param_types == [T.i32, T.i32]


def test_duplicate_function_rejected():
    src = "fn f() -> void { } fn f() -> void { }"
    with pytest.raises(CompileError, match="redeclared"):
        compile_to_typed_ast(src)


def test_global_var_signature():
    program, symtab = compile_to_typed_ast(
        "int G = 0; fn main() -> int { return G; }"
    )
    sym = symtab.lookup("G")
    assert sym.kind == "global"
    assert sym.type == T.i32


def test_simple_function_body_types_resolved():
    program, _ = compile_to_typed_ast(
        "fn add(int a, int b) -> int { return a + b; }"
    )
    fn = program.decls[0]
    ret = fn.body.stmts[0]      # Return
    assert ret.value.type == T.i32


def test_implicit_widening_int_to_long():
    program, _ = compile_to_typed_ast(
        "fn main() -> long { long r = 1; return r; }"
    )
    decl = program.decls[0].body.stmts[0]   # VarDecl
    # init expression is int literal; result type after semantic should be i64
    # via inserted Cast.
    assert decl.init.type == T.i64


def test_mixed_signed_unsigned_requires_cast():
    src = "fn main() -> int { int a = 1; uint b = 2; return a + b; }"
    with pytest.raises(CompileError, match="signed.*unsigned|cast"):
        compile_to_typed_ast(src)


def test_break_outside_loop_rejected():
    with pytest.raises(CompileError, match="break.*loop"):
        compile_to_typed_ast("fn main() -> void { break; }")


def test_continue_inside_while_ok():
    program, _ = compile_to_typed_ast(
        "fn main() -> void { while true { continue; } }"
    )
    body = program.decls[0].body.stmts[0].body.stmts
    assert body[0].__class__.__name__ == "Continue"


def test_array_indexing_types():
    program, _ = compile_to_typed_ast(
        "fn main() -> int { int a[3]; return a[1]; }"
    )
    ret_val = program.decls[0].body.stmts[1].value
    assert ret_val.type == T.i32


def test_pointer_in_grammar_rejected_semantically():
    # Pointer syntax was removed; this should be a syntax error, not a semantic one.
    with pytest.raises(SyntaxError):
        compile_to_typed_ast("fn main() -> void { int* p; }")


def test_print_builtin_accepts_int():
    # Just verify the call passes semantic without error.
    program, _ = compile_to_typed_ast(
        "fn main() -> void { print(42); }"
    )
    assert program is not None
