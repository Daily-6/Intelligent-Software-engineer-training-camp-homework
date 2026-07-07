from harness.core.llm import LLMClient, MockLLMClient, DeepSeekClient
from harness.core.action import Action, Message
import pytest

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
    script = [Action(tool_name="finish", args={}, thought="done")]
    client = MockLLMClient(script)
    client.complete([Message(role="user", content="go")])
    with pytest.raises(RuntimeError, match="script exhausted"):
        client.complete([Message(role="user", content="go")])

def test_deepseek_client_is_llm_client():
    client = DeepSeekClient(api_key="fake", model="deepseek-chat")
    assert isinstance(client, LLMClient)

def test_llm_client_is_abstract():
    with pytest.raises(TypeError):
        LLMClient()
