"""Unit tests for the markdown chunker — pure logic, no GCP calls."""

from sage.domain.qa.chunking import split_into_chunks


def test_splits_by_heading_and_keeps_section_label() -> None:
    text = "# Intro\nHello world\n\n# Details\nMore text here"

    chunks = split_into_chunks(text, max_chars=1000)

    assert [chunk.section for chunk in chunks] == ["Intro", "Details"]
    assert chunks[0].text == "Hello world"
    assert chunks[1].text == "More text here"


def test_splits_long_section_into_multiple_chunks() -> None:
    paragraph = "word " * 400
    text = f"# Section\n{paragraph}\n\n{paragraph}"

    chunks = split_into_chunks(text, max_chars=500)

    assert len(chunks) > 1
    assert all(chunk.section == "Section" for chunk in chunks)


def test_single_long_paragraph_respects_max_chars_and_keeps_all_words() -> None:
    text = "# Section\n" + "parola " * 2000

    chunks = split_into_chunks(text, max_chars=1500)

    assert all(len(chunk.text) <= 1500 for chunk in chunks)
    assert sum(len(chunk.text.split()) for chunk in chunks) == 2000


def test_word_longer_than_max_chars_is_split() -> None:
    chunks = split_into_chunks("x" * 250, max_chars=100)

    assert [len(chunk.text) for chunk in chunks] == [100, 100, 50]


def test_comment_inside_code_block_is_not_a_heading() -> None:
    text = "# Guida\nInstalla:\n\n```bash\n# installa le dipendenze\nuv sync\n```\n"

    chunks = split_into_chunks(text)

    assert {chunk.section for chunk in chunks} == {"Guida"}
    assert "# installa le dipendenze" in chunks[0].text


def test_hash_without_space_is_not_a_heading() -> None:
    chunks = split_into_chunks("# Titolo\n#hashtag nel testo")

    assert [chunk.section for chunk in chunks] == ["Titolo"]
    assert chunks[0].text == "#hashtag nel testo"
