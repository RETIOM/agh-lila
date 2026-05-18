import ply.yacc as yacc
from lila.syntax.tokens import tokens
from lila.tree import nodes as A


precedence = (
    (
        "right",
        "ASSIGN",
        "ADD_ASSIGN",
        "SUB_ASSIGN",
        "MUL_ASSIGN",
        "DIV_ASSIGN",
        "MOD_ASSIGN",
    ),
    ("left", "OR"),
    ("left", "AND"),
    ("left", "BIT_OR"),
    ("left", "BIT_XOR"),
    ("left", "BIT_AND"),
    ("left", "EQ", "NEQ"),
    ("left", "LT", "GT", "LE", "GE"),
    ("left", "LSHIFT", "RSHIFT"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "MOD"),
    ("left", "AS"),
    ("right", "UMINUS", "NOT", "BIT_NOT"),
    ("left", "INC", "DEC"),
    ("left", "LBRACKET"),
)


def p_program(p):
    """program : declaration_list"""
    p[0] = A.Program(decls=p[1], lineno=1)


def p_declaration_list_many(p):
    """declaration_list : declaration_list declaration"""
    p[0] = p[1] + [p[2]]


def p_declaration_list_one(p):
    """declaration_list : declaration"""
    p[0] = [p[1]]


def p_declaration(p):
    """declaration : var_declaration
    | fun_declaration"""
    p[0] = p[1]


def p_fun_declaration_with_params(p):
    """fun_declaration : FN ID LPAREN param_list RPAREN ARROW type LBRACE block RBRACE"""
    p[0] = A.FnDecl(
        name=p[2], params=p[4], return_type_node=p[7], body=p[9], lineno=p.lineno(1)
    )


def p_fun_declaration_no_params(p):
    """fun_declaration : FN ID LPAREN RPAREN ARROW type LBRACE block RBRACE"""
    p[0] = A.FnDecl(
        name=p[2], params=[], return_type_node=p[6], body=p[8], lineno=p.lineno(1)
    )


def p_param_list_many(p):
    """param_list : param_list COMMA param"""
    p[0] = p[1] + [p[3]]


def p_param_list_one(p):
    """param_list : param"""
    p[0] = [p[1]]


def p_param_plain(p):
    """param : type ID"""
    p[0] = A.Param(name=p[2], type_node=p[1], lineno=p.lineno(2))


def p_param_array(p):
    """param : type ID LBRACKET INTEGER_LITERAL RBRACKET"""
    p[0] = A.Param(name=p[2], type_node=p[1], array_size=p[4], lineno=p.lineno(2))


def p_type(p):
    """type : TYPE_CHAR
    | TYPE_SHORT
    | TYPE_INT
    | TYPE_LONG
    | TYPE_UCHAR
    | TYPE_USHORT
    | TYPE_UINT
    | TYPE_ULONG
    | TYPE_FLOAT
    | TYPE_DOUBLE
    | TYPE_BOOL
    | TYPE_VOID"""
    p[0] = A.TypeRef(name=p[1], lineno=p.lineno(1))


def p_block(p):
    """block : statement_list"""
    p[0] = A.Block(stmts=p[1], lineno=0)


def p_statement_list_many(p):
    """statement_list : statement_list statement"""
    p[0] = p[1] + [p[2]]


def p_statement_list_empty(p):
    """statement_list : empty"""
    p[0] = []


def p_statement(p):
    """statement : var_declaration
    | expr_statement
    | return_statement
    | break_statement
    | continue_statement
    | if_statement
    | while_statement
    | do_while_statement
    | for_statement"""
    p[0] = p[1]


def p_var_declaration_init(p):
    """var_declaration : type ID ASSIGN expr SEMI"""
    p[0] = A.VarDecl(name=p[2], type_node=p[1], init=p[4], lineno=p.lineno(2))


def p_var_declaration_no_init(p):
    """var_declaration : type ID SEMI"""
    p[0] = A.VarDecl(name=p[2], type_node=p[1], init=None, lineno=p.lineno(2))


