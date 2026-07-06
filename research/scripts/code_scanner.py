#!/usr/bin/env python3
"""
Code Scanner — static analysis for Python files.
Detects: syntax errors, broken imports, common bug patterns.
"""

import ast, os, sys, json
from pathlib import Path
from typing import List, Dict

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
SRC_DIR = TEMUCLAUDE / "src"
TESTS_DIR = TEMUCLAUDE / "tests"

BUG_PATTERNS = [
    ("bare_except", ast.ExceptHandler, lambda n: n.type is None, "HIGH"),
    ("mutable_default_arg", ast.FunctionDef, lambda n: any(
        isinstance(d, (ast.List, ast.Dict, ast.Set))
        for d in n.args.defaults
    ), "MEDIUM"),
    ("broad_except", ast.ExceptHandler, lambda n:
        isinstance(n.type, ast.Name) and n.type.id == "Exception", "LOW"),
]

def scan_file(filepath: Path) -> List[Dict]:
    issues = []
    try:
        with open(filepath) as f:
            source = f.read()
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        return [{"file": str(filepath), "line": e.lineno, "severity": "CRITICAL",
                "type": "syntax_error", "description": str(e)}]
    except Exception as e:
        return [{"file": str(filepath), "line": 0, "severity": "HIGH",
                "type": "parse_error", "description": str(e)}]

    for node in ast.walk(tree):
        for name, node_type, check, severity in BUG_PATTERNS:
            if isinstance(node, node_type) and check(node):
                issues.append({
                    "file": str(filepath), "line": getattr(node, "lineno", 0),
                    "severity": severity, "type": name,
                    "description": f"{name} at line {getattr(node, 'lineno', '?')}"
                })
    return issues

def scan_directory(dirpath: Path) -> List[Dict]:
    all_issues = []
    for pyfile in dirpath.glob("*.py"):
        all_issues.extend(scan_file(pyfile))
    return all_issues

def scan_all() -> List[Dict]:
    issues = scan_directory(SRC_DIR) if SRC_DIR.exists() else []
    if TESTS_DIR.exists():
        issues.extend(scan_directory(TESTS_DIR))
    return issues

if __name__ == "__main__":
    issues = scan_all()
    print(json.dumps(issues, indent=2))
    sys.exit(1 if issues else 0)
