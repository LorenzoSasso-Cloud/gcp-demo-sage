"""Text embedding via Vertex AI."""

from typing import Literal

from google.genai import types

from sage.config import get_app_config
from sage.integrations.llm.client import get_genai_client

EmbeddingTaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]


def embed_text(text: str, task_type: EmbeddingTaskType) -> list[float]:
    """Embed `text`; the dimension must match the Firestore vector index (devops/cloud/firestore.tf)."""
    config = get_app_config()
    client = get_genai_client()
    result = client.models.embed_content(
        model=config.embedding_model,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=config.embedding_dimension,
        ),
    )
    return result.embeddings[0].values
