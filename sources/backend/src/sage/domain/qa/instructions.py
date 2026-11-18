"""Additional instructions for the model, read from Cloud Storage at every request."""

import asyncio
import logging

from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError

from sage.integrations.storage.instructions import read_instructions

log = logging.getLogger(__name__)


async def load_instructions() -> str | None:
    """Return the instructions text, or None if the file is missing, empty or unreachable.

    The instructions refine the answer but aren't essential to it: a storage problem is logged
    and the question is still answered, instead of failing the request.
    """
    try:
        # read_instructions uses the blocking (sync) Cloud Storage client.
        instructions = await asyncio.to_thread(read_instructions)
    except (GoogleAPIError, GoogleAuthError):
        log.warning("Istruzioni non disponibili: rispondo senza", exc_info=True)
        return None

    return instructions.strip() or None
