#!/bin/bash
# Timuclaude — Production Start Script
# Starts the LiteLLM proxy with Timuclaude configuration

set -e

echo "=== Starting Timuclaude ==="

# Check environment
if [ -z "$TIMUCLAUDE_MASTER_KEY" ]; then
    echo "ERROR: TIMUCLAUDE_MASTER_KEY not set"
    echo "Run: export TIMUCLAUDE_MASTER_KEY=\$(openssl rand -hex 32)"
    exit 1
fi

# Check Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "ERROR: Ollama is not running"
    echo "Start it with: ollama serve"
    exit 1
fi

echo "Ollama: OK"
echo "Master key: set"
echo ""

# Start LiteLLM proxy
echo "Starting LiteLLM proxy on port 4000..."
exec python -m litellm --config config/litellm.yaml --port 4000 --host 0.0.0.0