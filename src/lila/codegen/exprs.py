from __future__ import annotations
import struct
from lila.tree import nodes as A
from lila.tree import types as T
from lila.diagnostics import CompileError


def lower_expr_rvalue(e, fb) -> str:
    if isinstance(e, A.IntLit):
        return str(e.value)
    if isinstance(e, A.BoolLit):
        return "1" if e.value else "0"
    if isinstance(e, A.CharLit):
        return str(ord(e.value))
    if isinstance(e, A.FloatLit):
        bits = struct.unpack("<Q", struct.pack("<d", float(e.value)))[0]
        return f"0x{bits:016X}"
    if isinstance(e, A.StringLit):
        name, n = fb.mod.intern_string(e.value)
        tmp = fb.fresh_tmp()
        fb.body.append(f"  {tmp} = getelementptr inbounds [{n} x i8], ptr {name}, i64 0, i64 0")
        return tmp
    if isinstance(e, A.Var):
        slot, ty = _lookup(e.name, fb)
        if isinstance(ty, T._ArrayType):
            if e.name in fb._array_params:
                # slot holds a ptr to the first element (passed by pointer)
                tmp = fb.fresh_tmp()
                fb.body.append(f"  {tmp} = load ptr, ptr {slot}")
                return tmp
            tmp = fb.fresh_tmp()
            fb.body.append(f"  {tmp} = getelementptr inbounds {T.llvm_repr(ty)}, ptr {slot}, i64 0, i64 0")
            return tmp
        tmp = fb.fresh_tmp()
        fb.body.append(f"  {tmp} = load {T.llvm_repr(ty)}, ptr {slot}")
        return tmp
    if isinstance(e, A.Index):
        addr = lower_lvalue_addr(e, fb)
        tmp = fb.fresh_tmp()
        fb.body.append(f"  {tmp} = load {T.llvm_repr(e.type)}, ptr {addr}")
        return tmp
    if isinstance(e, A.Cast):
        return _lower_cast(e, fb)
    if isinstance(e, A.UnOp):
        return _lower_unop(e, fb)
    if isinstance(e, (A.PreInc, A.PreDec, A.PostInc, A.PostDec)):
        return _lower_incdec(e, fb)
    if isinstance(e, A.BinOp):
        return _lower_binop(e, fb)
    if isinstance(e, A.Call):
        return _lower_call(e, fb)
    if isinstance(e, A.Assign):
        return _lower_assign(e, fb)
    raise CompileError(f"codegen for {e.__class__.__name__} not implemented", lineno=getattr(e, "lineno", 0))


def lower_lvalue_addr(e, fb) -> str:
    if isinstance(e, A.Var):
        slot, _ty = _lookup(e.name, fb)
        return slot
    if isinstance(e, A.Index):
        if isinstance(e.arr, A.Var):
            slot, ty = _lookup(e.arr.name, fb)
            idx = lower_expr_rvalue(e.idx, fb)
            idx_i64 = _to_i64(idx, e.idx.type, fb)
            tmp = fb.fresh_tmp()
            if isinstance(ty, T._ArrayType):
                if e.arr.name in fb._array_params:
                    # slot holds ptr to first element; load it first
                    ptr_val = fb.fresh_tmp()
                    fb.body.append(f"  {ptr_val} = load ptr, ptr {slot}")
                    fb.body.append(
                        f"  {tmp} = getelementptr inbounds {T.llvm_repr(ty.elem)}, ptr {ptr_val}, i64 {idx_i64}"
                    )
                else:
                    fb.body.append(
                        f"  {tmp} = getelementptr inbounds {T.llvm_repr(ty)}, ptr {slot}, i64 0, i64 {idx_i64}"
                    )
            else:
                elem = ty
                fb.body.append(
                    f"  {tmp} = getelementptr inbounds {T.llvm_repr(elem)}, ptr {slot}, i64 {idx_i64}"
                )
            return tmp
        ptr = lower_expr_rvalue(e.arr, fb)
        idx = lower_expr_rvalue(e.idx, fb)
        idx_i64 = _to_i64(idx, e.idx.type, fb)
        elem = e.type
        tmp = fb.fresh_tmp()
        fb.body.append(f"  {tmp} = getelementptr inbounds {T.llvm_repr(elem)}, ptr {ptr}, i64 {idx_i64}")
        return tmp
    raise CompileError("invalid lvalue", lineno=getattr(e, "lineno", 0))


def _lookup(name: str, fb):
    if name in fb.locals:
        return fb.locals[name]
    raise CompileError(f"unresolved name '{name}' at codegen time")


