import os
import json
import base64
from typing import Optional


class CredentialManager:
    def __init__(self, backend: str = "keyring", store_path: str = None):
        self._backend = backend
        self._store_path = store_path
        if backend == "keyring":
            import keyring
            self._keyring = keyring

    def store(self, key_name: str, value: str) -> None:
        if self._backend == "keyring":
            self._keyring.set_password("coding-agent-harness", key_name, value)
        elif self._backend == "file":
            self._file_store(key_name, value)

    def load(self, key_name: str) -> Optional[str]:
        if self._backend == "keyring":
            return self._keyring.get_password("coding-agent-harness", key_name)
        elif self._backend == "file":
            return self._file_load(key_name)
        return None

    def delete(self, key_name: str) -> None:
        if self._backend == "keyring":
            try:
                self._keyring.delete_password("coding-agent-harness", key_name)
            except self._keyring.errors.PasswordDeleteError:
                pass
        elif self._backend == "file":
            self._file_delete(key_name)

    def status(self, key_name: str) -> bool:
        return self.load(key_name) is not None

    def _file_store(self, key_name: str, value: str) -> None:
        data = {}
        if os.path.exists(self._store_path):
            with open(self._store_path, "r") as f:
                data = json.load(f)
        encoded = base64.b64encode(value.encode()).decode()
        data[key_name] = encoded
        with open(self._store_path, "w") as f:
            json.dump(data, f)

    def _file_load(self, key_name: str) -> Optional[str]:
        if not os.path.exists(self._store_path):
            return None
        with open(self._store_path, "r") as f:
            data = json.load(f)
        encoded = data.get(key_name)
        if encoded is None:
            return None
        return base64.b64decode(encoded.encode()).decode()

    def _file_delete(self, key_name: str) -> None:
        if not os.path.exists(self._store_path):
            return
        with open(self._store_path, "r") as f:
            data = json.load(f)
        data.pop(key_name, None)
        with open(self._store_path, "w") as f:
            json.dump(data, f)
