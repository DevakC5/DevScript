from typing import List
from parser import SayCommand

class Interpreter:
    def execute(self, commands: List[SayCommand]):
        for command in commands:
            if isinstance(command, SayCommand):
                print(command.text)
