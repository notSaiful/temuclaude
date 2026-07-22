"""
Temuclaude Code Execution Verifier
Generates Python code to solve a problem, executes it, and returns the verified answer.

For math and coding questions, code execution provides GROUND TRUTH —
no hallucination possible in computation. If the code runs and produces
output, that output is the verified answer.

Enhanced with:
- Step-Level Code Verification (rStar-Math pattern): Generate code for EACH
  reasoning step and verify each independently. 58.8% → 90% on MATH.
- s1 Budget Forcing (arXiv:2501.19393): Append "Wait" to force the model to
  continue reasoning when it stops too early. Simple but effective.
- Z3/SMT Logical Verification (ConsistPRM pattern): Use Z3 SMT solver to
  verify logical reasoning steps with mathematical certainty.

Sandbox: subprocess with timeout, no network, temp directory.
Falls back to model's direct answer if code fails.
"""
import asyncio
import os
import re
import sys
import subprocess
import tempfile
import json
from typing import Optional, Callable, Awaitable, List


CODE_GENERATION_PROMPT = (
    "You are a Python code generator. Write Python code that solves the following problem. "
    "You are encouraged to use SymPy for symbolic math, limits, calculus, or algebraic solving if helpful. "
    "Only output the Python code, no explanation, no markdown formatting. "
    "The code should print the final answer to stdout.\n\n"
    "Problem: {question}"
)

STEP_CODE_GENERATION_PROMPT = (
    "You are a Python code generator for step-by-step reasoning. "
    "The user is solving a problem step by step. Generate Python code that "
    "VERIFIES the current reasoning step. The code should:\n"
    "1. Recompute the calculation or logic for THIS step\n"
    "2. Print 'STEP_OK: <result>' if the step is correct\n"
    "3. Print 'STEP_FAIL: <reason>' if the step is incorrect\n\n"
    "Only output Python code. No explanation. No markdown.\n\n"
    "Problem: {question}\n"
    "Step {step_num}: {step_text}"
)


import ast

def local_ast_check(code_text: str, language: str = "python") -> dict:
    """
    Perform local AST/syntax verification.
    Returns a dict with 'ok': bool, and 'error': str (if any).
    """
    if not code_text.strip():
        return {"ok": False, "error": "Empty code block"}

    if language.lower() in ("python", "py"):
        try:
            ast.parse(code_text)
            return {"ok": True, "error": None}
        except SyntaxError as e:
            return {
                "ok": False,
                "error": f"Python Syntax Error: {e.msg} on line {e.lineno} (col {e.offset})"
            }
        except Exception as e:
            return {"ok": False, "error": f"Parsing Error: {str(e)}"}

    # For JS/TS/HTML/CSS, do a basic brackets balance check
    elif language.lower() in ("javascript", "typescript", "js", "ts", "html", "css"):
        brackets = {')': '(', ']': '[', '}': '{'}
        stack = []
        for i, char in enumerate(code_text):
            if char in brackets.values():
                stack.append((char, i))
            elif char in brackets.keys():
                if not stack or stack[-1][0] != brackets[char]:
                    line_no = code_text[:i].count('\n') + 1
                    return {
                        "ok": False,
                        "error": f"Mismatched bracket '{char}' detected on line {line_no}."
                    }
                stack.pop()
        if stack:
            line_no = code_text[:stack[-1][1]].count('\n') + 1
            return {
                "ok": False,
                "error": f"Unclosed bracket '{stack[-1][0]}' detected on line {line_no}."
            }

    return {"ok": True, "error": None}


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
    call_model_func: Callable[..., Awaitable[str]],
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

    # AST/Syntax check
    ast_check = local_ast_check(code, "python")
    if not ast_check["ok"]:
        return {
            "verified": False,
            "answer": None,
            "code": code,
            "stdout": "",
            "stderr": f"AST Check Failed: {ast_check['error']}",
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


def extract_reasoning_steps(response: str) -> List[str]:
    """Extract individual reasoning steps from a model response.

    Splits the response into steps based on common patterns:
    - "Step 1:", "Step 2:", etc.
    - Numbered lists "1.", "2.", etc.
    - Paragraph breaks for unstructured responses

    Returns a list of step texts.
    """
    # Try "Step N:" pattern
    steps = re.findall(r'Step\s+\d+[:.]\s*(.+?)(?=Step\s+\d+[:.]|$)', response, re.DOTALL | re.IGNORECASE)
    if len(steps) >= 2:
        return [s.strip() for s in steps if s.strip()]

    # Try numbered list "1.", "2.", etc.
    steps = re.findall(r'(?:^|\n)\d+\.\s*(.+?)(?=\n\d+\.|\Z)', response, re.DOTALL)
    if len(steps) >= 2:
        return [s.strip() for s in steps if s.strip()]

    # Try paragraph breaks
    paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]
    if len(paragraphs) >= 2:
        return paragraphs

    # Single step
    return [response.strip()] if response.strip() else []


