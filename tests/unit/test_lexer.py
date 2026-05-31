from lila.syntax.scanner import LILALexer
from lila.diagnostics import CompileError


def lex(source: str) -> list[tuple[str, object]]:
    lexer = LILALexer()
    lexer.build()
    lexer.lexer.input(source)
    return [(tok.type, tok.value) for tok in iter(lexer.lexer.token, None)]


def lex_collecting(source: str):
    lexer = LILALexer()
    lexer.build()
    lexer.lexer.input(source)
    toks = [(tok.type, tok.value) for tok in iter(lexer.lexer.token, None)]
    return toks, lexer.errors


def test_c_style_numeric_types_tokenize():
    types = "char short int long uchar ushort uint ulong float double bool void"
    expected = [
        ("TYPE_CHAR", "char"),
        ("TYPE_SHORT", "short"),
        ("TYPE_INT", "int"),
        ("TYPE_LONG", "long"),
        ("TYPE_UCHAR", "uchar"),
        ("TYPE_USHORT", "ushort"),
        ("TYPE_UINT", "uint"),
        ("TYPE_ULONG", "ulong"),
        ("TYPE_FLOAT", "float"),
        ("TYPE_DOUBLE", "double"),
        ("TYPE_BOOL", "bool"),
        ("TYPE_VOID", "void"),
    ]
    assert lex(types) == expected


def test_as_keyword():
    assert lex("as") == [("AS", "as")]


def test_break_continue_keywords():
    assert lex("break continue") == [("BREAK", "break"), ("CONTINUE", "continue")]


def test_old_rust_type_keywords_are_identifiers_now():
    # Old Rust-style type keywords are no longer reserved.
    result = lex("i8 i32 f64 u32")
    assert result == [("ID", "i8"), ("ID", "i32"), ("ID", "f64"), ("ID", "u32")]


def test_integer_and_float_literals():
    assert lex("42 3.14") == [("INTEGER_LITERAL", 42), ("FLOAT_LITERAL", 3.14)]


def test_illegal_char_is_collected_not_printed(capsys):
    toks, errors = lex_collecting("int @ x")
    # the '@' is skipped, surrounding tokens still produced
    assert ("TYPE_INT", "int") in toks
    assert ("ID", "x") in toks
    # error captured on the lexer, not printed
    assert len(errors) == 1
    assert isinstance(errors[0], CompileError)
    assert "illegal character" in errors[0].message
    assert errors[0].lineno == 1
    assert capsys.readouterr().out == ""
