#!/bin/bash
# Timuclaude — Setup Script
# Run this to set up the development environment

set -e

echo "=== Timuclaude Setup ==="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python: $PYTHON_VERSION"

# Check if Hermes venv exists (use it for Ollama + litellm)
HERMES_VENV="$HOME/.hermes/hermes-agent/venv"
if [ -d "$HERMES_VENV" ]; then
    echo "Using Hermes venv: $HERMES_VENV"
    PYTHON="$HERMES_VENV/bin/python"
    PIP="$HERMES_VENV/bin/pip"
else
    echo "Hermes venv not found, using system Python"
    PYTHON="python3"
    PIP="pip3"
fi

# Install dependencies
echo ""
echo "=== Installing dependencies ==="
$PIP install litellm "litellm[proxy]" openai pyyaml aiohttp 2>&1 | tail -5

# Set environment variables
echo ""
echo "=== Setting environment variables ==="
export TIMUCLAUDE_MASTER_KEY="${TIMUCLAUDE_MASTER_KEY:-$(openssl rand -hex 32)}"
echo "TIMUCLAUDE_MASTER_KEY is set (change it for production)"

# Check Ollama is running
echo ""
echo "=== Checking Ollama ==="
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Ollama is running"
    # Check cloud models are available
    for model in glm-5.2:cloud deepseek-v4-pro:cloud kimi-k2.6:cloud minimax-m3:cloud nemotron-3-ultra:cloud gpt-oss:120b-cloud; do
        if ollama show "$model" > /dev/null 2>&1; then
            echo "  OK: $model"
        else
            echo "  MISSING: $model (run: ollama pull $model)"
        fi
    done
else
    echo "WARNING: Ollama is not running. Start it with: ollama serve"
fi

# Run tests
echo ""
echo "=== Running tests ==="
$PYTHON tests/test_orchestrator.py

echo ""
echo "=== Setup complete ==="
echo "To start the LiteLLM proxy:"
echo "  export TIMUCLAUDE_MASTER_KEY=your-key"
echo "  $PYTHON -m litellm --config config/litellm-minimal.yaml --port 4000"