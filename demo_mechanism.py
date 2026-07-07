"""Mechanism demonstration: deterministic reproduction of governance, feedback, and HITL behaviors under mock LLM."""
import tempfile
import os
from harness.governance.guardrail import guardrail, GuardrailVerdict, Rule
from harness.governance.sandbox import sandbox
from harness.governance.hitl import HITLStateMachine, HITLState
from harness.governance.middleware import GovernanceMiddleware
from harness.core.action import Action, Message
from harness.core.llm import MockLLMClient
from harness.core.loop import AgentLoop
from harness.tools.dispatcher import ToolDispatcher
from harness.tools.file_tools import write_file
from harness.tools.test_tool import run_tests as tool_run_tests
from harness.config import Config, SandboxConfig
from harness.memory.store import MemoryStore


def demo_1_guardrail_blocks_dangerous_action():
    print("=" * 60)
    print("Demo 1: Guardrail blocks dangerous action (rm -rf /)")
    print("=" * 60)
    rules = [
        Rule(pattern=r"rm\s+-rf\s+/", severity="deny", tool="execute_shell", description="rm -rf root"),
    ]
    action = Action(tool_name="execute_shell", args={"command": "rm -rf /"}, thought="cleanup everything")
    verdict, reason = guardrail(action, rules)
    print(f"  Action: {action.tool_name}({action.args})")
    print(f"  Verdict: {verdict.value}")
    print(f"  Reason: {reason}")
    assert verdict == GuardrailVerdict.DENY, "FAIL: should be DENY"
    print("  [PASS] Dangerous action blocked\n")


def demo_2_feedback_loop_drives_correction():
    print("=" * 60)
    print("Demo 2: Feedback loop - failure feedback changes next action")
    print("=" * 60)
    root = tempfile.mkdtemp()
    test_file = os.path.join(root, "test_calc.py")
    write_file(test_file, "def test_add():\n    assert 1 + 1 == 3\n", root=root)
    script = [
        Action(tool_name="run_tests", args={"test_args": ""}, thought="run tests first"),
        {"if_context_contains": "failed", "action": Action(tool_name="write_file", args={"path": test_file, "content": "def test_add():\n    assert 1 + 1 == 2\n"}, thought="fix the failing test")},
        Action(tool_name="run_tests", args={"test_args": ""}, thought="re-run tests"),
        Action(tool_name="finish", args={}, thought="all fixed"),
    ]
    llm = MockLLMClient(script)
    dispatcher = ToolDispatcher()
    dispatcher.register("write_file", lambda args, ctx: write_file(args["path"], args["content"], root))
    dispatcher.register("finish", lambda args, ctx: type("R", (), {"success": True, "output": "done", "error": ""})())
    dispatcher.register("run_tests", lambda args, ctx: tool_run_tests(args.get("test_args", ""), cwd=root))
    config = Config.default()
    config.project_root = root
    mw = GovernanceMiddleware(rules=[], sandbox_config=config.sandbox, project_root=root)
    memory = MemoryStore()
    loop = AgentLoop(llm=llm, dispatcher=dispatcher, governance=mw, memory=memory, config=config)
    session = loop.run("fix the failing test")
    print(f"  Task: fix failing test")
    print(f"  Turns: {len(session.turns)}")
    for i, t in enumerate(session.turns):
        result_str = ""
        if t.action.result:
            result_str = f" -> success={t.action.result.success}"
        print(f"    Turn {i+1}: {t.action.tool_name}({t.action.thought}){result_str}")
    print(f"  Final status: {session.status}")
    assert session.status == "completed", "FAIL: should complete"
    print("  [PASS] Feedback loop drove self-correction\n")


def demo_3_hitl_state_machine():
    print("=" * 60)
    print("Demo 3: HITL state machine - approve then execute")
    print("=" * 60)
    root = tempfile.mkdtemp()
    rules = [
        Rule(pattern=r"git\s+push", severity="require_approval", tool="execute_shell", description="git push needs approval"),
    ]
    config = Config.default()
    config.project_root = root
    config.sandbox = SandboxConfig(command_policy="blacklist", blocked_commands=[])
    mw = GovernanceMiddleware(rules=rules, sandbox_config=config.sandbox, project_root=root)
    action = Action(tool_name="execute_shell", args={"command": "git push origin main"}, thought="push code")
    result1 = mw.process(action)
    print(f"  Action: {action.tool_name}({action.args})")
    print(f"  First process: blocked={result1.blocked}, reason={result1.reason}")
    assert result1.blocked, "FAIL: should be blocked pending approval"
    assert mw.is_pending(), "FAIL: should be pending"
    print(f"  State: PENDING_APPROVAL")
    print(f"  User approves...")
    mw.approve()
    result2 = mw.process(action)
    print(f"  Second process: blocked={result2.blocked}")
    assert not result2.blocked, "FAIL: should be allowed after approval"
    print("  [PASS] HITL approval flow works\n")


def demo_3b_hitl_deny():
    print("=" * 60)
    print("Demo 3b: HITL state machine - deny blocks execution")
    print("=" * 60)
    root = tempfile.mkdtemp()
    rules = [
        Rule(pattern=r"git\s+push", severity="require_approval", tool="execute_shell", description="git push"),
    ]
    config = Config.default()
    config.project_root = root
    config.sandbox = SandboxConfig(command_policy="blacklist", blocked_commands=[])
    mw = GovernanceMiddleware(rules=rules, sandbox_config=config.sandbox, project_root=root)
    action = Action(tool_name="execute_shell", args={"command": "git push --force"}, thought="force push")
    result1 = mw.process(action)
    print(f"  Action: {action.tool_name}({action.args})")
    print(f"  First process: blocked={result1.blocked}")
    assert result1.blocked
    print(f"  User denies...")
    mw.deny("no force push allowed")
    result2 = mw.process(action)
    print(f"  Second process: blocked={result2.blocked}, reason={result2.reason}")
    assert result2.blocked, "FAIL: should remain blocked after deny"
    assert "Denied" in result2.reason or "denied" in result2.reason.lower()
    print("  [PASS] HITL deny flow works\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CODING AGENT HARNESS - MECHANISM DEMONSTRATION")
    print("  (All scenarios run under mock LLM, no network needed)")
    print("=" * 60 + "\n")
    demo_1_guardrail_blocks_dangerous_action()
    demo_2_feedback_loop_drives_correction()
    demo_3_hitl_state_machine()
    demo_3b_hitl_deny()
    print("=" * 60)
    print("  ALL DEMOS PASSED")
    print("=" * 60)
