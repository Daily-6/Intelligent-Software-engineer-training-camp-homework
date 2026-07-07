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
