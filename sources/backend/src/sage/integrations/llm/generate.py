"""Thin async wrapper around the Gemini text-generation call."""

from google.genai import types

from sage.config import get_app_config
from sage.integrations.llm.client import get_genai_client

# Sage answers from short excerpts: a low thinking level keeps the response within a few
# seconds, while the model's default level took more than 90 seconds per question.
_THINKING_LEVEL = types.ThinkingLevel.LOW


async def generate_text(prompt: str) -> str | None:
    """Return the generated text, or None when the model produced no text (e.g. safety block).

    Uses the SDK's async client (`.aio`): the sync one would block the event loop, and with it
    every other request served by this instance, for the whole duration of the LLM call.
    """
    response = await get_genai_client().aio.models.generate_content(
        model=get_app_config().chat_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            # Sage passes no tools to the model: nothing for the SDK to call automatically.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            thinking_config=types.ThinkingConfig(thinking_level=_THINKING_LEVEL),
        ),
    )
    return response.text
