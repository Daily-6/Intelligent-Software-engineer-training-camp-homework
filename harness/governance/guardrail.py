import re
from enum import Enum
from dataclasses import dataclass
from harness.core.action import Action


class GuardrailVerdict(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class Rule:
    pattern: str
    severity: str
    tool: str
    description: str


def _get_action_text(action: Action) -> str:
    if action.tool_name == "execute_shell":
        return action.args.get("command", "")
    elif action.tool_name == "write_file":
        return action.args.get("path", "")
    elif action.tool_name == "read_file":
        return action.args.get("path", "")
    elif action.tool_name == "list_dir":
        return action.args.get("path", "")
    else:
        return str(action.args)


def guardrail(action: Action, rules: list) -> tuple:
    text = _get_action_text(action)
    deny_matched = None
    approval_matched = None
    for rule in rules:
        if rule.tool != action.tool_name:
            continue
        try:
            if re.search(rule.pattern, text, re.IGNORECASE):
                if rule.severity == "deny":
                    deny_matched = rule
                    break
                elif rule.severity == "require_approval" and approval_matched is None:
                    approval_matched = rule
        except re.error:
            continue
    if deny_matched:
        return GuardrailVerdict.DENY, f"Denied by rule: {deny_matched.description}"
    if approval_matched:
        return GuardrailVerdict.REQUIRE_APPROVAL, f"Approval required: {approval_matched.description}"
    return GuardrailVerdict.ALLOW, ""
