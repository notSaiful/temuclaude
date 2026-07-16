#!/usr/bin/env sh
set -eu

: "${TEMUCLAUDE_API_KEY:?TEMUCLAUDE_API_KEY must be configured as a Fly secret}"
: "${OPENROUTER_API_KEY:?OPENROUTER_API_KEY must be configured as a Fly secret}"
exec uvicorn api_server:app --host 0.0.0.0 --port "${PORT:-8080}" --proxy-headers