def _to_i64(v: str, ty, fb) -> str:
    """Ensure an index value is i64 for use in GEP instructions."""
    if T.width(ty) == 64:
        return v
    # Constant: just return as-is (LLVM accepts integer constants in GEP)
    try:
        int(v)
        return v
    except ValueError:
        pass
    tmp = fb.fresh_tmp()
    op = "sext" if T.is_signed_int(ty) else "zext"
    fb.body.append(f"  {tmp} = {op} {T.llvm_repr(ty)} {v} to i64")
    return tmp


def _lower_unop(e: A.UnOp, fb) -> str:
    v = lower_expr_rvalue(e.operand, fb)
    t = e.operand.type
    tmp = fb.fresh_tmp()
    if e.op == "-":
        if T.is_float(t):
            fb.body.append(f"  {tmp} = fneg {T.llvm_repr(t)} {v}")
        else:
            fb.body.append(f"  {tmp} = sub {T.llvm_repr(t)} 0, {v}")
    elif e.op == "!":
        fb.body.append(f"  {tmp} = xor i1 {v}, true")
    elif e.op == "~":
        fb.body.append(f"  {tmp} = xor {T.llvm_repr(t)} {v}, -1")
    return tmp


def _lower_incdec(e, fb) -> str:
    target_addr = lower_lvalue_addr(e.target, fb)
    t = e.target.type
    old = fb.fresh_tmp()
    fb.body.append(f"  {old} = load {T.llvm_repr(t)}, ptr {target_addr}")
    new = fb.fresh_tmp()
    op = "add" if isinstance(e, (A.PreInc, A.PostInc)) else "sub"
    fb.body.append(f"  {new} = {op} {T.llvm_repr(t)} {old}, 1")
    fb.body.append(f"  store {T.llvm_repr(t)} {new}, ptr {target_addr}")
    return new if isinstance(e, (A.PreInc, A.PreDec)) else old


def _lower_binop(e: A.BinOp, fb) -> str:
    op = e.op
    if op in ("&&", "||"):
        return _lower_short_circuit(e, fb)
    lhs = lower_expr_rvalue(e.lhs, fb)
    rhs = lower_expr_rvalue(e.rhs, fb)
    lt = e.lhs.type
    tmp = fb.fresh_tmp()
    if op in ("+", "-", "*", "/", "%"):
        if T.is_float(lt):
            opname = {"+": "fadd", "-": "fsub", "*": "fmul", "/": "fdiv", "%": "frem"}[op]
        else:
            if op == "/":
                opname = "sdiv" if T.is_signed_int(lt) else "udiv"
            elif op == "%":
                opname = "srem" if T.is_signed_int(lt) else "urem"
            else:
                opname = {"+": "add", "-": "sub", "*": "mul"}[op]
        fb.body.append(f"  {tmp} = {opname} {T.llvm_repr(lt)} {lhs}, {rhs}")
        return tmp
    if op in ("&", "|", "^"):
        name = {"&": "and", "|": "or", "^": "xor"}[op]
        fb.body.append(f"  {tmp} = {name} {T.llvm_repr(lt)} {lhs}, {rhs}")
        return tmp
    if op == "<<":
        fb.body.append(f"  {tmp} = shl {T.llvm_repr(lt)} {lhs}, {rhs}")
        return tmp
    if op == ">>":
        name = "ashr" if T.is_signed_int(lt) else "lshr"
        fb.body.append(f"  {tmp} = {name} {T.llvm_repr(lt)} {lhs}, {rhs}")
        return tmp
    if op in ("==", "!=", "<", "<=", ">", ">="):
        if T.is_float(lt):
            cc = {"==": "oeq", "!=": "one", "<": "olt", "<=": "ole", ">": "ogt", ">=": "oge"}[op]
            fb.body.append(f"  {tmp} = fcmp {cc} {T.llvm_repr(lt)} {lhs}, {rhs}")
            return tmp
        if op in ("==", "!="):
            cc = {"==": "eq", "!=": "ne"}[op]
        elif T.is_signed_int(lt):
            cc = {"<": "slt", "<=": "sle", ">": "sgt", ">=": "sge"}[op]
        else:
            cc = {"<": "ult", "<=": "ule", ">": "ugt", ">=": "uge"}[op]
        fb.body.append(f"  {tmp} = icmp {cc} {T.llvm_repr(lt)} {lhs}, {rhs}")
        return tmp
    raise CompileError(f"unhandled binop {op}")


