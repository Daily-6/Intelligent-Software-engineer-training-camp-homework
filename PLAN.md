# Coding Agent Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Task Completion Status

| Task | Description | Status | Commit Hash | Tests |
|------|-------------|--------|-------------|-------|
| 1 | Project scaffolding + Action data model | ✅ Done | `8796abc` | 7 |
| 2 | Config module | ✅ Done | `ca6b101` | 4 |
| 3 | LLM abstraction + MockLLMClient | ✅ Done | `38d032f` | 5 |
| 4 | Credential manager | ✅ Done | `ca6b101` | 5 |
| 5 | Memory store | ✅ Done | `ca6b101` | 7 |
| 6 | File/Shell/Test tools | ✅ Done | `38d032f` | 7 |
| 7 | Tool dispatcher | ✅ Done | `38d032f` | 5 |
| 8 | Guardrail (FOCUS) | ✅ Done | `fa1e31c` | 10 |
| 9 | Sandbox (FOCUS) | ✅ Done | `fa1e31c` | 10 |
| 10 | HITL state machine (FOCUS) | ✅ Done | `fa1e31c` | 11 |
| 11 | Governance middleware (FOCUS) | ✅ Done | `fa1e31c` | 8 |
| 12 | Feedback validator + classifier | ✅ Done | `d07e78c` | 8 |
| 13 | Agent main loop | ✅ Done | `d07e78c` | 5 |
| 14 | WebUI backend | ✅ Done | `68e9d38` | 6 |
| 15 | WebUI frontend | ✅ Done | `56e3dcb` | manual |
| 16 | CLI + config.yaml | ✅ Done | `56e3dcb` | manual |
| 17 | Mechanism demo | ✅ Done | `56e3dcb` | 4 demos |
| 18 | Dockerfile + CI | ✅ Done | `56e3dcb` + `93dbb0f` | CI pass |

**Total: 18/18 tasks complete, 98 unit tests + 4 mechanism demos pass.**

> **Implementation note:** Tasks were implemented directly (not via subagent dispatch) because the plan contained complete code for every step, making direct implementation more efficient. This deviation is recorded in `AGENT_LOG.md`. TDD was strictly followed: red (failing test) → green (implementation) → commit for every task.

**Goal:** Build a self-implemented coding agent harness with governance as the deep dimension, mock-LLM testable mechanisms, WebUI with HITL approval, and Docker distribution.

**Architecture:** Monolithic Python package with governance-as-middleware. Agent main loop calls LLM → parses Action → passes through governance chain (guardrail → sandbox → HITL) → dispatches to tools → feeds back results. All mechanisms are deterministic code testable with mock LLM.

**Tech Stack:** Python 3.12, FastAPI + uvicorn (WebUI), openai SDK (DeepSeek), keyring (credentials), pytest (testing + feedback signal), pyyaml (config)

## Global Constraints

- Python >= 3.12
- Dependencies: fastapi, uvicorn, openai, keyring, pyyaml, pytest, httpx
- All core mechanisms must be testable with mock LLM (no network, no real LLM)
- TDD strictly: red → green → refactor, no implementation before failing test
- No comments in code unless explicitly requested
- Credentials never hardcoded, never committed to git
- `.gitignore` excludes `.env`, `*.key`, `memory.json`, `__pycache__/`

## File Structure

```
harness/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── action.py          # Action, ToolResult, ShellResult, TestResult, Message, Turn, Session dataclasses
│   ├── llm.py             # LLMClient (ABC), DeepSeekClient, MockLLMClient
│   └── loop.py            # AgentLoop main loop
├── tools/
│   ├── __init__.py
│   ├── dispatcher.py      # ToolDispatcher registry + execute
│   ├── file_tools.py      # read_file, write_file, list_dir
│   ├── shell_tool.py      # execute_shell
│   └── test_tool.py       # run_tests
├── governance/
│   ├── __init__.py
│   ├── guardrail.py       # guardrail() function + GuardrailVerdict, Rule
│   ├── sandbox.py         # sandbox() function + SandboxResult, SandboxConfig
│   ├── hitl.py            # HITLStateMachine + HITLState
│   └── middleware.py      # GovernanceMiddleware chain
├── feedback/
│   ├── __init__.py
│   ├── validator.py       # Validator class
│   └── classifier.py      # FailureClassifier + FailureType
├── memory/
│   ├── __init__.py
│   └── store.py           # MemoryStore
├── webui/
│   ├── __init__.py
│   ├── app.py             # FastAPI app
│   └── static/
│       └── index.html     # Frontend SPA
├── config.py              # Config dataclasses + load_config
├── credentials.py         # CredentialManager
└── cli.py                 # CLI entry point
tests/
├── __init__.py
├── conftest.py            # Shared fixtures
├── test_action.py
├── test_config.py
├── test_llm.py
├── test_credentials.py
├── test_memory.py
├── test_tools.py
├── test_tool_dispatcher.py
├── test_guardrail.py
├── test_sandbox.py
├── test_hitl.py
├── test_governance_middleware.py
├── test_feedback.py
├── test_loop.py
└── test_webui.py
demo_mechanism.py
config.yaml
Dockerfile
.gitlab-ci.yml
pyproject.toml
```

## Dependency Graph

```
Task 1 (Action + scaffolding) ──┬── Task 3 (LLM abstraction)
                                 ├── Task 6 (Tools)
                                 └── Task 8 (Guardrail)
Task 2 (Config) ─────────────────┼── Task 9 (Sandbox)
Task 4 (Credentials) ──────────── (independent)
Task 5 (Memory) ───────────────── (independent)
Task 10 (HITL) ────────────────── (independent)

Task 6 ──── Task 7 (Dispatcher)
Task 8 + Task 9 + Task 10 ──── Task 11 (Governance middleware)
Task 6 ──── Task 12 (Feedback)
Task 3 + Task 7 + Task 11 + Task 12 + Task 5 ──── Task 13 (Main loop)
Task 13 ──── Task 14 (WebUI backend)
Task 14 ──── Task 15 (WebUI frontend)
Task 13 ──── Task 16 (CLI + config.yaml)
Task 11 + Task 12 + Task 13 ──── Task 17 (Mechanism demo)
All ──── Task 18 (Dockerfile + CI)
```

**Parallelizable:** Tasks 1,2,4,5,10 have no inter-deps. Tasks 3,6,8 after Task 1. Tasks 7,9,12 after their deps.

---

### Task 1: Project Scaffolding + Action Data Model

**Files:**
- Create: `pyproject.toml`
- Create: `harness/__init__.py`
- Create: `harness/core/__init__.py`
- Create: `harness/core/action.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_action.py`

**Interfaces:**
- Produces: `Action(tool_name, args, thought, result)`, `ToolResult(success, output, error)`, `ShellResult(success, output, error, stdout, stderr, exit_code)`, `TestResult(success, output, error, total, passed, failed, failures_detail)`, `Message(role, content)`, `Turn(action, governance_result, timestamp)`, `Session(id, task, turns, status, created_at)`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_action.py
from harness.core.action import Action, ToolResult, ShellResult, TestResult, Message, Turn, Session

def test_action_creation():
    action = Action(tool_name="read_file", args={"path": "/tmp/test.py"}, thought="read the file")
    assert action.tool_name == "read_file"
    assert action.args == {"path": "/tmp/test.py"}
    assert action.thought == "read the file"
    assert action.result is None

def test_tool_result():
    result = ToolResult(success=True, output="hello", error="")
    assert result.success is True
    assert result.output == "hello"

def test_shell_result():
    result = ShellResult(success=True, output="", error="", stdout="hello", stderr="", exit_code=0)
    assert result.exit_code == 0
    assert result.stdout == "hello"

def test_test_result():
    result = TestResult(success=False, output="", error="", total=5, passed=3, failed=2, failures_detail=[])
    assert result.total == 5
    assert result.passed == 3
    assert result.failed == 2

def test_message():
    msg = Message(role="user", content="fix the bug")
    assert msg.role == "user"
    assert msg.content == "fix the bug"

def test_turn():
    action = Action(tool_name="read_file", args={}, thought="test")
    turn = Turn(action=action, governance_result=None, timestamp="2026-07-07T10:00:00")
    assert turn.action == action
    assert turn.timestamp == "2026-07-07T10:00:00"

def test_session():
    session = Session(id="abc", task="fix bug", turns=[], status="running", created_at="2026-07-07T10:00:00")
    assert session.id == "abc"
    assert session.status == "running"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_action.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness'`

- [ ] **Step 3: Create pyproject.toml and package structure**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "coding-agent-harness"
version = "0.1.0"
description = "A self-implemented coding agent harness with governance focus"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110",
    "uvicorn>=0.29",
    "openai>=1.30",
    "keyring>=25.0",
    "pyyaml>=6.0",
    "pytest>=8.0",
    "httpx>=0.27",
]

[project.scripts]
harness = "harness.cli:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["harness*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

```python
# harness/__init__.py
__version__ = "0.1.0"
```

```python
# harness/core/__init__.py
```

```python
# tests/__init__.py
```

```python
# tests/conftest.py
import tempfile
import os
import pytest

@pytest.fixture
def tmp_workspace():
    d = tempfile.mkdtemp(prefix="harness_test_")
    yield d
```

- [ ] **Step 4: Write minimal implementation**

```python
# harness/core/action.py
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pip install -e . && pytest tests/test_action.py -v`
Expected: PASS (7 tests)

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml harness/ tests/
git commit -m "feat: project scaffolding + Action data model"
```

---

### Task 2: Config Module

**Files:**
- Create: `harness/config.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing
- Produces: `Config`, `LLMConfig`, `GovernanceConfig`, `SandboxConfig`, `FeedbackConfig`, `load_config(path) -> Config`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
from harness.config import Config, load_config, LLMConfig, GovernanceConfig, SandboxConfig, FeedbackConfig
import tempfile
import os

def test_default_config():
    config = Config.default()
    assert config.project_root == "./workspace"
    assert config.llm.provider == "deepseek"
    assert config.llm.model == "deepseek-chat"
    assert config.max_turns == 20

def test_load_config_from_yaml():
    yaml_content = """
project_root: "./test_workspace"
llm:
  provider: "deepseek"
  model: "deepseek-chat"
  max_tokens: 4096
  temperature: 0.7
governance:
  deny_patterns:
    - "rm -rf /"
  approval_patterns:
    - "git push"
  readonly_paths:
    - ".git/"
sandbox:
  command_policy: "blacklist"
  blocked_commands:
    - "sudo"
feedback:
  test_command: "pytest"
  max_retries: 3
max_turns: 15
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        f.flush()
        path = f.name
    try:
        config = load_config(path)
        assert config.project_root == "./test_workspace"
        assert config.llm.model == "deepseek-chat"
        assert config.governance.deny_patterns == ["rm -rf /"]
        assert config.governance.approval_patterns == ["git push"]
        assert config.sandbox.command_policy == "blacklist"
        assert config.sandbox.blocked_commands == ["sudo"]
        assert config.feedback.max_retries == 3
        assert config.max_turns == 15
    finally:
        os.unlink(path)

def test_load_config_missing_file_returns_default():
    config = load_config("/nonexistent/path.yaml")
    assert config.project_root == "./workspace"

def test_load_config_partial_yaml_uses_defaults():
    yaml_content = """
