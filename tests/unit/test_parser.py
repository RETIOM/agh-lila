import pytest
from lila.syntax.scanner import LILALexer
from lila.syntax.parser import build_parser
from lila.tree import nodes as A


def parse(source: str):
    lx = LILALexer()
    lx.build()
    parser = build_parser()
    return parser.parse(source, lexer=lx.lexer)


def test_empty_program_is_invalid():
    # Grammar requires at least one declaration.
    result = parse("")
    assert result is None


def test_var_decl_no_init():
    p = parse("int x;")
    assert isinstance(p, A.Program)
    assert len(p.decls) == 1
    v = p.decls[0]
    assert isinstance(v, A.VarDecl)
    assert v.name == "x"
    assert v.type_node.name == "int"
    assert v.init is None
    assert v.array_size is None


def test_var_decl_with_array_size():
    p = parse("int xs[10];")
    v = p.decls[0]
    assert v.array_size == 10


def test_fn_decl_with_params_and_body():
    p = parse("fn add(int a, int b) -> int { return a; }")
    f = p.decls[0]
    assert isinstance(f, A.FnDecl)
    assert f.name == "add"
    assert [pa.name for pa in f.params] == ["a", "b"]
    assert f.return_type_node.name == "int"
    assert isinstance(f.body, A.Block)
    assert len(f.body.stmts) == 1
    assert isinstance(f.body.stmts[0], A.Return)


def test_if_else_statement_shape():
    p = parse("fn main() -> void { if true { } else { } }")
    body = p.decls[0].body.stmts
    assert isinstance(body[0], A.If)
    assert isinstance(body[0].then_block, A.Block)
    assert isinstance(body[0].else_block, A.Block)


def test_while_and_do_while():
    p = parse("fn main() -> void { while true { } do { } while true; }")
    s = p.decls[0].body.stmts
    assert isinstance(s[0], A.While)
    assert isinstance(s[1], A.DoWhile)


def test_for_in_range():
    p = parse("fn main() -> void { for int i in 0..10 { } }")
    s = p.decls[0].body.stmts[0]
    assert isinstance(s, A.For)
    assert s.var_name == "i"
    assert s.var_type_node.name == "int"


def test_break_and_continue():
    p = parse("fn main() -> void { while true { break; continue; } }")
    body = p.decls[0].body.stmts[0].body.stmts
    assert isinstance(body[0], A.Break)
    assert isinstance(body[1], A.Continue)


def test_binary_arith_precedence():
    p = parse("fn main() -> int { return 1 + 2 * 3; }")
    expr = p.decls[0].body.stmts[0].value
    assert isinstance(expr, A.BinOp) and expr.op == "+"
    assert isinstance(expr.rhs, A.BinOp) and expr.rhs.op == "*"


def test_relational_and_logical():
    p = parse("fn main() -> bool { return 1 < 2 && 3 != 4; }")
    expr = p.decls[0].body.stmts[0].value
    assert isinstance(expr, A.BinOp) and expr.op == "&&"


def test_cast_expression():
    p = parse("fn main() -> int { return 'a' as int; }")
    expr = p.decls[0].body.stmts[0].value
    assert isinstance(expr, A.Cast)
    assert expr.target_type_node.name == "int"
    assert isinstance(expr.expr, A.CharLit)


def test_function_call_with_args():
    p = parse("fn main() -> void { println(42); }")
    s = p.decls[0].body.stmts[0]
    assert isinstance(s, A.ExprStmt)
    call = s.expr
    assert isinstance(call, A.Call) and call.name == "println"
    assert len(call.args) == 1


def test_index_and_assignment():
    p = parse("fn main() -> void { int a[3]; a[0] = 7; }")
    s = p.decls[0].body.stmts[1]
    assert isinstance(s.expr, A.Assign)
    assert isinstance(s.expr.target, A.Index)


def test_postfix_inc():
    p = parse("fn main() -> void { int i = 0; i++; }")
    s = p.decls[0].body.stmts[1]
    assert isinstance(s.expr, A.PostInc)


def test_unary_minus_and_not():
    p = parse("fn main() -> int { return -1 + !false; }")
    expr = p.decls[0].body.stmts[0].value
    assert isinstance(expr, A.BinOp)
    assert isinstance(expr.lhs, A.UnOp) and expr.lhs.op == "-"


def test_string_and_float_literals():
    p = parse('fn main() -> void { println("hi"); println(3.5); }')
    args0 = p.decls[0].body.stmts[0].expr.args
    args1 = p.decls[0].body.stmts[1].expr.args
    assert isinstance(args0[0], A.StringLit) and args0[0].value == "hi"
    assert isinstance(args1[0], A.FloatLit) and args1[0].value == 3.5
