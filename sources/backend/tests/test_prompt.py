"""The prompt sent to the model — pure logic, no GCP calls."""

from sage.domain.qa.generation import build_prompt
from sage.domain.qa.models import Chunk

CHUNK = Chunk(id="a-0", text="Sage usa Firestore.", source="a.md", section=None, chunk_index=0)


def test_instructions_are_added_to_the_prompt() -> None:
    prompt = build_prompt("Cos'è Sage?", [CHUNK], "Rispondi come Dante.")

    assert "Rispondi come Dante." in prompt
    assert "[a.md] Sage usa Firestore." in prompt
    assert prompt.index("Rispondi come Dante.") < prompt.index("Domanda: Cos'è Sage?")


def test_prompt_without_instructions_has_no_instructions_section() -> None:
    prompt = build_prompt("Cos'è Sage?", [CHUNK], None)

    assert "istruzioni aggiuntive" not in prompt


def test_curly_braces_in_user_content_do_not_break_the_prompt() -> None:
    prompt = build_prompt("Cosa fa {question}?", [CHUNK], "Usa {graffe} nel testo.")

    assert "Cosa fa {question}?" in prompt
    assert "Usa {graffe} nel testo." in prompt
