#!/usr/bin/env python3
"""
Temuclaude Smart Poster — agent-generated tweets based on real project activity.
This script is called by the cron job agent. It gathers context and provides it
to the agent, who then crafts an authentic tweet and posts it.

The agent's prompt (in the cron job) instructs it to:
1. Run this script to gather context
2. Craft a tweet based on real findings
3. Post via post.py
4. Fall back to evergreen content if nothing happened
"""

import os
import sys
import json
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKETING_DIR = os.path.dirname(os.path.abspath(__file__))

def run(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15, cwd=PROJECT_ROOT)
        return result.stdout.strip()
    except:
        return ""

def gather():
    """Gather all real context for the agent to use."""
    from gather_context import gather_all
    return gather_all()

def get_evergreen_fallback(slot):
    """Get evergreen content for when nothing happened."""
    evergreen = {
        "morning": [
            "The AI industry wants ONE model to rule them all. Wrong game. The right game: use ALL of them. Together. Every model has different blind spots. Fusion catches them. The future is not one model. It is orchestration.",
            "OpenAI spent $500M on GPT-5.6. Google spent $300M on Gemini 3.5. Temuclaude uses all of them. For free. On your laptop. No training budget. Just orchestration. Link in bio.",
        ],
        "midday": [
            "Why is Temuclaude open-source? Because AI should not be locked behind API keys and credit cards. Because a student in India should not need OpenAI credits for world-class AI. Free with Ollama. No cloud. No bills. Link in bio.",
            "I spent 3 days debugging why fusion gave worse answers than a single model. Problem: averaging answers. Fix: weighted voting by confidence. Sure models get more weight. +12% accuracy overnight.",
        ],
        "evening": [
            "Single LLMs get hard questions wrong. Not obviously wrong. Subtly, confidently wrong. The kind of wrong that ships to production and breaks things at 3 AM. And you do not know WHICH ones. That is the problem Temuclaude solves.",
        ],
    }
    return evergreen.get(slot, evergreen["morning"])

def post_tweet(text):
    """Post a tweet via Zernio SDK."""
    sys.path.insert(0, MARKETING_DIR)
    from post import post_tweet as _post_tweet
    return _post_tweet(text)

def log_post(content_key, tweet_text, result):
    """Log what was posted."""
    log_file = os.path.join(MARKETING_DIR, "posted_log.json")
    if os.path.exists(log_file):
        with open(log_file) as f:
            log = json.load(f)
    else:
        log = {"posted": [], "history": []}
    
    log["posted"].append(content_key)
    log["history"].append({
        "key": content_key,
        "text": tweet_text[:100],
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "result": "success" if result else "failed",
        "post_id": result.get("id") if result else None,
    })
    
    with open(log_file, "w") as f:
        json.dump(log, f, indent=2)

if __name__ == "__main__":
    # When run directly, just gather and print context
    data = gather()
    from gather_context import print_human_readable
    print_human_readable(data)
    print("\n\nEVERGREEN FALLBACK (if nothing to post about):")
    import sys
    slot = sys.argv[1] if len(sys.argv) > 1 else "morning"
    fallback = get_evergreen_fallback(slot)
    for i, tweet in enumerate(fallback, 1):
        print(f"  Evergreen {i}: {tweet[:80]}...")