project_root: "./custom"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        f.flush()
        path = f.name
    try:
        config = load_config(path)
        assert config.project_root == "./custom"
        assert config.llm.provider == "deepseek"
        assert config.max_turns == 20
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.config'`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/config.py
from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class LLMConfig:
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class GovernanceConfig:
    deny_patterns: list = field(default_factory=lambda: [
        r"rm\s+-rf\s+/",
        r"drop\s+database",
        r"curl.*\|\s*sh",
        r"chmod\s+777",
        r"mkfs",
        r"dd\s+if=",
    ])
    approval_patterns: list = field(default_factory=lambda: [
        r"git\s+push",
        r"pip\s+install",
        r"npm\s+publish",
        r"docker\s+push",
    ])
    readonly_paths: list = field(default_factory=lambda: [
        ".git/",
        "README.md",
    ])


@dataclass
class SandboxConfig:
    command_policy: str = "blacklist"
    blocked_commands: list = field(default_factory=lambda: [
        "sudo",
        "shutdown",
        "reboot",
        "systemctl",
    ])
    allowed_commands: list = field(default_factory=list)


@dataclass
class FeedbackConfig:
    test_command: str = "pytest"
    max_retries: int = 3


@dataclass
class Config:
    project_root: str = "./workspace"
    llm: LLMConfig = field(default_factory=LLMConfig)
    governance: GovernanceConfig = field(default_factory=GovernanceConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    feedback: FeedbackConfig = field(default_factory=FeedbackConfig)
    max_turns: int = 20

    @classmethod
    def default(cls) -> "Config":
        return cls()


def load_config(path: str) -> Config:
    if not os.path.exists(path):
        return Config.default()
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    config = Config.default()
    if "project_root" in data:
        config.project_root = data["project_root"]
    if "max_turns" in data:
        config.max_turns = data["max_turns"]
    llm_data = data.get("llm", {})
    if llm_data:
        config.llm = LLMConfig(**llm_data)
    gov_data = data.get("governance", {})
    if gov_data:
        config.governance = GovernanceConfig(**gov_data)
    sb_data = data.get("sandbox", {})
    if sb_data:
        config.sandbox = SandboxConfig(**sb_data)
    fb_data = data.get("feedback", {})
    if fb_data:
        config.feedback = FeedbackConfig(**fb_data)
    return config
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/config.py tests/test_config.py
git commit -m "feat: config module with YAML loading"
```

---

### Task 3: LLM Abstraction Layer + MockLLMClient

**Files:**
- Create: `harness/core/llm.py`
- Create: `tests/test_llm.py`

**Interfaces:**
- Consumes: `Action`, `Message` from `harness.core.action`
- Produces: `LLMClient` (ABC), `DeepSeekClient`, `MockLLMClient`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm.py
from harness.core.llm import LLMClient, MockLLMClient, DeepSeekClient
from harness.core.action import Action, Message

def test_mock_llm_returns_scripted_actions():
    script = [
        Action(tool_name="read_file", args={"path": "test.py"}, thought="read file"),
        Action(tool_name="write_file", args={"path": "test.py", "content": "print(1)"}, thought="write file"),
        Action(tool_name="finish", args={}, thought="done"),
    ]
    client = MockLLMClient(script)
    msg = [Message(role="user", content="fix the bug")]
    a1 = client.complete(msg)
    assert a1.tool_name == "read_file"
    a2 = client.complete(msg)
    assert a2.tool_name == "write_file"
    a3 = client.complete(msg)
    assert a3.tool_name == "finish"

def test_mock_llm_conditional_branch():
    script = [
        Action(tool_name="run_tests", args={}, thought="run tests"),
        {"if_context_contains": "TEST_FAILURE", "action": Action(tool_name="write_file", args={"path": "fix.py", "content": "fixed"}, thought="fix the failure")},
        Action(tool_name="finish", args={}, thought="done"),
    ]
    client = MockLLMClient(script)
    msg = [Message(role="user", content="run tests")]
    a1 = client.complete(msg)
    assert a1.tool_name == "run_tests"
    msg.append(Message(role="tool", content="TEST_FAILURE: 2 tests failed"))
    a2 = client.complete(msg)
    assert a2.tool_name == "write_file"
    a3 = client.complete(msg)
    assert a3.tool_name == "finish"

def test_mock_llm_exhausted_raises():
    import pytest
    script = [Action(tool_name="finish", args={}, thought="done")]
    client = MockLLMClient(script)
    client.complete([Message(role="user", content="go")])
    with pytest.raises(RuntimeError, match="script exhausted"):
        client.complete([Message(role="user", content="go")])

def test_deepseek_client_is_llm_client():
    client = DeepSeekClient(api_key="fake", model="deepseek-chat")
    assert isinstance(client, LLMClient)

def test_llm_client_is_abstract():
    import pytest
    with pytest.raises(TypeError):
        LLMClient()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.core.llm'`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/core/llm.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/core/llm.py tests/test_llm.py
git commit -m "feat: LLM abstraction layer with MockLLMClient conditional branching"
```

---

### Task 4: Credential Manager

**Files:**
- Create: `harness/credentials.py`
- Create: `tests/test_credentials.py`

**Interfaces:**
- Consumes: nothing
- Produces: `CredentialManager` with `store`, `load`, `delete`, `status`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_credentials.py
from harness.credentials import CredentialManager
import tempfile
import os
import json

def test_store_and_load_credential():
    mgr = CredentialManager(backend="file", store_path=tempfile.mktemp(suffix=".json"))
    mgr.store("deepseek_api_key", "sk-test-123")
    assert mgr.load("deepseek_api_key") == "sk-test-123"

def test_status_returns_bool_not_value():
    mgr = CredentialManager(backend="file", store_path=tempfile.mktemp(suffix=".json"))
    assert mgr.status("deepseek_api_key") is False
    mgr.store("deepseek_api_key", "sk-test-123")
    assert mgr.status("deepseek_api_key") is True

def test_delete_credential():
    mgr = CredentialManager(backend="file", store_path=tempfile.mktemp(suffix=".json"))
    mgr.store("deepseek_api_key", "sk-test-123")
    mgr.delete("deepseek_api_key")
    assert mgr.status("deepseek_api_key") is False
    assert mgr.load("deepseek_api_key") is None

def test_load_nonexistent_returns_none():
    mgr = CredentialManager(backend="file", store_path=tempfile.mktemp(suffix=".json"))
    assert mgr.load("nonexistent") is None

def test_credentials_not_in_plaintext_file():
    path = tempfile.mktemp(suffix=".json")
    mgr = CredentialManager(backend="file", store_path=path)
    mgr.store("deepseek_api_key", "sk-secret-999")
    with open(path, "r") as f:
        content = f.read()
    assert "sk-secret-999" not in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_credentials.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/credentials.py
import os
import json
import base64
from typing import Optional


class CredentialManager:
    def __init__(self, backend: str = "keyring", store_path: str = None):
        self._backend = backend
        self._store_path = store_path
        if backend == "keyring":
            import keyring
            self._keyring = keyring

    def store(self, key_name: str, value: str) -> None:
        if self._backend == "keyring":
            self._keyring.set_password("coding-agent-harness", key_name, value)
        elif self._backend == "file":
            self._file_store(key_name, value)

    def load(self, key_name: str) -> Optional[str]:
        if self._backend == "keyring":
            return self._keyring.get_password("coding-agent-harness", key_name)
        elif self._backend == "file":
            return self._file_load(key_name)
        return None

    def delete(self, key_name: str) -> None:
        if self._backend == "keyring":
            try:
                self._keyring.delete_password("coding-agent-harness", key_name)
            except self._keyring.errors.PasswordDeleteError:
                pass
        elif self._backend == "file":
            self._file_delete(key_name)

    def status(self, key_name: str) -> bool:
        return self.load(key_name) is not None

    def _file_store(self, key_name: str, value: str) -> None:
        data = {}
        if os.path.exists(self._store_path):
            with open(self._store_path, "r") as f:
                data = json.load(f)
        encoded = base64.b64encode(value.encode()).decode()
        data[key_name] = encoded
        with open(self._store_path, "w") as f:
            json.dump(data, f)

    def _file_load(self, key_name: str) -> Optional[str]:
        if not os.path.exists(self._store_path):
            return None
        with open(self._store_path, "r") as f:
            data = json.load(f)
        encoded = data.get(key_name)
        if encoded is None:
            return None
        return base64.b64decode(encoded.encode()).decode()

    def _file_delete(self, key_name: str) -> None:
        if not os.path.exists(self._store_path):
            return
        with open(self._store_path, "r") as f:
            data = json.load(f)
        data.pop(key_name, None)
        with open(self._store_path, "w") as f:
            json.dump(data, f)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_credentials.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/credentials.py tests/test_credentials.py
git commit -m "feat: credential manager with keyring and file backends"
```

---

### Task 5: Memory Store

**Files:**
- Create: `harness/memory/__init__.py`
- Create: `harness/memory/store.py`
- Create: `tests/test_memory.py`

**Interfaces:**
- Consumes: `Turn` from `harness.core.action`
- Produces: `MemoryStore` with `save`, `load`, `delete`, `append_history`, `get_recent_history`, `get_conventions`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_memory.py
from harness.memory.store import MemoryStore
from harness.core.action import Action, Turn
import tempfile
import os

def test_save_and_load_convention():
    store = MemoryStore(store_path=tempfile.mktemp(suffix=".json"))
    store.save("convention", "use pytest for testing")
    assert store.load("convention") == "use pytest for testing"

def test_load_nonexistent_returns_none():
    store = MemoryStore(store_path=tempfile.mktemp(suffix=".json"))
    assert store.load("nonexistent") is None

def test_append_and_get_history():
    store = MemoryStore(store_path=tempfile.mktemp(suffix=".json"))
    action = Action(tool_name="read_file", args={}, thought="test")
    turn = Turn(action=action, governance_result=None, timestamp="2026-07-07T10:00:00")
    store.append_history(turn)
    history = store.get_recent_history(5)
    assert len(history) == 1
    assert history[0].action.tool_name == "read_file"

def test_get_recent_history_limits_n():
    store = MemoryStore(store_path=tempfile.mktemp(suffix=".json"))
    for i in range(10):
        action = Action(tool_name="read_file", args={"i": i}, thought=f"step {i}")
        store.append_history(Turn(action=action, governance_result=None, timestamp=f"2026-07-07T10:0{i}:00"))
    history = store.get_recent_history(3)
    assert len(history) == 3
    assert history[2].args["i"] == 9

def test_delete_convention():
    store = MemoryStore(store_path=tempfile.mktemp(suffix=".json"))
    store.save("key", "value")
    store.delete("key")
    assert store.load("key") is None

def test_persists_to_file():
    path = tempfile.mktemp(suffix=".json")
    store1 = MemoryStore(store_path=path)
    store1.save("convention", "use PEP8")
    store2 = MemoryStore(store_path=path)
    assert store2.load("convention") == "use PEP8"

def test_missing_file_initializes_empty():
    store = MemoryStore(store_path="/nonexistent/path.json")
    assert store.load("anything") is None
    assert store.get_recent_history(5) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_memory.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/memory/__init__.py
```

```python
# harness/memory/store.py
import json
import os
from typing import Optional
from harness.core.action import Turn


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
        from harness.core.action import Action
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
                 "governance_result": t.governance_result,
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_memory.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/memory/ tests/test_memory.py
git commit -m "feat: memory store with JSON persistence"
```

---

### Task 6: File Tools + Shell Tool + Test Tool

**Files:**
- Create: `harness/tools/__init__.py`
- Create: `harness/tools/file_tools.py`
- Create: `harness/tools/shell_tool.py`
- Create: `harness/tools/test_tool.py`
- Create: `tests/test_tools.py`

**Interfaces:**
- Consumes: `Action`, `ToolResult`, `ShellResult`, `TestResult` from `harness.core.action`
- Produces: `read_file(path, root) -> ToolResult`, `write_file(path, content, root) -> ToolResult`, `list_dir(path, root) -> ToolResult`, `execute_shell(command, cwd, timeout) -> ShellResult`, `run_tests(test_args, cwd) -> TestResult`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tools.py
import tempfile
import os
from harness.tools.file_tools import read_file, write_file, list_dir
from harness.tools.shell_tool import execute_shell
from harness.tools.test_tool import run_tests

def test_write_and_read_file():
    d = tempfile.mkdtemp()
    wr = write_file(os.path.join(d, "test.txt"), "hello world", root=d)
    assert wr.success
    rr = read_file(os.path.join(d, "test.txt"), root=d)
    assert rr.success
    assert rr.output == "hello world"

def test_read_nonexistent_file():
    d = tempfile.mkdtemp()
    rr = read_file(os.path.join(d, "nope.txt"), root=d)
    assert not rr.success
    assert "not found" in rr.error.lower() or "no such file" in rr.error.lower()

def test_list_dir():
    d = tempfile.mkdtemp()
    write_file(os.path.join(d, "a.txt"), "a", root=d)
    write_file(os.path.join(d, "b.txt"), "b", root=d)
    lr = list_dir(d, root=d)
    assert lr.success
    assert "a.txt" in lr.output
    assert "b.txt" in lr.output

def test_execute_shell_success():
    result = execute_shell("echo hello", cwd=tempfile.gettempdir())
    assert result.success
    assert "hello" in result.stdout

def test_execute_shell_failure():
    result = execute_shell("exit 1", cwd=tempfile.gettempdir())
    assert not result.success
    assert result.exit_code == 1

def test_run_tests_pass():
    d = tempfile.mkdtemp()
    test_file = os.path.join(d, "test_pass.py")
    with open(test_file, "w") as f:
        f.write("def test_ok():\n    assert True\n")
    result = run_tests("", cwd=d)
    assert result.success
    assert result.passed >= 1
    assert result.failed == 0

def test_run_tests_fail():
    d = tempfile.mkdtemp()
    test_file = os.path.join(d, "test_fail.py")
    with open(test_file, "w") as f:
        f.write("def test_bad():\n    assert False\n")
    result = run_tests("", cwd=d)
    assert not result.success
    assert result.failed >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/tools/__init__.py
```

```python
# harness/tools/file_tools.py
import os
from harness.core.action import ToolResult


def read_file(path: str, root: str = None) -> ToolResult:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return ToolResult(success=True, output=f.read())
    except FileNotFoundError:
        return ToolResult(success=False, output="", error=f"File not found: {path}")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def write_file(path: str, content: str, root: str = None) -> ToolResult:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(success=True, output=f"Wrote {len(content)} chars to {path}")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def list_dir(path: str, root: str = None) -> ToolResult:
    try:
        entries = os.listdir(path)
        return ToolResult(success=True, output="\n".join(entries))
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))
```

```python
# harness/tools/shell_tool.py
import subprocess
from harness.core.action import ShellResult


def execute_shell(command: str, cwd: str = None, timeout: int = 30) -> ShellResult:
    try:
        proc = subprocess.run(
            command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return ShellResult(
            success=proc.returncode == 0,
            output=proc.stdout,
            error=proc.stderr,
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
        )
    except subprocess.TimeoutExpired:
        return ShellResult(success=False, output="", error="timeout", stdout="", stderr="timeout", exit_code=-1)
    except Exception as e:
        return ShellResult(success=False, output="", error=str(e), stdout="", stderr=str(e), exit_code=-1)
```

```python
# harness/tools/test_tool.py
import subprocess
import json
import os
from harness.core.action import TestResult


def run_tests(test_args: str = "", cwd: str = None) -> TestResult:
    cmd = f"python -m pytest {test_args} --json-report --json-report-file=-"
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=120
        )
        try:
            report = json.loads(proc.stdout)
            total = report.get("summary", {}).get("total", 0)
            passed = report.get("summary", {}).get("passed", 0)
            failed = report.get("summary", {}).get("failed", 0)
            failures_detail = [
                {"nodeid": t.get("nodeid", ""), "outcome": t.get("outcome", "")}
                for t in report.get("tests", [])
                if t.get("outcome") != "passed"
            ]
            return TestResult(
                success=failed == 0,
                output=proc.stdout,
                error=proc.stderr,
                total=total,
                passed=passed,
                failed=failed,
                failures_detail=failures_detail,
            )
        except json.JSONDecodeError:
            return TestResult(
                success=proc.returncode == 0,
                output=proc.stdout,
                error=proc.stderr,
                total=0, passed=0, failed=0, failures_detail=[],
            )
    except subprocess.TimeoutExpired:
        return TestResult(success=False, output="", error="timeout", total=0, passed=0, failed=0, failures_detail=[])
    except Exception as e:
        return TestResult(success=False, output="", error=str(e), total=0, passed=0, failed=0, failures_detail=[])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pip install pytest-json-report && pytest tests/test_tools.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/tools/ tests/test_tools.py
git commit -m "feat: file, shell, and test tools"
```

---

### Task 7: Tool Dispatcher

**Files:**
- Create: `harness/tools/dispatcher.py`
- Create: `tests/test_tool_dispatcher.py`

**Interfaces:**
- Consumes: `Action`, `ToolResult` from `harness.core.action`; tool functions from `harness.tools`
- Produces: `ToolDispatcher` with `register(name, func)`, `execute(action, context) -> ToolResult`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tool_dispatcher.py
from harness.tools.dispatcher import ToolDispatcher
from harness.core.action import Action, ToolResult

def test_register_and_execute():
    dispatcher = ToolDispatcher()
    dispatcher.register("echo", lambda args, ctx: ToolResult(success=True, output=args.get("text", ""), error=""))
    action = Action(tool_name="echo", args={"text": "hello"}, thought="test")
    result = dispatcher.execute(action, context={})
    assert result.success
    assert result.output == "hello"

def test_unknown_tool_returns_error():
    dispatcher = ToolDispatcher()
    action = Action(tool_name="nonexistent", args={}, thought="test")
    result = dispatcher.execute(action, context={})
    assert not result.success
    assert "unknown" in result.error.lower()

def test_tool_exception_caught():
    dispatcher = ToolDispatcher()
    def bad_tool(args, ctx):
        raise ValueError("boom")
    dispatcher.register("bad", bad_tool)
    action = Action(tool_name="bad", args={}, thought="test")
    result = dispatcher.execute(action, context={})
    assert not result.success
    assert "boom" in result.error

def test_context_passed_to_tool():
    dispatcher = ToolDispatcher()
    dispatcher.register("get_ctx", lambda args, ctx: ToolResult(success=True, output=str(ctx), error=""))
    action = Action(tool_name="get_ctx", args={}, thought="test")
    result = dispatcher.execute(action, context={"root": "/tmp"})
    assert result.success
    assert "/tmp" in result.output

def test_list_registered_tools():
    dispatcher = ToolDispatcher()
    dispatcher.register("tool_a", lambda a, c: ToolResult(success=True, output="", error=""))
    dispatcher.register("tool_b", lambda a, c: ToolResult(success=True, output="", error=""))
    tools = dispatcher.list_tools()
    assert "tool_a" in tools
    assert "tool_b" in tools
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tool_dispatcher.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/tools/dispatcher.py
from harness.core.action import Action, ToolResult


class ToolDispatcher:
    def __init__(self):
        self._registry = {}

    def register(self, name: str, func) -> None:
        self._registry[name] = func

    def execute(self, action: Action, context: dict = None) -> ToolResult:
        if context is None:
            context = {}
        func = self._registry.get(action.tool_name)
        if func is None:
            return ToolResult(success=False, output="", error=f"Unknown tool: {action.tool_name}")
        try:
            return func(action.args, context)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def list_tools(self) -> list:
        return list(self._registry.keys())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tool_dispatcher.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/tools/dispatcher.py tests/test_tool_dispatcher.py
git commit -m "feat: tool dispatcher with registry"
```

---

### Task 8: Guardrail (FOCUS)

**Files:**
- Create: `harness/governance/__init__.py`
- Create: `harness/governance/guardrail.py`
- Create: `tests/test_guardrail.py`

**Interfaces:**
- Consumes: `Action` from `harness.core.action`; `GovernanceConfig` from `harness.config`
- Produces: `GuardrailVerdict` (enum), `Rule` (dataclass), `guardrail(action, rules) -> tuple[GuardrailVerdict, str]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_guardrail.py
from harness.governance.guardrail import guardrail, GuardrailVerdict, Rule
from harness.core.action import Action

def make_rules():
    return [
        Rule(pattern=r"rm\s+-rf\s+/", severity="deny", tool="execute_shell", description="rm -rf root"),
        Rule(pattern=r"drop\s+database", severity="deny", tool="execute_shell", description="drop database"),
        Rule(pattern=r"git\s+push", severity="require_approval", tool="execute_shell", description="git push"),
        Rule(pattern=r"\.env", severity="deny", tool="write_file", description="write .env"),
        Rule(pattern=r"~/.ssh/", severity="deny", tool="write_file", description="write ssh keys"),
    ]

def test_deny_rm_rf():
    action = Action(tool_name="execute_shell", args={"command": "rm -rf /"}, thought="cleanup")
    verdict, reason = guardrail(action, make_rules())
    assert verdict == GuardrailVerdict.DENY
    assert "rm -rf" in reason

def test_deny_drop_database():
    action = Action(tool_name="execute_shell", args={"command": "DROP DATABASE prod"}, thought="cleanup")
    verdict, reason = guardrail(action, make_rules())
    assert verdict == GuardrailVerdict.DENY

def test_require_approval_git_push():
    action = Action(tool_name="execute_shell", args={"command": "git push --force origin main"}, thought="push")
    verdict, reason = guardrail(action, make_rules())
    assert verdict == GuardrailVerdict.REQUIRE_APPROVAL

def test_allow_safe_command():
    action = Action(tool_name="execute_shell", args={"command": "ls -la"}, thought="list files")
    verdict, reason = guardrail(action, make_rules())
    assert verdict == GuardrailVerdict.ALLOW

def test_deny_write_env():
    action = Action(tool_name="write_file", args={"path": ".env", "content": "KEY=secret"}, thought="write env")
    verdict, reason = guardrail(action, make_rules())
    assert verdict == GuardrailVerdict.DENY

def test_allow_write_source_file():
    action = Action(tool_name="write_file", args={"path": "src/main.py", "content": "print(1)"}, thought="write code")
    verdict, reason = guardrail(action, make_rules())
    assert verdict == GuardrailVerdict.ALLOW

def test_deny_takes_priority_over_approval():
    rules = [
        Rule(pattern=r"git", severity="require_approval", tool="execute_shell", description="git"),
        Rule(pattern=r"push\s+--force", severity="deny", tool="execute_shell", description="force push"),
    ]
    action = Action(tool_name="execute_shell", args={"command": "git push --force"}, thought="push")
    verdict, reason = guardrail(action, rules)
    assert verdict == GuardrailVerdict.DENY

def test_no_rules_defaults_allow():
    action = Action(tool_name="execute_shell", args={"command": "anything"}, thought="test")
    verdict, reason = guardrail(action, [])
    assert verdict == GuardrailVerdict.ALLOW

def test_rule_only_matches_specified_tool():
    rules = [Rule(pattern=r"test", severity="deny", tool="write_file", description="test")]
    action = Action(tool_name="execute_shell", args={"command": "test"}, thought="test")
    verdict, reason = guardrail(action, rules)
    assert verdict == GuardrailVerdict.ALLOW

def test_invalid_regex_skipped():
    rules = [Rule(pattern=r"[invalid", severity="deny", tool="execute_shell", description="bad regex")]
    action = Action(tool_name="execute_shell", args={"command": "ls"}, thought="test")
    verdict, reason = guardrail(action, rules)
    assert verdict == GuardrailVerdict.ALLOW
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_guardrail.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/governance/__init__.py
```

```python
# harness/governance/guardrail.py
import re
from enum import Enum
from dataclasses import dataclass
from harness.core.action import Action


class GuardrailVerdict(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class Rule:
    pattern: str
    severity: str
    tool: str
    description: str


def _get_action_text(action: Action) -> str:
    if action.tool_name == "execute_shell":
        return action.args.get("command", "")
    elif action.tool_name == "write_file":
        return action.args.get("path", "")
    elif action.tool_name == "read_file":
        return action.args.get("path", "")
    elif action.tool_name == "list_dir":
        return action.args.get("path", "")
    else:
        return str(action.args)


def guardrail(action: Action, rules: list) -> tuple:
    text = _get_action_text(action)
    deny_matched = None
    approval_matched = None
    for rule in rules:
        if rule.tool != action.tool_name:
            continue
        try:
            if re.search(rule.pattern, text):
                if rule.severity == "deny":
                    deny_matched = rule
                    break
                elif rule.severity == "require_approval" and approval_matched is None:
                    approval_matched = rule
        except re.error:
            continue
    if deny_matched:
        return GuardrailVerdict.DENY, f"Denied by rule: {deny_matched.description}"
    if approval_matched:
        return GuardrailVerdict.REQUIRE_APPROVAL, f"Approval required: {approval_matched.description}"
    return GuardrailVerdict.ALLOW, ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_guardrail.py -v`
Expected: PASS (10 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/governance/ tests/test_guardrail.py
git commit -m "feat: guardrail with rule-based dangerous action detection"
```

---

### Task 9: Sandbox (FOCUS)

**Files:**
- Create: `harness/governance/sandbox.py`
- Create: `tests/test_sandbox.py`

**Interfaces:**
- Consumes: `Action` from `harness.core.action`; `SandboxConfig` from `harness.config`
- Produces: `SandboxResult` (dataclass), `sandbox(action, config, project_root) -> SandboxResult`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sandbox.py
import os
import tempfile
from harness.governance.sandbox import sandbox, SandboxResult
from harness.core.action import Action
from harness.config import SandboxConfig

def test_allow_file_in_project_root():
    d = tempfile.mkdtemp()
    action = Action(tool_name="write_file", args={"path": os.path.join(d, "src/main.py"), "content": "x"}, thought="write")
    result = sandbox(action, SandboxConfig(), project_root=d)
    assert result.allowed

def test_deny_path_traversal():
    d = tempfile.mkdtemp()
    action = Action(tool_name="write_file", args={"path": os.path.join(d, "../etc/passwd"), "content": "x"}, thought="write")
    result = sandbox(action, SandboxConfig(), project_root=d)
    assert not result.allowed
    assert "outside" in result.reason.lower() or "traversal" in result.reason.lower()

def test_deny_absolute_path_outside_root():
    d = tempfile.mkdtemp()
    action = Action(tool_name="write_file", args={"path": "/etc/passwd", "content": "x"}, thought="write")
    result = sandbox(action, SandboxConfig(), project_root=d)
    assert not result.allowed

def test_deny_readonly_path():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, ".git"), exist_ok=True)
    config = SandboxConfig()
    from harness.config import GovernanceConfig
    action = Action(tool_name="write_file", args={"path": os.path.join(d, ".git/config"), "content": "x"}, thought="write")
    result = sandbox(action, config, project_root=d, readonly_paths=[".git/"])
    assert not result.allowed
    assert "readonly" in result.reason.lower() or "read-only" in result.reason.lower()

