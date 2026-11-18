"""Google Gen AI SDK client, in Vertex AI mode (ADC-based, no API key)."""

from functools import lru_cache

from google import genai

from sage.config import get_app_config

# Gemini models aren't served on every regional Vertex AI endpoint: "global" is the endpoint with the broadest model availability, independent of SAGE_REGION (which
# only places the infrastructure resources, via Terraform).
_VERTEX_LOCATION = "global"


@lru_cache
def get_genai_client() -> genai.Client:
    config = get_app_config()
    return genai.Client(vertexai=True, project=config.project_id, location=_VERTEX_LOCATION)
