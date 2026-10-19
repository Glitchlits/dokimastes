"""Model string parsing and provider auto-detection."""


def detect_provider_name(model_string: str) -> str:
    s = model_string.lower().strip()
    if ":" in s and "//" not in s:
        return "ollama"
    if s.startswith("claude"):
        return "anthropic"
    if s.startswith(("gpt", "o1", "o3", "o4")):
        return "openai"
    if s.startswith(("http://", "https://")):
        return "openai"
    return "ollama"


def normalize_model_name(model_string: str) -> str:
    s = model_string.strip()
    s = s.replace("/", "-").replace(":", "-")
    for c in " ()[]{}<>!@#$%^&*+=|\\'\";,?":
        s = s.replace(c, "")
    return s[:60]
