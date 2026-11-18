"""POST /api/ask with every GCP integration replaced by a fake."""

from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from google.api_core.exceptions import Forbidden, NotFound, RetryError
from google.genai.errors import ClientError

from sage.domain.qa.models import Chunk
from sage.webapp.app import app

CHUNK = Chunk(id="a-0", text="Sage usa Firestore.", source="a.md", section="Intro", chunk_index=0)
RATE_LIMITED = ClientError(429, {"error": {"code": 429, "message": "quota"}})


@pytest.fixture
def api() -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def generate_text() -> Iterator[AsyncMock]:
    with patch("sage.domain.qa.generation.generate_text", AsyncMock(return_value="Risposta")) as m:
        yield m


@pytest.fixture
def gcp(generate_text: AsyncMock) -> Iterator[dict]:
    with (
        patch("sage.domain.qa.instructions.read_instructions", return_value="Parla come Dante."),
        patch("sage.domain.qa.retrieval.embed_text", return_value=[0.1]) as embed,
        patch("sage.domain.qa.retrieval.find_nearest_chunks", return_value=[CHUNK]) as nearest,
    ):
        yield {"embed": embed, "nearest": nearest, "generate": generate_text}


def ask(api: TestClient):
    return api.post("/api/ask", json={"question": "Cos'è Sage?"})


def test_response_format_is_unchanged_and_instructions_reach_the_model(
    api: TestClient, gcp: dict
) -> None:
    response = ask(api)

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Risposta",
        "sources": [{"source": "a.md", "section": "Intro", "chunk_index": 0}],
    }
    assert "Parla come Dante." in gcp["generate"].await_args.args[0]


def test_instructions_are_read_at_every_request(api: TestClient, gcp: dict) -> None:
    with patch(
        "sage.domain.qa.instructions.read_instructions", side_effect=["Prima.", "Seconda."]
    ) as read:
        ask(api)
        ask(api)

    assert read.call_count == 2
    assert "Seconda." in gcp["generate"].await_args.args[0]


@pytest.mark.parametrize("error", [NotFound("manca"), Forbidden("vietato")])
def test_unavailable_instructions_do_not_fail_the_request(
    api: TestClient, gcp: dict, error: Exception
) -> None:
    with patch("sage.domain.qa.instructions.read_instructions", side_effect=error):
        response = ask(api)

    assert response.status_code == 200
    assert "istruzioni aggiuntive" not in gcp["generate"].await_args.args[0]


@pytest.mark.parametrize("error", [NotFound("manca"), RetryError("timeout", cause=None)])
def test_firestore_failure_falls_back_to_no_context(
    api: TestClient, gcp: dict, error: Exception
) -> None:
    gcp["nearest"].side_effect = error

    response = ask(api)

    assert response.status_code == 200
    assert response.json()["sources"] == []


def test_embedding_failure_returns_502(api: TestClient, gcp: dict) -> None:
    gcp["embed"].side_effect = RATE_LIMITED

    assert ask(api).status_code == 502


def test_model_failure_returns_502(api: TestClient, gcp: dict) -> None:
    gcp["generate"].side_effect = RATE_LIMITED

    assert ask(api).status_code == 502


def test_empty_model_answer_returns_502(api: TestClient, gcp: dict) -> None:
    gcp["generate"].return_value = None

    assert ask(api).status_code == 502
