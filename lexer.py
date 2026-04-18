from dataclasses import dataclass
from typing import List

@dataclass
class Token:
    type: str
    value: str
    line: int

class LexerError(Exception):
    def __init__(self, message: str, line: int):
        super().__init__(f"Error on line {line}: {message}")
        self.line = line

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1

    def tokenize(self) -> List[Token]:
        tokens = []
        lines = self.text.splitlines()
        
        for line_num, line_text in enumerate(lines, 1):
            stripped = line_text.strip()
            if not stripped:
                continue
            
            # Basic check for 'say' keyword
            if stripped.startswith("say"):
                tokens.append(Token("SAY", "say", line_num))
                # Move past 'say' and strip remaining whitespace
                content = stripped[3:].strip()
                
                if not content:
                    # This will be handled by the parser (missing string)
                    continue
                
                if content.startswith('"'):
                    # Find closing quote
                    end_quote = content.find('"', 1)
                    if end_quote == -1:
                        raise LexerError("Unclosed string literal", line_num)
                    
                    string_val = content[1:end_quote]
                    tokens.append(Token("STRING", string_val, line_num))
                    
                    # Check for trailing garbage after the closing quote
                    if content[end_quote+1:].strip():
                        raise LexerError("Unexpected characters after string", line_num)
                else:
                    raise LexerError("Expected string literal after 'say'", line_num)
            else:
                raise LexerError("Invalid syntax: line must start with 'say'", line_num)
        
        return tokens
