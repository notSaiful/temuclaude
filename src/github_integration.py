"""
Temuclaude GitHub Integration Module
GitHub API integration for code-related queries.

Features:
- Search repositories
- Get README content
- Get file contents
- Search code across repos
- Get repo metadata
- List issues

Uses GitHub REST API (no auth for public repos, token optional).
"""
import asyncio
import os
import re
from typing import Optional, List, Dict
from urllib.parse import quote

try:
    import aiohttp
except ImportError:
    aiohttp = None


GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def _get_headers() -> Dict:
    """Get headers for GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Temuclaude/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def _parse_repo_url(url: str) -> tuple:
    """Parse a GitHub URL to extract owner and repo.

    Returns (owner, repo) or (None, None).
    """
    match = re.match(r'https?://github\.com/([^/]+)/([^/\s]+)', url)
    if match:
        owner = match.group(1)
        repo = match.group(2).rstrip("/").removesuffix(".git")
        return owner, repo
    return None, None


async def search_repos(
    query: str,
    language: Optional[str] = None,
    sort: str = "stars",
    limit: int = 10,
) -> List[Dict]:
    """Search GitHub repositories.

    Args:
        query: Search query
        language: Filter by language
        sort: Sort by (stars, forks, updated)
        limit: Number of results

    Returns:
        List of repo dicts: {name, full_name, url, description, stars, language}
    """
    if aiohttp is None:
        raise RuntimeError("aiohttp not installed")

    q = query
    if language:
        q += f" language:{language}"

    params = {"q": q, "sort": sort, "order": "desc", "per_page": min(limit, 30)}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{GITHUB_API}/search/repositories",
            params=params,
            headers=_get_headers(),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            data = await resp.json()

    repos = []
    for item in data.get("items", [])[:limit]:
        repos.append({
            "name": item.get("name", ""),
            "full_name": item.get("full_name", ""),
            "url": item.get("html_url", ""),
            "description": item.get("description", ""),
            "stars": item.get("stargazers_count", 0),
            "language": item.get("language", ""),
            "forks": item.get("forks_count", 0),
        })

    return repos


async def get_readme(owner: str, repo: str) -> Dict:
    """Get README content of a repository.

    Returns:
        Dict with: content, encoding, url
    """
    if aiohttp is None:
        raise RuntimeError("aiohttp not installed")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/readme",
            headers=_get_headers(),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 404:
                return {"content": "", "error": "No README found"}
            data = await resp.json()

    import base64
    content = ""
    if data.get("encoding") == "base64":
        content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    else:
        content = data.get("content", "")

    return {
        "content": content,
        "encoding": data.get("encoding", ""),
        "url": data.get("html_url", ""),
    }


async def get_file(owner: str, repo: str, path: str, branch: Optional[str] = None) -> Dict:
    """Get file contents from a repository.

    Args:
        owner: Repo owner
        repo: Repo name
        path: File path
        branch: Branch name (default branch if None)

    Returns:
        Dict with: content, encoding, path, size
    """
    if aiohttp is None:
        raise RuntimeError("aiohttp not installed")

    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{quote(path, safe='/')}"
    if branch:
        url += f"?ref={branch}"

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=_get_headers(),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 404:
                return {"content": "", "error": "File not found"}
            data = await resp.json()

    import base64
    content = ""
    if data.get("encoding") == "base64":
        content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    else:
        content = data.get("content", "")

    return {
        "content": content,
        "encoding": data.get("encoding", ""),
        "path": data.get("path", path),
        "size": data.get("size", 0),
    }


async def search_code(query: str, language: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Search code across GitHub repositories.

    Args:
        query: Code search query
        language: Filter by language
        limit: Number of results

    Returns:
        List of {file, repo, url, text_matches}
    """
    if aiohttp is None:
        raise RuntimeError("aiohttp not installed")

    q = query
    if language:
        q += f" language:{language}"

    params = {"q": q, "per_page": min(limit, 30)}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{GITHUB_API}/search/code",
            params=params,
            headers=_get_headers(),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 403:
                return [{"error": "Code search requires authentication. Set GITHUB_TOKEN."}]
            data = await resp.json()

    results = []
    for item in data.get("items", [])[:limit]:
        results.append({
            "file": item.get("name", ""),
            "repo": item.get("repository", {}).get("full_name", ""),
            "url": item.get("html_url", ""),
            "path": item.get("path", ""),
        })

    return results


async def get_repo_info(owner: str, repo: str) -> Dict:
    """Get repository metadata.

    Returns:
        Dict with: name, description, stars, forks, language, license, topics, etc.
    """
    if aiohttp is None:
        raise RuntimeError("aiohttp not installed")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{GITHUB_API}/repos/{owner}/{repo}",
            headers=_get_headers(),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 404:
                return {"error": "Repository not found"}
            data = await resp.json()

    return {
        "name": data.get("name", ""),
        "full_name": data.get("full_name", ""),
        "description": data.get("description", ""),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "watchers": data.get("watchers_count", 0),
        "language": data.get("language", ""),
        "license": (data.get("license") or {}).get("name", ""),
        "topics": data.get("topics", []),
        "open_issues": data.get("open_issues_count", 0),
        "default_branch": data.get("default_branch", "main"),
        "created_at": data.get("created_at", ""),
        "updated_at": data.get("updated_at", ""),
        "url": data.get("html_url", ""),
    }


async def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10,
) -> List[Dict]:
    """List issues in a repository.

    Args:
        owner: Repo owner
        repo: Repo name
        state: "open", "closed", or "all"
        limit: Number of issues

    Returns:
        List of issue dicts
    """
    if aiohttp is None:
        raise RuntimeError("aiohttp not installed")

    params = {"state": state, "per_page": min(limit, 30), "sort": "created", "direction": "desc"}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues",
            params=params,
            headers=_get_headers(),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            data = await resp.json()

    issues = []
    for item in data[:limit]:
        if "pull_request" in item:
            continue  # Skip PRs
        issues.append({
            "number": item.get("number", 0),
            "title": item.get("title", ""),
            "state": item.get("state", ""),
            "url": item.get("html_url", ""),
            "labels": [l.get("name", "") for l in item.get("labels", [])],
            "created_at": item.get("created_at", ""),
        })

    return issues


def detect_github_url(text: str) -> Optional[str]:
    """Detect a GitHub URL in text."""
    match = re.search(r'https?://github\.com/[^\s<>"\']+', text)
    return match.group(0) if match else None