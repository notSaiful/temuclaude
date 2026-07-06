"""Tests for code_executor module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.code_executor import (
    execute_code, execute_code_safe, format_output,
    detect_code_request, extract_code_blocks
)


def test_execute_code_basic():
    result = execute_code("print('hello world')", timeout=10)
    assert "hello world" in result.stdout
    assert result.exit_code == 0
    assert result.timed_out == False


def test_execute_code_math():
    result = execute_code("x = 2 + 3\nprint(x)", timeout=10)
    assert "5" in result.stdout
    assert result.exit_code == 0


def test_execute_code_error():
    result = execute_code("raise ValueError('test error')", timeout=10)
    assert result.exit_code != 0
    assert "ValueError" in result.stderr


def test_execute_code_timeout():
    # Infinite loop
    result = execute_code("while True: pass", timeout=3)
    assert result.timed_out == True


def test_execute_code_safe_blocks_os():
    result = execute_code_safe("import os\nprint(os.listdir('/'))", timeout=10)
    assert result.exit_code != 0
    assert "blocked" in result.stderr.lower()


def test_format_output_success():
    from src.code_executor import ExecutionResult
    r = ExecutionResult(stdout="hello", stderr="", exit_code=0, timed_out=False)
    formatted = format_output(r)
    assert "hello" in formatted
    assert "0" in formatted


def test_format_output_timeout():
    from src.code_executor import ExecutionResult
    r = ExecutionResult(stdout="", stderr="", exit_code=-1, timed_out=True, error="timed out")
    formatted = format_output(r)
    assert "timed out" in formatted.lower()


def test_detect_code_request():
    assert detect_code_request("run this code: print('hi')") == True
    assert detect_code_request("```python\nprint('hi')\n```") == True
    assert detect_code_request("What is the weather?") == False


def test_extract_code_blocks():
    text = "Here's code:\n```python\nprint('hello')\n```\nDone."
    blocks = extract_code_blocks(text)
    assert len(blocks) == 1
    assert "print" in blocks[0]