def p_var_declaration_array(p):
    """var_declaration : type ID LBRACKET INTEGER_LITERAL RBRACKET SEMI"""
    p[0] = A.VarDecl(name=p[2], type_node=p[1], array_size=p[4], lineno=p.lineno(2))


def p_expr_statement(p):
    """expr_statement : expr SEMI"""
    p[0] = A.ExprStmt(expr=p[1], lineno=p[1].lineno)


def p_empty_statement(p):
    """expr_statement : SEMI"""
    p[0] = A.ExprStmt(expr=None, lineno=p.lineno(1))


def p_return_statement(p):
    """return_statement : RETURN expr SEMI
    | RETURN SEMI"""
    if len(p) == 4:
        p[0] = A.Return(value=p[2], lineno=p.lineno(1))
    else:
        p[0] = A.Return(value=None, lineno=p.lineno(1))


def p_break_statement(p):
    """break_statement : BREAK SEMI"""
    p[0] = A.Break(lineno=p.lineno(1))


def p_continue_statement(p):
    """continue_statement : CONTINUE SEMI"""
    p[0] = A.Continue(lineno=p.lineno(1))


def p_if_statement_no_else(p):
    """if_statement : IF expr LBRACE block RBRACE"""
    p[0] = A.If(cond=p[2], then_block=p[4], else_block=None, lineno=p.lineno(1))


def p_if_statement_with_else(p):
    """if_statement : IF expr LBRACE block RBRACE ELSE LBRACE block RBRACE"""
    p[0] = A.If(cond=p[2], then_block=p[4], else_block=p[8], lineno=p.lineno(1))


def p_while_statement(p):
    """while_statement : WHILE expr LBRACE block RBRACE"""
    p[0] = A.While(cond=p[2], body=p[4], lineno=p.lineno(1))


def p_do_while_statement(p):
    """do_while_statement : DO LBRACE block RBRACE WHILE expr SEMI"""
    p[0] = A.DoWhile(body=p[3], cond=p[6], lineno=p.lineno(1))


def p_for_statement(p):
    """for_statement : FOR type ID IN expr DOTDOT expr LBRACE block RBRACE"""
    p[0] = A.For(
        var_type_node=p[2],
        var_name=p[3],
        start=p[5],
        end=p[7],
        body=p[9],
        lineno=p.lineno(1),
    )


def p_empty(p):
    """empty :"""
    pass


# --- expressions ---


def p_expr_assign_id(p):
    """expr : ID ASSIGN expr
    | ID ADD_ASSIGN expr
    | ID SUB_ASSIGN expr
    | ID MUL_ASSIGN expr
    | ID DIV_ASSIGN expr
    | ID MOD_ASSIGN expr"""
    target = A.Var(name=p[1], lineno=p.lineno(1))
    p[0] = A.Assign(target=target, op=p[2], value=p[3], lineno=target.lineno)


def p_expr_assign_index(p):
    """expr : postfix_expr LBRACKET expr RBRACKET ASSIGN expr
    | postfix_expr LBRACKET expr RBRACKET ADD_ASSIGN expr
    | postfix_expr LBRACKET expr RBRACKET SUB_ASSIGN expr
    | postfix_expr LBRACKET expr RBRACKET MUL_ASSIGN expr
    | postfix_expr LBRACKET expr RBRACKET DIV_ASSIGN expr
    | postfix_expr LBRACKET expr RBRACKET MOD_ASSIGN expr"""
    target = A.Index(arr=p[1], idx=p[3], lineno=p[1].lineno)
    p[0] = A.Assign(target=target, op=p[5], value=p[6], lineno=target.lineno)


def p_expr_logor(p):
    """expr : logical_or_expr"""
    p[0] = p[1]


def p_logical_or(p):
    """logical_or_expr : logical_or_expr OR logical_and_expr"""
    p[0] = A.BinOp(op="||", lhs=p[1], rhs=p[3], lineno=p[1].lineno)


def p_logical_or_passthrough(p):
    """logical_or_expr : logical_and_expr"""
    p[0] = p[1]


def p_logical_and(p):
    """logical_and_expr : logical_and_expr AND equality_expr"""
    p[0] = A.BinOp(op="&&", lhs=p[1], rhs=p[3], lineno=p[1].lineno)


