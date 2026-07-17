"""Fly.io API entrypoint for TemuClaude's Python orchestration service.

The Vercel application remains the public product gateway. This service is for
server-to-server orchestration and deliberately requires a separate API key.
"""
from __future__ import annotations

import hmac
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from src.orchestrator import Temuclaude
from src.security_pipeline import secure_complete

MAX_MESSAGES = 50
MAX_MESSAGE_CHARS = 20_000
MAX_TOTAL_CHARS = 100_000


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)

    @field_validator("content")
    @classmethod
    def require_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content cannot be blank")
        return value


class ChatRequest(BaseModel):
    model: str = "temuclaude"
    messages: list[ChatMessage] = Field(min_length=1, max_length=MAX_MESSAGES)
    temperature: float = Field(default=0.6, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    model_profile: Literal["pro", "lite"] = "pro"
    budget_profile: Literal["max_quality", "max_savings", "balanced"] = "max_quality"

    @field_validator("messages")
    @classmethod
    def bound_total_input(cls, value: list[ChatMessage]) -> list[ChatMessage]:
        if sum(len(message.content) for message in value) > MAX_TOTAL_CHARS:
            raise ValueError("messages exceed 100,000 characters")
        return value


def _allowed_origins() -> list[str]:
    raw = os.environ.get("TEMUCLAUDE_CORS_ORIGINS", "")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.orchestrator = Temuclaude()
    yield


app = FastAPI(title="TemuClaude API", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)
origins = _allowed_origins()
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["POST"],
        allow_headers=["Authorization", "Content-Type"],
    )


def _require_api_key(authorization: str | None) -> None:
    expected = os.environ.get("TEMUCLAUDE_API_KEY", "")
    provided = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not expected or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/models")
async def list_models(authorization: str | None = Header(default=None)) -> dict:
    _require_api_key(authorization)
    return {"object": "list", "data": [{"id": "temuclaude", "object": "model", "owned_by": "temuclaude"}]}


@app.post("/v1/chat/completions")
async def chat_completions(payload: ChatRequest, request: Request, authorization: str | None = Header(default=None)) -> dict:
    _require_api_key(authorization)
    user_messages = [message.content for message in payload.messages if message.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="at least one user message is required")
    system_messages = [message.content for message in payload.messages if message.role == "system"]
    session_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    result = await secure_complete(
        user_messages[-1],
        app.state.orchestrator.complete,
        system_prompt="\n\n".join(system_messages) or None,
        session_id=session_id[:128],
        orchestrator_kwargs={"budget_profile": payload.budget_profile},
    )
    if result.blocked:
        raise HTTPException(status_code=400, detail=result.block_reason or "Request blocked by security policy")
    prompt_tokens = sum(len(message.content.split()) for message in payload.messages)
    completion_tokens = len(result.response.split())
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}", "object": "chat.completion", "created": int(time.time()),
        "model": payload.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": result.response}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": prompt_tokens + completion_tokens},
    }
