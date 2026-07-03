#!/usr/bin/env python3
"""
Timuclaude Marketing — Zernio Posting Script
Posts content to X/Twitter via Zernio API.

Usage:
  python post.py --file content/origin_story_thread.md --thread
  python post.py --file content/build_diary_week1.md --tweet 1
  python post.py --text "Quick post text here"
  python post.py --file content/origin_story_thread.md --thread --dry-run
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
import ssl

BASE_URL = "https://zernio.com/api/v1"

# Create SSL context that handles cert verification
import certifi
_ssl_ctx = ssl.create_default_context(cafile=certifi.where())


def load_api_key():
    key = os.environ.get("ZERNIO_API_KEY")
    if not key:
        # Try loading from .env
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("ZERNIO_API_KEY"):
                        key = line.strip().split("=", 1)[1].strip('"').strip("'")
                        break
    if not key:
        print("Error: ZERNIO_API_KEY not set")
        print("Get your key from https://zernio.com/dashboard -> Settings -> API Keys")
        sys.exit(1)
    return key


def api_call(endpoint, method="GET", data=None):
    """Make a REST API call to Zernio."""
    key = load_api_key()
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    
    body = None
    if data:
        body = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ssl_ctx) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"API Error {e.code}: {error_body[:500]}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_accounts():
    """Get list of connected accounts."""
    result = api_call("accounts")
    if result and "accounts" in result:
        return result["accounts"]
    return []


def get_twitter_account_id():
    """Find the Twitter account ID."""
    accounts = get_accounts()
    for acc in accounts:
        if acc.get("platform") == "twitter":
            return acc.get("_id")
    return None


def parse_markdown_content(filepath):
    """Parse a markdown content file into individual tweets.
    
    Expected format:
    ## Tweet N (LABEL)
    [tweet text]
    """
    with open(filepath, "r") as f:
        content = f.read()
    
    # Split on ## headers
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
        
        # Skip non-tweet sections
        if not header.lower().startswith("tweet"):
            continue
        
        tweets.append({
            "header": header,
            "text": body,
        })
    
    return tweets


def post_tweet(text, account_id=None, reply_to=None):
    """Post a single tweet via Zernio API."""
    data = {
        "platforms": ["twitter"],
        "text": text,
    }
    if account_id:
        data["accountId"] = account_id
    if reply_to:
        data["replyToId"] = reply_to
    
    result = api_call("posts", method="POST", data=data)
    return result


def post_thread(tweets, account_id=None, delay_seconds=3, dry_run=False):
    """Post a thread (chained tweets)."""
    if not tweets:
        print("No tweets to post")
        return
    
    if dry_run:
        for i, tweet in enumerate(tweets, 1):
            text = tweet["text"] if isinstance(tweet, dict) else tweet
            print(f"\n--- Tweet {i}: {tweet.get('header', '') if isinstance(tweet, dict) else ''} ---")
            print(text)
            print(f"({len(text)} chars)")
        print(f"\n{len(tweets)} tweets total. (DRY RUN — nothing posted)")
        return
    
    # Post first tweet
    first_text = tweets[0]["text"] if isinstance(tweets[0], dict) else tweets[0]
    print(f"Posting tweet 1/{len(tweets)}...")
    result = post_tweet(first_text, account_id)
    
    if not result:
        print("Failed to post first tweet. Aborting.")
        return
    
    post_id = result.get("_id") or result.get("id") or result.get("postId")
    print(f"  Posted: {post_id}")
    
    # Post remaining tweets as replies
    for i, tweet in enumerate(tweets[1:], 2):
        text = tweet["text"] if isinstance(tweet, dict) else tweet
        print(f"Posting tweet {i}/{len(tweets)}...")
        time.sleep(delay_seconds)
        
        result = post_tweet(text, account_id, reply_to=post_id)
        if not result:
            print(f"  Failed to post tweet {i}. Continuing anyway.")
            continue
        
        post_id = result.get("_id") or result.get("id") or result.get("postId")
        print(f"  Posted: {post_id}")
    
    print(f"\nThread complete: {len(tweets)} tweets posted")


def main():
    parser = argparse.ArgumentParser(description="Post to X/Twitter via Zernio")
    parser.add_argument("--file", help="Markdown file with tweet content")
    parser.add_argument("--text", help="Single tweet text")
    parser.add_argument("--thread", action="store_true", help="Post as a thread")
    parser.add_argument("--tweet", type=int, help="Which tweet number to post (for single tweet from file)")
    parser.add_argument("--account", help="Specific account ID to post to")
    parser.add_argument("--dry-run", action="store_true", help="Print tweets without posting")
    parser.add_argument("--list-accounts", action="store_true", help="List connected accounts")
    args = parser.parse_args()
    
    if args.list_accounts:
        accounts = get_accounts()
        print(f"\nConnected accounts ({len(accounts)}):")
        for acc in accounts:
            print(f"  {acc.get('platform'):10} @{acc.get('username', 'N/A'):20} ID: {acc.get('_id')}")
        return
    
    if args.file:
        tweets = parse_markdown_content(args.file)
        
        if not tweets:
            print("No tweets found in file")
            sys.exit(1)
        
        if args.tweet:
            # Post a single tweet from the file
            idx = args.tweet - 1
            if idx >= len(tweets):
                print(f"Tweet {args.tweet} not found (file has {len(tweets)} tweets)")
                sys.exit(1)
            tweets = [tweets[idx]]
        
        if args.dry_run:
            post_thread(tweets, dry_run=True)
            return
        
        # Get Twitter account ID
        account_id = args.account or get_twitter_account_id()
        if not account_id:
            print("No Twitter account found. Connect one at https://zernio.com/dashboard")
            sys.exit(1)
        
        print(f"Using account: {account_id}")
        
        if args.thread or len(tweets) > 1:
            post_thread(tweets, account_id=account_id)
        else:
            text = tweets[0]["text"]
            result = post_tweet(text, account_id)
            if result:
                print(f"Posted: {result}")
            else:
                print("Failed to post")
    
    elif args.text:
        if args.dry_run:
            print(f"[DRY RUN] {args.text}")
            return
        
        account_id = args.account or get_twitter_account_id()
        result = post_tweet(args.text, account_id)
        if result:
            print(f"Posted: {result}")
        else:
            print("Failed to post")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()