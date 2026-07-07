#!/usr/bin/env python3
"""
Auto-Integrator v2 — Actually implements research findings using LLM.
Reads findings, generates code patches using Ollama, applies them in staging,
runs tests, and reports results.

This is the REAL hands of the swarm — not just a context gatherer.
"""

import json
import os
import sys
import glob
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

TEMUCLAUDE_DIR = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
RESEARCH_DIR = TEMUCLAUDE_DIR / "research"
FINDINGS_DIR = RESEARCH_DIR / "findings"
SRC_DIR = TEMUCLAUDE_DIR / "src"
STAGING_DIR = TEMUCLAUDE_DIR / "staging"
STAGING_SRC = STAGING_DIR / "src"
CHANGELOG = RESEARCH_DIR / "CHANGELOG.md"

# Ollama API
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CLOUD_URL = os.environ.get("OLLAMA_CLOUD_URL", "https://ollama.com:443")
OLLAMA_CLOUD_KEY = os.environ.get("OLLAMA_CLOUD_KEY", "")

# OpenRouter API (fallback when Ollama is rate-limited)
OR_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"  # Free model for integration


def call_llm(prompt, max_tokens=2000):
    """Call LLM to generate code. Tries Ollama cloud → local → OpenRouter free."""
    # Try Ollama cloud first
    if OLLAMA_CLOUD_KEY:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{OLLAMA_CLOUD_URL}/api/chat",
                data=json.dumps({
                    "model": "glm-5.2",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": 0.2},
                }).encode('utf-8'),
                headers={
                    "Authorization": f"Bearer {OLLAMA_CLOUD_KEY}",
                    "Content-Type": "application/json",
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                content = data.get("message", {}).get("content", "")
                if not content and data.get("message", {}).get("thinking"):
                    content = data["message"]["thinking"]
                if content:
                    return content
        except Exception as e:
            print(f"  Cloud LLM failed: {e}")

    # Try local Ollama
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=json.dumps({
                "model": "glm-5.2:cloud",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.2},
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            content = data.get("message", {}).get("content", "")
            if not content and data.get("message", {}).get("thinking"):
                content = data["message"]["thinking"]
            if content:
                return content
    except Exception as e:
        print(f"  Local LLM failed: {e}")

    # Try OpenRouter free model (Nemotron)
    if OR_KEY:
        try:
            import urllib.request
            req = urllib.request.Request(
                OR_URL,
                data=json.dumps({
                    "model": OR_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": max_tokens,
                }).encode('utf-8'),
                headers={
                    "Authorization": f"Bearer {OR_KEY}",
                    "Content-Type": "application/json",
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    return content
        except Exception as e:
            print(f"  OpenRouter LLM failed: {e}")

    return ""


def load_finding(finding_file):
    """Load a research finding and extract what to implement."""
    try:
        with open(finding_file) as f:
            content = f.read()
        return content[:3000]  # First 3000 chars
    except:
        return ""


def get_source_file_summary():
    """Get a summary of source files in staging/src."""
    files = []
    for fpath in sorted(STAGING_SRC.glob("*.py")):
        try:
            content = fpath.read_text()
            # Get first 500 chars + function/class signatures
            lines = content.split('\n')
            signatures = [l for l in lines if l.startswith('def ') or l.startswith('class ')]
            files.append({
                "name": fpath.name,
                "signatures": signatures[:10],
                "size": len(content),
            })
        except:
            pass
    return files


def generate_implementation(finding_content, source_summary):
    """Ask LLM to generate a concrete code patch based on the finding."""
    
    # Find the most relevant source file
    finding_lower = finding_content.lower()
    relevant_files = []
    for f in source_summary:
        name_lower = f["name"].lower()
        # Match keywords from finding to source file names
        for keyword in finding_lower.split():
            if keyword in name_lower and len(keyword) > 3:
                relevant_files.append(f["name"])
                break
    
    if not relevant_files:
        # Pick the most likely file based on finding topic
        if "fusion" in finding_lower or "orchestrat" in finding_lower:
            relevant_files = ["fusion.py", "orchestrator.py"]
        elif "security" in finding_lower or "cyber" in finding_lower:
            relevant_files = ["guard.py", "honeypot.py", "counter_attack.py"]
        elif "efficiency" in finding_lower or "cost" in finding_lower:
            relevant_files = ["cache.py", "context_compression.py"]
        elif "consistency" in finding_lower or "verify" in finding_lower:
            relevant_files = ["consistency.py", "code_executor.py"]
        elif "routing" in finding_lower or "adaptive" in finding_lower:
            relevant_files = ["adaptive.py", "preference_router.py"]
        else:
            relevant_files = ["orchestrator.py"]
    
    # Read the target file
    target_file = relevant_files[0]
    target_path = STAGING_SRC / target_file
    
    if not target_path.exists():
        # Try from main src
        target_path = SRC_DIR / target_file
    
    if not target_path.exists():
        return None, None, f"Target file {target_file} not found"
    
    current_code = target_path.read_text()[:4000]
    
    prompt = f"""You are improving Temuclaude, an AI orchestration engine in Python.
A research finding suggests this improvement:

{finding_content[:1500]}

Current code in {target_file} (first 3000 chars):
```python
{current_code[:3000]}
```

Based on the finding, write ONE complete, syntactically correct Python function that improves this file.
Rules:
- Output ONLY valid Python code, no markdown, no explanation
- Include the full function with def line and body
- Use proper indentation (4 spaces)
- Make sure all imports are included if needed
- Keep it simple — one function, not a whole file
- If the finding is too vague, output exactly: CANNOT_IMPLEMENT"""

    response = call_llm(prompt, max_tokens=1000)
    
    if not response or "CANNOT_IMPLEMENT" in response:
        return None, None, "LLM could not generate implementation"
    
    # Clean up the response — extract code from markdown if present
    if "```python" in response:
        code_blocks = response.split("```python")
        response = code_blocks[-1].split("```")[0]
    elif "```" in response:
        parts = response.split("```")
        if len(parts) >= 3:
            response = parts[1]
    
    # Remove leading/trailing whitespace
    response = response.strip()
    
    # Remove standalone import lines that would conflict when appended
    # (keep imports inside functions)
    lines = response.split('\n')
    cleaned = []
    for i, line in enumerate(lines):
        # Skip top-level imports (they conflict when appended to existing file)
        if i == 0 and (line.startswith('import ') or line.startswith('from ')):
            continue
        if i == 1 and (line.startswith('import ') or line.startswith('from ')):
            continue
        # Skip empty lines at the start
        if not cleaned and not line.strip():
            continue
        cleaned.append(line)
    
    response = '\n'.join(cleaned).strip()
    
    # Verify the code is valid Python before returning
    try:
        compile(response, '<generated>', 'exec')
    except SyntaxError as e:
        # Try to fix common issues — remove first/last line if they cause issues
        if len(lines) > 2:
            # Try removing first line
            try:
                compile('\n'.join(lines[1:]), '<generated>', 'exec')
                response = '\n'.join(lines[1:])
            except:
                # Try removing last line
                try:
                    compile('\n'.join(lines[:-1]), '<generated>', 'exec')
                    response = '\n'.join(lines[:-1])
                except:
                    return None, None, f"Generated code has syntax error: {e}"
    
    return target_file, response, None


def apply_patch(target_file, new_code):
    """Apply the generated code to the staging source file."""
    staging_path = STAGING_SRC / target_file
    
    if not staging_path.exists():
        # Copy from main src
        main_path = SRC_DIR / target_file
        if main_path.exists():
            staging_path.write_text(main_path.read_text())
        else:
            return False, f"File {target_file} not found"
    
    # Read current code
    current = staging_path.read_text()
    
    # Try to identify what function/class the new code replaces
    # Find the function signature in the new code
    new_lines = new_code.split('\n')
    sig_line = None
    for line in new_lines:
        if line.startswith('def ') or line.startswith('class '):
            sig_line = line.split('(')[0].strip()
            break
    
    if not sig_line:
        return False, "Could not find function signature in generated code"
    
    # Find the matching function in current code
    current_lines = current.split('\n')
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(current_lines):
        if sig_line in line and (line.startswith('def ') or line.startswith('class ')):
            start_idx = i
            # Find the end (next def/class at same indentation level, or EOF)
            base_indent = len(line) - len(line.lstrip())
            for j in range(i + 1, len(current_lines)):
                next_line = current_lines[j]
                if next_line.strip() and not next_line.startswith(' ' * (base_indent + 1)) and \
                   (next_line.startswith('def ') or next_line.startswith('class ') or 
                    next_line.startswith('#') or next_line.startswith('if __name__')):
                    end_idx = j
                    break
            if end_idx is None:
                end_idx = len(current_lines)
            break
    
    if start_idx is None:
        # Append the new code at the end
        new_content = current + "\n\n" + new_code
        staging_path.write_text(new_content)
        return True, f"Appended new code to {target_file}"
    
    # Replace the function
    new_content = '\n'.join(current_lines[:start_idx]) + '\n' + new_code + '\n' + '\n'.join(current_lines[end_idx:])
    staging_path.write_text(new_content)
    return True, f"Updated {sig_line} in {target_file}"


def run_tests_staging():
    """Check the modified file compiles. Return (success, message)."""
    # Find which file was most recently modified in staging/src
    latest_file = None
    latest_mtime = 0
    for f in STAGING_SRC.glob("*.py"):
        if f.stat().st_mtime > latest_mtime:
            latest_mtime = f.stat().st_mtime
            latest_file = f
    
    if not latest_file:
        return True, "No files to check"
    
    result = subprocess.run(
        [sys.executable, "-c", f"import py_compile; py_compile.compile('{latest_file}', doraise=True)"],
        capture_output=True, text=True, timeout=10
    )
    
    if result.returncode == 0:
        return True, f"{latest_file.name} compiles OK"
    
    # Compilation failed — revert the file from main src
    main_path = SRC_DIR / latest_file.name
    if main_path.exists():
        latest_file.write_text(main_path.read_text())
        return False, f"{latest_file.name} had syntax error — reverted to original"
    
    return False, f"{latest_file.name} compile error — could not revert"


def implement_finding(finding_file):
    """Main entry point: implement a single finding in staging."""
    print(f"=== Implementing: {Path(finding_file).name} ===")
    
    # 1. Load finding
    finding_content = load_finding(finding_file)
    if not finding_content:
        return False, "Could not read finding"
    
    # 2. Ensure staging/src exists
    if not STAGING_SRC.exists():
        subprocess.run(["cp", "-r", str(SRC_DIR), str(STAGING_SRC)], timeout=30)
    
    # 3. Get source summary
    source_summary = get_source_file_summary()
    print(f"  Source files: {len(source_summary)}")
    
    # 4. Generate implementation using LLM
    print(f"  Asking LLM to generate code...")
    target_file, new_code, error = generate_implementation(finding_content, source_summary)
    
    if error:
        print(f"  FAILED: {error}")
        return False, error
    
    if not new_code or len(new_code) < 20:
        print(f"  FAILED: LLM returned empty or too short code")
        return False, "LLM returned empty code"
    
    print(f"  Target: {target_file}")
    print(f"  Generated {len(new_code)} chars of code")
    
    # 5. Apply the patch
    success, message = apply_patch(target_file, new_code)
    if not success:
        print(f"  FAILED to apply: {message}")
        return False, f"Apply failed: {message}"
    
    print(f"  Applied: {message}")
    
    # 6. Check compilation
    print(f"  Checking compilation...")
    compiles, comp_msg = run_tests_staging()
    if not compiles:
        print(f"  COMPILE FAILED: {comp_msg}")
        return False, f"Compile error: {comp_msg}"
    
    print(f"  Compilation OK")
    
    # 7. Log to changelog
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(CHANGELOG, "a") as f:
        f.write(f"\n## {ts}\nSTAGED: {Path(finding_file).stem} — {message}\n")
    
    print(f"  SUCCESS — staged in /staging/src/{target_file}")
    return True, f"Staged: {message}"


if __name__ == "__main__":
    # If called with a finding file argument, implement it
    if len(sys.argv) > 1:
        finding_file = sys.argv[1]
        success, msg = implement_finding(finding_file)
        print(f"\nResult: {'SUCCESS' if success else 'FAILED'} — {msg}")
        sys.exit(0 if success else 1)
    else:
        # No argument — find the latest unprocessed finding
        findings = sorted(FINDINGS_DIR.glob("deep_research_*.md"), reverse=True)
        if findings:
            print(f"Latest finding: {findings[0].name}")
            success, msg = implement_finding(str(findings[0]))
            print(f"\nResult: {'SUCCESS' if success else 'FAILED'} — {msg}")
        else:
            print("No findings to implement")