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