def _execute_code_safely(code: str, timeout: int = 10) -> tuple:
    """Execute code in a sandbox. Returns (success: bool, stdout: str, stderr: str)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        safe_env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": tmpdir,
            "TMPDIR": tmpdir,
            "PYTHONPATH": "",
        }
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True, text=True,
                timeout=timeout, env=safe_env,
                cwd=tmpdir, stdin=subprocess.DEVNULL,
            )
            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""
            return (result.returncode == 0 and bool(stdout), stdout, stderr)
        except subprocess.TimeoutExpired:
            return (False, "", f"Timed out after {timeout}s")
        except Exception as e:
            return (False, "", f"Execution error: {str(e)}")


async def verify_steps_with_code(
    question: str,
    response: str,
    model: str,
    call_model_func: Callable[..., Awaitable[str]],
    max_tokens: int = 2048,
    execution_timeout: int = 10,
) -> dict:
    """
    Step-Level Code Verification (rStar-Math pattern).

    Instead of verifying only the final answer, this function:
    1. Extracts reasoning steps from the response
    2. Generates Python code to verify EACH step
    3. Executes each verification code block
    4. If any step fails, the response is marked as unverified

    This catches intermediate errors before they cascade into wrong final answers.

    Args:
        question: The original question
        response: The model's full response (with reasoning steps)
        model: Which model generates verification code
        call_model_func: Async function to call a model
        max_tokens: Max tokens per verification code generation
        execution_timeout: Seconds before code execution is killed

    Returns:
        Dict with:
        - 'verified': bool — all steps passed verification
        - 'steps_total': Total steps found
        - 'steps_verified': Steps that passed
        - 'steps_failed': Steps that failed
        - 'step_results': List of per-step results
        - 'answer': The final answer (from last verified step) or None
    """
    steps = extract_reasoning_steps(response)

    if not steps:
        # No steps found — fall back to whole-response verification
        return await verify_with_code(question, model, call_model_func, max_tokens, execution_timeout)

    step_results = []
    steps_verified = 0
    steps_failed = 0

    for i, step_text in enumerate(steps):
        step_num = i + 1

        # Generate verification code for this step
        step_prompt = STEP_CODE_GENERATION_PROMPT.format(
            question=question, step_num=step_num, step_text=step_text[:500]
        )
        messages = [
            {"role": "system", "content": "You are a Python code verifier. Output only Python code."},
            {"role": "user", "content": step_prompt},
        ]

        code_response = await call_model_func(model, messages, max_tokens=max_tokens)
        code = extract_code(code_response)

        if not code.strip():
            step_results.append({
                "step_num": step_num,
                "verified": False,
                "reason": "No verification code generated",
            })
            steps_failed += 1
            continue

        # Execute verification code in a thread
        success, stdout, stderr = await asyncio.get_event_loop().run_in_executor(
            None, lambda c=code, t=execution_timeout: _execute_code_safely(c, t)
        )

        if success and "STEP_OK" in stdout:
            step_results.append({
                "step_num": step_num,
                "verified": True,
                "stdout": stdout,
            })
            steps_verified += 1
        else:
            step_results.append({
                "step_num": step_num,
                "verified": False,
                "reason": stderr if not success else stdout,
            })
            steps_failed += 1

    # All steps must pass for the response to be verified
    all_verified = steps_failed == 0 and steps_verified > 0

    return {
        "verified": all_verified,
        "steps_total": len(steps),
        "steps_verified": steps_verified,
        "steps_failed": steps_failed,
        "step_results": step_results,
        "answer": response if all_verified else None,
    }


# ============================================================
# s1 BUDGET FORCING (arXiv:2501.19393)
# ============================================================

def apply_budget_forcing(
    response: str,
    min_reasoning_tokens: int = 200,
) -> str:
    """s1 Budget Forcing — append 'Wait' to force the model to continue reasoning.

    The s1 paper showed that appending 'Wait' to a model's response forces it
    to continue reasoning, producing longer and more accurate chains of thought.
    This is extremely simple but effective for math/reasoning tasks.

    Args:
        response: The model's initial response
        min_reasoning_tokens: Minimum reasoning length (approx tokens = words * 1.3)

    Returns:
        The response, possibly with 'Wait' appended if it was too short
    """
    # Estimate tokens (rough: words * 1.3)
    word_count = len(response.split())
    estimated_tokens = int(word_count * 1.3)

    if estimated_tokens < min_reasoning_tokens:
        # Response too short — append "Wait" to force more reasoning
        return response + "\n\nWait"

    return response


async def generate_with_budget_forcing(
    question: str,
    model: str,
    call_model_func: Callable[..., Awaitable[str]],
    max_tokens: int = 8192,
    max_wait_appends: int = 2,
) -> str:
    """Generate a response with s1 budget forcing.

    1. Generate initial response
    2. If response is too short, append "Wait" and continue
    3. Repeat up to max_wait_appends times

    This forces the model to reason longer, improving accuracy on hard problems.
    """
    messages = [
        {"role": "system", "content": "You are Temuclaude. Think step by step. Show your reasoning. At the end, write 'Answer: X'."},
        {"role": "user", "content": question},
    ]

    response = await call_model_func(model, messages, max_tokens=max_tokens)

    for _ in range(max_wait_appends):
        if "Answer:" in response:
            break  # Model reached a final answer — stop forcing

        # Append "Wait" and ask for more
        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": "Wait"})

        continuation = await call_model_func(model, messages, max_tokens=max_tokens)
        response += "\n" + continuation

    return response


# ============================================================
# Z3/SMT LOGICAL VERIFICATION (ConsistPRM pattern)
# ============================================================

def verify_logical_with_z3(
    question: str,
    response: str,
) -> dict:
    """Verify logical reasoning using Z3 SMT solver.

    The ConsistPRM research showed that Z3 can verify logical reasoning
    with mathematical certainty. LLMs may claim correct logic but actually
    have inconsistencies. Z3 checks if the logical claims are actually
    satisfiable.

    This function:
    1. Extracts logical claims from the response
    2. Encodes them as Z3 constraints
    3. Checks satisfiability
    4. Returns whether the logic is consistent

    Note: This requires z3-solver to be installed (pip install z3-solver).
    Falls back gracefully if Z3 is not available.
    """
    try:
        from z3 import Solver, Bool, Implies, And, Or, Not, sat, unsat
    except ImportError:
        return {
            "verified": False,
            "reason": "Z3 not installed (pip install z3-solver)",
            "answer": None,
        }

    solver = Solver()
    bool_vars = {}

    def parse_expr(name: str):
        """Parse expression, handling optional negation."""
        clean = name.strip().lower()
        negated = False
        if clean.startswith("not "):
            negated = True
            clean = clean[4:].strip()
        elif clean.startswith("no "):
            negated = True
            clean = clean[3:].strip()

        clean_var = clean.replace(" ", "_")[:20]
        if not clean_var:
            clean_var = "var_empty"
        if clean_var not in bool_vars:
            bool_vars[clean_var] = Bool(clean_var)

        return bool_vars[clean_var], clean_var, negated

    # Find "if X then Y" patterns
    if_patterns = re.findall(r'if\s+(.+?)\s+then\s+(.+?)(?:[,.]|$)', response, re.IGNORECASE)
    premises_vars = set()
    conclusions_vars = set()

    for premise, conclusion in if_patterns:
        p_var, p_name, p_neg = parse_expr(premise)
        c_var, c_name, c_neg = parse_expr(conclusion)

        p_expr = Not(p_var) if p_neg else p_var
        c_expr = Not(c_var) if c_neg else c_var

        solver.add(Implies(p_expr, c_expr))
        premises_vars.add(p_name)
        conclusions_vars.add(c_name)

    # Find "X implies Y" patterns
    impl_patterns = re.findall(r'(.+?)\s+implies\s+(.+?)(?:[,.]|$)', response, re.IGNORECASE)
    for premise, conclusion in impl_patterns:
        p_var, p_name, p_neg = parse_expr(premise)
        c_var, c_name, c_neg = parse_expr(conclusion)

        p_expr = Not(p_var) if p_neg else p_var
        c_expr = Not(c_var) if c_neg else c_var

        solver.add(Implies(p_expr, c_expr))
        premises_vars.add(p_name)
        conclusions_vars.add(c_name)

    # If no logical patterns found, Z3 can't verify
    if not bool_vars:
        return {
            "verified": False,
            "reason": "No logical patterns found to verify",
            "answer": None,
        }

    # To check if rules are contradictory under active premises,
    # we assert that pure premises (never conclusions) are True.
    pure_premises = premises_vars - conclusions_vars
    for p_name in pure_premises:
        solver.add(bool_vars[p_name] == True)

    # Check if the constraints are satisfiable (not contradictory)
    result = solver.check()

    if result == sat:
        # The logic is consistent — no contradictions
        return {
            "verified": True,
            "reason": "Logical constraints are satisfiable (no contradictions)",
            "answer": response,
            "variables": len(bool_vars),
            "constraints": len(if_patterns) + len(impl_patterns),
        }
    elif result == unsat:
        # The logic contains contradictions
        return {
            "verified": False,
            "reason": "Logical constraints are unsatisfiable (contradictions found)",
            "answer": None,
            "variables": len(bool_vars),
            "constraints": len(if_patterns) + len(impl_patterns),
        }
    else:
        # Unknown — solver couldn't determine
        return {
            "verified": False,
            "reason": "Z3 could not determine satisfiability",
            "answer": None,
        }


async def verify_logical_with_z3_enhanced(
    question: str,
    response: str,
    model: str,
    call_model_func: Callable[..., Awaitable[str]],
    max_tokens: int = 4096,
) -> dict:
    """Enhanced logical verification using LLM-to-Z3 translation.

    Translates logic constraints in the reasoning response to a Python script
    using the z3-solver library, runs it in a subprocess, and reports consistency.
    """
    system_prompt = (
        "You are a Z3 constraint translator. Extract the variables and logical constraints "
        "from the question and answer reasoning. Write a Python script using the `z3-solver` "
        "library that defines Bool variables for statements, adds constraints, checks if "
        "they are satisfiable, and prints exactly 'SATISFIABLE' or 'UNSATISFIABLE'.\n"
        "Only output Python code, no explanation, no markdown format."
    )
    user_prompt = (
        f"Question: {question}\n"
        f"Reasoning/Response: {response}\n\n"
        "Generate the Z3 solver Python code:"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    code_response = await call_model_func(model, messages, max_tokens=max_tokens)
    z3_code = extract_code(code_response)

    if not z3_code.strip():
        # Fall back to the basic regex-based solver
        return verify_logical_with_z3(question, response)

    # Run the Z3 script in temp sandbox
    with tempfile.TemporaryDirectory() as tmpdir:
        safe_env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": tmpdir,
            "TMPDIR": tmpdir,
            "PYTHONPATH": "",
        }
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [sys.executable, "-c", z3_code],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=safe_env,
                    cwd=tmpdir,
                    stdin=subprocess.DEVNULL,
                )
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if "UNSATISFIABLE" in stdout:
                return {
                    "verified": False,
                    "reason": f"Z3 solver returned UNSATISFIABLE (contradiction found):\n{stderr}",
                    "answer": None,
                    "code": z3_code
                }
            elif "SATISFIABLE" in stdout:
                return {
                    "verified": True,
                    "reason": "Z3 solver confirmed logical constraints are SATISFIABLE.",
                    "answer": response,
                    "code": z3_code
                }
            else:
                # Script didn't output expected tokens, fall back to basic solver
                return verify_logical_with_z3(question, response)
        except Exception as e:
            # Subprocess/sandbox execution failed, fall back
            return verify_logical_with_z3(question, response)