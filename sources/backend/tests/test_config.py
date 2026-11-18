"""Resource names derived from the configuration."""

from sage.config import AppConfig


def test_shared_project_derives_names_from_prefix() -> None:
    config = AppConfig(project_id="progetto", resource_prefix="its-ict-sage-mario-rossi")

    assert config.instructions_bucket == "its-ict-sage-mario-rossi-instructions"
    assert config.firestore_database == "its-ict-sage-mario-rossi"
    assert config.bq_dataset == "its_ict_sage_mario_rossi_sage_analytics"


def test_dedicated_project_derives_bucket_from_project_id() -> None:
    config = AppConfig(project_id="progetto", resource_prefix="")

    assert config.instructions_bucket == "progetto-instructions"
