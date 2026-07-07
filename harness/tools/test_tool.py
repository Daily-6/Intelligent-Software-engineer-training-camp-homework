import subprocess
import json
import os
import tempfile
from harness.core.action import TestResult


def run_tests(test_args: str = "", cwd: str = None) -> TestResult:
    report_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    report_path = report_file.name
    report_file.close()
    cmd = f"python -m pytest {test_args} --json-report --json-report-file={report_path}"
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=120
        )
        try:
            with open(report_path, "r") as f:
                report = json.load(f)
            total = report.get("summary", {}).get("total", 0)
            passed = report.get("summary", {}).get("passed", 0)
            failed = report.get("summary", {}).get("failed", 0)
            failures_detail = [
                {"nodeid": t.get("nodeid", ""), "outcome": t.get("outcome", "")}
                for t in report.get("tests", [])
                if t.get("outcome") != "passed"
            ]
            return TestResult(
                success=failed == 0,
                output=proc.stdout,
                error=proc.stderr,
                total=total,
                passed=passed,
                failed=failed,
                failures_detail=failures_detail,
            )
        except (json.JSONDecodeError, FileNotFoundError):
            return TestResult(
                success=proc.returncode == 0,
                output=proc.stdout,
                error=proc.stderr,
                total=0, passed=0, failed=0, failures_detail=[],
            )
    except subprocess.TimeoutExpired:
        return TestResult(success=False, output="", error="timeout", total=0, passed=0, failed=0, failures_detail=[])
    except Exception as e:
        return TestResult(success=False, output="", error=str(e), total=0, passed=0, failed=0, failures_detail=[])
    finally:
        try:
            os.unlink(report_path)
        except OSError:
            pass
