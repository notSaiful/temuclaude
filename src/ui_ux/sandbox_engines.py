"""
Temuclaude Benchmark Scaffolding & Sandbox Engines

Contains sandbox environments for:
1. Programmatic file creation (Excel/PDF/PPTX) validation (GDPval-AA v2)
2. Interactive terminal execution & debug loop (Terminal-Bench v2.1)
"""
import os
import sys
import subprocess
import tempfile
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ProgrammaticFileSandbox:
    """Executes Python code to generate artifacts (docs/sheets/slides) and verifies them."""

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout

    def execute_and_verify(self, python_code: str, expected_filenames: List[str]) -> Dict[str, Any]:
        """Execute python code in a secure temp sandbox, checking for file output.
        
        Args:
            python_code: Python script to write files.
            expected_filenames: File names expected to be created (e.g., 'report.xlsx').
            
        Returns:
            Dict containing execution success, file logs, and output file statuses.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write Python script to temp directory
            script_path = os.path.join(temp_dir, "generator.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(python_code)

            # Prepare execution environment (no network, offline)
            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))

            try:
                # Execute Python script inside the temp directory
                result = subprocess.run(
                    [sys.executable, "generator.py"],
                    cwd=temp_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=self.timeout,
                    text=True
                )
                
                execution_ok = (result.returncode == 0)
                stdout = result.stdout
                stderr = result.stderr
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"Timeout expired after {self.timeout}s during file generation.",
                    "files_created": {}
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Execution failed: {e}",
                    "files_created": {}
                }

            # Check for created files
            file_results = {}
            for filename in expected_filenames:
                file_path = os.path.join(temp_dir, filename)
                exists = os.path.isfile(file_path)
                size = os.path.getsize(file_path) if exists else 0
                
                # Check formatting metadata if file is Excel
                file_metadata = {}
                if exists and filename.endswith(".xlsx"):
                    try:
                        import openpyxl
                        wb = openpyxl.load_workbook(file_path, read_only=True)
                        file_metadata["sheet_names"] = wb.sheetnames
                    except Exception as e:
                        file_metadata["xlsx_parse_error"] = str(e)
                
                file_results[filename] = {
                    "exists": exists,
                    "size_bytes": size,
                    "metadata": file_metadata
                }

            all_files_exist = all(meta["exists"] for meta in file_results.values())
            success = execution_ok and all_files_exist

            return {
                "success": success,
                "exit_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "files_created": file_results
            }


class PTYTerminalSandbox:
    """Executes shell commands in a local subprocess sandbox and parses outputs for debugging."""

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def execute_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute a terminal command and return execution details.
        
        Args:
            command: Shell command to run (e.g. 'pytest tests/').
            cwd: Working directory.
            
        Returns:
            Dict containing exit_code, stdout, stderr, and failure debug analysis.
        """
        # Clean command to prevent escape
        command = command.strip()

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                text=True
            )

            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode

            # Extract debugging context if failed
            debug_info = None
            if exit_code != 0:
                debug_info = self._generate_debug_context(command, stdout, stderr)

            return {
                "success": (exit_code == 0),
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "debug_info": debug_info
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -9,
                "stdout": "",
                "stderr": f"Command timed out after {self.timeout}s.",
                "debug_info": f"Timeout triggered on command: '{command}'"
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "debug_info": f"System error executing command: {e}"
            }

    def _generate_debug_context(self, command: str, stdout: str, stderr: str) -> str:
        """Construct a structured debug report from stdout/stderr for LLM self-correction."""
        error_context = stderr or stdout
        # Truncate error if too long
        if len(error_context) > 2000:
            error_context = error_context[:1000] + "\n\n... [TRUNCATED] ...\n\n" + error_context[-1000:]

        return (
            f"COMMAND FAILED: '{command}'\n"
            f"=== ERROR LOG ===\n"
            f"{error_context}\n"
            f"=================\n"
            f"Analyze the error logs above, explain why the command failed, "
            f"and propose a corrected command sequence or code patch."
        )
