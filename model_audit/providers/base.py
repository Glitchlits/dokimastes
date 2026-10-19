"""Provider base class."""

from abc import ABC, abstractmethod


class Provider(ABC):

    @abstractmethod
    def chat(self, messages: list[dict], model: str, system: str | None = None) -> str:
        """Send conversation, return response text."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models."""

    def model_info(self, model: str) -> dict:
        return {}
