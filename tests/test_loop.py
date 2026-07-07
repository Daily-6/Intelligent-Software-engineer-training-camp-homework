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
