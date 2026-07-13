"""Cloud Run compatibility hooks for the private Hermes API server.

TemuClaude's OpenAI-compatible endpoint emits a valid completed response after
its orchestration pipeline has finished.  Hermes normally prefers its provider
streaming path even for API-server callers without a stream consumer.  That is
useful for providers with native token streams, but it can incorrectly report
an empty stream for a completed-response gateway.

This hook affects only the API-server adapter and only when explicitly enabled
by the Cloud Run manifest.  Interactive Hermes platforms keep their default
streaming behavior.  Keeping the switch environment-gated makes rollback a
single safe configuration change.
"""

from __future__ import annotations

import os


def _enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _force_completed_provider_responses() -> None:
    if not _enabled(os.getenv("HERMES_API_SERVER_FORCE_NON_STREAMING")):
        return

    from gateway.platforms.api_server import APIServerAdapter

    original_create_agent = APIServerAdapter._create_agent
    if getattr(original_create_agent, "_temuclaude_force_non_streaming", False):
        return

    def create_agent_with_completed_provider_response(self, *args, **kwargs):
        agent = original_create_agent(self, *args, **kwargs)
        agent._disable_streaming = True
        return agent

    create_agent_with_completed_provider_response._temuclaude_force_non_streaming = True
    APIServerAdapter._create_agent = create_agent_with_completed_provider_response


try:
    _force_completed_provider_responses()
except Exception:
    # Never prevent the runtime from starting because an upstream Hermes image
    # changes an internal adapter name. The health probe will expose a failed
    # model request, and pinning the base image makes this path reproducible.
    pass
