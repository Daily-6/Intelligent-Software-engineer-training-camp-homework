import time
from enum import Enum


class HITLState(Enum):
    RUNNING = "running"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DENIED = "denied"
    STOPPED = "stopped"


class HITLStateMachine:
    def __init__(self, timeout_seconds: int = 300):
        self._state = HITLState.RUNNING
        self._deny_reason = None
        self._timeout = timeout_seconds
        self._pending_since = None

    def current_state(self) -> HITLState:
        if self._state == HITLState.PENDING_APPROVAL and self._pending_since is not None:
            elapsed = time.time() - self._pending_since
            if elapsed > self._timeout:
                self._deny_reason = "Approval timeout"
                self._state = HITLState.RUNNING
        return self._state

    def request_approval(self) -> None:
        if self.current_state() != HITLState.RUNNING:
            raise RuntimeError(f"cannot request approval from state {self._state}")
        self._state = HITLState.PENDING_APPROVAL
        self._pending_since = time.time()
        self._deny_reason = None

    def approve(self) -> None:
        if self.current_state() != HITLState.PENDING_APPROVAL:
            raise RuntimeError(f"cannot approve from state {self._state}")
        self._state = HITLState.RUNNING
        self._pending_since = None

    def deny(self, reason: str = "") -> None:
        if self.current_state() != HITLState.PENDING_APPROVAL:
            raise RuntimeError(f"cannot deny from state {self._state}")
        self._state = HITLState.RUNNING
        self._deny_reason = reason or "Denied by user"
        self._pending_since = None

    def stop(self) -> None:
        self._state = HITLState.STOPPED
        self._pending_since = None

    def reset(self) -> None:
        self._state = HITLState.RUNNING
        self._deny_reason = None
        self._pending_since = None

    def is_pending(self) -> bool:
        return self.current_state() == HITLState.PENDING_APPROVAL

    def get_deny_reason(self):
        return self._deny_reason
