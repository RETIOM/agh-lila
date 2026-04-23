# LILA - Light Intermediate Language Architect
- Tomasz Idźkowski - idzkowskit@student.agh.edu.pl
- Maksymilian Koleśniak - mkolesniak@student.agh.edu.pl

## Temat
Kompilator dla języka proceduralnego wykorzystującego składnię hybrydową opartą na C/Rust/Zig do reprezentacji LLVM.

## Opis
### Ogólne cele
Głównym celem projektu jest zaprojektowanie oraz implementacja kompilatora dla autorskiego języka programowania do LLVM. 
### Rodzaj translatora
Kompilator - program tłumaczy kod źródłowy napisany we własnym języku na kod LLVM IR.
### Planowany wynik działania programu
Kompialtor języka do kodu LLVM IR w formacie tekstowym `.ll`. Wygenerowany kod możę być następnie przetwarzany przez narzędzia LLVM.

## Język implementacji
`Python 3.14`

## Generator parserów
`PLY`

## Opis tokenów

|**Nazwa**|**Opis**|**Regex**|**Przykład**|
|---|---|---|---|
|**Identyfikatory i Literały**||||
|`ID`|Identyfikator zmiennej/funkcji|`r"[a-zA-Z_][a-zA-Z0-9_]*"`|`variable`, `_temp`, `counter123`|
|`INTEGER_LITERAL`|Literał całkowitoliczbowy|`r"[0-9]+"`|`42`, `0`, `1337`|
|`FLOAT_LITERAL`|Literał zmiennoprzecinkowy|`r"[0-9]+\.[0-9]+"`|`3.14`, `0.5`, `2.718`|
|`CHAR_LITERAL`|Literał znakowy|`r"'[^']'"`|`'a'`, `'x'`, `'0'`|
|`STRING_LITERAL`|Literał tekstowy|`r"\"[^\"]*\""`|`"hello"`, `"text"`|
|**Operatory Arytmetyczne**||||
|`PLUS`|Dodawanie|`r"\+"`|`+`|
|`MINUS`|Odejmowanie|`r"-"`|`-`|
|`TIMES`|Mnożenie / Wyłuskanie wskaźnika|`r"\*"`|`*`|
|`DIVIDE`|Dzielenie|`r"/"`|`/`|
|`MOD`|Reszta z dzielenia (modulo)|`r"%"`|`%`|
|`INC`|Inkrementacja|`r"\+\+"`|`++`|
|`DEC`|Dekrementacja|`r"--"`|`--`|
|**Operatory Relacyjne**||||
|`EQ`|Równość|`r"=="`|`==`|
|`NEQ`|Nierówność|`r"!="`|`!=`|
|`LT`|Mniejsze niż|`r"<"`|`<`|
|`GT`|Większe niż|`r">"`|`>`|
|`LE`|Mniejsze lub równe|`r"<="`|`<=`|
|`GE`|Większe lub równe|`r">="`|`>=`|
|**Operatory Logiczne**||||
|`AND`|Koniunkcja logiczna|`r"&&"`|`&&`|
|`OR`|Alternatywa logiczna|`r"\|"`|`\|`|
|`NOT`|Negacja logiczna|`r"!"`|`!`|
|**Operatory Bitowe**||||
|`BIT_AND`|Koniunkcja bitowa / Pobranie adresu|`r"&"`|`&`|
|`BIT_OR`|Alternatywa bitowa|`r"\|"`|`\|`|
|`BIT_XOR`|XOR bitowy|`r"\^"`|`^`|
|`BIT_NOT`|Negacja bitowa|`r"~"`|`~`|
|`LSHIFT`|Przesunięcie w lewo|`r"<<"`|`<<`|
|`RSHIFT`|Przesunięcie w prawo|`r">>"`|`>>`|
|**Operatory Przypisania**||||
|`ASSIGN`|Przypisanie podstawowe|`r"="`|`=`|
|`ADD_ASSIGN`|Przypisanie z dodawaniem|`r"\+="`|`+=`|
|`SUB_ASSIGN`|Przypisanie z odejmowaniem|`r"-="`|`-=`|
|`MUL_ASSIGN`|Przypisanie z mnożeniem|`r"\*="`|`*=`|
|`DIV_ASSIGN`|Przypisanie z dzieleniem|`r"/="`|`/=`|
|`MOD_ASSIGN`|Przypisanie z modulo|`r"%="`|`%=`|
|**Znaki Przestankowe**||||
|`LPAREN`|Nawias okrągły lewy|`r"\("`|`(`|
|`RPAREN`|Nawias okrągły prawy|`r"\)"`|`)`|
|`LBRACE`|Nawias klamrowy lewy|`r"\{"`|`{`|
|`RBRACE`|Nawias klamrowy prawy|`r"\}"`|`}`|
|`LBRACKET`|Nawias kwadratowy lewy|`r"\["`|`[`|
|`RBRACKET`|Nawias kwadratowy prawy|`r"\]"`|`]`|
|`COMMA`|Przecinek|`r","`|`,`|
|`SEMI`|Średnik|`r";"`|`;`|
|`ARROW`|Strzałka (typ zwracany)|`r"->"`|`->`|
|`DOTDOT`|Operator zakresu|`r"\.\."`|`..`|
|**Słowa Kluczowe - Deklaracje**||||
|`FN`|Deklaracja funkcji|`r"fn"`|`fn`|
|`RETURN`|Instrukcja powrotu|`r"return"`|`return`|
|**Słowa Kluczowe - Sterowanie**||||
|`IF`|Instrukcja warunkowa|`r"if"`|`if`|
|`ELSE`|Alternatywa warunku|`r"else"`|`else`|
|`FOR`|Pętla iteracyjna|`r"for"`|`for`|
|`IN`|Operator przynależności (w pętli)|`r"in"`|`in`|
|`WHILE`|Pętla z warunkiem początkowym|`r"while"`|`while`|
|`DO`|Pętla z warunkiem końcowym|`r"do"`|`do`|
|**Słowa Kluczowe - Wartości Logiczne**||||
|`TRUE`|Wartość prawda|`r"true"`|`true`|
|`FALSE`|Wartość fałsz|`r"false"`|`false`|
|**Typy Danych**||||
|`TYPE_INT`|Typ całkowity|`r"int"`|`int`|
|`TYPE_DOUBLE`|Typ zmiennoprzecinkowy podwójnej precyzji|`r"double"`|`double`|
|`TYPE_FLOAT`|Typ zmiennoprzecinkowy|`r"float"`|`float`|
|`TYPE_CHAR`|Typ znakowy|`r"char"`|`char`|
|`TYPE_BOOL`|Typ logiczny|`r"bool"`|`bool`|
|`TYPE_VOID`|Typ pusty|`r"void"`|`void`|

