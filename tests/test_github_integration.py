"""Tests for github_integration module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.github_integration import (
    _parse_repo_url, detect_github_url, _get_headers
)


def test_parse_repo_url():
    owner, repo = _parse_repo_url("https://github.com/microsoft/vscode")
    assert owner == "microsoft"
    assert repo == "vscode"


def test_parse_repo_url_with_dot_git():
    owner, repo = _parse_repo_url("https://github.com/microsoft/vscode.git")
    assert owner == "microsoft"
    assert repo == "vscode"


def test_parse_repo_url_invalid():
    owner, repo = _parse_repo_url("https://example.com/page")
    assert owner is None
    assert repo is None


def test_detect_github_url():
    result = detect_github_url("Check https://github.com/microsoft/vscode for details")
    assert result is not None
    assert "github.com" in result


def test_detect_github_url_none():
    assert detect_github_url("No URL here") is None


def test_get_headers():
    headers = _get_headers()
    assert "Accept" in headers
    assert "User-Agent" in headers
    assert "Temuclaude" in headers["User-Agent"]


def test_get_headers_with_token():
    import os
    old_token = os.environ.get("GITHUB_TOKEN", "")
    os.environ["GITHUB_TOKEN"] = "test_token_123"
    try:
        headers = _get_headers()
        assert "Authorization" in headers
        assert "test_token_123" in headers["Authorization"]
    finally:
        if old_token:
            os.environ["GITHUB_TOKEN"] = old_token
        else:
            os.environ.pop("GITHUB_TOKEN", None)