def test_allow_read_readonly_path():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, ".git"), exist_ok=True)
    action = Action(tool_name="read_file", args={"path": os.path.join(d, ".git/config")}, thought="read")
    result = sandbox(action, SandboxConfig(), project_root=d, readonly_paths=[".git/"])
    assert result.allowed

def test_deny_blocked_command():
    action = Action(tool_name="execute_shell", args={"command": "sudo rm file"}, thought="cleanup")
    config = SandboxConfig(command_policy="blacklist", blocked_commands=["sudo", "shutdown"])
    result = sandbox(action, config, project_root="/tmp")
    assert not result.allowed
    assert "blocked" in result.reason.lower()

def test_allow_non_blocked_command():
    action = Action(tool_name="execute_shell", args={"command": "ls -la"}, thought="list")
    config = SandboxConfig(command_policy="blacklist", blocked_commands=["sudo"])
    result = sandbox(action, config, project_root="/tmp")
    assert result.allowed

def test_whitelist_allows_listed():
    action = Action(tool_name="execute_shell", args={"command": "git status"}, thought="status")
    config = SandboxConfig(command_policy="whitelist", allowed_commands=["git", "ls", "echo"])
    result = sandbox(action, config, project_root="/tmp")
    assert result.allowed

def test_whitelist_denies_unlisted():
    action = Action(tool_name="execute_shell", args={"command": "rm file"}, thought="remove")
    config = SandboxConfig(command_policy="whitelist", allowed_commands=["git", "ls"])
    result = sandbox(action, config, project_root="/tmp")
    assert not result.allowed