## Gramatyka

### Lex

```python
tokens = (
    'ID', 'INTEGER_LITERAL', 'FLOAT_LITERAL', 'CHAR_LITERAL', 'STRING_LITERAL',
    
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'INC', 'DEC',
    
    'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE',
    'AND', 'OR', 'NOT',
    
    'BIT_AND', 'BIT_OR', 'BIT_XOR', 'BIT_NOT', 'LSHIFT', 'RSHIFT',
    
    'ASSIGN', 'ADD_ASSIGN', 'SUB_ASSIGN', 'MUL_ASSIGN', 'DIV_ASSIGN', 'MOD_ASSIGN',
    
    'LPAREN', 'RPAREN',
    'LBRACE', 'RBRACE',
    'LBRACKET', 'RBRACKET',
    'COMMA', 'SEMI',
    'ARROW', 'DOTDOT',
    
    'FN', 'RETURN', 
    'IF', 'ELSE', 
    'FOR', 'IN', 'WHILE', 'DO',
    'TRUE', 'FALSE',
    
    'TYPE_INT', 'TYPE_DOUBLE', 'TYPE_FLOAT', 'TYPE_CHAR', 'TYPE_BOOL', 'TYPE_VOID'
)


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

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_FLOAT_LITERAL(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INTEGER_LITERAL(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_CHAR_LITERAL(t):
    r"'[^']'"
    t.value = t.value[1:-1]
    return t

def t_STRING_LITERAL(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)
```

### Yacc

