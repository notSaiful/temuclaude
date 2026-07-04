#!/usr/bin/env python3
"""
Temuclaude Marketing — Zernio Posting Script (v2)
Posts content to X/Twitter via Zernio Python SDK.

Usage:
  python post.py --file content/origin_story_thread.md --thread
  python post.py --file content/build_diary_week1.md --tweet 1
  python post.py --text "Quick post text here"
  python post.py --file content/origin_story_thread.md --thread --dry-run
  python post.py --list-accounts
"""

import argparse
import os
import re
import sys
import time

from zernio import Zernio

TWITTER_ACCOUNT_ID = "6a420f509d9472faae1b5ca6"


def load_api_key():
    key = os.environ.get("ZERNIO_API_KEY")
    if not key:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("ZERNIO_API_KEY"):
                        key = line.strip().split("=", 1)[1].strip('"').strip("'")
                        break
    if not key:
        print("Error: ZERNIO_API_KEY not set")
        sys.exit(1)
    return key


def get_client():
    return Zernio(load_api_key())


def list_accounts():
    """List all connected accounts."""
    z = get_client()
    resp = z.accounts.list()
    print(f"\nConnected accounts:")
    for acc in resp.accounts:
        print(f"  {acc.platform.value:10} @{acc.username:20} ID: {acc.field_id}")
    return resp.accounts


def count_effective_chars(text):
    """Count effective Twitter chars (URLs = 23 chars)."""
    return len(re.sub(r'https?://\S+', 'x' * 23, text))


def post_tweet(text, account_id=TWITTER_ACCOUNT_ID, reply_to_id=None):
    """Post a single tweet via Zernio SDK."""
    z = get_client()

    effective = count_effective_chars(text)
    if effective > 280:
        print(f"  WARNING: Tweet is {effective} effective chars (limit 280)")
        return None

    platform_data = {
        "accountId": account_id,
        "platform": "twitter",
    }

    # Add replyTo if specified (for threads)
    if reply_to_id:
        platform_data["platformSpecificData"] = {
            "replyToTweetId": reply_to_id
        }

    try:
        result = z.posts.create(
            content=text,
            platforms=[platform_data],
            publish_now=True,
        )

        status = result.post.status
        if hasattr(status, 'value'):
            status = status.value

        if status == "published":
            post_id = result.post.field_id
            url = None
            tweet_id = None
            for p in result.post.platforms:
                if hasattr(p, 'platform_post_url') and p.platform_post_url:
                    url = p.platform_post_url
                if hasattr(p, 'platform_post_id') and p.platform_post_id:
                    tweet_id = p.platform_post_id
            return {
                "id": post_id,
                "status": "published",
                "url": url,
                "tweet_id": tweet_id,
            }
        else:
            err = None
            for p in result.post.platforms:
                if hasattr(p, 'error_message') and p.error_message:
                    err = p.error_message
            print(f"  Publish failed: {err}")
            return None

    except Exception as e:
        print(f"  Error: {e}")
        return None


def post_thread(tweets, account_id=TWITTER_ACCOUNT_ID, dry_run=False):
    """Post a thread (chained tweets)."""
    if not tweets:
        print("No tweets to post")
        return

    if dry_run:
        for i, tweet in enumerate(tweets, 1):
            text = tweet["text"] if isinstance(tweet, dict) else tweet
            eff = count_effective_chars(text)
            status = "OK" if eff <= 280 else f"TOO LONG ({eff})"
            print(f"\n--- Tweet {i}: {tweet.get('header', '') if isinstance(tweet, dict) else ''} ---")
            print(text)
            print(f"({eff} effective chars) [{status}]")
        print(f"\n{len(tweets)} tweets total. (DRY RUN)")
        return

    # Post first tweet
    first_text = tweets[0]["text"] if isinstance(tweets[0], dict) else tweets[0]
    print(f"Posting tweet 1/{len(tweets)}...")
    result = post_tweet(first_text, account_id)

    if not result:
        print("Failed to post first tweet. Aborting.")
        return

    print(f"  Posted! ID: {result['id']}")
    if result.get("url"):
        print(f"  URL: {result['url']}")

    # For threads, we need the tweet_id (not post_id) for reply chaining
    prev_tweet_id = result.get("tweet_id")
    if not prev_tweet_id:
        print("  Warning: no tweet_id returned, cannot chain thread as replies")
        print("  Posting remaining tweets as standalone posts...")
        prev_tweet_id = None

    for i, tweet in enumerate(tweets[1:], 2):
        text = tweet["text"] if isinstance(tweet, dict) else tweet
        print(f"Posting tweet {i}/{len(tweets)}...")
        time.sleep(3)

        result = post_tweet(text, account_id, reply_to_id=prev_tweet_id)
        if not result:
            print(f"  Failed to post tweet {i}. Continuing.")
            continue

        print(f"  Posted! ID: {result['id']}")
        prev_tweet_id = result.get("tweet_id") or prev_tweet_id

    print(f"\nThread complete: {len(tweets)} tweets posted")


def parse_markdown_content(filepath):
    """Parse a markdown content file into individual tweets."""
    with open(filepath, "r") as f:
        content = f.read()

    sections = re.split(r"^## ", content, flags=re.MULTILINE)

    tweets = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        lines = section.split("\n", 1)
        if len(lines) < 2:
            continue
        header = lines[0].strip()
        body = lines[1].strip()

        if not header.lower().startswith("tweet"):
            continue

        # CRITICAL: Remove external links to avoid 30-94% algorithm suppression
        # Links should go in replies, not in the tweet body
        body = re.sub(r'https?://\S+', 'Link in bio.', body)
        # Remove markdown bold
        body = body.replace("**", "")

        tweets.append({"header": header, "text": body})

    return tweets


def main():
    parser = argparse.ArgumentParser(description="Post to X/Twitter via Zernio")
    parser.add_argument("--file", help="Markdown file with tweet content")
    parser.add_argument("--text", help="Single tweet text")
    parser.add_argument("--thread", action="store_true", help="Post as a thread")
    parser.add_argument("--tweet", type=int, help="Which tweet number to post")
    parser.add_argument("--dry-run", action="store_true", help="Print without posting")
    parser.add_argument("--list-accounts", action="store_true", help="List accounts")
    args = parser.parse_args()

    if args.list_accounts:
        list_accounts()
        return

    if args.file:
        tweets = parse_markdown_content(args.file)
        if not tweets:
            print("No tweets found in file")
            sys.exit(1)

        if args.tweet:
            idx = args.tweet - 1
            if idx >= len(tweets):
                print(f"Tweet {args.tweet} not found (file has {len(tweets)} tweets)")
                sys.exit(1)
            tweets = [tweets[idx]]

        if args.thread or len(tweets) > 1:
            post_thread(tweets, dry_run=args.dry_run)
        else:
            if args.dry_run:
                eff = count_effective_chars(tweets[0]["text"])
                print(f"[DRY RUN] ({eff} effective chars)")
                print(tweets[0]["text"])
                return
            result = post_tweet(tweets[0]["text"])
            if result:
                print(f"Posted! ID: {result['id']}")
                if result.get("url"):
                    print(f"URL: {result['url']}")
            else:
                print("Failed to post")

    elif args.text:
        if args.dry_run:
            eff = count_effective_chars(args.text)
            print(f"[DRY RUN] ({eff} effective chars)")
            print(args.text)
            return
        result = post_tweet(args.text)
        if result:
            print(f"Posted! ID: {result['id']}")
        else:
            print("Failed to post")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()