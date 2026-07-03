#!/bin/bash
# Timuclaude — Production Start Script
# Starts the LiteLLM proxy with OpenRouter backend

set -e

echo "=== Starting Timuclaude ==="

# Check environment
if [ -z "$TIMUCLAUDE_MASTER_KEY" ]; then
    echo "ERROR: TIMUCLAUDE_MASTER_KEY not set"
    echo "Run: export TIMUCLAUDE_MASTER_KEY=\$(openssl rand -hex 32)"
    exit 1
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: OPENROUTER_API_KEY not set"
    echo "Get one at: https://openrouter.ai/keys"
    exit 1
fi

echo "OpenRouter API key: set"
echo "Master key: set"
echo ""

# Start LiteLLM proxy
echo "Starting LiteLLM proxy on port 4000 (OpenRouter backend)..."
exec python -m litellm --config config/litellm.yaml --port 4000 --host 0.0.0.0