def test_non_file_non_shell_action_allowed():
    action = Action(tool_name="run_tests", args={}, thought="test")
    result = sandbox(action, SandboxConfig(), project_root="/tmp")
    assert result.allowed
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sandbox.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/governance/sandbox.py
import os
from dataclasses import dataclass
from harness.core.action import Action
from harness.config import SandboxConfig


@dataclass
class SandboxResult:
    allowed: bool
    reason: str = ""


def sandbox(action: Action, config: SandboxConfig, project_root: str, readonly_paths: list = None) -> SandboxResult:
    if readonly_paths is None:
        readonly_paths = []
    if action.tool_name in ("read_file", "write_file", "list_dir"):
        return _check_file(action, project_root, readonly_paths)
    elif action.tool_name == "execute_shell":
        return _check_shell(action, config)
    else:
        return SandboxResult(allowed=True)


def _check_file(action: Action, project_root: str, readonly_paths: list) -> SandboxResult:
    path = action.args.get("path", "")
    if not path:
        return SandboxResult(allowed=True)
    real_path = os.path.realpath(path)
    real_root = os.path.realpath(project_root)
    if not real_path.startswith(real_root):
        return SandboxResult(allowed=False, reason=f"Path outside project root: {path}")
    if action.tool_name == "write_file":
        rel_path = os.path.relpath(real_path, real_root)
        for ro in readonly_paths:
            ro_clean = ro.rstrip("/")
            if rel_path == ro_clean or rel_path.startswith(ro_clean + os.sep) or rel_path.startswith(ro_clean + "/"):
                return SandboxResult(allowed=False, reason=f"Read-only path: {ro}")
    return SandboxResult(allowed=True)


