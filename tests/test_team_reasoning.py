"""Tests for team_reasoning module."""
import sys
import asyncio
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.team_reasoning import (
    build_leader_prompt, build_researcher_prompt, build_analyst_prompt,
    build_critic_prompt, team_solve, format_chatroom, TeamResult
)


def test_build_leader_prompt():
    messages = build_leader_prompt("How does AI work?")
    assert len(messages) == 2
    assert "Team Leader" in messages[0]["content"]


def test_build_researcher_prompt():
    messages = build_researcher_prompt("What is ML?", "")
    assert len(messages) == 2
    assert "Researcher" in messages[0]["content"]


def test_build_analyst_prompt():
    messages = build_analyst_prompt(["finding 1", "finding 2"], "How does AI work?")
    assert len(messages) == 2
    assert "Analyst" in messages[0]["content"]


def test_build_critic_prompt():
    messages = build_critic_prompt("Some analysis", "How does AI work?")
    assert len(messages) == 2
    assert "Critic" in messages[0]["content"]


def test_team_solve_fallback():
    result = asyncio.run(team_solve("What is 2+2?", model_fn=None))
    assert isinstance(result, TeamResult)
    assert result.plan
    assert result.final_answer


def test_team_solve_with_mock():
    async def mock_fn(messages):
        return "Mock response"
    result = asyncio.run(team_solve("test question", model_fn=mock_fn))
    assert isinstance(result, TeamResult)
    assert len(result.research) > 0


def test_format_chatroom():
    from src.team_reasoning import AgentMessage
    msgs = [
        AgentMessage(agent="Leader", content="Plan here", timestamp=0),
        AgentMessage(agent="Researcher", content="Found stuff", timestamp=1),
    ]
    result = format_chatroom(msgs)
    assert "[Leader]" in result
    assert "[Researcher]" in result