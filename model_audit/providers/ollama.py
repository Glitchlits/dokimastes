"""Ollama provider — local model serving."""

import json
import os
import urllib.request
import urllib.error

from model_audit.providers.base import Provider

DEFAULT_URL = "http://127.0.0.1:11434"


class OllamaProvider(Provider):

    def __init__(self):
        self.base_url = os.environ.get("OLLAMA_URL", DEFAULT_URL).rstrip("/")

    def chat(self, messages: list[dict], model: str, system: str | None = None) -> str:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)

        payload = json.dumps({
            "model": model,
            "messages": msgs,
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data.get("message", {}).get("content", "").strip()
        except urllib.error.URLError as e:
            raise ConnectionError(f"Ollama at {self.base_url}: {e}") from e

    def list_models(self) -> list[str]:
        req = urllib.request.Request(f"{self.base_url}/api/tags")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def model_info(self, model: str) -> dict:
        payload = json.dumps({"name": model}).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/show",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except Exception:
            return {}
