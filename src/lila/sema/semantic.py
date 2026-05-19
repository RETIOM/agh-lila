from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any

from lila.tree import nodes as A
from lila.tree import types as T
from lila.diagnostics import CompileError


@dataclass
class FnType:
    param_types: list[T.LilaType]
    return_type: T.LilaType


@dataclass
class Symbol:
    name: str
    kind: str                     # "fn" | "global" | "local" | "param"
    type: Any                     # LilaType, _ArrayType, or FnType
    # codegen fills these in later
    ir_name: Optional[str] = None


class SymbolTable:
    def __init__(self):
        self._scopes: list[dict[str, Symbol]] = [{}]

    def push(self):
        self._scopes.append({})

    def pop(self):
        self._scopes.pop()

    def define(self, sym: Symbol, lineno: int = 0):
        if sym.name in self._scopes[-1]:
            raise CompileError(f"name '{sym.name}' redeclared", lineno=lineno)
        self._scopes[-1][sym.name] = sym

    def lookup(self, name: str) -> Symbol:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        raise KeyError(name)

    def lookup_or_none(self, name: str) -> Optional[Symbol]:
        try:
            return self.lookup(name)
        except KeyError:
            return None


_TYPE_NAME_TO_LILA = {
    "char": T.i8, "short": T.i16, "int": T.i32, "long": T.i64,
    "uchar": T.u8, "ushort": T.u16, "uint": T.u32, "ulong": T.u64,
    "float": T.f32, "double": T.f64,
    "bool": T.BOOL, "void": T.VOID,
}

_REVERSE_TYPE_NAME = {v: k for k, v in _TYPE_NAME_TO_LILA.items()}


def _type_to_refname(t: T.LilaType) -> str:
    return _REVERSE_TYPE_NAME[t]


def resolve_typeref(node: A.TypeRef) -> T.LilaType:
    if node.name not in _TYPE_NAME_TO_LILA:
        raise CompileError(f"unknown type '{node.name}'", lineno=node.lineno)
    return _TYPE_NAME_TO_LILA[node.name]


def analyze(program: A.Program) -> tuple[A.Program, SymbolTable]:
    symtab = SymbolTable()
    _pass1_signatures(program, symtab)
    _pass2_bodies(program, symtab)
    return program, symtab


def _pass1_signatures(program: A.Program, symtab: SymbolTable) -> None:
    for decl in program.decls:
        if isinstance(decl, A.FnDecl):
            param_types = []
            for pa in decl.params:
                t = resolve_typeref(pa.type_node)
                if pa.array_size is not None:
                    t = T.Array(t, pa.array_size)
                param_types.append(t)
            ret = resolve_typeref(decl.return_type_node)
            symtab.define(
                Symbol(name=decl.name, kind="fn", type=FnType(param_types, ret)),
                lineno=decl.lineno,
            )
        elif isinstance(decl, A.VarDecl):
            t = resolve_typeref(decl.type_node)
            if decl.array_size is not None:
                t = T.Array(t, decl.array_size)
            symtab.define(
                Symbol(name=decl.name, kind="global", type=t),
                lineno=decl.lineno,
            )


def _pass2_bodies(program: A.Program, symtab: SymbolTable) -> None:
    for decl in program.decls:
        if isinstance(decl, A.FnDecl):
            _check_fn(decl, symtab)


def _check_fn(fn: A.FnDecl, symtab: SymbolTable) -> None:
    symtab.push()
    try:
        for pa in fn.params:
            t = resolve_typeref(pa.type_node)
            if pa.array_size is not None:
                t = T.Array(t, pa.array_size)
            symtab.define(Symbol(name=pa.name, kind="param", type=t), lineno=pa.lineno)
        ret_type = resolve_typeref(fn.return_type_node)
        ctx = _Ctx(symtab=symtab, return_type=ret_type, loop_depth=0)
        _check_block(fn.body, ctx)
    finally:
        symtab.pop()


@dataclass
class _Ctx:
    symtab: SymbolTable
    return_type: T.LilaType
    loop_depth: int = 0


