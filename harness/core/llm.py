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
            text = re.sub(r'```(?:json)?\s*', '', text).strip('`').strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                return Action(tool_name="error", args={}, thought=f"no JSON found in: {content[:200]}")
            json_str = text[start:end]
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                for replacement in [
                    json_str.replace("'", '"'),
                    re.sub(r'(\w+):', r'"\1":', json_str),
                    re.sub(r'(\w+):', r'"\1":', json_str.replace("'", '"')),
                ]:
                    try:
                        data = json.loads(replacement)
                        break
                    except json.JSONDecodeError:
                        continue
                else:
                    raise
            tool = data.get("tool") or data.get("tool_name") or data.get("action") or "error"
            args = data.get("args") or data.get("arguments") or data.get("parameters") or {}
            thought = data.get("thought") or data.get("reasoning") or data.get("reason") or ""
            return Action(tool_name=tool, args=args, thought=thought)
        except Exception as e:
            return self._parse_action_fallback(content)

    def _parse_action_fallback(self, content: str) -> Action:
        import re
        m = re.match(r'Action:\s*(\w+)\s*\((.*)\)\s*-?\s*(.*)', content, re.DOTALL)
        if m:
            tool_name = m.group(1)
            args_str = m.group(2)
            thought = m.group(3).strip()
            try:
                args = eval("(" + args_str + ")")
                if isinstance(args, tuple) and len(args) == 1:
                    args = args[0]
                if not isinstance(args, dict):
                    args = {"value": str(args)}
            except Exception:
                args = {"raw": args_str}
            return Action(tool_name=tool_name, args=args, thought=thought)
        return Action(tool_name="error", args={}, thought=f"unparseable: {content[:200]}")


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