def p_logical_and_passthrough(p):
    """logical_and_expr : equality_expr"""
    p[0] = p[1]


def p_equality(p):
    """equality_expr : equality_expr EQ rel_expr
    | equality_expr NEQ rel_expr"""
    op = "==" if p.slice[2].type == "EQ" else "!="
    p[0] = A.BinOp(op=op, lhs=p[1], rhs=p[3], lineno=p[1].lineno)


def p_equality_passthrough(p):
    """equality_expr : rel_expr"""
    p[0] = p[1]


def p_rel(p):
    """rel_expr : rel_expr LT shift_expr
    | rel_expr GT shift_expr
    | rel_expr LE shift_expr
    | rel_expr GE shift_expr"""
    table = {"LT": "<", "GT": ">", "LE": "<=", "GE": ">="}
    p[0] = A.BinOp(op=table[p.slice[2].type], lhs=p[1], rhs=p[3], lineno=p[1].lineno)


def p_rel_passthrough(p):
    """rel_expr : shift_expr"""
    p[0] = p[1]


def p_shift(p):
    """shift_expr : shift_expr LSHIFT additive_expr
    | shift_expr RSHIFT additive_expr"""
    op = "<<" if p.slice[2].type == "LSHIFT" else ">>"
    p[0] = A.BinOp(op=op, lhs=p[1], rhs=p[3], lineno=p[1].lineno)


def p_shift_passthrough(p):
    """shift_expr : bitor_expr"""
    p[0] = p[1]


def p_bitor(p):
    """bitor_expr : bitor_expr BIT_OR bitxor_expr"""
    p[0] = A.BinOp(op="|", lhs=p[1], rhs=p[3], lineno=p[1].lineno)


def p_bitor_passthrough(p):
    """bitor_expr : bitxor_expr"""
    p[0] = p[1]


def p_bitxor(p):
    """bitxor_expr : bitxor_expr BIT_XOR bitand_expr"""
    p[0] = A.BinOp(op="^", lhs=p[1], rhs=p[3], lineno=p[1].lineno)


def p_bitxor_passthrough(p):
    """bitxor_expr : bitand_expr"""
    p[0] = p[1]


def p_bitand(p):
    """bitand_expr : bitand_expr BIT_AND additive_expr"""
    p[0] = A.BinOp(op="&", lhs=p[1], rhs=p[3], lineno=p[1].lineno)


def p_bitand_passthrough(p):
    """bitand_expr : additive_expr"""
    p[0] = p[1]


def p_additive(p):
    """additive_expr : additive_expr PLUS multiplicative_expr
    | additive_expr MINUS multiplicative_expr"""
    op = "+" if p.slice[2].type == "PLUS" else "-"
    p[0] = A.BinOp(op=op, lhs=p[1], rhs=p[3], lineno=p[1].lineno)


def p_additive_passthrough(p):
    """additive_expr : multiplicative_expr"""
    p[0] = p[1]


def p_multiplicative(p):
    """multiplicative_expr : multiplicative_expr TIMES cast_expr
    | multiplicative_expr DIVIDE cast_expr
    | multiplicative_expr MOD cast_expr"""
    table = {"TIMES": "*", "DIVIDE": "/", "MOD": "%"}
    p[0] = A.BinOp(op=table[p.slice[2].type], lhs=p[1], rhs=p[3], lineno=p[1].lineno)


def p_multiplicative_passthrough(p):
    """multiplicative_expr : cast_expr"""
    p[0] = p[1]


def p_cast_expr(p):
    """cast_expr : cast_expr AS type"""
    p[0] = A.Cast(expr=p[1], target_type_node=p[3], lineno=p[1].lineno)


def p_cast_expr_passthrough(p):
    """cast_expr : unary_expr"""
    p[0] = p[1]


def p_unary_neg(p):
    """unary_expr : MINUS unary_expr %prec UMINUS"""
    p[0] = A.UnOp(op="-", operand=p[2], lineno=p.lineno(1))


def p_unary_not(p):
    """unary_expr : NOT unary_expr"""
    p[0] = A.UnOp(op="!", operand=p[2], lineno=p.lineno(1))


