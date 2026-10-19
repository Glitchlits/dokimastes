"""Base test class and score result."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ScoreResult:
    score: float
    sub_scores: dict = field(default_factory=dict)
    confidence: str = "moderate"
    variance: float = 0.0
    signals: dict = field(default_factory=dict)
    explanation: str = ""
    transcript: list[dict] = field(default_factory=list)
    harness: str = "api"


class BaseTest(ABC):
    name: str
    display_name: str
    min_tier: str = "quick"
    turn_count: int = 8

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not getattr(cls, '__abstractmethods__', None):
            if not getattr(cls, 'name', None):
                raise TypeError(f"{cls.__name__} must define 'name'")
            if not getattr(cls, 'display_name', None):
                raise TypeError(f"{cls.__name__} must define 'display_name'")

    @abstractmethod
    def get_script(self, depth: str = "quick", profile: dict | None = None) -> list:
        """Return list of user prompts. Items can be str or callable(transcript) -> str."""

    @abstractmethod
    def score_responses(self, transcript: list[dict]) -> ScoreResult:
        """Score a completed transcript using heuristics."""
