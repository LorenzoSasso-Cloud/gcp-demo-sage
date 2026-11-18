"""Markdown chunking, shared by the ingestion script (utils/ingest_documents.py) and
tests. Pure logic, no I/O and no GCP calls, so it stays trivially testable.
"""

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^#{1,6}\s+\S")
_CODE_FENCE = re.compile(r"^\s*(```|~~~)")


@dataclass(frozen=True)
class RawChunk:
    text: str
    section: str | None
    chunk_index: int


def split_into_chunks(markdown_text: str, max_chars: int = 1500) -> list[RawChunk]:
    """Split markdown into chunks, using the nearest heading above each chunk as its section."""
    chunks: list[RawChunk] = []

    for heading, body in _split_by_heading(markdown_text):
        for piece in _split_by_size(body, max_chars):
            if not piece.strip():
                continue
            chunks.append(RawChunk(text=piece.strip(), section=heading, chunk_index=len(chunks)))

    return chunks


def _split_by_heading(markdown_text: str) -> list[tuple[str | None, str]]:
    sections: list[tuple[str | None, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []
    in_code_block = False

    for line in markdown_text.splitlines():
        if _CODE_FENCE.match(line):
            in_code_block = not in_code_block

        # Inside a code block a leading "#" is a comment, not a heading.
        if not in_code_block and _HEADING.match(line):
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines)))
            current_heading = line.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines)))

    return sections or [(None, markdown_text)]


def _split_by_size(text: str, max_chars: int) -> list[str]:
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    pieces: list[str] = []
    current = ""
    for paragraph in paragraphs:
        for part in _split_long_paragraph(paragraph, max_chars):
            candidate = f"{current}\n\n{part}" if current else part
            if len(candidate) > max_chars and current:
                pieces.append(current)
                current = part
            else:
                current = candidate
    pieces.append(current)

    return pieces


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    """Break a paragraph longer than max_chars at word boundaries (mid-word only if unavoidable)."""
    if len(paragraph) <= max_chars:
        return [paragraph]

    parts: list[str] = []
    current = ""
    for word in paragraph.split():
        while len(word) > max_chars:
            if current:
                parts.append(current)
                current = ""
            parts.append(word[:max_chars])
            word = word[max_chars:]

        candidate = f"{current} {word}" if current else word
        if len(candidate) > max_chars:
            parts.append(current)
            current = word
        else:
            current = candidate

    if current:
        parts.append(current)
    return parts
