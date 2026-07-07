from harness.governance.hitl import HITLState, HITLStateMachine
import pytest

def test_initial_state_running():
    sm = HITLStateMachine()
    assert sm.current_state() == HITLState.RUNNING

def test_request_approval_transitions_to_pending():
    sm = HITLStateMachine()
    sm.request_approval()
    assert sm.current_state() == HITLState.PENDING_APPROVAL

def test_approve_transitions_back_to_running():
    sm = HITLStateMachine()
    sm.request_approval()
    sm.approve()
    assert sm.current_state() == HITLState.RUNNING

def test_deny_transitions_back_to_running():
    sm = HITLStateMachine()
    sm.request_approval()
    sm.deny("too dangerous")
    assert sm.current_state() == HITLState.RUNNING
    assert sm.get_deny_reason() == "too dangerous"

def test_stop_transitions_to_stopped():
    sm = HITLStateMachine()
    sm.stop()
    assert sm.current_state() == HITLState.STOPPED

def test_approve_without_pending_raises():
    sm = HITLStateMachine()
    with pytest.raises(RuntimeError, match="cannot approve"):
        sm.approve()

def test_deny_without_pending_raises():
    sm = HITLStateMachine()
    with pytest.raises(RuntimeError, match="cannot deny"):
        sm.deny("nope")

def test_request_approval_when_not_running_raises():
    sm = HITLStateMachine()
    sm.request_approval()
    with pytest.raises(RuntimeError, match="cannot request"):
        sm.request_approval()

def test_timeout_denies():
    sm = HITLStateMachine(timeout_seconds=0)
    sm.request_approval()
    import time
    time.sleep(0.1)
    assert sm.current_state() == HITLState.RUNNING
    assert sm.get_deny_reason() is not None
    assert "timeout" in sm.get_deny_reason().lower()

def test_reset():
    sm = HITLStateMachine()
    sm.request_approval()
    sm.reset()
    assert sm.current_state() == HITLState.RUNNING
    assert sm.get_deny_reason() is None

def test_is_pending():
    sm = HITLStateMachine()
    assert not sm.is_pending()
    sm.request_approval()
    assert sm.is_pending()
