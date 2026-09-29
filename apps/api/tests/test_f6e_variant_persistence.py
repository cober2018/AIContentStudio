"""FE-F6E planned append-only persistence contract."""

from sqlalchemy import inspect

from app.db import Base


def test_variant_metadata_contains_only_planned_tables_and_candidate_link():
    expected = {
        "channel_variant_revision",
        "channel_variant_asset_ref",
        "channel_variant_evidence_ref",
        "channel_variant_check_run",
    }
    assert expected.issubset(Base.metadata.tables)
    candidate = Base.metadata.tables["content_asset"]
    assert "channel_variant_revision_id" in candidate.c
    assert candidate.c.channel_variant_revision_id.nullable
    assert any(
        foreign_key.column.table.name == "channel_variant_revision"
        for foreign_key in candidate.c.channel_variant_revision_id.foreign_keys
    )
    variant = Base.metadata.tables["channel_variant_revision"]
    assert any(
        foreign_key.column.table.name == "channel_template_version"
        for foreign_key in variant.c.profile_template_version_id.foreign_keys
    )


def test_variant_series_has_database_cas_and_idempotency_constraints(db_session):
    inspector = inspect(db_session.bind)
    constraints = {
        tuple(item["column_names"])
        for item in inspector.get_unique_constraints("channel_variant_revision")
    }
    assert ("content_unit_id", "variant_key", "revision_no") in constraints
    assert ("content_unit_id", "variant_key", "idempotency_key") in constraints
