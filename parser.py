from dataclasses import dataclass
from typing import List
from lexer import Token

@dataclass
class SayCommand:
    text: str
    line: int

class ParserError(Exception):
    def __init__(self, message: str, line: int):
        super().__init__(f"Error on line {line}: {message}")
        self.line = line

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> List[SayCommand]:
        commands = []
        
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            
            if token.type == "SAY":
                self.pos += 1
                if self.pos < len(self.tokens) and self.tokens[self.pos].type == "STRING":
                    string_token = self.tokens[self.pos]
                    commands.append(SayCommand(string_token.value, string_token.line))
                    self.pos += 1
                else:
                    # We know it's 'say' but there's no following string
                    # Use the 'say' token's line number
                    raise ParserError("Invalid syntax: 'say' must be followed by a string", token.line)
            else:
                # This case might be reached if the lexer allows tokens other than SAY at the start
                raise ParserError(f"Unexpected token {token.type}", token.line)
        
        return commands
