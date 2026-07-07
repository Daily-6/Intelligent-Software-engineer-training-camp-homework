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
