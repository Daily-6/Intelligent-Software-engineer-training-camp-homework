import os
from harness.core.action import ToolResult


def read_file(path: str, root: str = None) -> ToolResult:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return ToolResult(success=True, output=f.read())
    except FileNotFoundError:
        return ToolResult(success=False, output="", error=f"File not found: {path}")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def write_file(path: str, content: str, root: str = None) -> ToolResult:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(success=True, output=f"Wrote {len(content)} chars to {path}")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def list_dir(path: str, root: str = None) -> ToolResult:
    try:
        entries = os.listdir(path)
        return ToolResult(success=True, output="\n".join(entries))
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))
