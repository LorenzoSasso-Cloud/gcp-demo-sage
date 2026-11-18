"""Thin async wrapper around the Gemini text-generation call."""

import asyncio
import logging
from typing import NamedTuple

import httpx
from google.genai import types
from google.genai.errors import APIError

from sage.config import get_app_config
from sage.integrations.llm.client import get_genai_client

log = logging.getLogger(__name__)

# Sage answers from short excerpts: a low thinking level keeps the response within a few
# seconds, while the model's default level took more than 90 seconds per question.
_THINKING_LEVEL = types.ThinkingLevel.LOW

# The main model usually answers in 3-15 seconds but sometimes stalls for minutes, and retrying
# it right away tends to stall again: a different, faster model answers in the meantime.
_FALLBACK_MODEL = "gemini-3.5-flash-lite"
_FAST_TIMEOUT_SECONDS = 20
_LAST_TIMEOUT_SECONDS = 60


class _Attempt(NamedTuple):
    model: str
    thinking_level: types.ThinkingLevel | None
    timeout_seconds: float


def _attempts(chat_model: str) -> tuple[_Attempt, ...]:
    return (
        _Attempt(chat_model, _THINKING_LEVEL, _FAST_TIMEOUT_SECONDS),
        _Attempt(_FALLBACK_MODEL, None, _FAST_TIMEOUT_SECONDS),
        _Attempt(chat_model, _THINKING_LEVEL, _LAST_TIMEOUT_SECONDS),
    )


async def generate_text(prompt: str) -> str | None:
    """Return the generated text, or None when the model produced no text (e.g. safety block).

    Uses the SDK's async client (`.aio`): the sync one would block the event loop, and with it
    every other request served by this instance, for the whole duration of the LLM call.

    Raises the last error when every attempt fails or exceeds its time limit.
    """
    client = get_genai_client()
    attempts = _attempts(get_app_config().chat_model)
    last_error: Exception | None = None

    for number, attempt in enumerate(attempts, start=1):
        thinking_config = (
            types.ThinkingConfig(thinking_level=attempt.thinking_level)
            if attempt.thinking_level
            else None
        )
        config = types.GenerateContentConfig(
            # Sage passes no tools to the model: nothing for the SDK to call automatically.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            thinking_config=thinking_config,
        )
        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=attempt.model, contents=prompt, config=config
                ),
                timeout=attempt.timeout_seconds,
            )
        except (TimeoutError, APIError, httpx.HTTPError) as exc:
            last_error = exc
            log.warning(
                "Tentativo %d/%d con %s fallito: %s",
                number,
                len(attempts),
                attempt.model,
                type(exc).__name__,
            )
        else:
            return response.text

    raise last_error
