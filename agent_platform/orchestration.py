from typing import Callable, Dict, Any
import importlib

def has_langgraph() -> bool:
    try:
        importlib.import_module('langgraph')
        return True
    except Exception:
        return False

class SimpleGraph:
    def __init__(self):
        self.nodes = []
    def add(self, fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.nodes.append(fn)
        return self
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        x = payload
        for fn in self.nodes:
            x = fn(x)
        return x
