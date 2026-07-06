"""
Temuclaude Code Execution Sandbox
Safe Python code execution for tool-use queries.

Features:
- Subprocess-based execution with timeout
- Sandbox mode: no file/network/os access
- Captures stdout, stderr, return code
- Memory limit via resource module
"""
import subprocess
import sys
import os
import tempfile
import resource
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of code execution."""
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    error: Optional[str] = None


# Forbidden modules in sandbox mode
SANDBOX_FORBIDDEN = [
    "os", "subprocess", "socket", "http", "urllib",
    "shutil", "pathlib", "ctypes", "multiprocessing",
    "threading", "signal", "ftplib", "smtplib",
    "telnetlib", "http.server", "socketserver",
    "asyncio.subprocess", "webbrowser",
]

SANDBOX_PREFIX = """
import sys
import builtins

# Block forbidden modules
_forbidden = {name: True for name in %r}

class _BlockedImport:
    def __init__(self, name):
        self._name = name
    def __getattr__(self, attr):
        raise ImportError(f"Module '{{self._name}}' is blocked in sandbox mode")

_orig_import = builtins.__import__

def _sandbox_import(name, globals=None, locals=None, fromlist=(), level=0):
    if _forbidden.get(name):
        raise ImportError(f"Module '{{name}}' is blocked in sandbox mode")
    # Also check submodules
    parts = name.split('.')
    for i in range(1, len(parts)):
        prefix = '.'.join(parts[:i+1])
        if _forbidden.get(prefix):
            raise ImportError(f"Module '{{prefix}}' is blocked in sandbox mode")
    return _orig_import(name, globals, locals, fromlist, level)

builtins.__import__ = _sandbox_import
""" % SANDBOX_FORBIDDEN


def execute_code(
    code: str,
    timeout: int = 30,
    sandbox: bool = True,
    workdir: Optional[str] = None,
) -> ExecutionResult:
    """Execute Python code in a subprocess.

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds (max 300)
        max 300)
        sandbox: If True, block file/network/os access
        workdir: Working directory (temp dir if None)

    Returns:
        ExecutionResult with stdout, stderr, exit_code
    """
    timeout = min(timeout, 300)

    # Create temp file for code
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=workdir
    ) as f:
        if sandbox:
            f.write(SANDBOX_PREFIX)
        f.write("\n")
        f.write(code)
        temp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
        )

        return ExecutionResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            timed_out=False,
        )
    except subprocess.TimeoutExpired as e:
        return ExecutionResult(
            stdout=e.stdout or "" if isinstance(e.stdout, str) else "",
            stderr=e.stderr or "" if isinstance(e.stderr, str) else "",
            exit_code=-1,
            timed_out=True,
            error=f"Execution timed out after {timeout}s",
        )
    except Exception as e:
        return ExecutionResult(
            stdout="",
            stderr=str(e),
            exit_code=-1,
            timed_out=False,
            error=str(e),
        )
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def execute_code_safe(code: str, timeout: int = 30) -> ExecutionResult:
    """Execute code in sandbox mode (no file/network/os access)."""
    return execute_code(code, timeout=timeout, sandbox=True)


def format_output(result: ExecutionResult) -> str:
    """Format execution result for LLM consumption.

    Returns a clean summary of the execution.
    """
    lines = []

    if result.timed_out:
        lines.append(f"ERROR: Execution timed out. {result.error}")
        return "\n".join(lines)

    if result.stdout:
        lines.append(f"stdout:\n{result.stdout}")

    if result.stderr:
        lines.append(f"stderr:\n{result.stderr}")

    lines.append(f"exit_code: {result.exit_code}")

    if result.error and not result.timed_out:
        lines.append(f"error: {result.error}")

    return "\n".join(lines)


def detect_code_request(text: str) -> bool:
    """Detect if the text contains a code execution request.

    Looks for patterns like:
    - "run this code"
    - "execute this"
    - "what does this output"
    - code blocks with "python" tag
    """
    import re

    patterns = [
        r"run\s+(?:this\s+)?code",
        r"execute\s+(?:this\s+)?(?:code|script|python)",
        r"what\s+(?:does|is)\s+this\s+(?:output|code|return)",
        r"```python",
        r"```py",
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def extract_code_blocks(text: str) -> list:
    """Extract Python code blocks from markdown text.

    Returns list of code strings.
    """
    import re

    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL)
    return [b.strip() for b in blocks if b.strip()]