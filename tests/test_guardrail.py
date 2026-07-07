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
