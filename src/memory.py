from __future__ import annotations

from dataclasses import dataclass, field

from .config import settings


@dataclass
class ConversationMemory:
    turns: list[dict] = field(default_factory=list)  

    def add(self, role: str, content: str):
        self.turns.append({"role": role, "content": content})
        # keep only the most recent N turns (user+assistant pairs)
        max_items = settings.memory_turns * 2
        if len(self.turns) > max_items:
            self.turns = self.turns[-max_items:]

    def as_list(self) -> list[dict]:
        return list(self.turns)

    def clear(self):
        self.turns = []
