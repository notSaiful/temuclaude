#!/usr/bin/env python3
"""Radar Sources — monitors industry signals from multiple sources."""

import json, os, sys, time, re, subprocess
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen, Request

USER_AGENT = "TemuclaudeRadar/1.0"

def fetch_url(url, timeout=30):
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""

def fetch_json(url, timeout=30):
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return {}

def scan_hackernews():
    signals = []
    data = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    for story_id in data[:30]:
        story = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if not story:
            continue
        title = story.get("title", "").lower()
        ai_kw = ["ai", "llm", "model", "gpt", "gemini", "claude", "openai", "anthropic",
                 "inference", "transformer", "neural", "agent", "vllm", "huggingface"]
        if any(kw in title for kw in ai_kw):
            signals.append({
                "source": "hackernews",
                "title": story.get("title", ""),
                "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                "score": story.get("score", 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        time.sleep(0.3)
    return signals

def scan_github_trending():
    signals = []
    url = ("https://api.github.com/search/repositories?"
           "q=topic:llm+created:>2026-06-01&sort=stars&order=desc&per_page=20")
    data = fetch_json(url)
    for repo in data.get("items", []):
        signals.append({
            "source": "github_trending",
            "title": repo.get("full_name", ""),
            "url": repo.get("html_url", ""),
            "stars": repo.get("stargazers_count", 0),
            "description": repo.get("description", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return signals

def scan_huggingface_models():
    signals = []
    data = fetch_json("https://huggingface.co/api/models?sort=downloads&direction=-1&limit=20&full=true")
    for model in data[:20]:
        if model.get("downloads", 0) < 1000:
            continue
        signals.append({
            "source": "huggingface",
            "title": model.get("modelId", ""),
            "url": f"https://huggingface.co/{model.get('modelId', '')}",
            "downloads": model.get("downloads", 0),
            "tags": model.get("tags", []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return signals

def scan_rss_feeds():
    signals = []
    feeds = [
        ("Anthropic", "https://www.anthropic.com/rss.xml"),
        ("HuggingFace", "https://huggingface.co/blog/feed.xml"),
        ("LangChain", "https://blog.langchain.dev/rss/"),
    ]
    for name, url in feeds:
        content = fetch_url(url, timeout=15)
        if not content:
            continue
        items = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)
        for item in items[:3]:
            title = re.search(r"<title>(.*?)</title>", item, re.DOTALL)
            if title:
                signals.append({
                    "source": f"rss_{name.lower()}",
                    "title": title.group(1).strip(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    return signals

def scan_competitor_changelogs():
    signals = []
    for repo in [("vllm-project/vllm", "vllm_releases"), ("BerriAI/litellm", "litellm_releases")]:
        url = f"https://api.github.com/repos/{repo[0]}/releases?per_page=3"
        data = fetch_json(url)
        for release in data[:3]:
            signals.append({
                "source": repo[1],
                "title": f"{repo[1].split('_')[0]} {release.get('tag_name', '')}",
                "url": release.get("html_url", ""),
                "description": (release.get("body", "") or "")[:500],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    return signals

def scan_reddit():
    signals = []
    for sub in ["LocalLLaMA", "MachineLearning"]:
        data = fetch_json(f"https://www.reddit.com/r/{sub}/hot.json?limit=10")
        for post in data.get("data", {}).get("children", [])[:10]:
            p = post.get("data", {})
            signals.append({
                "source": f"reddit_{sub}",
                "title": p.get("title", ""),
                "url": p.get("url", ""),
                "score": p.get("score", 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    return signals

def scan_all_sources():
    all_signals = []
    for fn in [scan_hackernews, scan_github_trending, scan_huggingface_models,
               scan_rss_feeds, scan_competitor_changelogs, scan_reddit]:
        try:
            all_signals.extend(fn())
        except Exception:
            pass
    return all_signals

if __name__ == "__main__":
    signals = scan_all_sources()
    print(json.dumps(signals, indent=2))
