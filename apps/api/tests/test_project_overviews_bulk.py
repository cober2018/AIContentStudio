"""Batch Overview parity, live gates, and bounded Home summary reads."""

from copy import deepcopy

import pytest
from sqlalchemy import event, select

from app.models import (
    ContentAsset,
    ContentPersona,
    ContentProject,
    ContentUnit,
    CreativeBriefRevision,
    DeliveryAttempt,
    DeliveryReceipt,
    DeliveryTarget,
    FactPack,
    FactPackItem,
    IdentitySnapshot,
    Material,
    MaterialRevision,
    ProjectFactBoundaryRevision,
    Review,
    Workflow,
    WorkflowRun,
    WorkflowStep,
)
from app.services.candidates import candidate_hash
from app.services.project_overview import project_overview, project_overviews
from app.services.project_projection_context import ProjectProjectionContext


@pytest.fixture
def projection_env(db_session):
    db = db_session
    pack = FactPack(name="批量证据", version=1, status="frozen", checksum="7" * 64)
    db.add(pack)
    db.flush()
    project = ContentProject(owner_user_id=1, title="Batch")
    persona = ContentPersona(owner_user_id=1, name="Author")
    material = Material(title="Cover", kind="image")
    workflow = Workflow(name="Batch", definition_json={})
    db.add_all([project, persona, material, workflow])
    db.flush()
    snapshot = IdentitySnapshot(owner_user_id=1, persona_id=persona.id,
                                effective_profile_json={"voice": "clear"}, checksum="i" * 64)
    revision = MaterialRevision(material_id=material.id, content_hash="m" * 64,
                                public_use_allowed=True, rights_status="cleared")
    boundary = ProjectFactBoundaryRevision(project_id=project.id, revision_no=2,
                                           fact_pack_id=pack.id, fact_pack_version=1,
                                           fact_pack_checksum=pack.checksum)
    item = FactPackItem(fact_pack_id=pack.id, evidence_kind="author_opinion",
                        snapshot_checksum="e" * 64, public_use_allowed=True)
    db.add_all([snapshot, revision, boundary, item])
    db.flush()
    unit = ContentUnit(project_id=project.id, persona_id=persona.id, identity_snapshot_id=snapshot.id,
                       title="Current", modality="text", status="ready")
    db.add_all([unit, CreativeBriefRevision(project_id=project.id, revision_no=2,
                                                objective="Latest", checksum="b" * 64)])
    db.flush()
    db.add_all([
        CreativeBriefRevision(project_id=project.id, revision_no=1, objective="Old", checksum="a" * 64),
        ProjectFactBoundaryRevision(project_id=project.id, revision_no=1,
                                    fact_pack_id=pack.id, fact_pack_version=1,
                                    fact_pack_checksum="old"),
        ContentUnit(project_id=project.id, persona_id=persona.id, title="Archived", modality="video",
                    status="archived"),
    ])
    old = ContentAsset(project_id=project.id, content_unit_id=unit.id, channel="wechat",
                       title="Old", final_body="Old", candidate_hash="o" * 64)
    db.add(old)
    db.flush()
    manifest = {"schema_version": 3, "evidence": {"boundary_id": boundary.id},
                "media": [{"material_revision_id": revision.id}]}
    checksum = candidate_hash(manifest)
    candidate = ContentAsset(project_id=project.id, content_unit_id=unit.id, channel="wechat",
                             title="Current", final_body="Body",
                             candidate_manifest_json=manifest, candidate_hash=checksum,
                             approved_candidate_hash=checksum, status="approved")
    db.add(candidate)
    db.flush()
    target = DeliveryTarget(content_asset_id=candidate.id, channel="wechat", content_form="article",
                            account_ref="owner", authorization_version="v1", approved_candidate_hash=checksum,
                            status="human_confirmed")
    historical_target = DeliveryTarget(content_asset_id=old.id, channel="wechat", content_form="article",
                                       account_ref="old", authorization_version="v1",
                                       approved_candidate_hash=old.candidate_hash, status="reconciliation_needed")
    run = WorkflowRun(workflow_id=workflow.id, content_unit_id=unit.id, status="succeeded")
    db.add_all([target, historical_target, run,
                Review(content_asset_id=candidate.id, decision="approved", reviewer_id="reviewer",
                       candidate_hash=checksum)])
    db.flush()
    attempt = DeliveryAttempt(target_id=target.id, attempt_no=1, idempotency_key="attempt",
                              status="unknown", response_metadata_json={"reconciled": "delivered"})
    db.add_all([attempt, DeliveryReceipt(target_id=target.id, approved_candidate_hash=checksum,
                                        status="human_confirmed", evidence_ref="human"),
                WorkflowStep(run_id=run.id, node_id="input", node_type="human", status="waiting_input")])
    db.commit()
    return locals()


