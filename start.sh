#!/bin/bash
# Timuclaude — Production Start Script
# Starts the LiteLLM proxy with auto-detect backend
#
# If OPENROUTER_API_KEY is set → uses OpenRouter (production, scales to thousands of users)
# If Ollama is running locally → uses Ollama (development, flat $20-100/mo)

set -e

echo "=== Starting Timuclaude ==="

# Check master key
if [ -z "$TIMUCLAUDE_MASTER_KEY" ]; then
    echo "ERROR: TIMUCLAUDE_MASTER_KEY not set"
    echo "Run: export TIMUCLAUDE_MASTER_KEY=\$(openssl rand -hex 32)"
    exit 1
fi

# Auto-detect backend
if [ -n "$OPENROUTER_API_KEY" ]; then
    echo "Backend: OpenRouter (production mode)"
    echo "Master key: set"
    echo ""
    echo "Starting LiteLLM proxy on port 4000 (OpenRouter backend)..."
    exec python -m litellm --config config/litellm.yaml --port 4000 --host 0.0.0.0
else
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "ERROR: Neither OpenRouter nor Ollama is available"
        echo "Set OPENROUTER_API_KEY (get one at https://openrouter.ai/keys)"
        echo "Or start Ollama with: ollama serve"
        exit 1
    fi
    echo "Backend: Ollama (development mode)"
    echo "Master key: set"
    echo ""
    echo "Starting LiteLLM proxy on port 4000 (Ollama backend)..."
    exec python -m litellm --config config/litellm.yaml --port 4000 --host 0.0.0.0
fi