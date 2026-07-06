#!/bin/bash
# Temuclaude autonomous daily poster — runs via cron, no LLM cost
# Posts 2 tweets/day at optimal times (morning + midday slots)
# Uses pre-written content in marketing/content/, rotates through available tweets
# Logs to posted_log.json, avoids reposts, skips content >280 chars (free account limit)

cd /Users/saiful/temuclaude

SLOT="$1"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Running auto_post slot=$SLOT"

# Run the daily poster
python3 marketing/daily_poster.py --slot "$SLOT" 2>&1

EXIT_CODE=$?
echo "[$TIMESTAMP] Exit code: $EXIT_CODE"

# If poster failed (content too long or error), try evergreen fallback from smart_poster
if [ $EXIT_CODE -ne 0 ]; then
    echo "[$TIMESTAMP] Daily poster failed, trying evergreen fallback..."
    python3 -c "
import sys
sys.path.insert(0, 'marketing')
from smart_poster import get_evergreen_fallback
import random
fallbacks = get_evergreen_fallback('$SLOT')
tweet = random.choice(fallbacks)
print(f'Evergreen tweet: {tweet[:80]}...')
from post import post_tweet
result = post_tweet(tweet)
if result:
    print(f'POSTED! ID: {result[\"id\"]}')
else:
    print('Evergreen post also failed')
" 2>&1
fi

echo "[$TIMESTAMP] Done."