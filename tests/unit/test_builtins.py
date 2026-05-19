from lila.codegen.builtins import BUILTIN_NAMES, format_for_type
from lila.tree import types as T


def test_builtin_names_set():
    assert BUILTIN_NAMES == {"print", "println", "read_i32", "read_f64", "read_char"}


def test_format_for_signed_ints():
    assert format_for_type(T.i16) == "%d"
    assert format_for_type(T.i32) == "%d"
    assert format_for_type(T.i64) == "%lld"


def test_format_for_unsigned_ints():
    assert format_for_type(T.u8) == "%u"
    assert format_for_type(T.u32) == "%u"
    assert format_for_type(T.u64) == "%llu"


def test_format_for_floats():
    assert format_for_type(T.f32) == "%g"
    assert format_for_type(T.f64) == "%g"


def test_format_for_char_string_bool():
    assert format_for_type(T.i8) == "%c"
    assert format_for_type(T.BOOL) == "%d"
    assert format_for_type(T.String) == "%s"
