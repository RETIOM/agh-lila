from lila.tree.nodes import (
    Program,
    FnDecl,
    Param,
    VarDecl,
    Block,
    If,
    While,
    DoWhile,
    For,
    Return,
    Break,
    Continue,
    ExprStmt,
    Assign,
    BinOp,
    UnOp,
    PreInc,
    PreDec,
    PostInc,
    PostDec,
    Index,
    Call,
    Cast,
    Var,
    IntLit,
    FloatLit,
    CharLit,
    StringLit,
    BoolLit,
)


def test_program_construction():
    p = Program(decls=[])
    assert p.decls == []
    assert p.lineno == 0


def test_node_carries_location():
    v = Var(name="x", lineno=3, col=7)
    assert v.lineno == 3 and v.col == 7


def test_binop_holds_operator_and_children():
    b = BinOp(op="+", lhs=IntLit(1), rhs=IntLit(2))
    assert b.op == "+"
    assert isinstance(b.lhs, IntLit) and b.lhs.value == 1
