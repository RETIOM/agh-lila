from lila.tree import types as T
from lila.tree import nodes as A


BUILTIN_NAMES = {"print", "println", "read_i32", "read_f64", "read_char"}


def format_for_type(t: T.LilaType) -> str:
    if t == T.BOOL:
        return "%d"
    if t == T.i8:
        return "%c"
    if T.is_signed_int(t):
        return "%lld" if t.width == 64 else "%d"
    if T.is_unsigned_int(t):
        return "%llu" if t.width == 64 else "%u"
    if T.is_float(t):
        return "%g"
    if t == T.String:
        return "%s"
    raise TypeError(f"no printf format for {t}")


def widening_for_varargs(t: T.LilaType) -> T.LilaType:
    """Return the type to pass to printf varargs (C integer promotion rules)."""
    if t == T.BOOL or t == T.i8:
        return T.i32
    if T.is_signed_int(t) and t.width < 32:
        return T.i32
    if T.is_unsigned_int(t) and t.width < 32:
        return T.u32
    if t == T.f32:
        return T.f64
    return t


def lower_builtin_call(e: A.Call, fb) -> str:
    if e.name in ("print", "println"):
        return _lower_print(e, fb, newline=(e.name == "println"))
    if e.name == "read_i32":
        return _lower_read(fb, T.i32, "%d")
    if e.name == "read_f64":
        return _lower_read(fb, T.f64, "%lf")
    if e.name == "read_char":
        return _lower_read(fb, T.i8, " %c")
    raise RuntimeError(f"unknown builtin {e.name}")


def _lower_print(e: A.Call, fb, *, newline: bool) -> str:
    from lila.codegen.exprs import lower_expr_rvalue
    if not e.args:
        # println() with no arg → just a newline
        fmt_str = "\n"
        name, n = fb.mod.intern_format(fmt_str)
        fmt_ptr = fb.fresh_tmp()
        fb.body.append(
            f"  {fmt_ptr} = getelementptr inbounds [{n} x i8], ptr {name}, i64 0, i64 0"
        )
        tmp = fb.fresh_tmp()
        fb.body.append(f"  {tmp} = call i32 (ptr, ...) @printf(ptr {fmt_ptr})")
        return ""
    arg = e.args[0]
    base_fmt = format_for_type(arg.type)
    fmt_str = base_fmt + ("\n" if newline else "")
    name, n = fb.mod.intern_format(fmt_str)
    fmt_ptr = fb.fresh_tmp()
    fb.body.append(
        f"  {fmt_ptr} = getelementptr inbounds [{n} x i8], ptr {name}, i64 0, i64 0"
    )
    v = lower_expr_rvalue(arg, fb)
    target_type = widening_for_varargs(arg.type)
    if target_type != arg.type:
        v = _widen(v, arg.type, target_type, fb)
    tmp = fb.fresh_tmp()
    fb.body.append(
        f"  {tmp} = call i32 (ptr, ...) @printf(ptr {fmt_ptr}, {T.llvm_repr(target_type)} {v})"
    )
    return ""


def _widen(v: str, src: T.LilaType, dst: T.LilaType, fb) -> str:
    tmp = fb.fresh_tmp()
    if T.is_int(src) and T.is_int(dst):
        op = "sext" if T.is_signed_int(src) else "zext"
        fb.body.append(f"  {tmp} = {op} {T.llvm_repr(src)} {v} to {T.llvm_repr(dst)}")
    elif T.is_float(src) and T.is_float(dst):
        fb.body.append(f"  {tmp} = fpext {T.llvm_repr(src)} {v} to {T.llvm_repr(dst)}")
    else:
        raise RuntimeError(f"cannot widen {src} to {dst}")
    return tmp


def _lower_read(fb, ret_type: T.LilaType, fmt: str) -> str:
    name, n = fb.mod.intern_format(fmt)
    fmt_ptr = fb.fresh_tmp()
    fb.body.append(
        f"  {fmt_ptr} = getelementptr inbounds [{n} x i8], ptr {name}, i64 0, i64 0"
    )
    slot = fb.fresh_tmp()
    fb.body.append(f"  {slot} = alloca {T.llvm_repr(ret_type)}")
    sc = fb.fresh_tmp()
    fb.body.append(
        f"  {sc} = call i32 (ptr, ...) @scanf(ptr {fmt_ptr}, ptr {slot})"
    )
    out = fb.fresh_tmp()
    fb.body.append(f"  {out} = load {T.llvm_repr(ret_type)}, ptr {slot}")
    return out
