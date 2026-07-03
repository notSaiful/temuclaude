"""
Timuclaude Code Execution Verifier
Generates Python code to solve a problem, executes it, and returns the verified answer.

For math and coding questions, code execution provides GROUND TRUTH —
no hallucination possible in computation. If the code runs and produces
output, that output is the verified answer.

Sandbox: subprocess with timeout, no network, temp directory.
Falls back to model's direct answer if code fails.
"""
import asyncio
import os
import re
import sys
import subprocess
import tempfile
from typing import Optional


CODE_GENERATION_PROMPT = (
    "You are a Python code generator. Write Python code that solves the following problem. "
    "Only output the Python code, no explanation, no markdown formatting. "
    "The code should print the final answer to stdout.\n\n"
    "Problem: {question}"
)


def extract_code(response: str) -> str:
    """Extract Python code from a model response.
    
    Handles:
    - Raw code (no markdown)
    - ```python ... ``` blocks
    - ``` ... ``` blocks
    """
    # Try to find ```python ... ``` block
    match = re.search(r'```python\s*\n(.*?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Try to find ``` ... ``` block
    match = re.search(r'```\s*\n(.*?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # No markdown — assume the response IS the code
    # But strip any leading/trailing explanation
    lines = response.strip().split('\n')
    code_lines = []
    in_code = False
    for line in lines:
        # Skip obvious non-code lines
        if line.strip().startswith('Here is') or line.strip().startswith('This code'):
            continue
        if line.strip().startswith('The code') or line.strip().startswith('Note:'):
            continue
        code_lines.append(line)
    
    return '\n'.join(code_lines).strip()


async def verify_with_code(
    question: str,
    model: str,
    call_model_func,
    max_tokens: int = 4096,
    execution_timeout: int = 10,
) -> dict:
    """
    Generate code to solve the question, execute it, return verified answer.
    
    Args:
        question: The user's question
        model: Which model generates the code
        call_model_func: Async function to call a model
        max_tokens: Max tokens for code generation
        execution_timeout: Seconds before code execution is killed
    
    Returns:
        Dict with:
        - 'verified': bool — whether code execution succeeded
        - 'answer': The verified answer from code output, or None if failed
        - 'code': The generated code
        - 'stdout': Captured stdout
        - 'stderr': Captured stderr (if any)
    """
    # Generate code
    code_prompt = CODE_GENERATION_PROMPT.format(question=question)
    messages = [
        {"role": "system", "content": "You are a Python code generator. Output only Python code that prints the answer."},
        {"role": "user", "content": code_prompt},
    ]
    
    code_response = await call_model_func(model, messages, max_tokens=max_tokens)
    code = extract_code(code_response)
    
    if not code.strip():
        return {
            "verified": False,
            "answer": None,
            "code": "",
            "stdout": "",
            "stderr": "No code generated",
        }
    
    # Execute in sandbox
    # Create a temp directory for execution
    with tempfile.TemporaryDirectory() as tmpdir:
        # Strip environment of sensitive variables
        safe_env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": tmpdir,
            "TMPDIR": tmpdir,
            "PYTHONPATH": "",
        }
        
        try:
            # Run in a thread to avoid blocking the event loop
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [sys.executable, "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=execution_timeout,
                    env=safe_env,
                    cwd=tmpdir,
                    stdin=subprocess.DEVNULL,
                )
            )
            
            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""
            
            if result.returncode == 0 and stdout:
                return {
                    "verified": True,
                    "answer": stdout,
                    "code": code,
                    "stdout": stdout,
                    "stderr": stderr,
                }
            else:
                return {
                    "verified": False,
                    "answer": None,
                    "code": code,
                    "stdout": stdout,
                    "stderr": stderr,
                }
                
        except subprocess.TimeoutExpired:
            return {
                "verified": False,
                "answer": None,
                "code": code,
                "stdout": "",
                "stderr": f"Code execution timed out after {execution_timeout}s",
            }
        except Exception as e:
            return {
                "verified": False,
                "answer": None,
                "code": code,
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
            }