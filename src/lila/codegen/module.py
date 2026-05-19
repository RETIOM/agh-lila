from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from lila.tree import nodes as A
from lila.tree import types as T
from lila.diagnostics import CompileError


def emit_ir(program: A.Program) -> str:
    em = Module()
    em.emit_preamble()
    for decl in program.decls:
        if isinstance(decl, A.FnDecl):
            em.emit_fn(decl)
        elif isinstance(decl, A.VarDecl):
            em.emit_global(decl)
    return em.finish()


@dataclass
class _LoopFrame:
    continue_label: str
    break_label: str


class Module:
    def __init__(self):
        self.lines: list[str] = []
        self.globals: list[str] = []
        self.string_pool: dict[str, str] = {}
        self._str_counter = 0
        self._fmt_pool: dict[str, str] = {}
        self._fmt_counter = 0

    def emit_preamble(self):
        self.lines.append('; LILA compiler output')
        self.lines.append('declare i32 @printf(ptr, ...)')
        self.lines.append('declare i32 @scanf(ptr, ...)')

    def intern_string(self, value: str) -> tuple[str, int]:
        if value not in self.string_pool:
            name = f"@.str.{self._str_counter}"
            self._str_counter += 1
            self.string_pool[value] = name
            n = len(value.encode("utf-8")) + 1
            esc = _escape_string(value)
            self.globals.append(
                f'{name} = private unnamed_addr constant [{n} x i8] c"{esc}\\00"'
            )
        name = self.string_pool[value]
        n = len(value.encode("utf-8")) + 1
        return name, n

    def intern_format(self, fmt: str) -> tuple[str, int]:
        if fmt not in self._fmt_pool:
            name = f"@.fmt.{self._fmt_counter}"
            self._fmt_counter += 1
            self._fmt_pool[fmt] = name
            n = len(fmt.encode("utf-8")) + 1
            esc = _escape_string(fmt)
            self.globals.append(
                f'{name} = private unnamed_addr constant [{n} x i8] c"{esc}\\00"'
            )
        name = self._fmt_pool[fmt]
        n = len(fmt.encode("utf-8")) + 1
        return name, n

    def emit_global(self, decl: A.VarDecl):
        from lila.sema.semantic import resolve_typeref
        ty = resolve_typeref(decl.type_node)
        if decl.array_size is not None:
            ty = T.Array(ty, decl.array_size)
        repr_ty = T.llvm_repr(ty)
        self.globals.append(f"@{decl.name} = global {repr_ty} zeroinitializer")

    def emit_fn(self, fn: A.FnDecl):
        FnBuilder(self, fn).emit()

    def finish(self) -> str:
        return "\n".join(self.globals + [""] + self.lines) + "\n"


def _escape_string(s: str) -> str:
    out = []
    for ch in s:
        c = ord(ch)
        if ch == "\\":
            out.append("\\5C")
        elif ch == '"':
            out.append('\\22')
        elif ch == '\n':
            out.append('\\0A')
        elif 32 <= c < 127:
            out.append(ch)
        else:
            out.append(f"\\{c:02X}")
    return "".join(out)


class FnBuilder:
    def __init__(self, mod: Module, fn: A.FnDecl):
        self.mod = mod
        self.fn = fn
        self.body: list[str] = []
        self._tmp = 0
        self._lbl = 0
        self.locals: dict[str, tuple[str, object]] = {}   # name -> (slot, type)
        self.loops: list[_LoopFrame] = []
        self._array_params: set[str] = set()   # names of params passed as ptr
        from lila.sema.semantic import resolve_typeref
        self._resolve = resolve_typeref

    def fresh_tmp(self) -> str:
        n = f"%t{self._tmp}"; self._tmp += 1; return n

    def fresh_label(self, prefix="bb") -> str:
        n = f"{prefix}{self._lbl}"; self._lbl += 1; return n

    def emit(self):
        ret_t = self._resolve(self.fn.return_type_node)
        params_ir = []
        param_types = []
        for pa in self.fn.params:
            t = self._resolve(pa.type_node)
            if pa.array_size is not None:
                t = T.Array(t, pa.array_size)
                ir = "ptr"
            else:
                ir = T.llvm_repr(t)
            params_ir.append(f"{ir} %arg.{pa.name}")
            param_types.append((pa.name, t, ir))
        sig = f"define {T.llvm_repr(ret_t)} @{self.fn.name}({', '.join(params_ir)}) {{"
        self.body.append(sig)
        self.body.append("entry:")
        for name, t, ir in param_types:
            slot = f"%{name}.addr"
            self.body.append(f"  {slot} = alloca {ir}")
            self.body.append(f"  store {ir} %arg.{name}, ptr {slot}")
            self.locals[name] = (slot, t)
            if isinstance(t, T._ArrayType):
                self._array_params.add(name)
        from lila.codegen.stmts import lower_block
        lower_block(self.fn.body, self)
        # ensure terminator
        last = self.body[-1].lstrip() if self.body else ""
        if not (last.startswith("ret ") or last.startswith("br ")):
            if ret_t == T.VOID:
                self.body.append("  ret void")
            else:
                self.body.append(f"  ret {T.llvm_repr(ret_t)} 0")
        self.body.append("}")
        self.mod.lines.extend(self.body)
