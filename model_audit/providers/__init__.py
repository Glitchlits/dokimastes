"""Provider registry and auto-detection."""

from model_audit.models import detect_provider_name
from model_audit.providers.base import Provider


_PROVIDERS = {}


def _ensure_registry():
    if _PROVIDERS:
        return
    from model_audit.providers.ollama import OllamaProvider
    from model_audit.providers.anthropic import AnthropicProvider
    from model_audit.providers.openai import OpenAIProvider
    _PROVIDERS["ollama"] = OllamaProvider
    _PROVIDERS["anthropic"] = AnthropicProvider
    _PROVIDERS["openai"] = OpenAIProvider


def get_provider(name: str) -> Provider:
    _ensure_registry()
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name}. Available: {list(_PROVIDERS.keys())}")
    return cls()


def detect_provider(model_string: str) -> tuple[str, Provider]:
    name = detect_provider_name(model_string)
    return name, get_provider(name)


def list_all_models() -> dict[str, list[str]]:
    _ensure_registry()
    result = {}
    for name, cls in _PROVIDERS.items():
        try:
            p = cls()
            models = p.list_models()
            if models:
                result[name] = models
        except Exception:
            pass
    return result
