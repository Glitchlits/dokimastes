"""OpenAI provider — GPT models via Chat Completions API."""

import json
import os
import urllib.request
import urllib.error

from model_audit.providers.base import Provider

API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(Provider):

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")

    def chat(self, messages: list[dict], model: str, system: str | None = None) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)

        payload = json.dumps({
            "model": model,
            "messages": msgs,
            "max_tokens": 4096,
        }).encode()

        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            raise ConnectionError(f"OpenAI API {e.code}: {body[:200]}") from e

    def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "o3",
            "o4-mini",
        ]
