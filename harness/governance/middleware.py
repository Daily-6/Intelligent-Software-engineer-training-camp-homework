from dataclasses import dataclass
from harness.core.action import Action
from harness.governance.guardrail import guardrail, GuardrailVerdict, Rule
from harness.governance.sandbox import sandbox, SandboxResult
from harness.governance.hitl import HITLStateMachine
from harness.config import SandboxConfig


@dataclass
class GovernanceResult:
    blocked: bool
    reason: str = ""
    verdict: GuardrailVerdict = GuardrailVerdict.ALLOW


class GovernanceMiddleware:
    def __init__(self, rules: list, sandbox_config: SandboxConfig, project_root: str, readonly_paths: list = None):
        self._rules = rules
        self._sandbox_config = sandbox_config
        self._project_root = project_root
        self._readonly_paths = readonly_paths or []
        self._hitl = HITLStateMachine()
        self._pending_action = None
        self._approved_action = None
        self._denied_action = None
        self._denied_reason = None

    def process(self, action: Action) -> GovernanceResult:
        if self._denied_action is not None and self._actions_match(action, self._denied_action):
            reason = self._denied_reason or "Denied by user"
            self._denied_action = None
            self._denied_reason = None
            return GovernanceResult(blocked=True, reason=f"Denied by user: {reason}", verdict=GuardrailVerdict.REQUIRE_APPROVAL)

        if self._approved_action is not None and self._actions_match(action, self._approved_action):
            self._approved_action = None
            sb_result = sandbox(action, self._sandbox_config, self._project_root, self._readonly_paths)
            if not sb_result.allowed:
                return GovernanceResult(blocked=True, reason=f"Blocked by sandbox: {sb_result.reason}", verdict=GuardrailVerdict.ALLOW)
            return GovernanceResult(blocked=False, verdict=GuardrailVerdict.ALLOW)

        verdict, reason = guardrail(action, self._rules)
        if verdict == GuardrailVerdict.DENY:
            return GovernanceResult(blocked=True, reason=f"Denied by guardrail: {reason}", verdict=verdict)
        if verdict == GuardrailVerdict.REQUIRE_APPROVAL:
            if not self._hitl.is_pending():
                self._hitl.request_approval()
                self._pending_action = action
                return GovernanceResult(blocked=True, reason=f"Pending approval: {reason}", verdict=verdict)
            else:
                return GovernanceResult(blocked=True, reason="Pending approval: waiting for user decision", verdict=GuardrailVerdict.REQUIRE_APPROVAL)

        sb_result = sandbox(action, self._sandbox_config, self._project_root, self._readonly_paths)
        if not sb_result.allowed:
            return GovernanceResult(blocked=True, reason=f"Blocked by sandbox: {sb_result.reason}", verdict=GuardrailVerdict.ALLOW)
        return GovernanceResult(blocked=False, verdict=GuardrailVerdict.ALLOW)

    def _actions_match(self, a1: Action, a2: Action) -> bool:
        return a1.tool_name == a2.tool_name and a1.args == a2.args

    def approve(self) -> None:
        self._hitl.approve()
        self._approved_action = self._pending_action
        self._pending_action = None

    def deny(self, reason: str = "") -> None:
        self._hitl.deny(reason)
        self._denied_action = self._pending_action
        self._denied_reason = reason or "Denied by user"
        self._pending_action = None

    def is_pending(self) -> bool:
        return self._hitl.is_pending()

    def get_pending_action(self):
        return self._pending_action
