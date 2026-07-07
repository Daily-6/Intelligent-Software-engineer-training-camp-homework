import tempfile
import os
from harness.tools.file_tools import read_file, write_file, list_dir
from harness.tools.shell_tool import execute_shell
from harness.tools.test_tool import run_tests

def test_write_and_read_file():
    d = tempfile.mkdtemp()
    wr = write_file(os.path.join(d, "test.txt"), "hello world", root=d)
    assert wr.success
    rr = read_file(os.path.join(d, "test.txt"), root=d)
    assert rr.success
    assert rr.output == "hello world"

def test_read_nonexistent_file():
    d = tempfile.mkdtemp()
    rr = read_file(os.path.join(d, "nope.txt"), root=d)
    assert not rr.success
    assert "not found" in rr.error.lower() or "no such file" in rr.error.lower()

def test_list_dir():
    d = tempfile.mkdtemp()
    write_file(os.path.join(d, "a.txt"), "a", root=d)
    write_file(os.path.join(d, "b.txt"), "b", root=d)
    lr = list_dir(d, root=d)
    assert lr.success
    assert "a.txt" in lr.output
    assert "b.txt" in lr.output

def test_execute_shell_success():
    result = execute_shell("echo hello", cwd=tempfile.gettempdir())
    assert result.success
    assert "hello" in result.stdout

def test_execute_shell_failure():
    result = execute_shell("exit 1", cwd=tempfile.gettempdir())
    assert not result.success
    assert result.exit_code == 1

def test_run_tests_pass():
    d = tempfile.mkdtemp()
    test_file = os.path.join(d, "test_pass.py")
    with open(test_file, "w") as f:
        f.write("def test_ok():\n    assert True\n")
    result = run_tests("", cwd=d)
    assert result.success
    assert result.passed >= 1
    assert result.failed == 0

def test_run_tests_fail():
    d = tempfile.mkdtemp()
    test_file = os.path.join(d, "test_fail.py")
    with open(test_file, "w") as f:
        f.write("def test_bad():\n    assert False\n")
    result = run_tests("", cwd=d)
    assert not result.success
    assert result.failed >= 1
