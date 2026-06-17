from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    usage: dict[str, Any]


class OpenRouterClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 45,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")
        self.timeout = timeout
        self.base_url = os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
        )

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def chat_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        max_tokens: int = 700,
        temperature: float = 0.2,
    ) -> tuple[dict[str, Any], LLMResponse]:
        response = self.chat(
            [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False, indent=2),
                },
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return extract_json_object(response.content), response

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 700,
        temperature: float = 0.2,
    ) -> LLMResponse:
        if not self.api_key:
            raise LLMError("OPENROUTER_API_KEY is not set.")

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://course-project.local",
                "X-Title": "Course Stock Agent Minimal Version",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as handle:
                payload = json.loads(handle.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"OpenRouter request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMError("OpenRouter request timed out.") from exc

        choices = payload.get("choices") or []
        if not choices:
            raise LLMError(f"OpenRouter response has no choices: {payload}")
        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        if not content.strip():
            raise LLMError(f"OpenRouter response content is empty: {payload}")
        return LLMResponse(
            content=content,
            model=str(payload.get("model") or self.model),
            usage=payload.get("usage") or {},
        )


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise LLMError(f"Model did not return JSON: {text}")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMError(f"Model returned invalid JSON: {text}") from exc
