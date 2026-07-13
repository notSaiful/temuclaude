# Pin the upstream Hermes runtime by immutable Linux/amd64 digest. Using a
# digest prevents an unreviewed upstream `latest` update from changing the
# production agent at deploy time.
FROM nousresearch/hermes-agent@sha256:6ba9f2e4de551c768852f6c7f468ed10d2aec02a921e89722a96b7de507b418a

# Cloud Run injects PORT and expects a process that listens on it. Hermes'
# OpenAI-compatible API server is the right surface for TemuClaude: it exposes
# chat, runs, approvals, streaming, and health checks. `hermes serve` is the
# dashboard/WebSocket protocol and is intentionally not used here.
#
# The deploy must supply API_SERVER_KEY from Secret Manager. The image contains
# no credentials or unsafe default. A model-provider credential is configured
# separately at deploy time.
ENV PORT=8080 \
    API_SERVER_ENABLED=true \
    API_SERVER_HOST=0.0.0.0 \
    API_SERVER_MODEL_NAME=temuclaude-hermes \
    HERMES_HOME=/opt/data \
    HERMES_WRITE_SAFE_ROOT=/opt/data

# The API server must not inherit Hermes' broad interactive CLI toolset.
# Production capability is added later through individually reviewed tool
# bridges that retain TemuClaude approval records. Until then, API callers
# get model + run/approval APIs only: no shell, filesystem, browser, or MCP.
COPY services/hermes/config.cloudrun.yaml /opt/data/config.yaml

EXPOSE 8080

# `gateway run --no-supervise` remains in the foreground so Cloud Run can
# supervise it. Do not use `--oneshot`, `--yolo`, or `--accept-hooks`: each
# removes a human safety gate that must remain available to the control plane.
CMD ["sh", "-c", "export API_SERVER_PORT=\"${PORT:-8080}\"; exec hermes gateway run --no-supervise"]