```python
precedence = (
    ('right', 'ASSIGN', 'ADD_ASSIGN', 'SUB_ASSIGN', 'MUL_ASSIGN', 'DIV_ASSIGN', 'MOD_ASSIGN'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'BIT_OR'),
    ('left', 'BIT_XOR'),
    ('left', 'BIT_AND'),
    ('left', 'EQ', 'NEQ'),
    ('left', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'LSHIFT', 'RSHIFT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'UMINUS', 'NOT', 'BIT_NOT', 'USTAR', 'UAMP'),
    ('left', 'INC', 'DEC'),
)

def p_program(p):
    '''program : declaration_list'''

def p_declaration_list(p):
    '''declaration_list : declaration_list declaration
                        | declaration'''

def p_declaration(p):
    '''declaration : var_declaration
                   | fun_declaration'''

def p_fun_declaration(p):
    '''fun_declaration : FN ID LPAREN param_list RPAREN ARROW type LBRACE block RBRACE
                       | FN ID LPAREN RPAREN ARROW type LBRACE block RBRACE'''

def p_param_list(p):
    '''param_list : param_list COMMA param
                  | param'''

def p_param(p):
    '''param : type ID
             | type TIMES ID'''

def p_type(p):
    '''type : TYPE_INT
            | TYPE_DOUBLE
            | TYPE_FLOAT
            | TYPE_CHAR
            | TYPE_BOOL
            | TYPE_VOID'''

def p_block(p):
    '''block : statement_list'''

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | empty'''

def p_statement(p):
    '''statement : var_declaration
                 | expr_statement
                 | return_statement
                 | if_statement
                 | while_statement
                 | do_while_statement
                 | for_statement'''

def p_var_declaration(p):
    '''var_declaration : type ID ASSIGN expr SEMI
                       | type ID SEMI
                       | type TIMES ID ASSIGN expr SEMI
                       | type TIMES ID SEMI
                       | type ID LBRACKET expr RBRACKET SEMI'''

def p_expr_statement(p):
    '''expr_statement : expr SEMI
                      | SEMI'''

def p_return_statement(p):
    '''return_statement : RETURN expr SEMI
                        | RETURN SEMI'''

def p_if_statement(p):
    '''if_statement : IF expr LBRACE block RBRACE
                    | IF expr LBRACE block RBRACE ELSE LBRACE block RBRACE'''

def p_while_statement(p):
    '''while_statement : WHILE expr LBRACE block RBRACE'''

def p_do_while_statement(p):
    '''do_while_statement : DO LBRACE block RBRACE WHILE expr SEMI'''

def p_for_statement(p):
    '''for_statement : FOR type ID IN expr DOTDOT expr LBRACE block RBRACE'''

def p_expr(p):
    '''expr : lvalue ASSIGN expr
            | lvalue ADD_ASSIGN expr
            | lvalue SUB_ASSIGN expr
            | lvalue MUL_ASSIGN expr
            | lvalue DIV_ASSIGN expr
            | lvalue MOD_ASSIGN expr
            | logical_or_expr'''

def p_logical_or_expr(p):
    '''logical_or_expr : logical_or_expr OR logical_and_expr
                       | logical_and_expr'''

def p_logical_and_expr(p):
    '''logical_and_expr : logical_and_expr AND equality_expr
                        | equality_expr'''

def p_equality_expr(p):
    '''equality_expr : equality_expr EQ rel_expr
                     | equality_expr NEQ rel_expr
                     | rel_expr'''

def p_rel_expr(p):
    '''rel_expr : rel_expr LT shift_expr
                | rel_expr GT shift_expr
                | rel_expr LE shift_expr
                | rel_expr GE shift_expr
                | shift_expr'''

def p_shift_expr(p):
    '''shift_expr : shift_expr LSHIFT additive_expr
                  | shift_expr RSHIFT additive_expr
                  | additive_expr'''

def p_additive_expr(p):
    '''additive_expr : additive_expr PLUS multiplicative_expr
                     | additive_expr MINUS multiplicative_expr
                     | multiplicative_expr'''

def p_multiplicative_expr(p):
    '''multiplicative_expr : multiplicative_expr TIMES unary_expr
                           | multiplicative_expr DIVIDE unary_expr
                           | multiplicative_expr MOD unary_expr
                           | unary_expr'''

def p_unary_expr(p):
    '''unary_expr : MINUS unary_expr
                  | NOT unary_expr
                  | BIT_NOT unary_expr
                  | TIMES unary_expr
                  | BIT_AND lvalue
                  | INC lvalue
                  | DEC lvalue
                  | postfix_expr'''

def p_postfix_expr(p):
    '''postfix_expr : lvalue INC
                    | lvalue DEC
                    | primary_expr'''

def p_lvalue(p):
    '''lvalue : ID
              | TIMES unary_expr
              | postfix_expr LBRACKET expr RBRACKET'''

def p_primary_expr(p):
    '''primary_expr : ID
                    | INTEGER_LITERAL
                    | FLOAT_LITERAL
                    | CHAR_LITERAL
                    | STRING_LITERAL
                    | TRUE
                    | FALSE
                    | LPAREN expr RPAREN
                    | fun_call'''

def p_fun_call(p):
    '''fun_call : ID LPAREN arg_list RPAREN
                | ID LPAREN RPAREN'''

def p_arg_list(p):
    '''arg_list : arg_list COMMA expr
                | expr'''

def p_empty(p):
    '''empty :'''
    pass

def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}'")
    else:
        print("Syntax error at EOF")
```
