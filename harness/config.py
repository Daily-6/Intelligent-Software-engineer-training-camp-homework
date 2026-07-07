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
