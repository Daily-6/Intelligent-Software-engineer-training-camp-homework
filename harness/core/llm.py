from abc import ABC, abstractmethod
from typing import Optional
import json
from harness.core.action import Action, Message


class LLMClient(ABC):
    @abstractmethod
    def complete(self, messages: list[Message]) -> Action:
        ...


class DeepSeekClient(LLMClient):
    def __init__(self, api_key: str, model: str = "deepseek-chat", max_tokens: int = 4096, temperature: float = 0.7, base_url: str = None):
        from openai import OpenAI
        import os
        if base_url is None:
            base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def complete(self, messages: list[Message]) -> Action:
        openai_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        content = response.choices[0].message.content
        return self._parse_action(content)

    def _parse_action(self, content: str) -> Action:
        import re
        try:
            text = content.strip()
            text = re.sub(r'```(?:json)?\s*', '', text)
            text = text.strip('`').strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                return Action(tool_name="error", args={}, thought=f"no JSON found in: {content[:200]}")
            json_str = text[start:end]
            json_str = json_str.replace("'", '"')
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)
            data = json.loads(json_str)
            tool = data.get("tool") or data.get("tool_name") or data.get("action") or "error"
            args = data.get("args") or data.get("arguments") or data.get("parameters") or {}
            thought = data.get("thought") or data.get("reasoning") or data.get("reason") or ""
            return Action(tool_name=tool, args=args, thought=thought)
        except Exception as e:
            return Action(tool_name="error", args={}, thought=f"parse error: {e}, raw: {content[:200]}")


class MockLLMClient(LLMClient):
    def __init__(self, script: list):
        self._script = list(script)
        self._index = 0

    def complete(self, messages: list[Message]) -> Action:
        if self._index >= len(self._script):
            raise RuntimeError("script exhausted")
        item = self._script[self._index]
        self._index += 1
        if isinstance(item, dict) and "if_context_contains" in item:
            context_text = " ".join(m.content for m in messages)
            if item["if_context_contains"] in context_text:
                return item["action"]
            return self.complete(messages)
        return item
