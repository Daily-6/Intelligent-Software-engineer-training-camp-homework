from enum import Enum
from harness.core.action import TestResult


class FailureType(Enum):
    PASS = "pass"
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    TEST_FAILURE = "test_failure"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class FailureClassifier:
    def classify(self, result: TestResult) -> tuple:
        if result.success:
            return FailureType.PASS, "All tests passed"
        error = result.error.lower() + " " + result.output.lower()
        if "syntaxerror" in error:
            return FailureType.SYNTAX_ERROR, "Syntax error detected"
        if "modulenotfounderror" in error or "importerror" in error:
            return FailureType.IMPORT_ERROR, "Import error detected"
        if "timeout" in error:
            return FailureType.TIMEOUT, "Test timed out"
        if result.failed > 0:
            return FailureType.TEST_FAILURE, f"{result.failed} test(s) failed"
        return FailureType.UNKNOWN, "Unknown failure"
