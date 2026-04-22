import ply.lex as lex
from src.tokens import tokens

class LILALexer(object):
    reserved = {
        'fn': 'FN',
        'return': 'RETURN',
        'if': 'IF',
        'else': 'ELSE',
        'for': 'FOR',
        'in': 'IN',
        'while': 'WHILE',
        'do': 'DO',
        'true': 'TRUE',
        'false': 'FALSE',
        'int': 'TYPE_INT',
        'double': 'TYPE_DOUBLE',
        'float': 'TYPE_FLOAT',
        'char': 'TYPE_CHAR',
        'bool': 'TYPE_BOOL',
        'void': 'TYPE_VOID'
    }
    
    tokens = tokens + tuple(reserved.values())
    
    t_PLUS       = r'\+'
    t_MINUS      = r'-'
    t_TIMES      = r'\*'
    t_DIVIDE     = r'/'
    t_MOD        = r'%'
    t_INC        = r'\+\+'
    t_DEC        = r'--'

    t_EQ         = r'=='
    t_NEQ        = r'!='
    t_LT         = r'<'
    t_GT         = r'>'
    t_LE         = r'<='
    t_GE         = r'>='

    t_AND        = r'&&'
    t_OR         = r'\|\|'
    t_NOT        = r'!'

    t_BIT_AND    = r'&'
    t_BIT_OR     = r'\|'
    t_BIT_XOR    = r'\^'
    t_BIT_NOT    = r'~'
    t_LSHIFT     = r'<<'
    t_RSHIFT     = r'>>'

    t_ASSIGN     = r'='
    t_ADD_ASSIGN = r'\+='
    t_SUB_ASSIGN = r'-='
    t_MUL_ASSIGN = r'\*='
    t_DIV_ASSIGN = r'/='
    t_MOD_ASSIGN = r'%='

    t_LPAREN     = r'\('
    t_RPAREN     = r'\)'
    t_LBRACE     = r'\{'
    t_RBRACE     = r'\}'
    t_LBRACKET   = r'\['
    t_RBRACKET   = r'\]'
    t_COMMA      = r','
    t_SEMI       = r';'
    t_ARROW      = r'->'
    t_DOTDOT     = r'\.\.'

    # Skip whitespace
    t_ignore = ' \t'

    

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        t.type = self.reserved.get(t.value, 'ID')
        return t

    def t_FLOAT_LITERAL(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    def t_INTEGER_LITERAL(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_CHAR_LITERAL(self, t):
        r"'[^']'"
        t.value = t.value[1:-1]
        return t

    def t_STRING_LITERAL(self, t):
        r'"[^"]*"'
        t.value = t.value[1:-1]
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}'")
        t.lexer.skip(1)
        
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