def _lower_short_circuit(e: A.BinOp, fb) -> str:
    slot = fb.fresh_tmp()
    fb.body.append(f"  {slot} = alloca i1")
    lhs = lower_expr_rvalue(e.lhs, fb)
    if e.op == "&&":
        rhs_lbl = fb.fresh_label("and.rhs")
        cont_lbl = fb.fresh_label("and.cont")
        false_lbl = fb.fresh_label("and.false")
        fb.body.append(f"  br i1 {lhs}, label %{rhs_lbl}, label %{false_lbl}")
        fb.body.append(f"{rhs_lbl}:")
        rhs = lower_expr_rvalue(e.rhs, fb)
        fb.body.append(f"  store i1 {rhs}, ptr {slot}")
        fb.body.append(f"  br label %{cont_lbl}")
        fb.body.append(f"{false_lbl}:")
        fb.body.append(f"  store i1 false, ptr {slot}")
        fb.body.append(f"  br label %{cont_lbl}")
        fb.body.append(f"{cont_lbl}:")
    else:
        rhs_lbl = fb.fresh_label("or.rhs")
        cont_lbl = fb.fresh_label("or.cont")
        true_lbl = fb.fresh_label("or.true")
        fb.body.append(f"  br i1 {lhs}, label %{true_lbl}, label %{rhs_lbl}")
        fb.body.append(f"{true_lbl}:")
        fb.body.append(f"  store i1 true, ptr {slot}")
        fb.body.append(f"  br label %{cont_lbl}")
        fb.body.append(f"{rhs_lbl}:")
        rhs = lower_expr_rvalue(e.rhs, fb)
        fb.body.append(f"  store i1 {rhs}, ptr {slot}")
        fb.body.append(f"  br label %{cont_lbl}")
        fb.body.append(f"{cont_lbl}:")
    out = fb.fresh_tmp()
    fb.body.append(f"  {out} = load i1, ptr {slot}")
    return out


def _lower_cast(e: A.Cast, fb) -> str:
    # Fold integer literal casts to avoid emitting sext/zext for constants
    if isinstance(e.expr, A.IntLit) and T.is_int(e.type):
        return str(e.expr.value)
    v = lower_expr_rvalue(e.expr, fb)
    src, dst = e.expr.type, e.type
    if src == dst:
        return v
    sw, dw = T.width(src), T.width(dst)
    tmp = fb.fresh_tmp()
    if T.is_int(src) and T.is_int(dst):
        if dw > sw:
            op = "sext" if T.is_signed_int(src) else "zext"
        elif dw < sw:
            op = "trunc"
        else:
            return v
        fb.body.append(f"  {tmp} = {op} {T.llvm_repr(src)} {v} to {T.llvm_repr(dst)}")
        return tmp
    if T.is_int(src) and T.is_float(dst):
        op = "sitofp" if T.is_signed_int(src) else "uitofp"
        fb.body.append(f"  {tmp} = {op} {T.llvm_repr(src)} {v} to {T.llvm_repr(dst)}")
        return tmp
    if T.is_float(src) and T.is_int(dst):
        op = "fptosi" if T.is_signed_int(dst) else "fptoui"
        fb.body.append(f"  {tmp} = {op} {T.llvm_repr(src)} {v} to {T.llvm_repr(dst)}")
        return tmp
    if T.is_float(src) and T.is_float(dst):
        op = "fpext" if dw > sw else "fptrunc"
        fb.body.append(f"  {tmp} = {op} {T.llvm_repr(src)} {v} to {T.llvm_repr(dst)}")
        return tmp
    raise CompileError(f"unhandled cast {src} -> {dst}")


def _lower_assign(e: A.Assign, fb) -> str:
    rhs = lower_expr_rvalue(e.value, fb)
    addr = lower_lvalue_addr(e.target, fb)
    fb.body.append(f"  store {T.llvm_repr(e.target.type)} {rhs}, ptr {addr}")
    return rhs


def _lower_call(e: A.Call, fb) -> str:
    from lila.codegen.builtins import lower_builtin_call, BUILTIN_NAMES
    if e.name in BUILTIN_NAMES:
        return lower_builtin_call(e, fb)
    arg_strs = []
    for a in e.args:
        v = lower_expr_rvalue(a, fb)
        # Arrays decay to ptr when passed as arguments
        ir_type = "ptr" if isinstance(a.type, T._ArrayType) else T.llvm_repr(a.type)
        arg_strs.append(f"{ir_type} {v}")
    if e.type == T.VOID:
        fb.body.append(f"  call void @{e.name}({', '.join(arg_strs)})")
        return ""
    tmp = fb.fresh_tmp()
    fb.body.append(f"  {tmp} = call {T.llvm_repr(e.type)} @{e.name}({', '.join(arg_strs)})")
    return tmp
