"""Retrieval step of the RAG pipeline: embed the question, fetch the nearest chunks."""

import asyncio
import logging

import httpx
from google.api_core.exceptions import GoogleAPIError
from google.genai.errors import APIError

from sage.domain.qa.exceptions import EmbeddingError
from sage.domain.qa.models import Chunk
from sage.integrations.firestore.chunks import find_nearest_chunks
from sage.integrations.llm.embeddings import embed_text

log = logging.getLogger(__name__)


async def retrieve_relevant_chunks(question: str) -> list[Chunk]:
    # embed_text and find_nearest_chunks use blocking (sync) GCP SDK clients.
    try:
        embedding = await asyncio.to_thread(embed_text, question, "RETRIEVAL_QUERY")
    except (APIError, httpx.HTTPError) as exc:
        log.exception("Calcolo dell'embedding della domanda fallito")
        raise EmbeddingError("Servizio di embedding non disponibile") from exc

    try:
        chunks = await asyncio.to_thread(find_nearest_chunks, embedding)
    except GoogleAPIError:
        # Firestore not provisioned yet (database/collection missing), or not reachable: this
        # integration is meant to be added incrementally, so fall back to no context instead
        # of failing the request. GoogleAPIError also covers timeouts (RetryError).
        log.warning(
            "Firestore non raggiungibile: rispondo senza contesto documentale", exc_info=True
        )
        return []

    log.info("Recuperati %d chunk da Firestore", len(chunks))
    return chunks
