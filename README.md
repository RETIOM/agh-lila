# LILA — Light Intermediate Language Architecture

- Tomasz Idźkowski — idzkowskit@student.agh.edu.pl
- Maksymilian Koleśniak — mkolesniak@student.agh.edu.pl

## Temat

Kompilator dla języka proceduralnego wykorzystującego składnię hybrydową opartą na C/Rust/Zig do reprezentacji LLVM.

## Opis

### Ogólne cele

Głównym celem projektu jest zaprojektowanie oraz implementacja kompilatora dla autorskiego języka programowania do LLVM.

### Rodzaj translatora

Kompilator — program tłumaczy kod źródłowy napisany we własnym języku na kod LLVM IR.

### Wynik działania programu

Kompilator języka do kodu LLVM IR w formacie tekstowym `.ll`. Wygenerowany kod może być następnie przetwarzany przez narzędzia LLVM (`llc`, `clang`, `lli`).

## Język implementacji

`Python 3.14`

## Generator parserów

`PLY` (Python Lex-Yacc)

---

## Krótka instrukcja obsługi

### Wymagania

- Python 3.14+
- [`uv`](https://github.com/astral-sh/uv) lub `pip`
- LLVM (`llc`, `clang`, `lli`) — wymagane tylko do kompilacji do pliku obiektowego / wykonywalnego / uruchomienia JIT

### Instalacja

```bash
# sklonuj repozytorium, następnie:
uv sync          # tworzy .venv i instaluje zależności
# lub:
pip install -e .
```

### Użycie

```
lila <plik.lila> [--tokens | --ast | --ir | --obj | --exe] [-o WYJŚCIE] [--run]
```

| Flaga | Opis |
|---|---|
| `--tokens` | Wypisz strumień tokenów |
| `--ast` | Wypisz drzewo składniowe (AST) |
| `--ir` | Generuj LLVM IR (`.ll`) — **domyślne** |
| `--obj` | Kompiluj do pliku obiektowego (`.o`) przez `llc` |
| `--exe` | Kompiluj do pliku wykonywalnego przez `clang` |
| `--run` | Uruchom natychmiast przez JIT (`lli`) zamiast zapisywać plik |
| `-o PLIK` | Ścieżka pliku wyjściowego; `-` wypisuje na stdout |
| `--keep-temps` | Nie usuwaj tymczasowych plików `.ll` przy `--exe` |

### Uruchomienie przez `.venv`

```bash
.venv/bin/lila <plik.lila> [opcje]
```

---

## Przykład użycia

### Sortowanie bąbelkowe (`examples/bubble_sort.lila`)

```lila
fn main() -> int {
    int xs[8];
    xs[0] = 5; xs[1] = 3; xs[2] = 8; xs[3] = 1;
    xs[4] = 9; xs[5] = 2; xs[6] = 7; xs[7] = 4;

    while true {
        bool swapped = false;
        for int i in 0..7 {
            if xs[i] > xs[i + 1] {
                int tmp = xs[i];
                xs[i] = xs[i + 1];
                xs[i + 1] = tmp;
                swapped = true;
            }
        }
        if !swapped { break; }
    }

    for int i in 0..8 {
        println(xs[i]);
    }
    return 0;
}
```

**Krok 1 — podgląd tokenów:**
```bash
.venv/bin/lila examples/bubble_sort.lila --tokens -o -
```

**Krok 2 — podgląd AST:**
```bash
.venv/bin/lila examples/bubble_sort.lila --ast -o -
```

**Krok 3 — generowanie LLVM IR (plik `bubble_sort.ll`):**
```bash
.venv/bin/lila examples/bubble_sort.lila --ir
```

**Krok 4 — bezpośrednie uruchomienie przez JIT:**
```bash
.venv/bin/lila examples/bubble_sort.lila --run
# wypisze: 1 2 3 4 5 6 7 8 (każda liczba w nowej linii)
```

**Krok 5 — kompilacja do pliku wykonywalnego i uruchomienie:**
```bash
.venv/bin/lila examples/bubble_sort.lila --exe -o bubble_sort
./bubble_sort
```

### Szyfr Cezara (`examples/caesar.lila`)

```bash
.venv/bin/lila examples/caesar.lila --run
# wypisze: khoor!
```

---

## Opis tokenów

| **Nazwa** | **Opis** | **Regex** | **Przykład** |
|---|---|---|---|
| **Identyfikatory i literały** ||||
| `ID` | Identyfikator zmiennej/funkcji | `[a-zA-Z_][a-zA-Z0-9_]*` | `variable`, `_tmp`, `counter1` |
| `INTEGER_LITERAL` | Literał całkowitoliczbowy | `\d+` | `42`, `0`, `1337` |
| `FLOAT_LITERAL` | Literał zmiennoprzecinkowy | `\d+\.\d+` | `3.14`, `0.5` |
| `CHAR_LITERAL` | Literał znakowy | `'[^']'` | `'a'`, `'x'` |
| `STRING_LITERAL` | Literał tekstowy | `"[^"]*"` | `"hello"`, `"text"` |
| **Operatory arytmetyczne** ||||
| `PLUS` | Dodawanie | `\+` | `+` |
| `MINUS` | Odejmowanie | `-` | `-` |
| `TIMES` | Mnożenie | `\*` | `*` |
| `DIVIDE` | Dzielenie | `/` | `/` |
| `MOD` | Reszta z dzielenia | `%` | `%` |
| `INC` | Inkrementacja | `\+\+` | `++` |
| `DEC` | Dekrementacja | `--` | `--` |
| **Operatory relacyjne** ||||
| `EQ` | Równość | `==` | `==` |
| `NEQ` | Nierówność | `!=` | `!=` |
| `LT` | Mniejsze niż | `<` | `<` |
| `GT` | Większe niż | `>` | `>` |
| `LE` | Mniejsze lub równe | `<=` | `<=` |
| `GE` | Większe lub równe | `>=` | `>=` |
| **Operatory logiczne** ||||
| `AND` | Koniunkcja logiczna | `&&` | `&&` |
| `OR` | Alternatywa logiczna | `\|\|` | `\|\|` |
| `NOT` | Negacja logiczna | `!` | `!` |
| **Operatory bitowe** ||||
| `BIT_AND` | Koniunkcja bitowa | `&` | `&` |
| `BIT_OR` | Alternatywa bitowa | `\|` | `\|` |
| `BIT_XOR` | XOR bitowy | `\^` | `^` |
| `BIT_NOT` | Negacja bitowa | `~` | `~` |
| `LSHIFT` | Przesunięcie w lewo | `<<` | `<<` |
| `RSHIFT` | Przesunięcie w prawo | `>>` | `>>` |
| **Operatory przypisania** ||||
| `ASSIGN` | Przypisanie | `=` | `=` |
| `ADD_ASSIGN` | Przypisanie z dodawaniem | `\+=` | `+=` |
| `SUB_ASSIGN` | Przypisanie z odejmowaniem | `-=` | `-=` |
| `MUL_ASSIGN` | Przypisanie z mnożeniem | `\*=` | `*=` |
| `DIV_ASSIGN` | Przypisanie z dzieleniem | `/=` | `/=` |
| `MOD_ASSIGN` | Przypisanie z modulo | `%=` | `%=` |
| **Znaki przestankowe** ||||
| `LPAREN` | Nawias okrągły lewy | `\(` | `(` |
| `RPAREN` | Nawias okrągły prawy | `\)` | `)` |
| `LBRACE` | Nawias klamrowy lewy | `\{` | `{` |
| `RBRACE` | Nawias klamrowy prawy | `\}` | `}` |
| `LBRACKET` | Nawias kwadratowy lewy | `\[` | `[` |
| `RBRACKET` | Nawias kwadratowy prawy | `\]` | `]` |
| `COMMA` | Przecinek | `,` | `,` |
| `SEMI` | Średnik | `;` | `;` |
| `ARROW` | Strzałka (typ zwracany funkcji) | `->` | `->` |
| `DOTDOT` | Operator zakresu (pętla `for`) | `\.\.` | `..` |
| **Słowa kluczowe — deklaracje** ||||
| `FN` | Deklaracja funkcji | `fn` | `fn` |
| `RETURN` | Instrukcja powrotu | `return` | `return` |
| **Słowa kluczowe — sterowanie** ||||
| `IF` | Instrukcja warunkowa | `if` | `if` |
| `ELSE` | Gałąź alternatywna | `else` | `else` |
| `FOR` | Pętla zakresowa | `for` | `for` |
| `IN` | Operator zakresu w pętli `for` | `in` | `in` |
| `WHILE` | Pętla z warunkiem wstępnym | `while` | `while` |
| `DO` | Pętla z warunkiem końcowym | `do` | `do` |
| `BREAK` | Wyjście z pętli | `break` | `break` |
| `CONTINUE` | Następna iteracja | `continue` | `continue` |
| `AS` | Rzutowanie typów | `as` | `as` |
| **Słowa kluczowe — wartości logiczne** ||||
| `TRUE` | Wartość prawda | `true` | `true` |
| `FALSE` | Wartość fałsz | `false` | `false` |
| **Typy danych** ||||
| `TYPE_CHAR` | Znak / liczba całkowita 8-bit ze znakiem | `char` | `char` |
| `TYPE_SHORT` | Liczba całkowita 16-bit ze znakiem | `short` | `short` |
| `TYPE_INT` | Liczba całkowita 32-bit ze znakiem | `int` | `int` |
| `TYPE_LONG` | Liczba całkowita 64-bit ze znakiem | `long` | `long` |
| `TYPE_UCHAR` | Liczba całkowita 8-bit bez znaku | `uchar` | `uchar` |
| `TYPE_USHORT` | Liczba całkowita 16-bit bez znaku | `ushort` | `ushort` |
| `TYPE_UINT` | Liczba całkowita 32-bit bez znaku | `uint` | `uint` |
| `TYPE_ULONG` | Liczba całkowita 64-bit bez znaku | `ulong` | `ulong` |
| `TYPE_FLOAT` | Liczba zmiennoprzecinkowa 32-bit | `float` | `float` |
| `TYPE_DOUBLE` | Liczba zmiennoprzecinkowa 64-bit | `double` | `double` |
| `TYPE_BOOL` | Typ logiczny | `bool` | `bool` |
| `TYPE_VOID` | Typ pusty | `void` | `void` |

---

## Gramatyka

### Lekser (`LILALexer`)

Lekser jest zaimplementowany jako klasa PLY. Słowa kluczowe są rozpoznawane wewnątrz reguły `t_ID` poprzez słownik `reserved`.

```python
class LILALexer:
    reserved = {
        'fn': 'FN', 'return': 'RETURN',
        'if': 'IF', 'else': 'ELSE',
        'for': 'FOR', 'in': 'IN',
        'while': 'WHILE', 'do': 'DO',
        'break': 'BREAK', 'continue': 'CONTINUE',
        'as': 'AS',
        'true': 'TRUE', 'false': 'FALSE',
        'char': 'TYPE_CHAR', 'short': 'TYPE_SHORT',
        'int': 'TYPE_INT',   'long': 'TYPE_LONG',
        'uchar': 'TYPE_UCHAR', 'ushort': 'TYPE_USHORT',
        'uint': 'TYPE_UINT', 'ulong': 'TYPE_ULONG',
        'float': 'TYPE_FLOAT', 'double': 'TYPE_DOUBLE',
        'bool': 'TYPE_BOOL', 'void': 'TYPE_VOID',
    }

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

    # komentarze są pomijane (nie generują tokenów)
    def t_LINE_COMMENT(self, t):
        r'//[^\n]*'
        pass

    def t_BLOCK_COMMENT(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')
```

### Parser (`build_parser`) — priorytety operatorów

```python
precedence = (
    ('right', 'ASSIGN', 'ADD_ASSIGN', 'SUB_ASSIGN', 'MUL_ASSIGN', 'DIV_ASSIGN', 'MOD_ASSIGN'),
    ('left',  'OR'),
    ('left',  'AND'),
    ('left',  'BIT_OR'),
    ('left',  'BIT_XOR'),
    ('left',  'BIT_AND'),
    ('left',  'EQ', 'NEQ'),
    ('left',  'LT', 'GT', 'LE', 'GE'),
    ('left',  'LSHIFT', 'RSHIFT'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'TIMES', 'DIVIDE', 'MOD'),
    ('left',  'AS'),                        # rzutowanie
    ('right', 'UMINUS', 'NOT', 'BIT_NOT'),  # operatory jednoargumentowe
    ('left',  'INC', 'DEC'),
    ('left',  'LBRACKET'),                  # indeksowanie tablicy
)
```

### Parser — reguły gramatyczne

```
program
    : declaration_list

declaration_list
    : declaration_list declaration
    | declaration

declaration
    : var_declaration
    | fun_declaration

fun_declaration
    : FN ID LPAREN param_list RPAREN ARROW type LBRACE block RBRACE
    | FN ID LPAREN RPAREN ARROW type LBRACE block RBRACE

param_list
    : param_list COMMA param
    | param

param
    : type ID
    | type ID LBRACKET INTEGER_LITERAL RBRACKET   (* tablica jako parametr *)

type
    : TYPE_CHAR | TYPE_SHORT | TYPE_INT | TYPE_LONG
    | TYPE_UCHAR | TYPE_USHORT | TYPE_UINT | TYPE_ULONG
    | TYPE_FLOAT | TYPE_DOUBLE | TYPE_BOOL | TYPE_VOID

block
    : statement_list

statement_list
    : statement_list statement
    | empty

statement
    : var_declaration
    | expr_statement
    | return_statement
    | break_statement
    | continue_statement
    | if_statement
    | while_statement
    | do_while_statement
    | for_statement

var_declaration
    : type ID ASSIGN expr SEMI
    | type ID SEMI
    | type ID LBRACKET INTEGER_LITERAL RBRACKET SEMI   (* deklaracja tablicy *)

expr_statement
    : expr SEMI
    | SEMI

return_statement
    : RETURN expr SEMI
    | RETURN SEMI

break_statement    : BREAK SEMI
continue_statement : CONTINUE SEMI

if_statement
    : IF expr LBRACE block RBRACE
    | IF expr LBRACE block RBRACE ELSE LBRACE block RBRACE

while_statement
    : WHILE expr LBRACE block RBRACE

do_while_statement
    : DO LBRACE block RBRACE WHILE expr SEMI

for_statement
    : FOR type ID IN expr DOTDOT expr LBRACE block RBRACE

expr
    : ID ASSIGN expr | ID ADD_ASSIGN expr | ...   (* przypisanie do zmiennej *)
    | postfix_expr LBRACKET expr RBRACKET ASSIGN expr | ...   (* przypisanie do elementu tablicy *)
    | logical_or_expr

logical_or_expr  : logical_or_expr OR logical_and_expr  | logical_and_expr
logical_and_expr : logical_and_expr AND equality_expr   | equality_expr
equality_expr    : equality_expr (EQ | NEQ) rel_expr    | rel_expr
rel_expr         : rel_expr (LT | GT | LE | GE) shift_expr | shift_expr
shift_expr       : shift_expr (LSHIFT | RSHIFT) bitor_expr  | bitor_expr
bitor_expr       : bitor_expr BIT_OR bitxor_expr        | bitxor_expr
bitxor_expr      : bitxor_expr BIT_XOR bitand_expr      | bitand_expr
bitand_expr      : bitand_expr BIT_AND additive_expr    | additive_expr
additive_expr    : additive_expr (PLUS | MINUS) multiplicative_expr | multiplicative_expr
multiplicative_expr : multiplicative_expr (TIMES | DIVIDE | MOD) cast_expr | cast_expr

cast_expr        : cast_expr AS type   (* rzutowanie jawne *)
                 | unary_expr

unary_expr
    : MINUS unary_expr   (* negacja arytmetyczna *)
    | NOT unary_expr
    | BIT_NOT unary_expr
    | INC ID | DEC ID    (* pre-inkrementacja/dekrementacja *)
    | postfix_expr

postfix_expr
    : ID INC | ID DEC
    | postfix_expr LBRACKET expr RBRACKET INC
    | postfix_expr LBRACKET expr RBRACKET DEC
    | postfix_expr LBRACKET expr RBRACKET   (* indeksowanie tablicy *)
    | primary_expr

primary_expr
    : INTEGER_LITERAL | FLOAT_LITERAL | CHAR_LITERAL | STRING_LITERAL
    | TRUE | FALSE
    | ID
    | LPAREN expr RPAREN
    | ID LPAREN arg_list RPAREN   (* wywołanie funkcji *)
    | ID LPAREN RPAREN

arg_list
    : expr
    | arg_list COMMA expr
```