def _check_block(block: A.Block, ctx: _Ctx) -> None:
    ctx.symtab.push()
    try:
        for s in block.stmts:
            _check_stmt(s, ctx)
    finally:
        ctx.symtab.pop()


def _check_stmt(s, ctx: _Ctx) -> None:
    if isinstance(s, A.VarDecl):
        t = resolve_typeref(s.type_node)
        if s.array_size is not None:
            t = T.Array(t, s.array_size)
        if s.init is not None:
            _check_expr(s.init, ctx)
            s.init = _coerce(s.init, t, "initializer")
        ctx.symtab.define(Symbol(name=s.name, kind="local", type=t), lineno=s.lineno)
    elif isinstance(s, A.ExprStmt):
        if s.expr is not None:
            _check_expr(s.expr, ctx)
    elif isinstance(s, A.Return):
        if s.value is None:
            if ctx.return_type != T.VOID:
                raise CompileError("missing return value", lineno=s.lineno)
        else:
            _check_expr(s.value, ctx)
            s.value = _coerce(s.value, ctx.return_type, "return")
    elif isinstance(s, A.If):
        _check_expr(s.cond, ctx)
        _require_bool(s.cond, "if condition")
        _check_block(s.then_block, ctx)
        if s.else_block is not None:
            _check_block(s.else_block, ctx)
    elif isinstance(s, A.While):
        _check_expr(s.cond, ctx)
        _require_bool(s.cond, "while condition")
        ctx.loop_depth += 1
        try:
            _check_block(s.body, ctx)
        finally:
            ctx.loop_depth -= 1
    elif isinstance(s, A.DoWhile):
        ctx.loop_depth += 1
        try:
            _check_block(s.body, ctx)
        finally:
            ctx.loop_depth -= 1
        _check_expr(s.cond, ctx)
        _require_bool(s.cond, "do-while condition")
    elif isinstance(s, A.For):
        t = resolve_typeref(s.var_type_node)
        if not T.is_int(t):
            raise CompileError("for-loop variable must be integer", lineno=s.lineno)
        _check_expr(s.start, ctx)
        s.start = _coerce(s.start, t, "for start")
        _check_expr(s.end, ctx)
        s.end = _coerce(s.end, t, "for end")
        ctx.symtab.push()
        ctx.symtab.define(Symbol(name=s.var_name, kind="local", type=t), lineno=s.lineno)
        ctx.loop_depth += 1
        try:
            _check_block(s.body, ctx)
        finally:
            ctx.loop_depth -= 1
            ctx.symtab.pop()
    elif isinstance(s, A.Break):
        if ctx.loop_depth == 0:
            raise CompileError("`break` outside of a loop", lineno=s.lineno)
    elif isinstance(s, A.Continue):
        if ctx.loop_depth == 0:
            raise CompileError("`continue` outside of a loop", lineno=s.lineno)
    else:
        raise CompileError(f"unhandled statement {s.__class__.__name__}", lineno=getattr(s, "lineno", 0))


def _require_bool(expr, what: str) -> None:
    if expr.type != T.BOOL:
        raise CompileError(f"{what} must be bool, got {expr.type}", lineno=expr.lineno)


def _builtin_signature(name: str, args: list) -> Optional[T.LilaType]:
    """Return the return type if name+args matches a built-in, else None."""
    if name in ("print", "println"):
        if name == "println" and len(args) == 0:
            return T.VOID
        if len(args) != 1:
            return None
        a = args[0].type
        if T.is_numeric(a) or a == T.BOOL or a == T.String:
            return T.VOID
        return None
    if name == "read_i32" and len(args) == 0:
        return T.i32
    if name == "read_f64" and len(args) == 0:
        return T.f64
    if name == "read_char" and len(args) == 0:
        return T.i8
    return None


