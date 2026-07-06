#!/usr/bin/env python3
"""
Marketing Daemon — generates fresh content from project context every 4 hours.
Gathers git log, test count, research findings, benchmark results.
Writes new short-form tweets to marketing/content/short_form/.
Tracks engagement on posted tweets. Uses Ollama free models.
"""

import json, time, os, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
CONTENT_DIR = TEMUCLAUDE / "marketing" / "content" / "short_form"
POSTED_LOG = TEMUCLAUDE / "marketing" / "posted_log.json"


class MarketingDaemon(DaemonBase):
    def __init__(self):
        super().__init__("marketing_daemon")
        self.content_count = 0

    def run_once(self) -> bool:
        context = self._gather_context()
        tweet = self._generate_tweet(context)
        if tweet and self._validate_tweet(tweet):
            self._save_tweet(tweet)
            self.logger.info(f"Generated tweet {self.content_count}: {tweet[:60]}...")
        else:
            self.logger.info("No new tweet generated this cycle")
        self._track_engagement()
        return True

    def _gather_context(self) -> dict:
        context = {}
        # Git log
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True, text=True, timeout=10, cwd=TEMUCLAUDE
            )
            context["recent_commits"] = result.stdout.strip()
        except Exception:
            context["recent_commits"] = ""

        # Test count
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--co", "-q"],
                capture_output=True, text=True, timeout=30, cwd=TEMUCLAUDE
            )
            for line in result.stdout.split("\n"):
                if "test" in line.lower() and "collected" in line.lower():
                    context["test_count"] = line.strip()
                    break
        except Exception:
            context["test_count"] = "unknown"

        # Source files
        src_dir = TEMUCLAUDE / "src"
        context["source_files"] = len(list(src_dir.glob("*.py"))) if src_dir.exists() else 0

        # Research findings count
        findings_dir = TEMUCLAUDE / "research" / "findings"
        context["research_reports"] = len(list(findings_dir.glob("deep_research_*.md"))) if findings_dir.exists() else 0

        return context

    def _generate_tweet(self, context: dict) -> str:
        try:
            from ollama_client import call_model
            prompt = f"""Write a tweet about Temuclaude, an open-source AI that beats frontier models at 50x lower cost.
Use this real context:
- Recent commits: {context.get('recent_commits', 'unknown')[:200]}
- Tests: {context.get('test_count', 'unknown')}
- Source modules: {context.get('source_files', 0)}
- Research reports: {context.get('research_reports', 0)}

Write ONE tweet under 250 characters. No hashtags. No links. Just punchy, factual content.
Focus on one impressive fact. Be direct."""

            result = call_model("glm-5.2:cloud", prompt, max_tokens=300)
            response = result.get("response", "").strip()
            # Clean up any preamble
            if "##" in response:
                response = response.split("##")[-1].strip()
            return response
        except Exception as e:
            self.logger.exception(f"Tweet generation failed: {e}")
            return ""

    def _validate_tweet(self, tweet: str) -> bool:
        import re
        effective = len(re.sub(r'https?://\S+', 'x' * 23, tweet))
        if effective > 280:
            return False
        if len(tweet) < 20:
            return False
        # Check not a duplicate of recent posts
        if POSTED_LOG.exists():
            try:
                posts = json.loads(POSTED_LOG.read_text())
                recent = [p.get("content", "") for p in posts[-10:]]
                if tweet in recent:
                    return False
            except Exception:
                pass
        return True

    def _save_tweet(self, tweet: str):
        CONTENT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        filename = f"generated_{ts}.md"
        filepath = CONTENT_DIR / filename
        content = f"## Tweet 1\n\n{tweet}\n"
        filepath.write_text(content)
        self.content_count += 1

    def _track_engagement(self):
        # Check engagement on last 5 posted tweets
        if not POSTED_LOG.exists():
            return
        try:
            posts = json.loads(POSTED_LOG.read_text())
            recent = posts[-5:]
            for post in recent:
                # Would call Twitter API here to get engagement
                pass
        except Exception:
            pass


def main():
    daemon = MarketingDaemon()
    daemon.run(interval=14400)  # 4 hours


if __name__ == "__main__":
    main()
