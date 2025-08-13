from collections import deque

class ConversationMemory:
    def __init__(self, max_turns: int = 6):
        self.buffer = deque(maxlen=max_turns)

    def add(self, role: str, content: str):
        self.buffer.append({"role": role, "content": content})

    def summary(self) -> str:
        return " \n".join([f"{m['role']}: {m['content']}" for m in self.buffer])
