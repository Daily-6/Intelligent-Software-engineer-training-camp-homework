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