def _summary(overview):
    result = deepcopy(overview)
    for unit in result["review"]["units"]:
        unit["history"] = []
        for target in unit["targets"]:
            target["attempts"] = []
            target["receipts"] = []
    return result


@pytest.mark.parametrize("change,summary", [
    ("none", "delivered"), ("unknown", "unknown"), ("reconciliation", "unknown"),
    ("revision_revoked", "blocked"),
    ("evidence_revoked", "blocked"), ("pack_changed", "blocked"),
    ("boundary_changed", "stale"),
    ("missing_media", "blocked"), ("integrity", "blocked"),
])
def test_bulk_reuses_current_projection_and_live_gates(projection_env, change, summary):
    data = projection_env
    db, project = data["db"], data["project"]
    if change == "unknown":
        data["attempt"].response_metadata_json = {}
    elif change == "reconciliation":
        data["target"].status = "reconciliation_needed"
    elif change == "revision_revoked":
        data["revision"].status = "revoked"
    elif change == "evidence_revoked":
        data["item"].public_use_allowed = False
    elif change == "pack_changed":
        data["pack"].checksum = "changed"
    elif change == "boundary_changed":
        db.add(ProjectFactBoundaryRevision(project_id=project.id, revision_no=3,
                                           fact_pack_id=data["pack"].id, fact_pack_version=1,
                                           fact_pack_checksum=data["pack"].checksum))
    elif change == "missing_media":
        candidate = data["candidate"]
        candidate.candidate_manifest_json = {**candidate.candidate_manifest_json, "media": [{"material_revision_id": 9999}]}
        checksum = candidate_hash(candidate.candidate_manifest_json)
        candidate.candidate_hash = candidate.approved_candidate_hash = checksum
    elif change == "integrity":
        data["candidate"].candidate_hash = "bad"
    db.commit()
    expected = project_overview(db, project.id)
    assert expected["review"]["units"][0]["summary"] == summary
    assert expected["brief"]["revision"] == 2
    assert expected["factBoundary"]["revision"] == (3 if change == "boundary_changed" else 2)
    for summary_only in (False, True):
        project_id = project.id
        db.expunge_all()
        actual = project_overviews(db, [project_id, project_id], summary_only=summary_only)
        assert actual == {project_id: _summary(expected) if summary_only else expected}


def test_empty_projects_have_constant_query_count(db_session):
    statements = []
    engine = db_session.get_bind()

    def record(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        assert project_overviews(db_session, [], summary_only=True) == {}
        assert statements == []
        project_overviews(db_session, [1], summary_only=True)
        count = len(statements)
        statements.clear()
        result = project_overviews(db_session, range(1, 101), summary_only=True)
        assert len(statements) == count == 3
        assert len(result) == 100
        assert all(row["stage"] == "brief_needed" for row in result.values())
    finally:
        event.remove(engine, "before_cursor_execute", record)


def test_summary_never_loads_history_or_receipt_attempt_payloads(projection_env):
    db = projection_env["db"]
    project_id = projection_env["project"].id
    current_id = projection_env["candidate"].id
    db.expunge_all()
    loaded = []
    statements = []

    def record_row(_session, row):
        loaded.append(row)

    def record_sql(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)

    event.listen(db, "loaded_as_persistent", record_row)
    event.listen(db.get_bind(), "before_cursor_execute", record_sql)
    try:
        context = ProjectProjectionContext(db, [project_id], summary_only=True)
        assert [row.id for row in loaded if isinstance(row, ContentAsset)] == [current_id]
        assert not any(isinstance(row, (DeliveryReceipt, DeliveryAttempt)) for row in loaded)
        assert not any("delivery_receipt" in sql for sql in statements)
        assert all("remote_id" not in sql and "error" not in sql for sql in statements if "delivery_attempt" in sql)
        before = len(statements)
        result = project_overview(db, project_id, context=context)
        assert len(statements) == before
        assert result["review"]["units"][0]["history"] == []
        with pytest.raises(ValueError, match="Unsupported"):
            context.live_reads(project_id).scalar(select(ContentAsset))
    finally:
        event.remove(db, "loaded_as_persistent", record_row)
        event.remove(db.get_bind(), "before_cursor_execute", record_sql)