def _check_expr(e, ctx: _Ctx) -> None:
    if isinstance(e, A.IntLit):
        e.type = T.i32
    elif isinstance(e, A.FloatLit):
        e.type = T.f64
    elif isinstance(e, A.CharLit):
        e.type = T.i8
    elif isinstance(e, A.StringLit):
        e.type = T.String
    elif isinstance(e, A.BoolLit):
        e.type = T.BOOL
    elif isinstance(e, A.Var):
        sym = ctx.symtab.lookup_or_none(e.name)
        if sym is None:
            raise CompileError(f"undefined name '{e.name}'", lineno=e.lineno)
        if sym.kind == "fn":
            raise CompileError(f"'{e.name}' is a function, not a value", lineno=e.lineno)
        e.type = sym.type
    elif isinstance(e, A.Index):
        _check_expr(e.arr, ctx)
        if not isinstance(e.arr.type, T._ArrayType):
            raise CompileError("indexing non-array", lineno=e.lineno)
        _check_expr(e.idx, ctx)
        if not T.is_int(e.idx.type):
            raise CompileError("array index must be integer", lineno=e.lineno)
        e.type = e.arr.type.elem
    elif isinstance(e, A.Call):
        for a in e.args:
            _check_expr(a, ctx)
        builtin_ret = _builtin_signature(e.name, e.args)
        if builtin_ret is not None:
            e.type = builtin_ret
            return
        sym = ctx.symtab.lookup_or_none(e.name)
        if sym is None or sym.kind != "fn":
            raise CompileError(f"undefined function '{e.name}'", lineno=e.lineno)
        ft: FnType = sym.type
        if len(e.args) != len(ft.param_types):
            raise CompileError(
                f"function '{e.name}' expects {len(ft.param_types)} args, got {len(e.args)}",
                lineno=e.lineno,
            )
        coerced = []
        for arg, pt in zip(e.args, ft.param_types):
            coerced.append(_coerce(arg, pt, f"argument to {e.name}"))
        e.args = coerced
        e.type = ft.return_type
    elif isinstance(e, A.Cast):
        _check_expr(e.expr, ctx)
        tgt = resolve_typeref(e.target_type_node)
        if not T.convertible_with_cast(e.expr.type, tgt):
            raise CompileError(f"cannot cast {e.expr.type} to {tgt}", lineno=e.lineno)
        e.type = tgt
    elif isinstance(e, A.UnOp):
        _check_expr(e.operand, ctx)
        t = e.operand.type
        if e.op == "-":
            if not (T.is_signed_int(t) or T.is_float(t)):
                raise CompileError(f"unary `-` requires signed numeric, got {t}", lineno=e.lineno)
            e.type = t
        elif e.op == "!":
            if t != T.BOOL:
                raise CompileError(f"`!` requires bool, got {t}", lineno=e.lineno)
            e.type = T.BOOL
        elif e.op == "~":
            if not T.is_int(t):
                raise CompileError(f"`~` requires integer, got {t}", lineno=e.lineno)
            e.type = t
        else:
            raise CompileError(f"unhandled unary op {e.op}", lineno=e.lineno)
    elif isinstance(e, (A.PreInc, A.PreDec, A.PostInc, A.PostDec)):
        _check_expr(e.target, ctx)
        if not T.is_int(e.target.type):
            raise CompileError("++/-- requires integer operand", lineno=e.lineno)
        e.type = e.target.type
    elif isinstance(e, A.BinOp):
        _check_expr(e.lhs, ctx)
        _check_expr(e.rhs, ctx)
        e.type = _check_binop(e, ctx)
    elif isinstance(e, A.Assign):
        _check_expr(e.target, ctx)
        if not isinstance(e.target, (A.Var, A.Index)):
            raise CompileError("invalid assignment target", lineno=e.lineno)
        _check_expr(e.value, ctx)
        if e.op == "=":
            e.value = _coerce(e.value, e.target.type, "assignment")
        else:
            # compound assignment: rhs must be promotable to lhs type
            e.value = _coerce(e.value, e.target.type, "compound rhs")
        e.type = e.target.type
    else:
        raise CompileError(f"unhandled expression {e.__class__.__name__}", lineno=getattr(e, "lineno", 0))


