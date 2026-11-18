"""Errors raised by the QA pipeline. Plain Python exceptions, no FastAPI imports."""


class SageError(Exception):
    """Base class for QA-pipeline failures. Translated to HTTPException at the API boundary."""


class EmbeddingError(SageError):
    """The question could not be embedded (Vertex AI error, quota exhausted, ...)."""


class GenerationError(SageError):
    """The model call failed, or the model returned no text."""
