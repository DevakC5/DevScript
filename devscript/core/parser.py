from typing import List
from devscript.utils.tokens import TokenType, Token
from devscript.utils.errors import ParserError
from devscript.core.ast_nodes import (
    Expr, Stmt, NumberExpr, StringExpr, VariableExpr, 
    BinaryOpExpr, UnaryOpExpr, CallExpr, SayStmt, 
    AssignStmt, IfStmt, WhileStmt, Block, ArrayLiteralExpr
)

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self, offset=0):
        if self.pos + offset >= len(self.tokens):
            return Token(TokenType.EOF, None, -1, -1)
        return self.tokens[self.pos + offset]

    def _advance(self):
        token = self._peek()
        self.pos += 1
        return token

    def _match(self, *types):
        if self._peek().type in types:
            return self._advance()
        return None

    def _consume(self, type, message):
        token = self._match(type)
        if token is None:
            curr = self._peek()
            raise ParserError(f"{message} (Expected {type.name}, got {curr.type.name})", curr.line, curr.column)
        return token

    def parse(self) -> Block:
        statements = []
        while self._peek().type != TokenType.EOF:
            if self._peek().type == TokenType.NEWLINE:
                self._advance()
                continue
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return Block(statements)

    def parse_statement(self) -> Stmt:
        token = self._peek()
        
        if token.type == TokenType.SAY:
            return self.parse_say()
        elif token.type == TokenType.LET:
            return self.parse_assignment()
        elif token.type == TokenType.IF:
            return self.parse_if()
        elif token.type == TokenType.WHILE:
            return self.parse_while()
        else:
            expr = self.parse_expression()
            return expr if isinstance(expr, Stmt) else None

    def parse_say(self) -> SayStmt:
        self._advance() # consume 'say'
        expr = self.parse_expression()
        return SayStmt(expr)

    def parse_assignment(self) -> AssignStmt:
        self._advance() # consume 'let'
        name_token = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'let'")
        self._consume(TokenType.ASSIGN, "Expected '=' after variable name")
        value = self.parse_expression()
        return AssignStmt(name_token.value, value)

    def parse_if(self) -> IfStmt:
        self._advance() # consume 'if'
        condition = self.parse_expression()
        self._consume(TokenType.ARROW, "Expected '->' after if condition")
        
        then_branch = []
        while self._peek().type not in (TokenType.ELSE, TokenType.END, TokenType.EOF):
            if self._peek().type == TokenType.NEWLINE:
                self._advance()
                continue
            then_branch.append(self.parse_statement())
            
        else_branch = None
        if self._match(TokenType.ELSE):
            self._consume(TokenType.ARROW, "Expected '->' after else")
            else_branch = []
            while self._peek().type not in (TokenType.END, TokenType.EOF):
                if self._peek().type == TokenType.NEWLINE:
                    self._advance()
                    continue
                else_branch.append(self.parse_statement())
                
        self._consume(TokenType.END, "Expected 'end' to close if block")
        return IfStmt(condition, then_branch, else_branch)

    def parse_while(self) -> WhileStmt:
        self._advance() # consume 'while'
        condition = self.parse_expression()
        self._consume(TokenType.ARROW, "Expected '->' after while condition")
        
        body = []
        while self._peek().type not in (TokenType.END, TokenType.EOF):
            if self._peek().type == TokenType.NEWLINE:
                self._advance()
                continue
            body.append(self.parse_statement())
            
        self._consume(TokenType.END, "Expected 'end' to close while block")
        return WhileStmt(condition, body)

    # Expression Parsing (Precedence)
    
    def parse_expression(self) -> Expr:
        return self.parse_comparison()

    def parse_comparison(self) -> Expr:
        left = self.parse_additive()
        while self._peek().type in (TokenType.EQ, TokenType.NE, TokenType.GT, TokenType.LT, TokenType.GE, TokenType.LE):
            op_token = self._advance()
            right = self.parse_additive()
            left = BinaryOpExpr(left, op_token.value, right)
        return left

    def parse_additive(self) -> Expr:
        left = self.parse_multiplicative()
        while self._peek().type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self._advance()
            right = self.parse_multiplicative()
            left = BinaryOpExpr(left, op_token.value, right)
        return left

    def parse_multiplicative(self) -> Expr:
        left = self.parse_power()
        while self._peek().type in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            op_token = self._advance()
            right = self.parse_power()
            left = BinaryOpExpr(left, op_token.value, right)
        return left

    def parse_power(self) -> Expr:
        left = self.parse_unary()
        if self._match(TokenType.POWER):
            op_token = self.tokens[self.pos - 1]
            right = self.parse_power() # Right associative
            return BinaryOpExpr(left, op_token.value, right)
        return left

    def parse_unary(self) -> Expr:
        if self._match(TokenType.PLUS, TokenType.MINUS):
            op_token = self.tokens[self.pos - 1]
            operand = self.parse_unary()
            return UnaryOpExpr(op_token.value, operand)
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        token = self._peek()
        
        if self._match(TokenType.NUMBER):
            return NumberExpr(token.value)
        
        if self._match(TokenType.STRING):
            return StringExpr(token.value)
        
        if self._match(TokenType.IDENTIFIER):
            name = token.value
            if self._match(TokenType.LPAREN):
                args = []
                if self._peek().type != TokenType.RPAREN:
                    args.append(self.parse_expression())
                    while self._match(TokenType.COMMA):
                        args.append(self.parse_expression())
                self._consume(TokenType.RPAREN, "Expected ')' after function arguments")
                return CallExpr(name, args)
            return VariableExpr(name)
        
        if self._match(TokenType.LPAREN):
            expr = self.parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')'")
            return expr

        if self._match(TokenType.LBRACKET):
            elements = []
            if self._peek().type != TokenType.RBRACKET:
                elements.append(self.parse_expression())
                while self._match(TokenType.COMMA):
                    elements.append(self.parse_expression())
            self._consume(TokenType.RBRACKET, "Expected ']' after array elements")
            return ArrayLiteralExpr(elements)
        
        raise ParserError(f"Expected expression, got {token.type.name}", token.line, token.column)