_ARITH_OPS = {"+", "-", "*", "/", "%"}
_BITWISE_OPS = {"&", "|", "^"}
_SHIFT_OPS = {"<<", ">>"}
_REL_OPS = {"<", "<=", ">", ">=", "==", "!="}
_LOGICAL_OPS = {"&&", "||"}


def _resolve_literal_types(lhs, rhs) -> None:
    """If one side is an IntLit (typed i32) and the other is a different int type,
    retype the literal to match the non-literal side so usual_promotion succeeds."""
    lhs_is_lit = isinstance(lhs, A.IntLit) and lhs.type == T.i32
    rhs_is_lit = isinstance(rhs, A.IntLit) and rhs.type == T.i32
    if lhs_is_lit and not rhs_is_lit and T.is_int(rhs.type):
        lhs.type = rhs.type
    elif rhs_is_lit and not lhs_is_lit and T.is_int(lhs.type):
        rhs.type = lhs.type


def _check_binop(e: A.BinOp, ctx: _Ctx) -> T.LilaType:
    op = e.op
    _resolve_literal_types(e.lhs, e.rhs)
    lt, rt = e.lhs.type, e.rhs.type
    if op in _LOGICAL_OPS:
        if lt != T.BOOL or rt != T.BOOL:
            raise CompileError(f"`{op}` requires bool operands", lineno=e.lineno)
        return T.BOOL
    if op in _ARITH_OPS:
        if not (T.is_numeric(lt) and T.is_numeric(rt)):
            raise CompileError(f"`{op}` requires numeric operands", lineno=e.lineno)
        if op == "%" and (T.is_float(lt) or T.is_float(rt)):
            raise CompileError("`%` requires integer operands", lineno=e.lineno)
        try:
            common = T.usual_promotion(lt, rt)
        except TypeError as exc:
            raise CompileError(str(exc), lineno=e.lineno) from exc
        e.lhs = _coerce(e.lhs, common, f"`{op}` lhs")
        e.rhs = _coerce(e.rhs, common, f"`{op}` rhs")
        return common
    if op in _BITWISE_OPS:
        if not (T.is_int(lt) and T.is_int(rt)):
            raise CompileError(f"`{op}` requires integer operands", lineno=e.lineno)
        try:
            common = T.usual_promotion(lt, rt)
        except TypeError as exc:
            raise CompileError(str(exc), lineno=e.lineno) from exc
        e.lhs = _coerce(e.lhs, common, f"`{op}` lhs")
        e.rhs = _coerce(e.rhs, common, f"`{op}` rhs")
        return common
    if op in _SHIFT_OPS:
        if not (T.is_int(lt) and T.is_int(rt)):
            raise CompileError(f"`{op}` requires integer operands", lineno=e.lineno)
        return lt
    if op in _REL_OPS:
        if not ((T.is_numeric(lt) and T.is_numeric(rt)) or (lt == T.BOOL and rt == T.BOOL)):
            raise CompileError(f"`{op}` requires comparable operands", lineno=e.lineno)
        if T.is_numeric(lt) and T.is_numeric(rt):
            try:
                common = T.usual_promotion(lt, rt)
            except TypeError as exc:
                raise CompileError(str(exc), lineno=e.lineno) from exc
            e.lhs = _coerce(e.lhs, common, f"`{op}` lhs")
            e.rhs = _coerce(e.rhs, common, f"`{op}` rhs")
        return T.BOOL
    raise CompileError(f"unhandled binop `{op}`", lineno=e.lineno)


def _coerce(expr, target: T.LilaType, what: str):
    if expr.type == target:
        return expr
    # Integer literals can be directly typed to any integer target type
    if isinstance(expr, A.IntLit) and T.is_int(target):
        expr.type = target
        return expr
    if T.is_implicit_convertible(expr.type, target):
        cast = A.Cast(expr=expr, target_type_node=A.TypeRef(name=_type_to_refname(target)), lineno=expr.lineno)
        cast.type = target
        return cast
    raise CompileError(
        f"cannot convert {expr.type} to {target} in {what}; use `as` cast",
        lineno=expr.lineno,
    )
