from typing import Any, Dict, Optional

class Environment:
    def __init__(self, parent: Optional['Environment'] = None):
        self.parent = parent
        self.variables: Dict[str, Any] = {}

    def define(self, name: str, value: Any):
        self.variables[name] = value

    def assign(self, name: str, value: Any):
        if name in self.variables:
            self.variables[name] = value
            return True
        if self.parent:
            return self.parent.assign(name, value)
        return False

    def get(self, name: str) -> Any:
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        return None
