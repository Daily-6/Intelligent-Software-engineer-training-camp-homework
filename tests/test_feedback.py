import tempfile
import os
from harness.feedback.validator import Validator
from harness.feedback.classifier import FailureClassifier, FailureType
from harness.core.action import TestResult

def test_validator_runs_passing_tests():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "test_ok.py"), "w") as f:
        f.write("def test_ok():\n    assert True\n")
    v = Validator()
    result = v.run("", cwd=d)
    assert result.success
    assert result.passed >= 1

def test_validator_runs_failing_tests():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "test_bad.py"), "w") as f:
        f.write("def test_bad():\n    assert False\n")
    v = Validator()
    result = v.run("", cwd=d)
    assert not result.success
    assert result.failed >= 1

def test_classifier_pass():
    result = TestResult(success=True, output="", error="", total=3, passed=3, failed=0, failures_detail=[])
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.PASS

def test_classifier_syntax_error():
    result = TestResult(
        success=False, output="", error="SyntaxError: invalid syntax",
        total=1, passed=0, failed=1, failures_detail=[{"nodeid": "test.py", "outcome": "failed"}]
    )
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.SYNTAX_ERROR

def test_classifier_import_error():
    result = TestResult(
        success=False, output="", error="ModuleNotFoundError: No module named 'foo'",
        total=1, passed=0, failed=1, failures_detail=[]
    )
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.IMPORT_ERROR

def test_classifier_test_failure():
    result = TestResult(
        success=False, output="", error="AssertionError: assert 1 == 2",
        total=1, passed=0, failed=1, failures_detail=[{"nodeid": "test.py::test_eq", "outcome": "failed"}]
    )
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.TEST_FAILURE

def test_classifier_timeout():
    result = TestResult(
        success=False, output="", error="timeout",
        total=0, passed=0, failed=0, failures_detail=[]
    )
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.TIMEOUT

def test_classifier_unknown():
    result = TestResult(
        success=False, output="", error="some weird error",
        total=0, passed=0, failed=0, failures_detail=[]
    )
    classifier = FailureClassifier()
    ftype, desc = classifier.classify(result)
    assert ftype == FailureType.UNKNOWN
