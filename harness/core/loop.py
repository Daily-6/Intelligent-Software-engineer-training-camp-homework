import uuid
from datetime import datetime
from harness.core.action import Action, Message, Turn, Session, ToolResult
from harness.core.llm import LLMClient
from harness.tools.dispatcher import ToolDispatcher
from harness.governance.middleware import GovernanceMiddleware
from harness.memory.store import MemoryStore
from harness.config import Config


class AgentLoop:
    def __init__(self, llm: LLMClient, dispatcher: ToolDispatcher, governance: GovernanceMiddleware, memory: MemoryStore, config: Config):
        self._llm = llm
        self._dispatcher = dispatcher
        self._governance = governance
        self._memory = memory
        self._config = config
        self._stopped = False

    def run(self, task: str) -> Session:
        session_id = str(uuid.uuid4())[:8]
        session = Session(
            id=session_id,
            task=task,
            turns=[],
            status="running",
            created_at=datetime.now().isoformat(),
        )
        messages = [
            Message(role="system", content=self._system_prompt()),
            Message(role="user", content=task),
        ]
        conventions = self._memory.get_conventions()
        if conventions:
            messages.insert(1, Message(role="system", content=f"Project conventions: {conventions}"))
        turn_count = 0
        while turn_count < self._config.max_turns and not self._stopped:
            action = self._llm.complete(messages)
            gov_result = self._governance.process(action)
            turn = Turn(
                action=action,
                governance_result=gov_result,
                timestamp=datetime.now().isoformat(),
            )
            session.turns.append(turn)
            self._memory.append_history(turn)
            if gov_result.blocked:
                messages.append(Message(role="assistant", content=f"Action: {action.tool_name}({action.args}) - {action.thought}"))
                messages.append(Message(role="tool", content=f"BLOCKED: {gov_result.reason}"))
                turn_count += 1
                continue
            if action.tool_name == "finish":
                action.result = ToolResult(success=True, output="Task completed")
                session.status = "completed"
                break
            result = self._dispatcher.execute(action, context={"root": self._config.project_root})
            action.result = result
            messages.append(Message(role="assistant", content=f"Action: {action.tool_name}({action.args}) - {action.thought}"))
            messages.append(Message(role="tool", content=f"Result: success={result.success}, output={result.output}, error={result.error}"))
            turn_count += 1
        if session.status == "running":
            session.status = "stopped"
        return session

    def stop(self):
        self._stopped = True

    def _system_prompt(self) -> str:
        return (
            "You are a coding agent. Output a JSON action with fields: tool, args, thought. "
            "Available tools: read_file, write_file, list_dir, execute_shell, run_tests, finish. "
            "Use 'finish' when the task is complete."
        )
