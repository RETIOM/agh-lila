from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, Any


@dataclass
class Node:
    lineno: int = field(default=0, kw_only=True)
    col: int = field(default=0, kw_only=True)
    # Filled in by semantic analysis; left as Any to avoid circular import with types.
    type: Any = field(default=None, kw_only=True)


@dataclass
class Program(Node):
    decls: list["Decl"] = field(default_factory=list)


@dataclass
class Param(Node):
    name: str = ""
    type_node: Any = None  # a TypeRef carrying the source type
    array_size: Optional[int] = None  # set if declared as `T name[N]`


@dataclass
class FnDecl(Node):
    name: str = ""
    params: list[Param] = field(default_factory=list)
    return_type_node: Any = None
    body: "Block" = None


@dataclass
class VarDecl(Node):
    name: str = ""
    type_node: Any = None
    init: Optional["Expr"] = None
    array_size: Optional[int] = None  # `T name[N];`
    is_pointer: bool = False  # `T* name;` — accepted by grammar, rejected by semantic


Decl = Union[FnDecl, VarDecl]


@dataclass
class Block(Node):
    stmts: list["Stmt"] = field(default_factory=list)


# --- Statements ---


@dataclass
class If(Node):
    cond: "Expr" = None
    then_block: Block = None
    else_block: Optional[Block] = None


@dataclass
class While(Node):
    cond: "Expr" = None
    body: Block = None


@dataclass
class DoWhile(Node):
    body: Block = None
    cond: "Expr" = None


@dataclass
class For(Node):
    var_name: str = ""
    var_type_node: Any = None
    start: "Expr" = None
    end: "Expr" = None
    body: Block = None


@dataclass
class Return(Node):
    value: Optional["Expr"] = None


@dataclass
class Break(Node):
    pass


@dataclass
class Continue(Node):
    pass


@dataclass
class ExprStmt(Node):
    expr: "Expr" = None


Stmt = Union[VarDecl, If, While, DoWhile, For, Return, Break, Continue, ExprStmt]


# --- Expressions ---


@dataclass
class Assign(Node):
    target: "Expr" = None  # Var or Index
    op: str = "="  # one of =, +=, -=, *=, /=, %=
    value: "Expr" = None


@dataclass
class BinOp(Node):
    op: str = ""
    lhs: "Expr" = None
    rhs: "Expr" = None


@dataclass
class UnOp(Node):
    op: str = ""  # -, !, ~
    operand: "Expr" = None


@dataclass
class PreInc(Node):
    target: "Expr" = None


@dataclass
class PreDec(Node):
    target: "Expr" = None


@dataclass
class PostInc(Node):
    target: "Expr" = None


@dataclass
class PostDec(Node):
    target: "Expr" = None


@dataclass
class Index(Node):
    arr: "Expr" = None
    idx: "Expr" = None


@dataclass
class Call(Node):
    name: str = ""
    args: list["Expr"] = field(default_factory=list)


@dataclass
class Cast(Node):
    expr: "Expr" = None
    target_type_node: Any = None


@dataclass
class Var(Node):
    name: str = ""


@dataclass
class IntLit(Node):
    value: int = 0


@dataclass
class FloatLit(Node):
    value: float = 0.0


@dataclass
class CharLit(Node):
    value: str = ""


@dataclass
class StringLit(Node):
    value: str = ""


@dataclass
class BoolLit(Node):
    value: bool = False


Expr = Union[
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
]


# --- TypeRef: a syntactic type reference produced by the parser ---


@dataclass
class TypeRef(Node):
    name: str = ""  # one of: i8, i16, ..., bool, char, void
