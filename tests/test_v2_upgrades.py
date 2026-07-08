import pytest
import os
import json
import asyncio
from typing import Dict, Any

from src.memory_bank_v2 import VoyagerMemoryBank
from src.ui_ux.sandbox_engines import ProgrammaticFileSandbox, PTYTerminalSandbox
from src.verifier import verify_logical_with_z3_enhanced, verify_logical_with_z3
from src.orchestrator import Temuclaude


def test_voyager_memory_bank(tmp_path):
    """Test skill storage and retrieval in VoyagerMemoryBank."""
    storage_file = os.path.join(tmp_path, "skills_library.json")
    bank = VoyagerMemoryBank(storage_path=storage_file)
    
    # Check loading empty library
    assert len(bank.skills) == 0
    
    # Add a skill
    bank.add_skill(
        query="write a python list sorting function",
        skill_code="def sort_list(lst):\n    return sorted(lst)",
        task_type="coding",
        metadata={"author": "test"}
    )
    
    assert len(bank.skills) == 1
    assert bank.skills[0]["task_type"] == "coding"
    
    # Reload and check persistence
    bank2 = VoyagerMemoryBank(storage_path=storage_file)
    assert len(bank2.skills) == 1
    
    # Retrieve skill by keyword fallback
    results = bank2.find_skills(query="python function sort a list", task_type="coding")
    assert len(results) == 1
    assert "sort_list" in results[0]["skill_code"]


def test_programmatic_file_sandbox():
    """Test generating files in ProgrammaticFileSandbox."""
    sandbox = ProgrammaticFileSandbox(timeout=5)
    
    code = (
        "import openpyxl\n"
        "wb = openpyxl.Workbook()\n"
        "ws = wb.active\n"
        "ws['A1'] = 'Test Excel File'\n"
        "wb.save('report.xlsx')\n"
    )
    
    result = sandbox.execute_and_verify(code, expected_filenames=["report.xlsx"])
    assert result["success"] is True
    assert "report.xlsx" in result["files_created"]
    assert result["files_created"]["report.xlsx"]["exists"] is True
    assert result["files_created"]["report.xlsx"]["size_bytes"] > 0
    assert "Sheet" in result["files_created"]["report.xlsx"]["metadata"].get("sheet_names", [])


def test_pty_terminal_sandbox():
    """Test running shell commands in PTYTerminalSandbox."""
    sandbox = PTYTerminalSandbox(timeout=5)
    
    # Success case
    result = sandbox.execute_command("echo 'hello terminal'")
    assert result["success"] is True
    assert "hello terminal" in result["stdout"]
    assert result["exit_code"] == 0
    assert result["debug_info"] is None
    
    # Failure case
    result_fail = sandbox.execute_command("nonexistent_command_xyz_123")
    assert result_fail["success"] is False
    assert result_fail["exit_code"] != 0
    assert result_fail["debug_info"] is not None
    assert "COMMAND FAILED" in result_fail["debug_info"]


@pytest.mark.asyncio
async def test_verify_logical_with_z3_enhanced():
    """Test logical verification utilizing verify_logical_with_z3_enhanced with mock."""
    question = "If it rains then the ground is wet. It rains. Is the ground wet?"
    response = "Yes, since rain implies wet ground and it is raining, the ground must be wet."
    
    # Mock model call that returns Z3 solver Python code
    z3_mock_code = (
        "from z3 import Solver, Bool, Implies, And, sat\n"
        "solver = Solver()\n"
        "rains = Bool('rains')\n"
        "ground_wet = Bool('ground_wet')\n"
        "solver.add(Implies(rains, ground_wet))\n"
        "solver.add(rains)\n"
        "solver.add(ground_wet)\n"
        "print('SATISFIABLE' if solver.check() == sat else 'UNSATISFIABLE')\n"
    )
    
    async def mock_call(model, messages, max_tokens=2048, temperature=0.0):
        return f"```python\n{z3_mock_code}```"
        
    result = await verify_logical_with_z3_enhanced(
        question, response, "deepseek-v4-pro", mock_call
    )
    
    assert result["verified"] is True
    assert "SATISFIABLE" in result["reason"]
    assert result["code"] == z3_mock_code.strip()


@pytest.mark.asyncio
async def test_project_multimodal_inputs():
    """Test multimodal visual projection helper in orchestrator."""
    tc = Temuclaude()
    
    # Mock visual query containing path to a chart image
    visual_query = "Describe the data points in this chart: /Users/saiful/chart.png"
    
    # Mock fallback to call_model
    mock_description = "The chart is a bar chart showing Sales data with points at Q1: 100, Q2: 120, Q3: 150."
    
    # Patch call_model_with_fallback
    async def mock_call(model, messages, max_tokens=1024, temperature=0.0):
        return mock_description
        
    tc.call_model_with_fallback = mock_call
    
    projected = await tc.project_multimodal_inputs(visual_query)
    
    assert "Visual Component Description" in projected
    assert "Q1: 100" in projected
