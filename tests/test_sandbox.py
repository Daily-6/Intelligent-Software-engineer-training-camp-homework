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
