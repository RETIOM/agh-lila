import pytest
from lila.diagnostics import CompileError, format_error


def test_compile_error_carries_location():
    err = CompileError("undefined variable 'x'", lineno=12, col=5, path="foo.lila")
    assert err.lineno == 12
    assert err.col == 5
    assert err.path == "foo.lila"


def test_format_error_uses_file_line_col():
    err = CompileError("bad type", lineno=3, col=8, path="foo.lila")
    assert format_error(err) == "foo.lila:3:8: error: bad type"


def test_format_error_without_path():
    err = CompileError("bad type", lineno=3, col=8)
    assert format_error(err) == "<input>:3:8: error: bad type"
