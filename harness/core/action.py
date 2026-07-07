from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str = ""


@dataclass
class ShellResult(ToolResult):
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


@dataclass
class TestResult(ToolResult):
    __test__ = False
    total: int = 0
    passed: int = 0
    failed: int = 0
    failures_detail: list = field(default_factory=list)


@dataclass
class Action:
    tool_name: str
    args: dict
    thought: str
    result: Optional[ToolResult] = None


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Turn:
    action: Action
    governance_result: Optional[object]
    timestamp: str


@dataclass
class Session:
    id: str
    task: str
    turns: list
    status: str
    created_at: str