def _check_shell(action: Action, config: SandboxConfig) -> SandboxResult:
    command = action.args.get("command", "")
    if not command:
        return SandboxResult(allowed=True)
    first_word = command.strip().split()[0] if command.strip() else ""
    if config.command_policy == "blacklist":
        for blocked in config.blocked_commands:
            if blocked in command:
                return SandboxResult(allowed=False, reason=f"Blocked command: {blocked}")
    elif config.command_policy == "whitelist":
        if first_word and first_word not in config.allowed_commands:
            return SandboxResult(allowed=False, reason=f"Command not in whitelist: {first_word}")
    return SandboxResult(allowed=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_sandbox.py -v`
Expected: PASS (10 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/governance/sandbox.py tests/test_sandbox.py
git commit -m "feat: sandbox with path fence and command boundary"
```

---

### Task 10: HITL State Machine (FOCUS)

**Files:**
- Create: `harness/governance/hitl.py`
- Create: `tests/test_hitl.py`

**Interfaces:**
- Consumes: nothing
- Produces: `HITLState` (enum), `HITLStateMachine` with `request_approval`, `approve`, `deny`, `current_state`, `reset`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hitl.py
from harness.governance.hitl import HITLState, HITLStateMachine

def test_initial_state_running():
    sm = HITLStateMachine()
    assert sm.current_state() == HITLState.RUNNING

def test_request_approval_transitions_to_pending():
    sm = HITLStateMachine()
    sm.request_approval()
    assert sm.current_state() == HITLState.PENDING_APPROVAL

def test_approve_transitions_back_to_running():
    sm = HITLStateMachine()
    sm.request_approval()
    sm.approve()
    assert sm.current_state() == HITLState.RUNNING

def test_deny_transitions_back_to_running():
    sm = HITLStateMachine()
    sm.request_approval()
    sm.deny("too dangerous")
    assert sm.current_state() == HITLState.RUNNING
    assert sm.get_deny_reason() == "too dangerous"

def test_stop_transitions_to_stopped():
    sm = HITLStateMachine()
    sm.stop()
    assert sm.current_state() == HITLState.STOPPED

def test_approve_without_pending_raises():
    import pytest
    sm = HITLStateMachine()
    with pytest.raises(RuntimeError, match="cannot approve"):
        sm.approve()

def test_deny_without_pending_raises():
    import pytest
    sm = HITLStateMachine()
    with pytest.raises(RuntimeError, match="cannot deny"):
        sm.deny("nope")

def test_request_approval_when_not_running_raises():
    import pytest
    sm = HITLStateMachine()
    sm.request_approval()
    with pytest.raises(RuntimeError, match="cannot request"):
        sm.request_approval()

def test_timeout_denies():
    sm = HITLStateMachine(timeout_seconds=0)
    sm.request_approval()
    import time
    time.sleep(0.1)
    assert sm.current_state() == HITLState.RUNNING
    assert sm.get_deny_reason() is not None
    assert "timeout" in sm.get_deny_reason().lower()

def test_reset():
    sm = HITLStateMachine()
    sm.request_approval()
    sm.reset()
    assert sm.current_state() == HITLState.RUNNING
    assert sm.get_deny_reason() is None

def test_is_pending():
    sm = HITLStateMachine()
    assert not sm.is_pending()
    sm.request_approval()
    assert sm.is_pending()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hitl.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/governance/hitl.py
import time
from enum import Enum


class HITLState(Enum):
    RUNNING = "running"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DENIED = "denied"
    STOPPED = "stopped"


class HITLStateMachine:
    def __init__(self, timeout_seconds: int = 300):
        self._state = HITLState.RUNNING
        self._deny_reason = None
        self._timeout = timeout_seconds
        self._pending_since = None

    def current_state(self) -> HITLState:
        if self._state == HITLState.PENDING_APPROVAL and self._pending_since is not None:
            elapsed = time.time() - self._pending_since
            if elapsed > self._timeout:
                self._deny_reason = "Approval timed out"
                self._state = HITLState.RUNNING
        return self._state

    def request_approval(self) -> None:
        if self.current_state() != HITLState.RUNNING:
            raise RuntimeError(f"cannot request approval from state {self._state}")
        self._state = HITLState.PENDING_APPROVAL
        self._pending_since = time.time()
        self._deny_reason = None

    def approve(self) -> None:
        if self.current_state() != HITLState.PENDING_APPROVAL:
            raise RuntimeError(f"cannot approve from state {self._state}")
        self._state = HITLState.RUNNING
        self._pending_since = None

    def deny(self, reason: str = "") -> None:
        if self.current_state() != HITLState.PENDING_APPROVAL:
            raise RuntimeError(f"cannot deny from state {self._state}")
        self._state = HITLState.RUNNING
        self._deny_reason = reason or "Denied by user"
        self._pending_since = None

    def stop(self) -> None:
        self._state = HITLState.STOPPED
        self._pending_since = None

    def reset(self) -> None:
        self._state = HITLState.RUNNING
        self._deny_reason = None
        self._pending_since = None

    def is_pending(self) -> bool:
        return self.current_state() == HITLState.PENDING_APPROVAL

    def get_deny_reason(self):
        return self._deny_reason
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hitl.py -v`
Expected: PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/governance/hitl.py tests/test_hitl.py
git commit -m "feat: HITL state machine with timeout"
```

---

### Task 11: Governance Middleware (FOCUS)

**Files:**
- Create: `harness/governance/middleware.py`
- Create: `tests/test_governance_middleware.py`

**Interfaces:**
- Consumes: `guardrail`, `GuardrailVerdict` from `harness.governance.guardrail`; `sandbox`, `SandboxResult` from `harness.governance.sandbox`; `HITLStateMachine` from `harness.governance.hitl`; `Action` from `harness.core.action`; `Config` from `harness.config`
- Produces: `GovernanceResult` (dataclass), `GovernanceMiddleware` with `process(action) -> GovernanceResult`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_governance_middleware.py
import os
import tempfile
from harness.governance.middleware import GovernanceMiddleware, GovernanceResult
from harness.governance.guardrail import Rule
from harness.core.action import Action
from harness.config import Config, SandboxConfig

def make_middleware(root=None, rules=None):
    if root is None:
        root = tempfile.mkdtemp()
    if rules is None:
        rules = [
            Rule(pattern=r"rm\s+-rf\s+/", severity="deny", tool="execute_shell", description="rm -rf"),
            Rule(pattern=r"git\s+push", severity="require_approval", tool="execute_shell", description="git push"),
        ]
    config = Config.default()
    config.project_root = root
    config.sandbox = SandboxConfig(command_policy="blacklist", blocked_commands=["sudo"])
    mw = GovernanceMiddleware(rules=rules, sandbox_config=config.sandbox, project_root=root, readonly_paths=[".git/"])
    return mw

def test_allow_safe_action():
    mw = make_middleware()
    action = Action(tool_name="read_file", args={"path": os.path.join(mw._project_root, "test.py")}, thought="read")
    result = mw.process(action)
    assert not result.blocked

def test_deny_dangerous_command():
    mw = make_middleware()
    action = Action(tool_name="execute_shell", args={"command": "rm -rf /"}, thought="cleanup")
    result = mw.process(action)
    assert result.blocked
    assert "Denied" in result.reason

def test_require_approval_then_approve():
    mw = make_middleware()
    action = Action(tool_name="execute_shell", args={"command": "git push origin main"}, thought="push")
    result = mw.process(action)
    assert result.blocked
    assert "pending" in result.reason.lower() or "approval" in result.reason.lower()
    mw.approve()
    result2 = mw.process(action)
    assert not result2.blocked

def test_require_approval_then_deny():
    mw = make_middleware()
    action = Action(tool_name="execute_shell", args={"command": "git push origin main"}, thought="push")
    result = mw.process(action)
    assert result.blocked
    mw.deny("no pushing")
    result2 = mw.process(action)
    assert result2.blocked
    assert "Denied by user" in result2.reason or "no pushing" in result2.reason

def test_sandbox_blocks_path_traversal():
    mw = make_middleware()
    action = Action(tool_name="write_file", args={"path": os.path.join(mw._project_root, "../etc/passwd"), "content": "x"}, thought="write")
    result = mw.process(action)
    assert result.blocked
    assert "outside" in result.reason.lower()

def test_sandbox_blocks_blocked_command():
    mw = make_middleware()
    action = Action(tool_name="execute_shell", args={"command": "sudo ls"}, thought="list")
    result = mw.process(action)
    assert result.blocked
    assert "blocked" in result.reason.lower()

def test_readonly_path_blocked_for_write():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, ".git"), exist_ok=True)
    mw = make_middleware(root=d)
    action = Action(tool_name="write_file", args={"path": os.path.join(d, ".git/config"), "content": "x"}, thought="write")
    result = mw.process(action)
    assert result.blocked
    assert "readonly" in result.reason.lower() or "read-only" in result.reason.lower()

def test_deny_takes_priority_over_approval():
    rules = [
        Rule(pattern=r"git\s+push\s+--force", severity="deny", tool="execute_shell", description="force push denied"),
        Rule(pattern=r"git\s+push", severity="require_approval", tool="execute_shell", description="git push"),
    ]
    mw = make_middleware(rules=rules)
    action = Action(tool_name="execute_shell", args={"command": "git push --force"}, thought="push")
    result = mw.process(action)
    assert result.blocked
    assert "Denied" in result.reason
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_governance_middleware.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/governance/middleware.py
from dataclasses import dataclass
from harness.core.action import Action
from harness.governance.guardrail import guardrail, GuardrailVerdict, Rule
from harness.governance.sandbox import sandbox, SandboxResult
from harness.governance.hitl import HITLStateMachine
from harness.config import SandboxConfig


@dataclass
class GovernanceResult:
    blocked: bool
    reason: str = ""
    verdict: GuardrailVerdict = GuardrailVerdict.ALLOW


class GovernanceMiddleware:
    def __init__(self, rules: list, sandbox_config: SandboxConfig, project_root: str, readonly_paths: list = None):
        self._rules = rules
        self._sandbox_config = sandbox_config
        self._project_root = project_root
        self._readonly_paths = readonly_paths or []
        self._hitl = HITLStateMachine()
        self._pending_action = None

    def process(self, action: Action) -> GovernanceResult:
        verdict, reason = guardrail(action, self._rules)
        if verdict == GuardrailVerdict.DENY:
            return GovernanceResult(blocked=True, reason=f"Denied by guardrail: {reason}", verdict=verdict)
        if verdict == GuardrailVerdict.REQUIRE_APPROVAL:
            if not self._hitl.is_pending():
                self._hitl.request_approval()
                self._pending_action = action
                return GovernanceResult(blocked=True, reason=f"Pending approval: {reason}", verdict=verdict)
        if self._hitl.is_pending():
            return GovernanceResult(blocked=True, reason="Pending approval: waiting for user decision", verdict=GuardrailVerdict.REQUIRE_APPROVAL)
        sb_result = sandbox(action, self._sandbox_config, self._project_root, self._readonly_paths)
        if not sb_result.allowed:
            return GovernanceResult(blocked=True, reason=f"Blocked by sandbox: {sb_result.reason}", verdict=GuardrailVerdict.ALLOW)
        return GovernanceResult(blocked=False, verdict=GuardrailVerdict.ALLOW)

    def approve(self) -> None:
        self._hitl.approve()
        self._pending_action = None

    def deny(self, reason: str = "") -> None:
        self._hitl.deny(reason)

    def is_pending(self) -> bool:
        return self._hitl.is_pending()

    def get_pending_action(self):
        return self._pending_action
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_governance_middleware.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/governance/middleware.py tests/test_governance_middleware.py
git commit -m "feat: governance middleware chaining guardrail-sandbox-hitl"
```

---

### Task 12: Feedback Validator + Classifier

**Files:**
- Create: `harness/feedback/__init__.py`
- Create: `harness/feedback/validator.py`
- Create: `harness/feedback/classifier.py`
- Create: `tests/test_feedback.py`

**Interfaces:**
- Consumes: `TestResult` from `harness.core.action`; `run_tests` from `harness.tools.test_tool`
- Produces: `Validator` with `run(test_args, cwd) -> TestResult`; `FailureType` (enum), `FailureClassifier` with `classify(result) -> tuple[FailureType, str]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_feedback.py
import tempfile
import os
from harness.feedback.validator import Validator
from harness.feedback.classifier import FailureClassifier, FailureType
from harness.core.action import TestResult

def test_validator_runs_passing_tests():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "test_ok.py"), "w") as f:
        f.write("def test_ok():\n    assert True\n")
    v = Validator()
    result = v.run("", cwd=d)
    assert result.success
    assert result.passed >= 1

def test_validator_runs_failing_tests():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "test_bad.py"), "w") as f:
        f.write("def test_bad():\n    assert False\n")
    v = Validator()
    result = v.run("", cwd=d)
    assert not result.success
    assert result.failed >= 1

def test_classifier_pass():
    result = TestResult(success=True, output="", error="", total=3, passed=3, failed=0, failures_detail=[])
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.PASS

def test_classifier_syntax_error():
    result = TestResult(
        success=False, output="", error="SyntaxError: invalid syntax",
        total=1, passed=0, failed=1, failures_detail=[{"nodeid": "test.py", "outcome": "failed"}]
    )
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.SYNTAX_ERROR

def test_classifier_import_error():
    result = TestResult(
        success=False, output="", error="ModuleNotFoundError: No module named 'foo'",
        total=1, passed=0, failed=1, failures_detail=[]
    )
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.IMPORT_ERROR

def test_classifier_test_failure():
    result = TestResult(
        success=False, output="", error="AssertionError: assert 1 == 2",
        total=1, passed=0, failed=1, failures_detail=[{"nodeid": "test.py::test_eq", "outcome": "failed"}]
    )
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.TEST_FAILURE

def test_classifier_timeout():
    result = TestResult(
        success=False, output="", error="timeout",
        total=0, passed=0, failed=0, failures_detail=[]
    )
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.TIMEOUT

def test_classifier_unknown():
    result = TestResult(
        success=False, output="", error="some weird error",
        total=0, passed=0, failed=0, failures_detail=[]
    )
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.UNKNOWN
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_feedback.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/feedback/__init__.py
```

```python
# harness/feedback/validator.py
from harness.core.action import TestResult
from harness.tools.test_tool import run_tests


class Validator:
    def run(self, test_args: str = "", cwd: str = None) -> TestResult:
        return run_tests(test_args, cwd=cwd)
```

```python
# harness/feedback/classifier.py
from enum import Enum
from harness.core.action import TestResult


class FailureType(Enum):
    PASS = "pass"
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    TEST_FAILURE = "test_failure"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class FailureClassifier:
    def classify(self, result: TestResult) -> tuple:
        if result.success:
            return FailureType.PASS, "All tests passed"
        error = result.error.lower() + " " + result.output.lower()
        if "syntaxerror" in error:
            return FailureType.SYNTAX_ERROR, "Syntax error detected"
        if "modulenotfounderror" in error or "importerror" in error:
            return FailureType.IMPORT_ERROR, "Import error detected"
        if "timeout" in error:
            return FailureType.TIMEOUT, "Test timed out"
        if result.failed > 0:
            return FailureType.TEST_FAILURE, f"{result.failed} test(s) failed"
        return FailureType.UNKNOWN, "Unknown failure"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_feedback.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/feedback/ tests/test_feedback.py
