"""Reads the additional instructions file from the `<prefix>-instructions` bucket."""

from sage.config import get_app_config
from sage.integrations.storage.client import get_storage_client


def read_instructions() -> str:
    config = get_app_config()
    blob = get_storage_client().bucket(config.instructions_bucket).blob(config.instructions_object)
    return blob.download_as_text(encoding="utf-8")
