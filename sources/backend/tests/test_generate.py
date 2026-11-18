"""Time limits and fallback model of the Gemini call, with a fake client."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from google.genai.errors import ServerError

from sage.domain.qa.exceptions import GenerationError
from sage.domain.qa.generation import generate_answer
from sage.integrations.llm import generate

UNAVAILABLE = ServerError(503, {"error": {"code": 503, "message": "unavailable"}})


class FakeModels:
    def __init__(self, outcomes: list[float | Exception]) -> None:
        self.outcomes = outcomes
        self.models: list[str] = []

    async def generate_content(self, *, model: str, **_: object) -> SimpleNamespace:
        outcome = self.outcomes[len(self.models)]
        self.models.append(model)
        if isinstance(outcome, Exception):
            raise outcome
        await asyncio.sleep(outcome)
        return SimpleNamespace(text="Risposta")


def use_fake(models: FakeModels):
    client = SimpleNamespace(aio=SimpleNamespace(models=models))
    return (
        patch.object(generate, "get_genai_client", lambda: client),
        patch.object(generate, "get_app_config", lambda: SimpleNamespace(chat_model="principale")),
        patch.object(generate, "_FAST_TIMEOUT_SECONDS", 0.05),
        patch.object(generate, "_LAST_TIMEOUT_SECONDS", 0.05),
    )


async def test_main_model_answers_on_the_first_attempt() -> None:
    models = FakeModels([0])
    client, config, fast, last = use_fake(models)

    with client, config, fast, last:
        assert await generate.generate_text("prompt") == "Risposta"

    assert models.models == ["principale"]


@pytest.mark.parametrize("failure", [1, UNAVAILABLE])
async def test_stalled_or_failing_model_falls_back(failure: float | Exception) -> None:
    models = FakeModels([failure, 0])
    client, config, fast, last = use_fake(models)

    with client, config, fast, last:
        assert await generate.generate_text("prompt") == "Risposta"

    assert models.models == ["principale", generate._FALLBACK_MODEL]


async def test_gives_up_after_the_last_attempt() -> None:
    models = FakeModels([1, 1, 1])
    client, config, fast, last = use_fake(models)

    with client, config, fast, last, pytest.raises(TimeoutError):
        await generate.generate_text("prompt")

    assert models.models == ["principale", generate._FALLBACK_MODEL, "principale"]


async def test_timeout_becomes_a_generation_error() -> None:
    with (
        patch("sage.domain.qa.generation.generate_text", AsyncMock(side_effect=TimeoutError())),
        pytest.raises(GenerationError),
    ):
        await generate_answer("domanda", [])
