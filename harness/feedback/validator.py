from harness.core.action import TestResult
from harness.tools.test_tool import run_tests


class Validator:
    def run(self, test_args: str = "", cwd: str = None) -> TestResult:
        return run_tests(test_args, cwd=cwd)
