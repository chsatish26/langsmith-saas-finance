import yaml, os
from pydantic import BaseModel, ValidationError
from typing import Dict

class RegistryError(Exception): pass

def load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def validate_registry(data: dict, name: str):
    if not isinstance(data, dict):
        raise RegistryError(f"{name} must be a dict")

class AgentSpec(BaseModel):
    id: str
    description: str = ""
    tools: list = []
    memory_turns: int = 6

class ToolSpec(BaseModel):
    name: str
    impl: str
    input_schema: dict = {}
    output_schema: dict = {}

def load_agents(path: str) -> Dict[str, AgentSpec]:
    raw = load_yaml(path)
    validate_registry(raw, "agents.yml")
    out = {}
    for k, v in raw.items():
        try:
            out[k] = AgentSpec(id=k, **(v or {}))
        except ValidationError as e:
            raise RegistryError(f"Invalid agent {k}: {e}")
    return out

def load_tools(path: str) -> Dict[str, ToolSpec]:
    raw = load_yaml(path)
    validate_registry(raw, "tools.yml")
    out = {}
    for k, v in raw.items():
        try:
            out[k] = ToolSpec(name=k, **(v or {}))
        except ValidationError as e:
            raise RegistryError(f"Invalid tool {k}: {e}")
    return out