def p_unary_bitnot(p):
    """unary_expr : BIT_NOT unary_expr"""
    p[0] = A.UnOp(op="~", operand=p[2], lineno=p.lineno(1))


def p_pre_inc_id(p):
    """unary_expr : INC ID"""
    target = A.Var(name=p[2], lineno=p.lineno(2))
    p[0] = A.PreInc(target=target, lineno=p.lineno(1))


def p_pre_dec_id(p):
    """unary_expr : DEC ID"""
    target = A.Var(name=p[2], lineno=p.lineno(2))
    p[0] = A.PreDec(target=target, lineno=p.lineno(1))


def p_unary_passthrough(p):
    """unary_expr : postfix_expr"""
    p[0] = p[1]


def p_post_inc_id(p):
    """postfix_expr : ID INC"""
    target = A.Var(name=p[1], lineno=p.lineno(1))
    p[0] = A.PostInc(target=target, lineno=target.lineno)


def p_post_dec_id(p):
    """postfix_expr : ID DEC"""
    target = A.Var(name=p[1], lineno=p.lineno(1))
    p[0] = A.PostDec(target=target, lineno=target.lineno)


def p_post_inc_index(p):
    """postfix_expr : postfix_expr LBRACKET expr RBRACKET INC"""
    target = A.Index(arr=p[1], idx=p[3], lineno=p[1].lineno)
    p[0] = A.PostInc(target=target, lineno=target.lineno)


def p_post_dec_index(p):
    """postfix_expr : postfix_expr LBRACKET expr RBRACKET DEC"""
    target = A.Index(arr=p[1], idx=p[3], lineno=p[1].lineno)
    p[0] = A.PostDec(target=target, lineno=target.lineno)


def p_postfix_passthrough(p):
    """postfix_expr : primary_expr"""
    p[0] = p[1]


def p_postfix_index(p):
    """postfix_expr : postfix_expr LBRACKET expr RBRACKET"""
    p[0] = A.Index(arr=p[1], idx=p[3], lineno=p[1].lineno)


def p_primary_int(p):
    """primary_expr : INTEGER_LITERAL"""
    p[0] = A.IntLit(value=p[1], lineno=p.lineno(1))


def p_primary_float(p):
    """primary_expr : FLOAT_LITERAL"""
    p[0] = A.FloatLit(value=p[1], lineno=p.lineno(1))


def p_primary_char(p):
    """primary_expr : CHAR_LITERAL"""
    p[0] = A.CharLit(value=p[1], lineno=p.lineno(1))


def p_primary_string(p):
    """primary_expr : STRING_LITERAL"""
    p[0] = A.StringLit(value=p[1], lineno=p.lineno(1))


def p_primary_true(p):
    """primary_expr : TRUE"""
    p[0] = A.BoolLit(value=True, lineno=p.lineno(1))


def p_primary_false(p):
    """primary_expr : FALSE"""
    p[0] = A.BoolLit(value=False, lineno=p.lineno(1))


def p_primary_id(p):
    """primary_expr : ID"""
    p[0] = A.Var(name=p[1], lineno=p.lineno(1))


def p_primary_paren(p):
    """primary_expr : LPAREN expr RPAREN"""
    p[0] = p[2]


def p_primary_call(p):
    """primary_expr : ID LPAREN arg_list RPAREN"""
    p[0] = A.Call(name=p[1], args=p[3], lineno=p.lineno(1))


def p_primary_call_empty(p):
    """primary_expr : ID LPAREN RPAREN"""
    p[0] = A.Call(name=p[1], args=[], lineno=p.lineno(1))


def p_arg_list_one(p):
    """arg_list : expr"""
    p[0] = [p[1]]


def p_arg_list_many(p):
    """arg_list : arg_list COMMA expr"""
    p[0] = p[1] + [p[3]]


def p_error(p):
    if p:
        raise SyntaxError(f"syntax error at '{p.value}' on line {p.lineno}")
    # EOF with no input: grammar requires at least one declaration,
    # so return None via the normal PLY mechanism.
    return None


def build_parser(**kwargs):
    return yacc.yacc(write_tables=False, debug=False, **kwargs)
