"""Generation step of the RAG pipeline: build the grounded prompt, call the LLM."""

import logging
from pathlib import Path

import httpx
from google.genai.errors import APIError

from sage.domain.qa.exceptions import GenerationError
from sage.domain.qa.models import Chunk
from sage.integrations.llm.generate import generate_text

log = logging.getLogger(__name__)

_PROMPT_TEMPLATE = (Path(__file__).parent / "prompts" / "answer_prompt.txt").read_text(
    encoding="utf-8"
)
_NO_DOCUMENTS_CONTEXT = (
    "Nessun documento disponibile (base di conoscenza non ancora popolata o non configurata)."
)
_INSTRUCTIONS_SECTION = """
Segui anche le seguenti istruzioni aggiuntive in ogni risposta. Riguardano stile e forma: i
contenuti devono comunque provenire solo dagli estratti. Metti le citazioni tra parentesi
quadre su una riga finale, separata dal testo della risposta.

{instructions}
"""


def build_prompt(question: str, chunks: list[Chunk], instructions: str | None = None) -> str:
    context = (
        "\n\n".join(f"[{chunk.source}] {chunk.text}" for chunk in chunks)
        if chunks
        else _NO_DOCUMENTS_CONTEXT
    )
    instructions_section = (
        _INSTRUCTIONS_SECTION.format(instructions=instructions) if instructions else ""
    )
    return _PROMPT_TEMPLATE.format(
        instructions=instructions_section, context=context, question=question
    )


async def generate_answer(
    question: str, chunks: list[Chunk], instructions: str | None = None
) -> str:
    prompt = build_prompt(question, chunks, instructions)

    try:
        answer = await generate_text(prompt)
    except (APIError, httpx.HTTPError, TimeoutError) as exc:
        log.exception("Chiamata al modello fallita")
        raise GenerationError("Servizio di generazione non disponibile") from exc

    if not answer:
        log.error("Il modello non ha restituito testo")
        raise GenerationError("Il modello non ha prodotto una risposta")

    return answer
