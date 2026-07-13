# Pin the upstream Hermes runtime by immutable Linux/amd64 digest.  Render's
# managed Docker runtime is amd64; using a digest prevents an unreviewed
# upstream `latest` update from changing the production agent at deploy time.
FROM nousresearch/hermes-agent@sha256:6ba9f2e4de551c768852f6c7f468ed10d2aec02a921e89722a96b7de507b418a

# The upstream image owns process supervision, runs as a non-root user after
# bootstrapping its state directory, and starts the dashboard only when this
# flag is set. Render routes web services to port 10000 by default.
ENV HERMES_DASHBOARD=true \
    HERMES_DASHBOARD_HOST=0.0.0.0 \
    HERMES_DASHBOARD_PORT=10000 \
    HERMES_HOME=/opt/data \
    HERMES_WRITE_SAFE_ROOT=/opt/data

EXPOSE 10000

# Keep s6 (the upstream supervisor) alive for the dashboard. Do not replace
# this with `hermes --oneshot`: that mode bypasses interactive approvals.
CMD ["sleep", "infinity"]
