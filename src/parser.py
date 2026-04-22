import ply.yacc as yacc
from src.tokens import tokens

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
        
parser = yacc.yacc()