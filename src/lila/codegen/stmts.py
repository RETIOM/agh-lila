from lila.tree import nodes as A
from lila.tree import types as T
from lila.codegen.exprs import lower_expr_rvalue
from lila.diagnostics import CompileError
from lila.codegen.module import _LoopFrame


def lower_block(block: A.Block, fb) -> None:
    for s in block.stmts:
        lower_stmt(s, fb)


def _is_terminator(fb) -> bool:
    if not fb.body:
        return False
    last = fb.body[-1].lstrip()
    return last.startswith("ret ") or last.startswith("br ")


def lower_stmt(s, fb) -> None:
    if isinstance(s, A.Return):
        if s.value is None:
            fb.body.append("  ret void")
        else:
            v = lower_expr_rvalue(s.value, fb)
            fb.body.append(f"  ret {T.llvm_repr(s.value.type)} {v}")
    elif isinstance(s, A.VarDecl):
        _lower_var_decl(s, fb)
    elif isinstance(s, A.ExprStmt):
        if s.expr is not None:
            lower_expr_rvalue(s.expr, fb)
    elif isinstance(s, A.If):
        _lower_if(s, fb)
    elif isinstance(s, A.While):
        _lower_while(s, fb)
    elif isinstance(s, A.DoWhile):
        _lower_dowhile(s, fb)
    elif isinstance(s, A.For):
        _lower_for(s, fb)
    elif isinstance(s, A.Break):
        if not fb.loops:
            raise CompileError("`break` outside of a loop")
        fb.body.append(f"  br label %{fb.loops[-1].break_label}")
        dead = fb.fresh_label("dead")
        fb.body.append(f"{dead}:")
    elif isinstance(s, A.Continue):
        if not fb.loops:
            raise CompileError("`continue` outside of a loop")
        fb.body.append(f"  br label %{fb.loops[-1].continue_label}")
        dead = fb.fresh_label("dead")
        fb.body.append(f"{dead}:")
    else:
        raise CompileError(f"unhandled stmt {s.__class__.__name__}")


def _lower_var_decl(s: A.VarDecl, fb) -> None:
    t = fb._resolve(s.type_node)
    if s.array_size is not None:
        t = T.Array(t, s.array_size)
    slot = f"%{s.name}.addr"
    fb.body.append(f"  {slot} = alloca {T.llvm_repr(t)}")
    fb.locals[s.name] = (slot, t)
    if s.init is not None:
        v = lower_expr_rvalue(s.init, fb)
        fb.body.append(f"  store {T.llvm_repr(t)} {v}, ptr {slot}")


def _lower_if(s: A.If, fb) -> None:
    cond = lower_expr_rvalue(s.cond, fb)
    then_lbl = fb.fresh_label("if.then")
    cont_lbl = fb.fresh_label("if.cont")
    if s.else_block is not None:
        else_lbl = fb.fresh_label("if.else")
        fb.body.append(f"  br i1 {cond}, label %{then_lbl}, label %{else_lbl}")
        fb.body.append(f"{then_lbl}:")
        lower_block(s.then_block, fb)
        if not _is_terminator(fb):
            fb.body.append(f"  br label %{cont_lbl}")
        fb.body.append(f"{else_lbl}:")
        lower_block(s.else_block, fb)
        if not _is_terminator(fb):
            fb.body.append(f"  br label %{cont_lbl}")
        fb.body.append(f"{cont_lbl}:")
    else:
        fb.body.append(f"  br i1 {cond}, label %{then_lbl}, label %{cont_lbl}")
        fb.body.append(f"{then_lbl}:")
        lower_block(s.then_block, fb)
        if not _is_terminator(fb):
            fb.body.append(f"  br label %{cont_lbl}")
        fb.body.append(f"{cont_lbl}:")


