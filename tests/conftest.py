import tempfile
import pytest

@pytest.fixture
def tmp_workspace():
    d = tempfile.mkdtemp(prefix="harness_test_")
    yield d
