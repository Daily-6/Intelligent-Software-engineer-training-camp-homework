import json
import os
from typing import Optional
from harness.core.action import Turn, Action


class MemoryStore:
    def __init__(self, store_path: str = None):
        self._store_path = store_path
        self._data = {"conventions": {}, "history": []}
        self._load()

    def _load(self):
        if self._store_path and os.path.exists(self._store_path):
            try:
                with open(self._store_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._data["conventions"] = raw.get("conventions", {})
                self._data["history"] = [self._turn_from_dict(t) for t in raw.get("history", [])]
            except (json.JSONDecodeError, IOError):
                pass

    def _turn_from_dict(self, d: dict) -> Turn:
        action = Action(**d["action"])
        return Turn(action=action, governance_result=d.get("governance_result"), timestamp=d["timestamp"])

    def _save(self):
        if not self._store_path:
            return
        try:
            with open(self._store_path, "w", encoding="utf-8") as f:
                json.dump(self._data_to_dict(), f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def _data_to_dict(self) -> dict:
        return {
            "conventions": self._data["conventions"],
            "history": [
                {"action": {"tool_name": t.action.tool_name, "args": t.action.args, "thought": t.action.thought},
                 "governance_result": {"blocked": t.governance_result.blocked, "reason": t.governance_result.reason} if t.governance_result and hasattr(t.governance_result, 'blocked') else None,
                 "timestamp": t.timestamp}
                for t in self._data["history"]
            ],
        }

    def save(self, key: str, value: str) -> None:
        self._data["conventions"][key] = value
        self._save()

    def load(self, key: str) -> Optional[str]:
        return self._data["conventions"].get(key)

    def delete(self, key: str) -> None:
        self._data["conventions"].pop(key, None)
        self._save()

    def append_history(self, turn: Turn) -> None:
        self._data["history"].append(turn)
        self._save()

    def get_recent_history(self, n: int) -> list:
        return self._data["history"][-n:] if n > 0 else []

    def get_conventions(self) -> dict:
        return dict(self._data["conventions"])
