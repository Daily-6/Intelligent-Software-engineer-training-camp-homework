from harness.credentials import CredentialManager
import tempfile

def test_store_and_load_credential():
    mgr = CredentialManager(backend="file", store_path=tempfile.mktemp(suffix=".json"))
    mgr.store("deepseek_api_key", "sk-test-123")
    assert mgr.load("deepseek_api_key") == "sk-test-123"

def test_status_returns_bool_not_value():
    mgr = CredentialManager(backend="file", store_path=tempfile.mktemp(suffix=".json"))
    assert mgr.status("deepseek_api_key") is False
    mgr.store("deepseek_api_key", "sk-test-123")
    assert mgr.status("deepseek_api_key") is True

def test_delete_credential():
    mgr = CredentialManager(backend="file", store_path=tempfile.mktemp(suffix=".json"))
    mgr.store("deepseek_api_key", "sk-test-123")
    mgr.delete("deepseek_api_key")
    assert mgr.status("deepseek_api_key") is False
    assert mgr.load("deepseek_api_key") is None

def test_load_nonexistent_returns_none():
    mgr = CredentialManager(backend="file", store_path=tempfile.mktemp(suffix=".json"))
    assert mgr.load("nonexistent") is None

def test_credentials_not_in_plaintext_file():
    path = tempfile.mktemp(suffix=".json")
    mgr = CredentialManager(backend="file", store_path=path)
    mgr.store("deepseek_api_key", "sk-secret-999")
    with open(path, "r") as f:
        content = f.read()
    assert "sk-secret-999" not in content
