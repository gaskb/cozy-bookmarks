from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str
    content: str


class AIProviderError(Exception):
    pass


class AIProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[ChatMessage]) -> str: ...
