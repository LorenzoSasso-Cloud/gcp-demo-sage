"""The ingestion script must not lose existing chunks when Vertex AI fails midway."""

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).parents[1] / "utils" / "ingest_documents.py"
spec = importlib.util.spec_from_file_location("ingest_documents", SCRIPT)
ingest_documents = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest_documents)


@pytest.fixture(autouse=True)
def project_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAGE_PROJECT_ID", "progetto")


def test_embedding_failure_leaves_existing_chunks_untouched(tmp_path: Path) -> None:
    document = tmp_path / "doc.md"
    document.write_text("# A\nuno\n\n# B\ndue\n", encoding="utf-8")

    with (
        patch.object(ingest_documents, "embed_text", side_effect=[[0.1], RuntimeError("429")]),
        patch.object(ingest_documents, "delete_chunks_for_source") as delete,
        patch.object(ingest_documents, "add_chunk") as add,
        pytest.raises(RuntimeError),
    ):
        ingest_documents.ingest_file(document)

    delete.assert_not_called()
    add.assert_not_called()
