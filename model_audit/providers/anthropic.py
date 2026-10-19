"""Anthropic provider — Claude models via Messages API."""

import json
import os
import urllib.request
import urllib.error

from model_audit.providers.base import Provider

API_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider(Provider):

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    def chat(self, messages: list[dict], model: str, system: str | None = None) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        body = {
            "model": model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            body["system"] = system

        payload = json.dumps(body).encode()
        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        return block["text"].strip()
                return data["content"][0].get("text", str(data["content"][0])).strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode() if e.fp else ""
            raise ConnectionError(f"Anthropic API {e.code}: {err_body[:200]}") from e

    def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        return [
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-haiku-5-5",
        ]
