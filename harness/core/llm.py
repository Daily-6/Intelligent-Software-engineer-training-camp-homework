from abc import ABC, abstractmethod
from typing import Optional
import json
from harness.core.action import Action, Message


class LLMClient(ABC):
    @abstractmethod
    def complete(self, messages: list[Message]) -> Action:
        ...


class DeepSeekClient(LLMClient):
    def __init__(self, api_key: str, model: str = "deepseek-chat", max_tokens: int = 4096, temperature: float = 0.7):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
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
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start == -1 or end == 0:
                return Action(tool_name="error", args={}, thought="no JSON found", result=None)
            data = json.loads(content[start:end])
            return Action(
                tool_name=data.get("tool", "error"),
                args=data.get("args", {}),
                thought=data.get("thought", ""),
            )
        except (json.JSONDecodeError, KeyError) as e:
            return Action(tool_name="error", args={}, thought=f"parse error: {e}")


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