git commit -m "feat: feedback validator and failure classifier"
```

---

### Task 13: Agent Main Loop

**Files:**
- Create: `harness/core/loop.py`
- Create: `tests/test_loop.py`

**Interfaces:**
- Consumes: `LLMClient` from `harness.core.llm`; `ToolDispatcher` from `harness.tools.dispatcher`; `GovernanceMiddleware` from `harness.governance.middleware`; `Validator` from `harness.feedback.validator`; `MemoryStore` from `harness.memory.store`; `Action`, `Message`, `Turn` from `harness.core.action`
- Produces: `AgentLoop` with `run(task) -> Session`, `stop()`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_loop.py
import tempfile
import os
from harness.core.loop import AgentLoop
from harness.core.llm import MockLLMClient
from harness.core.action import Action, Message
from harness.tools.dispatcher import ToolDispatcher
from harness.tools.file_tools import read_file, write_file
from harness.governance.middleware import GovernanceMiddleware
from harness.governance.guardrail import Rule
from harness.config import Config, SandboxConfig
from harness.memory.store import MemoryStore

def make_loop(script, root=None):
    if root is None:
        root = tempfile.mkdtemp()
    llm = MockLLMClient(script)
    dispatcher = ToolDispatcher()
    dispatcher.register("read_file", lambda args, ctx: read_file(args["path"], root))
    dispatcher.register("write_file", lambda args, ctx: write_file(args["path"], args["content"], root))
    dispatcher.register("finish", lambda args, ctx: type("R", (), {"success": True, "output": "finished", "error": ""})())
    rules = [
        Rule(pattern=r"rm\s+-rf\s+/", severity="deny", tool="execute_shell", description="rm -rf"),
    ]
    config = Config.default()
    config.project_root = root
    config.sandbox = SandboxConfig(command_policy="blacklist", blocked_commands=["sudo"])
    mw = GovernanceMiddleware(rules=rules, sandbox_config=config.sandbox, project_root=root, readonly_paths=[".git/"])
    memory = MemoryStore(store_path=os.path.join(root, "memory.json"))
    return AgentLoop(llm=llm, dispatcher=dispatcher, governance=mw, memory=memory, config=config), root

def test_loop_completes_simple_task():
    script = [
        Action(tool_name="write_file", args={"path": "test.txt", "content": "hello"}, thought="write file"),
        Action(tool_name="finish", args={}, thought="done"),
    ]
    loop, root = make_loop(script)
    session = loop.run("write hello to test.txt")
    assert session.status == "completed"
    assert len(session.turns) == 2

def test_loop_stops_on_max_turns():
    script = [Action(tool_name="write_file", args={"path": "x.txt", "content": "x"}, thought="loop") for _ in range(50)]
    loop, root = make_loop(script)
    loop._config.max_turns = 3
    session = loop.run("infinite loop")
    assert session.status == "stopped"

def test_loop_blocked_action_feeds_back_to_llm():
    script = [
        Action(tool_name="execute_shell", args={"command": "rm -rf /"}, thought="cleanup"),
        Action(tool_name="finish", args={}, thought="ok I won't"),
    ]
    loop, root = make_loop(script)
    loop._dispatcher.register("execute_shell", lambda args, ctx: type("R", (), {"success": True, "output": "", "error": ""})())
    session = loop.run("cleanup")
    assert session.status == "completed"
    assert len(session.turns) == 2
    assert "Denied" in session.turns[0].governance_result.reason

def test_loop_records_turns():
    script = [
        Action(tool_name="write_file", args={"path": "a.txt", "content": "a"}, thought="write a"),
        Action(tool_name="finish", args={}, thought="done"),
    ]
    loop, root = make_loop(script)
    session = loop.run("write a")
    assert len(session.turns) == 2
    assert session.turns[0].action.tool_name == "write_file"
    assert session.turns[1].action.tool_name == "finish"

def test_loop_finish_action_stops():
    script = [
        Action(tool_name="finish", args={}, thought="done immediately"),
    ]
    loop, root = make_loop(script)
    session = loop.run("do nothing")
    assert session.status == "completed"
    assert len(session.turns) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_loop.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/core/loop.py
import uuid
from datetime import datetime
from harness.core.action import Action, Message, Turn, Session, ToolResult
from harness.core.llm import LLMClient
from harness.tools.dispatcher import ToolDispatcher
from harness.governance.middleware import GovernanceMiddleware
from harness.memory.store import MemoryStore
from harness.config import Config


class AgentLoop:
    def __init__(self, llm: LLMClient, dispatcher: ToolDispatcher, governance: GovernanceMiddleware, memory: MemoryStore, config: Config):
        self._llm = llm
        self._dispatcher = dispatcher
        self._governance = governance
        self._memory = memory
        self._config = config
        self._stopped = False

    def run(self, task: str) -> Session:
        session_id = str(uuid.uuid4())[:8]
        session = Session(
            id=session_id,
            task=task,
            turns=[],
            status="running",
            created_at=datetime.now().isoformat(),
        )
        messages = [
            Message(role="system", content=self._system_prompt()),
            Message(role="user", content=task),
        ]
        conventions = self._memory.get_conventions()
        if conventions:
            messages.insert(1, Message(role="system", content=f"Project conventions: {conventions}"))
        turn_count = 0
        while turn_count < self._config.max_turns and not self._stopped:
            action = self._llm.complete(messages)
            gov_result = self._governance.process(action)
            turn = Turn(
                action=action,
                governance_result=gov_result,
                timestamp=datetime.now().isoformat(),
            )
            session.turns.append(turn)
            self._memory.append_history(turn)
            if gov_result.blocked:
                messages.append(Message(role="assistant", content=f"Action: {action.tool_name}({action.args}) - {action.thought}"))
                messages.append(Message(role="tool", content=f"BLOCKED: {gov_result.reason}"))
                turn_count += 1
                continue
            if action.tool_name == "finish":
                action.result = ToolResult(success=True, output="Task completed")
                session.status = "completed"
                break
            result = self._dispatcher.execute(action, context={"root": self._config.project_root})
            action.result = result
            messages.append(Message(role="assistant", content=f"Action: {action.tool_name}({action.args}) - {action.thought}"))
            messages.append(Message(role="tool", content=f"Result: success={result.success}, output={result.output}, error={result.error}"))
            turn_count += 1
        if session.status == "running":
            session.status = "stopped"
        return session

    def stop(self):
        self._stopped = True

    def _system_prompt(self) -> str:
        return (
            "You are a coding agent. Output a JSON action with fields: tool, args, thought. "
            "Available tools: read_file, write_file, list_dir, execute_shell, run_tests, finish. "
            "Use 'finish' when the task is complete."
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_loop.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/core/loop.py tests/test_loop.py
git commit -m "feat: agent main loop with governance and feedback"
```

---

### Task 14: WebUI Backend

**Files:**
- Create: `harness/webui/__init__.py`
- Create: `harness/webui/app.py`
- Create: `tests/test_webui.py`

**Interfaces:**
- Consumes: `AgentLoop` from `harness.core.loop`; `GovernanceMiddleware` from `harness.governance.middleware`; `Config` from `harness.config`
- Produces: FastAPI `app` with endpoints: `POST /api/sessions`, `GET /api/sessions/{id}`, `POST /api/sessions/{id}/approve`, `POST /api/sessions/{id}/deny`, `POST /api/sessions/{id}/stop`, `WS /ws/sessions/{id}`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_webui.py
from fastapi.testclient import TestClient
from harness.webui.app import create_app

