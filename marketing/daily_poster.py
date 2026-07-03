#!/usr/bin/env python3
"""
Timuclaude Daily Poster — posts 2 tweets per day at optimal times.
Run via cron: 0 7,12 * * * (7 AM and 12 PM ET)

This script:
1. Picks the right content for the time slot
2. Removes links (algorithm suppression)
3. Posts via Zernio SDK
4. Logs what was posted

Usage:
  python daily_poster.py --slot morning
  python daily_poster.py --slot midday
  python daily_poster.py --slot afternoon
"""

import os
import re
import sys
import json
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from post import get_client, post_tweet, count_effective_chars, TWITTER_ACCOUNT_ID

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content")
LOG_FILE = os.path.join(os.path.dirname(__file__), "posted_log.json")

# Content rotation — each slot has a type
SLOT_CONTENT = {
    "morning": [
        # Proof/benchmark content
        {"file": "conviction_01.md", "tweet": 1},
        {"file": "david_vs_goliath_01.md", "tweet": 1},
        {"file": "origin_story_thread.md", "tweet": 1},  # Long-form origin story
    ],
    "midday": [
        # Build diary / knowledge content
        {"file": "build_diary_week1.md", "tweet": 1},
        {"file": "build_diary_week1.md", "tweet": 2},
        {"file": "build_diary_week1.md", "tweet": 3},
        {"file": "build_diary_week1.md", "tweet": 4},
        {"file": "build_diary_week1.md", "tweet": 5},
        {"file": "build_diary_week1.md", "tweet": 6},
        {"file": "build_diary_week1.md", "tweet": 7},
        {"file": "why_opensource_01.md", "tweet": 1},
    ],
    "afternoon": [
        # Community / engagement content
        {"file": "conviction_01.md", "tweet": 1},
        {"file": "david_vs_goliath_01.md", "tweet": 1},
        {"file": "why_opensource_01.md", "tweet": 1},
    ],
}


def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"posted": [], "last_slot": {}}


def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def get_next_content(slot):
    """Get the next unposted content for this slot."""
    log = load_log()
    posted_keys = set(log.get("posted", []))
    candidates = SLOT_CONTENT.get(slot, [])

    for item in candidates:
        key = f"{item['file']}_{item['tweet']}"
        if key not in posted_keys:
            return item, key

    # All content used — rotate back
    if candidates:
        return candidates[0], f"{candidates[0]['file']}_{candidates[0]['tweet']}"
    return None, None


def clean_tweet(text):
    """Remove links and markdown from tweet text."""
    text = re.sub(r'https?://\S+', 'Link in bio.', text)
    text = text.replace("**", "")
    return text


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Daily Timuclaude poster")
    parser.add_argument("--slot", required=True, choices=["morning", "midday", "afternoon"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    item, key = get_next_content(args.slot)
    if not item:
        print(f"No content for slot: {args.slot}")
        sys.exit(1)

    filepath = os.path.join(CONTENT_DIR, item["file"])
    if not os.path.exists(filepath):
        print(f"Content file not found: {filepath}")
        sys.exit(1)

    # Parse the file
    from post import parse_markdown_content
    tweets = parse_markdown_content(filepath)

    if item["tweet"] - 1 >= len(tweets):
        print(f"Tweet {item['tweet']} not found in {item['file']}")
        sys.exit(1)

    tweet_text = tweets[item["tweet"] - 1]["text"]
    tweet_text = clean_tweet(tweet_text)

    eff = count_effective_chars(tweet_text)
    print(f"Slot: {args.slot}")
    print(f"Content: {item['file']} tweet {item['tweet']}")
    print(f"Effective chars: {eff}")

    # Note: With X Premium, long-form posts up to 25,000 chars are allowed
    # Without Premium, limit is 280 chars
    # For now, skip posts that are too long for free accounts
    if eff > 280:
        print(f"TOO LONG for free account ({eff} chars) — will work with X Premium")
        print("Skipping for now. Get X Premium to enable long-form posts.")
        # Mark as posted so we don't get stuck
        log = load_log()
        log["posted"].append(key)
        save_log(log)
        sys.exit(1)

    if args.dry_run:
        print(f"\n[DRY RUN]\n{tweet_text}")
        return

    # Post it
    result = post_tweet(tweet_text)
    if result:
        print(f"POSTED! ID: {result['id']}")
        log = load_log()
        log["posted"].append(key)
        log["last_slot"][args.slot] = datetime.now().isoformat()
        save_log(log)
    else:
        print("Failed to post")


if __name__ == "__main__":
    main()