def _lower_while(s: A.While, fb) -> None:
    cond_lbl = fb.fresh_label("while.cond")
    body_lbl = fb.fresh_label("while.body")
    exit_lbl = fb.fresh_label("while.exit")
    fb.body.append(f"  br label %{cond_lbl}")
    fb.body.append(f"{cond_lbl}:")
    cond = lower_expr_rvalue(s.cond, fb)
    fb.body.append(f"  br i1 {cond}, label %{body_lbl}, label %{exit_lbl}")
    fb.body.append(f"{body_lbl}:")
    fb.loops.append(_LoopFrame(continue_label=cond_lbl, break_label=exit_lbl))
    lower_block(s.body, fb)
    fb.loops.pop()
    if not _is_terminator(fb):
        fb.body.append(f"  br label %{cond_lbl}")
    fb.body.append(f"{exit_lbl}:")


def _lower_dowhile(s: A.DoWhile, fb) -> None:
    body_lbl = fb.fresh_label("do.body")
    cond_lbl = fb.fresh_label("do.cond")
    exit_lbl = fb.fresh_label("do.exit")
    fb.body.append(f"  br label %{body_lbl}")
    fb.body.append(f"{body_lbl}:")
    fb.loops.append(_LoopFrame(continue_label=cond_lbl, break_label=exit_lbl))
    lower_block(s.body, fb)
    fb.loops.pop()
    if not _is_terminator(fb):
        fb.body.append(f"  br label %{cond_lbl}")
    fb.body.append(f"{cond_lbl}:")
    cond = lower_expr_rvalue(s.cond, fb)
    fb.body.append(f"  br i1 {cond}, label %{body_lbl}, label %{exit_lbl}")
    fb.body.append(f"{exit_lbl}:")


def _lower_for(s: A.For, fb) -> None:
    from lila.sema.semantic import resolve_typeref
    t = resolve_typeref(s.var_type_node)
    start_v = lower_expr_rvalue(s.start, fb)
    end_v = lower_expr_rvalue(s.end, fb)
    slot_name = f"%for.{s.var_name}.{fb._lbl}.addr"
    fb.body.append(f"  {slot_name} = alloca {T.llvm_repr(t)}")
    prev_binding = fb.locals.get(s.var_name)
    fb.locals[s.var_name] = (slot_name, t)
    fb.body.append(f"  store {T.llvm_repr(t)} {start_v}, ptr {slot_name}")
    cond_lbl = fb.fresh_label("for.cond")
    body_lbl = fb.fresh_label("for.body")
    inc_lbl = fb.fresh_label("for.inc")
    exit_lbl = fb.fresh_label("for.exit")
    fb.body.append(f"  br label %{cond_lbl}")
    fb.body.append(f"{cond_lbl}:")
    cur = fb.fresh_tmp()
    fb.body.append(f"  {cur} = load {T.llvm_repr(t)}, ptr {slot_name}")
    cmp = fb.fresh_tmp()
    cc = "slt" if T.is_signed_int(t) else "ult"
    fb.body.append(f"  {cmp} = icmp {cc} {T.llvm_repr(t)} {cur}, {end_v}")
    fb.body.append(f"  br i1 {cmp}, label %{body_lbl}, label %{exit_lbl}")
    fb.body.append(f"{body_lbl}:")
    fb.loops.append(_LoopFrame(continue_label=inc_lbl, break_label=exit_lbl))
    lower_block(s.body, fb)
    fb.loops.pop()
    if not _is_terminator(fb):
        fb.body.append(f"  br label %{inc_lbl}")
    fb.body.append(f"{inc_lbl}:")
    old = fb.fresh_tmp()
    fb.body.append(f"  {old} = load {T.llvm_repr(t)}, ptr {slot_name}")
    new_v = fb.fresh_tmp()
    fb.body.append(f"  {new_v} = add {T.llvm_repr(t)} {old}, 1")
    fb.body.append(f"  store {T.llvm_repr(t)} {new_v}, ptr {slot_name}")
    fb.body.append(f"  br label %{cond_lbl}")
    fb.body.append(f"{exit_lbl}:")
    if prev_binding is None:
        fb.locals.pop(s.var_name, None)
    else:
        fb.locals[s.var_name] = prev_binding
