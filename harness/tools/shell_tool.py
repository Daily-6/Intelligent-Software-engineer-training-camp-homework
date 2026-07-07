import subprocess
from harness.core.action import ShellResult


def execute_shell(command: str, cwd: str = None, timeout: int = 30) -> ShellResult:
    try:
        proc = subprocess.run(
            command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return ShellResult(
            success=proc.returncode == 0,
            output=proc.stdout,
            error=proc.stderr,
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
        )
    except subprocess.TimeoutExpired:
        return ShellResult(success=False, output="", error="timeout", stdout="", stderr="timeout", exit_code=-1)
    except Exception as e:
        return ShellResult(success=False, output="", error=str(e), stdout="", stderr=str(e), exit_code=-1)
