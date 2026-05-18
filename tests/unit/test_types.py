import pytest
from lila.tree.types import (
    Array,
    String,
    i8,
    i32,
    i64,
    u8,
    u16,
    u32,
    u64,
    f32,
    f64,
    BOOL,
    VOID,
    is_signed_int,
    is_unsigned_int,
    is_int,
    is_float,
    width,
    llvm_repr,
    usual_promotion,
    is_implicit_convertible,
    convertible_with_cast,
)


def test_int_kind_predicates():
    assert is_signed_int(i32) and not is_unsigned_int(i32)
    assert is_unsigned_int(u32) and not is_signed_int(u32)
    assert is_int(i64) and is_int(u8) and is_int(i8) and is_int(BOOL)
    assert not is_int(f32)


def test_float_predicates():
    assert is_float(f32) and is_float(f64)
    assert not is_float(i32)


def test_widths():
    assert width(i8) == 8 and width(i64) == 64
    assert width(u16) == 16
    assert width(f32) == 32 and width(f64) == 64
    assert width(BOOL) == 1


def test_llvm_repr_scalars():
    assert llvm_repr(i32) == "i32"
    assert llvm_repr(u32) == "i32"  # LLVM ints carry no sign
    assert llvm_repr(f32) == "float"
    assert llvm_repr(f64) == "double"
    assert llvm_repr(BOOL) == "i1"
    assert llvm_repr(i8) == "i8"  # char is signed 8-bit
    assert llvm_repr(VOID) == "void"


def test_llvm_repr_array_and_string():
    assert llvm_repr(Array(i32, 10)) == "[10 x i32]"
    assert llvm_repr(String) == "ptr"


def test_usual_promotion_same_signedness():
    assert usual_promotion(i8, i32) == i32
    assert usual_promotion(u16, u64) == u64
    assert usual_promotion(i32, i32) == i32


def test_usual_promotion_int_with_float():
    assert usual_promotion(i32, f64) == f64
    assert usual_promotion(u8, f32) == f32


def test_usual_promotion_float_widening():
    assert usual_promotion(f32, f64) == f64


def test_usual_promotion_signed_unsigned_mix_is_error():
    with pytest.raises(Exception):
        usual_promotion(i32, u32)


def test_is_implicit_convertible_widening():
    assert is_implicit_convertible(i8, i32)
    assert is_implicit_convertible(u8, u32)
    assert is_implicit_convertible(f32, f64)
    assert is_implicit_convertible(i32, f64)


def test_is_implicit_convertible_rejects_narrowing_and_sign_change():
    assert not is_implicit_convertible(i32, i8)
    assert not is_implicit_convertible(i32, u32)
    assert not is_implicit_convertible(f64, f32)
    assert not is_implicit_convertible(f32, i32)


def test_convertible_with_cast_permissive():
    assert convertible_with_cast(i32, u8)
    assert convertible_with_cast(f64, i32)
    assert convertible_with_cast(i8, i32)  # char (i8) can cast to int (i32)


def test_bool_widens_to_i32_in_promotion():
    assert usual_promotion(BOOL, i32) == i32


def test_char_is_signed_eight_bit():
    # char is now i8 (signed 8-bit), following C semantics
    assert is_signed_int(i8)
    assert not is_unsigned_int(i8)
    assert width(i8) == 8
