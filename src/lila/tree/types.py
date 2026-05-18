from dataclasses import dataclass
from enum import Enum, auto


class Kind(Enum):
    SIGNED_INT = auto()
    UNSIGNED_INT = auto()
    FLOAT = auto()
    BOOL = auto()
    VOID = auto()
    ARRAY = auto()
    STRING = auto()


@dataclass(frozen=True)
class LilaType:
    kind: Kind
    width: int = 0  # bits; 0 for VOID/STRING/ARRAY

    def __repr__(self) -> str:
        return _names.get(self, f"LilaType({self.kind.name}, {self.width})")


@dataclass(frozen=True)
class _ArrayType:
    kind: Kind
    elem: LilaType
    n: int
    width: int = 0


def Array(elem: LilaType, n: int) -> _ArrayType:
    return _ArrayType(kind=Kind.ARRAY, elem=elem, n=n)


i8 = LilaType(Kind.SIGNED_INT, 8)
i16 = LilaType(Kind.SIGNED_INT, 16)
i32 = LilaType(Kind.SIGNED_INT, 32)
i64 = LilaType(Kind.SIGNED_INT, 64)
u8 = LilaType(Kind.UNSIGNED_INT, 8)
u16 = LilaType(Kind.UNSIGNED_INT, 16)
u32 = LilaType(Kind.UNSIGNED_INT, 32)
u64 = LilaType(Kind.UNSIGNED_INT, 64)
f32 = LilaType(Kind.FLOAT, 32)
f64 = LilaType(Kind.FLOAT, 64)
BOOL = LilaType(Kind.BOOL, 1)
VOID = LilaType(Kind.VOID, 0)
String = LilaType(Kind.STRING, 0)

_names = {
    i8: "char",
    i16: "short",
    i32: "int",
    i64: "long",
    u8: "uchar",
    u16: "ushort",
    u32: "uint",
    u64: "ulong",
    f32: "float",
    f64: "double",
    BOOL: "bool",
    VOID: "void",
    String: "string",
}


def is_signed_int(t) -> bool:
    return getattr(t, "kind", None) == Kind.SIGNED_INT


def is_unsigned_int(t) -> bool:
    return getattr(t, "kind", None) == Kind.UNSIGNED_INT


def is_int(t) -> bool:
    return getattr(t, "kind", None) in (Kind.SIGNED_INT, Kind.UNSIGNED_INT, Kind.BOOL)


def is_float(t) -> bool:
    return getattr(t, "kind", None) == Kind.FLOAT


def is_numeric(t) -> bool:
    return is_int(t) or is_float(t)


def width(t) -> int:
    if isinstance(t, _ArrayType):
        return 0
    return t.width


def llvm_repr(t) -> str:
    if isinstance(t, _ArrayType):
        return f"[{t.n} x {llvm_repr(t.elem)}]"
    if t.kind == Kind.STRING:
        return "ptr"
    if t.kind == Kind.VOID:
        return "void"
    if t.kind == Kind.BOOL:
        return "i1"
    if t.kind == Kind.FLOAT:
        return "float" if t.width == 32 else "double"
    # signed and unsigned integers share the same LLVM repr
    return f"i{t.width}"


def _normalize_for_promo(t: LilaType) -> LilaType:
    # bool widens for arithmetic
    if t.kind == Kind.BOOL:
        return i32
    return t


def usual_promotion(a: LilaType, b: LilaType) -> LilaType:
    a, b = _normalize_for_promo(a), _normalize_for_promo(b)
    if is_float(a) or is_float(b):
        if is_float(a) and is_float(b):
            return a if a.width >= b.width else b
        f = a if is_float(a) else b
        return f
    # both ints
    if a.kind != b.kind:
        raise TypeError(f"cannot mix signed and unsigned ({a!r}, {b!r}); use `as` cast")
    return a if a.width >= b.width else b


def is_implicit_convertible(src: LilaType, dst: LilaType) -> bool:
    if src == dst:
        return True
    # bool widens to same-signedness ints of greater width
    src_n = _normalize_for_promo(src)
    # int → wider int (same signedness)
    if (
        is_int(src_n)
        and is_int(dst)
        and src_n.kind == dst.kind
        and src_n.width <= dst.width
    ):
        return True
    # float → wider float
    if is_float(src) and is_float(dst) and src.width <= dst.width:
        return True
    # int → float
    if is_int(src) and is_float(dst):
        return True
    return False


def convertible_with_cast(src: LilaType, dst: LilaType) -> bool:
    return is_numeric(src) and is_numeric(dst)
