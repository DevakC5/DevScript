import re
from devscript.utils.tokens import TokenType, Token
from devscript.utils.errors import LexerError

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

    def _peek(self, offset=0):
        if self.pos + offset >= len(self.source):
            return None
        return self.source[self.pos + offset]

    def _advance(self):
        char = self._peek()
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def tokenize(self):
        tokens = []
        
        # Map of multi-character operators
        multi_char_ops = {
            '==': TokenType.EQ,
            '!=': TokenType.NE,
            '>=': TokenType.GE,
            '<=': TokenType.LE,
            '->': TokenType.ARROW,
        }
        
        # Map of single-character operators
        single_char_ops = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MULTIPLY,
            '/': TokenType.DIVIDE,
            '%': TokenType.MODULO,
            '^': TokenType.POWER,
            '=': TokenType.ASSIGN,
            '>': TokenType.GT,
            '<': TokenType.LT,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ',': TokenType.COMMA,
        }

        keywords = {
            'let': TokenType.LET,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'while': TokenType.WHILE,
            'end': TokenType.END,
            'say': TokenType.SAY,
        }

        while self.pos < len(self.source):
            char = self._peek()

            if char is None:
                break

            # Skip whitespace except newlines
            if char.isspace() and char != '\n':
                self._advance()
                continue

            # Handle Newlines
            if char == '\n':
                tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column))
                self._advance()
                continue

            # Handle Strings
            if char == '"':
                start_line = self.line
                start_col = self.column
                self._advance() # skip opening quote
                string_val = ""
                while self._peek() is not None and self._peek() != '"':
                    string_val += self._advance()
                
                if self._peek() is None:
                    raise LexerError("Unclosed string literal", start_line, start_col)
                
                self._advance() # skip closing quote
                tokens.append(Token(TokenType.STRING, string_val, start_line, start_col))
                continue

            # Handle Numbers
            if char.isdigit():
                start_line = self.line
                start_col = self.column
                num_str = ""
                while self._peek() is not None and (self._peek().isdigit() or self._peek() == '.'):
                    num_str += self._advance()
                
                try:
                    val = float(num_str) if '.' in num_str else int(num_str)
                    tokens.append(Token(TokenType.NUMBER, val, start_line, start_col))
                except ValueError:
                    raise LexerError(f"Invalid number format: {num_str}", start_line, start_col)
                continue

            # Handle Identifiers and Keywords
            if char.isalpha() or char == '_':
                start_line = self.line
                start_col = self.column
                ident = ""
                while self._peek() is not None and (self._peek().isalnum() or self._peek() == '_'):
                    ident += self._advance()
                
                token_type = keywords.get(ident, TokenType.IDENTIFIER)
                tokens.append(Token(token_type, ident, start_line, start_col))
                continue

            # Handle Multi-character operators
            two_char = self.source[self.pos : self.pos + 2]
            if two_char in multi_char_ops:
                start_line = self.line
                start_col = self.column
                tokens.append(Token(multi_char_ops[two_char], two_char, start_line, start_col))
                self._advance()
                self._advance()
                continue

            # Handle Single-character operators
            if char in single_char_ops:
                start_line = self.line
                start_col = self.column
                tokens.append(Token(single_char_ops[char], char, start_line, start_col))
                self._advance()
                continue

            raise LexerError(f"Unexpected character: {char}", self.line, self.column)

        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens
