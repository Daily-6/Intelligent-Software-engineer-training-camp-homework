from harness.memory.store import MemoryStore
from harness.core.action import Action, Turn
import tempfile

def test_save_and_load_convention():
    store = MemoryStore(store_path=tempfile.mktemp(suffix=".json"))
    store.save("convention", "use pytest for testing")
    assert store.load("convention") == "use pytest for testing"

def test_load_nonexistent_returns_none():
    store = MemoryStore(store_path=tempfile.mktemp(suffix=".json"))
    assert store.load("nonexistent") is None

def test_append_and_get_history():
    store = MemoryStore(store_path=tempfile.mktemp(suffix=".json"))
    action = Action(tool_name="read_file", args={}, thought="test")
    turn = Turn(action=action, governance_result=None, timestamp="2026-07-07T10:00:00")
    store.append_history(turn)
    history = store.get_recent_history(5)
    assert len(history) == 1
    assert history[0].action.tool_name == "read_file"

def test_get_recent_history_limits_n():
    store = MemoryStore(store_path=tempfile.mktemp(suffix=".json"))
    for i in range(10):
        action = Action(tool_name="read_file", args={"i": i}, thought=f"step {i}")
        store.append_history(Turn(action=action, governance_result=None, timestamp=f"2026-07-07T10:0{i}:00"))
    history = store.get_recent_history(3)
    assert len(history) == 3
    assert history[2].action.args["i"] == 9

def test_delete_convention():
    store = MemoryStore(store_path=tempfile.mktemp(suffix=".json"))
    store.save("key", "value")
    store.delete("key")
    assert store.load("key") is None

def test_persists_to_file():
    path = tempfile.mktemp(suffix=".json")
    store1 = MemoryStore(store_path=path)
    store1.save("convention", "use PEP8")
    store2 = MemoryStore(store_path=path)
    assert store2.load("convention") == "use PEP8"

def test_missing_file_initializes_empty():
    store = MemoryStore(store_path="/nonexistent/path.json")
    assert store.load("anything") is None
    assert store.get_recent_history(5) == []
