from dataclasses import dataclass
from enum import Enum, auto

class TokenType(Enum):
    # Keywords
    LET = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    END = auto()
    SAY = auto()

    # Literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # Operators
    PLUS = auto()        # +
    MINUS = auto()       # -
    MULTIPLY = auto()    # *
    DIVIDE = auto()      # /
    MODULO = auto()      # %
    POWER = auto()       # ^
    ASSIGN = auto()      # =
    EQ = auto()          # ==
    NE = auto()          # !=
    GT = auto()          # >
    LT = auto()          # <
    GE = auto()          # >=
    LE = auto()          # <=

    # Delimiters
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACKET = auto()    # [
    RBRACKET = auto()    # ]
    COMMA = auto()       # ,
    ARROW = auto()       # ->
    NEWLINE = auto()     # \n
    EOF = auto()         # End of File

@dataclass
class Token:
    type: TokenType
    value: any
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, line={self.line}, col={self.column})"
