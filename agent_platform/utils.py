import time, json, os
from typing import Any

def now_ms() -> int:
    return int(time.time() * 1000)

def dump_json(path: str, obj: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2)