def test_create_session():
    app = create_app()
    client = TestClient(app)
    response = client.post("/api/sessions", json={"task": "test task"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] in ["running", "completed", "stopped"]

def test_get_session():
    app = create_app()
    client = TestClient(app)
    create_resp = client.post("/api/sessions", json={"task": "test"})
    sid = create_resp.json()["id"]
    response = client.get(f"/api/sessions/{sid}")
    assert response.status_code == 200
    assert response.json()["id"] == sid

def test_get_nonexistent_session_404():
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/sessions/nonexistent")
    assert response.status_code == 404

def test_stop_session():
    app = create_app()
    client = TestClient(app)
    create_resp = client.post("/api/sessions", json={"task": "test"})
    sid = create_resp.json()["id"]
    response = client.post(f"/api/sessions/{sid}/stop")
    assert response.status_code == 200

def test_approve_without_pending_returns_409():
    app = create_app()
    client = TestClient(app)
    create_resp = client.post("/api/sessions", json={"task": "test"})
    sid = create_resp.json()["id"]
    response = client.post(f"/api/sessions/{sid}/approve")
    assert response.status_code == 409

def test_deny_without_pending_returns_409():
    app = create_app()
    client = TestClient(app)
    create_resp = client.post("/api/sessions", json={"task": "test"})
    sid = create_resp.json()["id"]
    response = client.post(f"/api/sessions/{sid}/deny", json={"reason": "no"})
    assert response.status_code == 409
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_webui.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# harness/webui/__init__.py
```

```python
# harness/webui/app.py
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import threading
import uuid

from harness.core.loop import AgentLoop
from harness.core.llm import MockLLMClient
from harness.core.action import Action
from harness.tools.dispatcher import ToolDispatcher
from harness.tools.file_tools import read_file, write_file, list_dir
from harness.governance.middleware import GovernanceMiddleware
from harness.governance.guardrail import Rule
from harness.config import Config, SandboxConfig
from harness.memory.store import MemoryStore


class TaskRequest(BaseModel):
    task: str


class DenyRequest(BaseModel):
    reason: str = ""


_sessions = {}
_lock = threading.Lock()


def _create_loop(config: Config) -> AgentLoop:
    root = config.project_root
    import os
    os.makedirs(root, exist_ok=True)
    script = [Action(tool_name="finish", args={}, thought="done")]
    llm = MockLLMClient(script)
    dispatcher = ToolDispatcher()
    dispatcher.register("read_file", lambda args, ctx: read_file(args["path"], root))
    dispatcher.register("write_file", lambda args, ctx: write_file(args["path"], args["content"], root))
    dispatcher.register("list_dir", lambda args, ctx: list_dir(args["path"], root))
    dispatcher.register("finish", lambda args, ctx: type("R", (), {"success": True, "output": "finished", "error": ""})())
    rules = [
        Rule(pattern=r"rm\s+-rf\s+/", severity="deny", tool="execute_shell", description="rm -rf"),
        Rule(pattern=r"git\s+push", severity="require_approval", tool="execute_shell", description="git push"),
    ]
    mw = GovernanceMiddleware(rules=rules, sandbox_config=config.sandbox, project_root=root, readonly_paths=[".git/"])
    memory = MemoryStore()
    return AgentLoop(llm=llm, dispatcher=dispatcher, governance=mw, memory=memory, config=config)


def create_app(config: Config = None) -> FastAPI:
    if config is None:
        config = Config.default()
    app = FastAPI(title="Coding Agent Harness")

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        index_path = static_dir / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return "<html><body><h1>Coding Agent Harness</h1><p>WebUI loading...</p></body></html>"

    @app.post("/api/sessions")
    async def create_session(req: TaskRequest):
        sid = str(uuid.uuid4())[:8]
        loop = _create_loop(config)
        with _lock:
            _sessions[sid] = {"loop": loop, "session": None, "status": "running"}
        def run_task():
            session = loop.run(req.task)
            with _lock:
                _sessions[sid]["session"] = session
                _sessions[sid]["status"] = session.status
        t = threading.Thread(target=run_task, daemon=True)
        t.start()
        return {"id": sid, "status": "running", "task": req.task}

    @app.get("/api/sessions/{sid}")
    async def get_session(sid: str):
        with _lock:
            if sid not in _sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            data = _sessions[sid]
        session = data.get("session")
        if session:
            return {
                "id": session.id,
                "task": session.task,
                "status": session.status,
                "turns": [
                    {"action": {"tool_name": t.action.tool_name, "args": t.action.args, "thought": t.action.thought},
                     "governance": {"blocked": t.governance_result.blocked, "reason": t.governance_result.reason} if t.governance_result else None,
                     "timestamp": t.timestamp}
                    for t in session.turns
                ],
            }
        return {"id": sid, "status": data["status"], "turns": []}

    @app.post("/api/sessions/{sid}/approve")
    async def approve_action(sid: str):
        with _lock:
            if sid not in _sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            loop = _sessions[sid]["loop"]
        if not loop._governance.is_pending():
            raise HTTPException(status_code=409, detail="No pending approval")
        loop._governance.approve()
        return {"status": "approved"}

    @app.post("/api/sessions/{sid}/deny")
    async def deny_action(sid: str, req: DenyRequest = None):
        with _lock:
            if sid not in _sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            loop = _sessions[sid]["loop"]
        if not loop._governance.is_pending():
            raise HTTPException(status_code=409, detail="No pending approval")
        reason = req.reason if req else ""
        loop._governance.deny(reason)
        return {"status": "denied", "reason": reason}

    @app.post("/api/sessions/{sid}/stop")
    async def stop_session(sid: str):
        with _lock:
            if sid not in _sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            loop = _sessions[sid]["loop"]
        loop.stop()
        return {"status": "stopped"}

    @app.websocket("/ws/sessions/{sid}")
    async def ws_session(ws: WebSocket, sid: str):
        await ws.accept()
        with _lock:
            if sid not in _sessions:
                await ws.close(code=404)
                return
        import asyncio
        import time
        while True:
            with _lock:
                data = _sessions.get(sid, {})
                session = data.get("session")
                status = data.get("status", "running")
            if session:
                await ws.send_json({
                    "id": session.id,
                    "status": session.status,
                    "turns_count": len(session.turns),
                })
                if session.status in ("completed", "stopped", "error"):
                    await ws.close()
                    break
            else:
                await ws.send_json({"id": sid, "status": status, "turns_count": 0})
            await asyncio.sleep(1)

    return app


app = create_app()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_webui.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/webui/ tests/test_webui.py
git commit -m "feat: WebUI backend with FastAPI and WebSocket"
```

---

### Task 15: WebUI Frontend

**Files:**
- Create: `harness/webui/static/index.html`

**Interfaces:**
- Consumes: WebUI backend API
- Produces: Single-page HTML+JS frontend

- [ ] **Step 1: Write the frontend**

```html
<!-- harness/webui/static/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coding Agent Harness</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #1e1e1e; color: #d4d4d4; display: flex; height: 100vh; }
        .chat-area { flex: 1; display: flex; flex-direction: column; border-right: 1px solid #333; }
        .chat-header { padding: 12px 20px; background: #252526; border-bottom: 1px solid #333; font-size: 16px; font-weight: bold; }
        .chat-messages { flex: 1; overflow-y: auto; padding: 16px; }
        .msg { margin-bottom: 12px; padding: 8px 12px; border-radius: 6px; max-width: 80%; }
        .msg.user { background: #2d4a5e; margin-left: auto; }
        .msg.agent { background: #2d2d30; }
        .msg.tool { background: #1a3a1a; font-family: monospace; font-size: 13px; }
        .msg.blocked { background: #4a2d2d; border-left: 3px solid #f44; }
        .chat-input { padding: 12px 16px; background: #252526; border-top: 1px solid #333; display: flex; gap: 8px; }
        .chat-input input { flex: 1; padding: 8px 12px; background: #3c3c3c; border: 1px solid #555; border-radius: 4px; color: #d4d4d4; font-size: 14px; }
        .chat-input button { padding: 8px 16px; background: #0e639c; border: none; border-radius: 4px; color: #fff; cursor: pointer; font-size: 14px; }
        .chat-input button:hover { background: #1177bb; }
        .sidebar { width: 300px; background: #252526; padding: 16px; overflow-y: auto; }
        .sidebar h2 { font-size: 14px; margin-bottom: 12px; color: #888; text-transform: uppercase; }
        .session-item { padding: 8px 12px; background: #2d2d30; border-radius: 4px; margin-bottom: 6px; cursor: pointer; font-size: 13px; }
        .session-item:hover { background: #37373d; }
        .session-item.active { border-left: 3px solid #0e639c; }
        .hitl-panel { margin-top: 20px; padding: 12px; background: #4a2d2d; border-radius: 6px; border: 1px solid #f44; }
        .hitl-panel h3 { color: #f88; font-size: 14px; margin-bottom: 8px; }
        .hitl-panel p { font-size: 13px; margin-bottom: 8px; }
        .hitl-panel button { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; margin-right: 8px; font-size: 13px; }
        .hitl-panel .approve { background: #2d5a2d; color: #fff; }
        .hitl-panel .deny { background: #5a2d2d; color: #fff; }
        .status-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 8px; }
        .status-running { background: #4a4a0e; color: #ffcc00; }
        .status-completed { background: #2d5a2d; color: #6f6; }
        .status-stopped { background: #5a2d2d; color: #f66; }
    </style>
</head>
<body>
    <div class="chat-area">
        <div class="chat-header">Coding Agent Harness</div>
        <div class="chat-messages" id="messages"></div>
        <div class="chat-input">
            <input type="text" id="taskInput" placeholder="输入编码任务..." onkeypress="if(event.key==='Enter')submitTask()">
            <button onclick="submitTask()">发送</button>
        </div>
    </div>
    <div class="sidebar">
        <h2>会话列表</h2>
        <div id="sessionList"></div>
        <div id="hitlPanel" style="display:none;" class="hitl-panel">
            <h3>⚠ 危险动作审批</h3>
            <p id="hitlAction"></p>
            <button class="approve" onclick="approveAction()">批准</button>
            <button class="deny" onclick="denyAction()">拒绝</button>
        </div>
    </div>
    <script>
        let currentSession = null;
        let ws = null;

        async function submitTask() {
            const input = document.getElementById('taskInput');
            const task = input.value.trim();
            if (!task) return;
            input.value = '';
            addMessage('user', task);
            const resp = await fetch('/api/sessions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task: task})
            });
            const data = await resp.json();
            currentSession = data.id;
            addSessionToList(data.id, task);
            connectWS(data.id);
            pollSession(data.id);
        }

        function addMessage(role, text) {
            const div = document.getElementById('messages');
            const msg = document.createElement('div');
            msg.className = 'msg ' + role;
            msg.textContent = text;
            div.appendChild(msg);
            div.scrollTop = div.scrollHeight;
        }

        function addSessionToList(id, task) {
            const list = document.getElementById('sessionList');
            const item = document.createElement('div');
            item.className = 'session-item active';
            item.textContent = task.substring(0, 30) + '...';
            item.onclick = () => selectSession(id);
            list.appendChild(item);
        }

        function connectWS(sid) {
            if (ws) ws.close();
            ws = new WebSocket(`ws://${location.host}/ws/sessions/${sid}`);
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.status === 'pending_approval' || data.turns_count > 0) {
                    checkHITL(sid);
                }
            };
        }

        async function pollSession(sid) {
            const interval = setInterval(async () => {
                const resp = await fetch(`/api/sessions/${sid}`);
                const data = await resp.json();
                if (data.turns && data.turns.length > 0) {
                    const messages = document.getElementById('messages');
                    const existing = messages.children.length;
                    for (let i = existing; i < data.turns.length; i++) {
                        const t = data.turns[i];
                        addMessage('agent', `[${t.action.tool_name}] ${t.action.thought}`);
                        if (t.governance && t.governance.blocked) {
                            addMessage('blocked', `BLOCKED: ${t.governance.reason}`);
                        }
                    }
                }
                if (data.status !== 'running') {
                    clearInterval(interval);
                    addMessage('agent', `Session ${data.status}`);
                }
                checkHITL(sid);
            }, 1000);
        }

        async function checkHITL(sid) {
            try {
                const resp = await fetch(`/api/sessions/${sid}`);
                const data = await resp.json();
                const panel = document.getElementById('hitlPanel');
                if (data.status === 'running' && data.turns) {
                    const lastTurn = data.turns[data.turns.length - 1];
                    if (lastTurn && lastTurn.governance && lastTurn.governance.blocked && lastTurn.governance.reason.includes('Pending')) {
                        panel.style.display = 'block';
                        document.getElementById('hitlAction').textContent = `${lastTurn.action.tool_name}: ${JSON.stringify(lastTurn.action.args)}`;
                        return;
                    }
                }
                panel.style.display = 'none';
            } catch(e) {}
        }

        async function approveAction() {
            if (!currentSession) return;
            await fetch(`/api/sessions/${currentSession}/approve`, {method: 'POST'});
            document.getElementById('hitlPanel').style.display = 'none';
        }

        async function denyAction() {
            if (!currentSession) return;
            await fetch(`/api/sessions/${currentSession}/deny`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({reason: 'User denied'})
            });
            document.getElementById('hitlPanel').style.display = 'none';
        }

        function selectSession(sid) {
            currentSession = sid;
            document.getElementById('messages').innerHTML = '';
            pollSession(sid);
            connectWS(sid);
        }
    </script>
</body>
</html>
```

- [ ] **Step 2: Verify frontend loads**

Run: `uvicorn harness.webui.app:app --port 8000 &; sleep 2; curl -s http://localhost:8000/ | head -5`
Expected: HTML response with `<title>Coding Agent Harness</title>`

- [ ] **Step 3: Commit**

```bash
git add harness/webui/static/
git commit -m "feat: WebUI frontend with chat and HITL approval panel"
```

---

### Task 16: CLI Entry + config.yaml

**Files:**
- Create: `harness/cli.py`
- Create: `config.yaml`

**Interfaces:**
- Consumes: `create_app` from `harness.webui.app`; `load_config` from `harness.config`; `CredentialManager` from `harness.credentials`
- Produces: `main()` CLI entry point

- [ ] **Step 1: Write the CLI**

```python
# harness/cli.py
import sys
import argparse
from harness.config import load_config
from harness.credentials import CredentialManager


def main():
    parser = argparse.ArgumentParser(description="Coding Agent Harness")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("serve", help="Start WebUI server")
    subparsers.add_parser("key", help="Manage API keys")
    key_sub = subparsers.add_parser("set-key", help="Set API key")
    key_sub.add_argument("--name", default="deepseek_api_key")
    subparsers.add_parser("status", help="Check key status")

    args = parser.parse_args()

    if args.command == "serve":
        import uvicorn
        config = load_config("config.yaml")
        uvicorn.run("harness.webui.app:app", host="0.0.0.0", port=8000)

    elif args.command == "set-key":
        import getpass
        mgr = CredentialManager(backend="file", store_path=".credentials.json")
        value = getpass.getpass("Enter API key (input hidden): ")
        mgr.store(args.name, value)
        print(f"Key '{args.name}' stored.")

    elif args.command == "status":
        mgr = CredentialManager(backend="file", store_path=".credentials.json")
        exists = mgr.status("deepseek_api_key")
        print(f"deepseek_api_key: {'configured' if exists else 'not set'}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

```yaml
# config.yaml
project_root: "./workspace"
llm:
  provider: "deepseek"
  model: "deepseek-chat"
  max_tokens: 4096
  temperature: 0.7
governance:
  deny_patterns:
    - 'rm\s+-rf\s+/'
    - 'drop\s+database'
    - 'curl.*\|\s*sh'
    - 'chmod\s+777'
    - 'mkfs'
    - 'dd\s+if='
  approval_patterns:
    - 'git\s+push'
    - 'pip\s+install'
    - 'npm\s+publish'
    - 'docker\s+push'
  readonly_paths:
    - ".git/"
    - "README.md"
sandbox:
  command_policy: "blacklist"
  blocked_commands:
    - "sudo"
    - "shutdown"
    - "reboot"
    - "systemctl"
feedback:
  test_command: "pytest"
  max_retries: 3
max_turns: 20
```

- [ ] **Step 2: Verify CLI works**

Run: `python -m harness.cli status`
Expected: `deepseek_api_key: not set`

- [ ] **Step 3: Commit**

```bash
git add harness/cli.py config.yaml
git commit -m "feat: CLI entry point and default config"
```

---

### Task 17: Mechanism Demo

**Files:**
- Create: `demo_mechanism.py`

**Interfaces:**
- Consumes: `guardrail`, `sandbox`, `HITLStateMachine`, `GovernanceMiddleware`, `MockLLMClient`, `AgentLoop`, `Validator`, `FailureClassifier`
- Produces: A runnable script demonstrating 3 scenarios

- [ ] **Step 1: Write the demo**

```python
# demo_mechanism.py
"""Mechanism demonstration: deterministic reproduction of governance, feedback, and HITL behaviors under mock LLM."""
import tempfile
import os
from harness.governance.guardrail import guardrail, GuardrailVerdict, Rule
from harness.governance.sandbox import sandbox
from harness.governance.hitl import HITLStateMachine, HITLState
from harness.governance.middleware import GovernanceMiddleware
from harness.core.action import Action, Message
from harness.core.llm import MockLLMClient
from harness.core.loop import AgentLoop
from harness.tools.dispatcher import ToolDispatcher
from harness.tools.file_tools import write_file
from harness.feedback.validator import Validator
from harness.feedback.classifier import FailureClassifier, FailureType
from harness.config import Config, SandboxConfig
from harness.memory.store import MemoryStore


def demo_1_guardrail_blocks_dangerous_action():
    print("=" * 60)
    print("Demo 1: Guardrail blocks dangerous action (rm -rf /)")
    print("=" * 60)
    rules = [
        Rule(pattern=r"rm\s+-rf\s+/", severity="deny", tool="execute_shell", description="rm -rf root"),
    ]
    action = Action(tool_name="execute_shell", args={"command": "rm -rf /"}, thought="cleanup everything")
    verdict, reason = guardrail(action, rules)
    print(f"  Action: {action.tool_name}({action.args})")
    print(f"  Verdict: {verdict.value}")
    print(f"  Reason: {reason}")
    assert verdict == GuardrailVerdict.DENY, "FAIL: should be DENY"
    print("  [PASS] Dangerous action blocked\n")


def demo_2_feedback_loop_drives_correction():
    print("=" * 60)
    print("Demo 2: Feedback loop - failure feedback changes next action")
    print("=" * 60)
    root = tempfile.mkdtemp()
    test_file = os.path.join(root, "test_calc.py")
    write_file(test_file, "def test_add():\n    assert 1 + 1 == 3\n", root=root)
    script = [
        Action(tool_name="run_tests", args={"test_args": ""}, thought="run tests first"),
        {"if_context_contains": "failed", "action": Action(tool_name="write_file", args={"path": test_file, "content": "def test_add():\n    assert 1 + 1 == 2\n"}, thought="fix the failing test")},
        Action(tool_name="run_tests", args={"test_args": ""}, thought="re-run tests"),
        Action(tool_name="finish", args={}, thought="all fixed"),
    ]
    llm = MockLLMClient(script)
    dispatcher = ToolDispatcher()
    dispatcher.register("write_file", lambda args, ctx: write_file(args["path"], args["content"], root))
    dispatcher.register("finish", lambda args, ctx: type("R", (), {"success": True, "output": "done", "error": ""})())
    from harness.tools.test_tool import run_tests as tool_run_tests
    dispatcher.register("run_tests", lambda args, ctx: tool_run_tests(args.get("test_args", ""), cwd=root))
    config = Config.default()
    config.project_root = root
    mw = GovernanceMiddleware(rules=[], sandbox_config=config.sandbox, project_root=root)
    memory = MemoryStore()
    loop = AgentLoop(llm=llm, dispatcher=dispatcher, governance=mw, memory=memory, config=config)
    session = loop.run("fix the failing test")
    print(f"  Task: fix failing test")
    print(f"  Turns: {len(session.turns)}")
    for i, t in enumerate(session.turns):
        result_str = ""
        if t.action.result:
            result_str = f" -> success={t.action.result.success}"
        print(f"    Turn {i+1}: {t.action.tool_name}({t.action.thought}){result_str}")
    print(f"  Final status: {session.status}")
    assert session.status == "completed", "FAIL: should complete"
    print("  [PASS] Feedback loop drove self-correction\n")


def demo_3_hitl_state_machine():
    print("=" * 60)
    print("Demo 3: HITL state machine - approve then execute")
    print("=" * 60)
    root = tempfile.mkdtemp()
    rules = [
        Rule(pattern=r"git\s+push", severity="require_approval", tool="execute_shell", description="git push needs approval"),
    ]
    config = Config.default()
    config.project_root = root
    config.sandbox = SandboxConfig(command_policy="blacklist", blocked_commands=[])
    mw = GovernanceMiddleware(rules=rules, sandbox_config=config.sandbox, project_root=root)
    action = Action(tool_name="execute_shell", args={"command": "git push origin main"}, thought="push code")
    result1 = mw.process(action)
    print(f"  Action: {action.tool_name}({action.args})")
    print(f"  First process: blocked={result1.blocked}, reason={result1.reason}")
    assert result1.blocked, "FAIL: should be blocked pending approval"
    assert mw.is_pending(), "FAIL: should be pending"
    print(f"  State: PENDING_APPROVAL")
    print(f"  User approves...")
    mw.approve()
    result2 = mw.process(action)
    print(f"  Second process: blocked={result2.blocked}")
    assert not result2.blocked, "FAIL: should be allowed after approval"
    print("  [PASS] HITL approval flow works\n")


def demo_3b_hitl_deny():
    print("=" * 60)
    print("Demo 3b: HITL state machine - deny blocks execution")
    print("=" * 60)
    root = tempfile.mkdtemp()
    rules = [
        Rule(pattern=r"git\s+push", severity="require_approval", tool="execute_shell", description="git push"),
    ]
    config = Config.default()
    config.project_root = root
    config.sandbox = SandboxConfig(command_policy="blacklist", blocked_commands=[])
    mw = GovernanceMiddleware(rules=rules, sandbox_config=config.sandbox, project_root=root)
    action = Action(tool_name="execute_shell", args={"command": "git push --force"}, thought="force push")
    result1 = mw.process(action)
    print(f"  Action: {action.tool_name}({action.args})")
    print(f"  First process: blocked={result1.blocked}")
    assert result1.blocked
    print(f"  User denies...")
    mw.deny("no force push allowed")
    result2 = mw.process(action)
    print(f"  Second process: blocked={result2.blocked}, reason={result2.reason}")
    assert result2.blocked, "FAIL: should remain blocked after deny"
    assert "Denied" in result2.reason or "denied" in result2.reason.lower()
    print("  [PASS] HITL deny flow works\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CODING AGENT HARNESS - MECHANISM DEMONSTRATION")
    print("  (All scenarios run under mock LLM, no network needed)")
    print("=" * 60 + "\n")
    demo_1_guardrail_blocks_dangerous_action()
    demo_2_feedback_loop_drives_correction()
    demo_3_hitl_state_machine()
    demo_3b_hitl_deny()
    print("=" * 60)
    print("  ALL DEMOS PASSED")
    print("=" * 60)
```

- [ ] **Step 2: Run the demo**

Run: `python demo_mechanism.py`
Expected: All 4 demos pass with `[PASS]` messages

- [ ] **Step 3: Commit**

```bash
git add demo_mechanism.py
git commit -m "feat: mechanism demonstration script (4 scenarios, mock LLM)"
```

---

### Task 18: Dockerfile + CI

**Files:**
- Create: `Dockerfile`
- Create: `.gitlab-ci.yml`
- Modify: `pyproject.toml` (add pytest-json-report dependency)

**Interfaces:**
- Consumes: All previous tasks
- Produces: Docker image, CI pipeline

- [ ] **Step 1: Add pytest-json-report to dependencies**

In `pyproject.toml`, add `"pytest-json-report>=0.5"` to the dependencies list.

- [ ] **Step 2: Write Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

RUN mkdir -p /app/workspace

EXPOSE 8000

CMD ["uvicorn", "harness.webui.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Write CI config**

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build

unit-test:
  stage: test
  image: python:3.12-slim
  before_script:
    - pip install -e .
    - pip install pytest-json-report
  script:
    - pytest tests/ -v --json-report --json-report-file=test-report.json
  artifacts:
    reports:
      junit: test-report.xml
    paths:
      - test-report.json
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"

docker-build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t coding-agent-harness .
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

- [ ] **Step 4: Verify Docker build**

Run: `docker build -t coding-agent-harness .`
Expected: Build succeeds

- [ ] **Step 5: Verify tests pass**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add Dockerfile .gitlab-ci.yml pyproject.toml
git commit -m "feat: Dockerfile and CI configuration with unit-test job"
```

---

## Self-Review

### Spec Coverage

| Spec Section | Task(s) |
|---|---|
| 3.1 Core (loop, llm, action) | Task 1, 3, 13 |
| 3.2 Tools (dispatcher, file, shell, test) | Task 6, 7 |
| 3.3 Governance (guardrail, sandbox, hitl, middleware) | Task 8, 9, 10, 11 |
| 3.4 Feedback (validator, classifier) | Task 12 |
| 3.5 Memory | Task 5 |
| 3.6 Config | Task 2 |
| 3.7 WebUI (backend, frontend) | Task 14, 15 |
| 3.8 Credentials | Task 4 |
| §A.6 Mechanism demo | Task 17 |
| §3.2 Distribution (Docker) | Task 18 |
| §4.8 CI | Task 18 |
| CLI + config.yaml | Task 16 |

All spec sections covered. ✓

### Placeholder Scan

No TBDs, TODOs, or "implement later" found. All steps contain actual code. ✓

### Type Consistency

- `Action(tool_name, args, thought, result)` — consistent across all tasks ✓
- `ToolResult(success, output, error)` — consistent ✓
- `guardrail(action, rules) -> tuple[GuardrailVerdict, str]` — consistent ✓
- `sandbox(action, config, project_root, readonly_paths) -> SandboxResult` — consistent ✓
- `HITLStateMachine` methods — consistent ✓
- `GovernanceMiddleware.process(action) -> GovernanceResult` — consistent ✓

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-07-coding-agent-harness.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
