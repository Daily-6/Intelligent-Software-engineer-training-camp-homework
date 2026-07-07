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
    if not os.path.isabs(path):
        path = os.path.join(project_root, path)
    if path == "." or path == "./" or path == project_root:
        path = project_root
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
