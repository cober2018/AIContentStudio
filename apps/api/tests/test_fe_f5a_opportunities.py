from datetime import timedelta

from sqlalchemy import func, select

from app.models import (
    ContentOpportunity,
    ContentProject,
    CreativeBriefRevision,
    OpportunityProjectConversion,
    ProjectFactBoundaryRevision,
    ProjectSourceBinding,
    utcnow,
)

BASE = "/api/v1/content-opportunities"


def opportunity(client):
    response = client.post(BASE, json={"title": "真实机会", "summary": "值得做的依据"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def assessed(client, oid):
    response = client.post(
        f"{BASE}/{oid}/assessments",
        json={"expected_revision": 0, "assessment": {"why_now": "新的证据", "recommended_modalities": ["text"]}},
    )
    assert response.status_code == 201, response.text
    assert client.patch(f"{BASE}/{oid}", json={"status": "qualified"}).status_code == 200


def test_failed_patch_does_not_leave_write_transaction(client, db_session):
    oid = opportunity(client)
    before = db_session.get(ContentOpportunity, oid).updated_at
    assert client.patch(f"{BASE}/{oid}", json={"status": "converted"}).status_code == 422
    db_session.commit()
    db_session.expire_all()
    assert db_session.get(ContentOpportunity, oid).updated_at == before


def test_conversion_rejects_unsupported_brief_modality(client, db_session):
    oid = opportunity(client)
    assessed(client, oid)
    response = client.post(
        f"{BASE}/{oid}/convert-to-project",
        json={
            "expected_assessment_revision": 1,
            "idempotency_key": "bad-modality",
            "brief_overrides": {"modality_scope": ["audio"]},
        },
    )
    assert response.status_code == 422, response.text
    assert db_session.scalar(select(func.count()).select_from(ContentProject)) == 0


def test_opportunity_owner_boundary(client):
    oid = opportunity(client)
    for path in [f"/{oid}", f"/{oid}/signals", f"/{oid}/assessments", f"/{oid}/conversion"]:
        assert client.get(BASE + path, headers={"X-Studio-User": "other@studio.local"}).status_code == 404


def test_assessment_append_only_conflict_and_unknown(client):
    oid = opportunity(client)
    assessed(client, oid)
    first = client.get(f"{BASE}/{oid}/assessments").json()[0]
    assert first["assessment"]["similarity_state"] == "unknown"
    assert (
        client.post(
            f"{BASE}/{oid}/assessments", json={"expected_revision": 0, "assessment": {"why_now": "并发覆盖"}}
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"{BASE}/{oid}/assessments", json={"expected_revision": 1, "assessment": {"why_now": "更新依据"}}
        ).status_code
        == 201
    )
    history = client.get(f"{BASE}/{oid}/assessments").json()
    assert len(history) == 2
    assert history[1] == first


def test_conversion_idempotent_and_origin_survives_archive(client, db_session):
    oid = opportunity(client)
    assessed(client, oid)
    payload = {"expected_assessment_revision": 1, "idempotency_key": "one-project"}
    first = client.post(f"{BASE}/{oid}/convert-to-project", json=payload)
    assert first.status_code == 201, first.text
    pid = first.json()["project_id"]
    assert client.post(f"{BASE}/{oid}/convert-to-project", json=payload).json()["project_id"] == pid
    assert db_session.scalar(select(func.count()).select_from(ContentProject)) == 1
    assert db_session.scalar(select(func.count()).select_from(CreativeBriefRevision)) == 1
    assert db_session.scalar(select(func.count()).select_from(OpportunityProjectConversion)) == 1
    assert client.patch(f"{BASE}/{oid}", json={"summary": "偷改"}).status_code == 409
    assert client.delete(f"{BASE}/{oid}").status_code == 204
    origin = client.get(f"/api/v1/content-projects/{pid}/origin").json()
    assert origin["opportunity_id"] == oid
    assert origin["status"] == "archived"


def test_home_prioritizes_older_high_priority_before_recent_limit(client, db_session):
    oid = opportunity(client)
    row = db_session.get(ContentOpportunity, oid)
    row.priority = "high"
    row.updated_at = utcnow() - timedelta(days=2)
    db_session.add_all(
        [
            ContentOpportunity(
                owner_user_id=row.owner_user_id, title=str(index), priority="low", created_by=row.created_by
            )
            for index in range(201)
        ]
    )
    db_session.commit()
    response = client.get("/api/v1/home")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["opportunities"][0]["id"] == oid
    assert data["upcoming"] == []
    assert data["capabilities"]["schedule"] is False


def test_analysis_unavailable_never_invents_assessment(client):
    oid = opportunity(client)
    assert client.post(f"{BASE}/{oid}/analyze").json()["status"] == "capability_unavailable"
    assert client.get(f"{BASE}/{oid}/assessments").json() == []


def test_converted_identity_scope_remains_editable_in_normal_brief(client):
    oid = opportunity(client)
    brand = client.post("/api/v1/content-brands", json={"name": "品牌"}).json()["id"]
    response = client.post(
        f"{BASE}/{oid}/assessments",
        json={
            "expected_revision": 0,
            "assessment": {"why_now": "身份推荐", "recommended_identity_refs": [{"brand_id": brand}]},
        },
    )
    assert response.status_code == 201, response.text
    client.patch(f"{BASE}/{oid}", json={"status": "qualified"})
    converted = client.post(
        f"{BASE}/{oid}/convert-to-project", json={"expected_assessment_revision": 1, "idempotency_key": "identity-edit"}
    )
    assert converted.status_code == 201, converted.text
    pid = converted.json()["project_id"]
    brief = client.get(f"/api/v1/content-projects/{pid}/brief").json()
    payload = {
        key: value
        for key, value in brief.items()
        if key
        in {
            "objective",
            "primary_audience",
            "core_message",
            "angle",
            "required_evidence",
            "content_constraints",
            "identity_scope",
            "modality_scope",
            "channel_scope",
            "cta",
            "references",
        }
    }
    payload.update(expected_revision=1, objective="仅修改目标")
    edited = client.post(f"/api/v1/content-projects/{pid}/brief/revisions", json=payload)
    assert edited.status_code == 201, edited.text
    assert edited.json()["identity_scope"] == [{"brand_id": brand}]


def test_signal_is_immutable_and_conversion_seeds_only_selected_source(client, db_session):
    oid = opportunity(client)
    sid = client.post("/api/v1/sources/text", json={"title": "证据来源", "content": "原始正文留在真源"}).json()["id"]
    endpoint = f"{BASE}/{oid}/signals"
    first = client.post(
        endpoint, json={"signal_type": "source_document", "source_entity_id": sid, "annotation": {"note": "first"}}
    ).json()
    assert client.delete(f"{endpoint}/{first['id']}").status_code == 204
    second = client.post(
        endpoint, json={"signal_type": "source_document", "source_entity_id": sid, "annotation": {"note": "override"}}
    ).json()
    assert second["id"] == first["id"]
    assert second["annotation"] == {"note": "first"}
    assert "content" not in second
    assessed(client, oid)
    response = client.post(
        f"{BASE}/{oid}/convert-to-project",
        json={"expected_assessment_revision": 1, "idempotency_key": "selected", "selected_signal_ids": [first["id"]]},
    )
    assert response.status_code == 201, response.text
    pid = response.json()["project_id"]
    bindings = db_session.scalars(select(ProjectSourceBinding).where(ProjectSourceBinding.project_id == pid)).all()
    assert [row.source_document_id for row in bindings] == [sid]
    assert db_session.scalar(select(func.count()).select_from(ProjectFactBoundaryRevision)) == 0
    assert client.get(f"/api/v1/content-projects/{pid}/overview").json()["stage"] == "evidence_needed"


def test_conversion_rolls_back_when_event_write_fails(client, db_session, monkeypatch):
    from app.routers import opportunities as router

    oid = opportunity(client)
    assessed(client, oid)

    def fail(*args, **kwargs):
        raise RuntimeError("injected event failure")

    monkeypatch.setattr(router, "record_project_event", fail)
    import pytest

    with pytest.raises(RuntimeError, match="injected"):
        client.post(
            f"{BASE}/{oid}/convert-to-project", json={"expected_assessment_revision": 1, "idempotency_key": "rollback"}
        )
    assert db_session.scalar(select(func.count()).select_from(ContentProject)) == 0
    assert db_session.scalar(select(func.count()).select_from(CreativeBriefRevision)) == 0
    assert db_session.scalar(select(func.count()).select_from(OpportunityProjectConversion)) == 0
    assert db_session.get(ContentOpportunity, oid).status == "qualified"


def test_home_decision_order_and_entity_dedupe():
    from app.services.home_projection import compose_decisions

    overview = {
        "risks": [
            {"code": "unit_unknown", "unit_id": 1},
            {"code": "run_unknown", "unit_id": 1, "run_id": 2},
            {"code": "unit_stale", "unit_id": 3},
            {"code": "identity_unready", "unit_id": 4},
        ],
        "pendingDecisions": [{"unit_id": 5}],
        "review": {
            "units": [
                {"unit_id": 1, "summary": "unknown"},
                {"unit_id": 6, "summary": "blocked"},
                {"unit_id": 7, "summary": "approved"},
            ]
        },
    }
    rows = compose_decisions(8, overview)
    assert [row["code"] for row in rows] == [
        "unknown",
        "blocked",
        "stale",
        "waiting_human",
        "authorization",
        "identity_unready",
    ]


def test_home_does_not_hide_projection_failure(client, monkeypatch):
    from app.services import home_projection

    client.post("/api/v1/content-projects", json={"title": "projection"})

    def fail(*args, **kwargs):
        raise RuntimeError("core projection failure")

    monkeypatch.setattr(home_projection, "project_overviews", fail)
    import pytest

    with pytest.raises(RuntimeError, match="core projection"):
        client.get("/api/v1/home")


def test_malformed_conversion_scope_is_validation_error(client):
    oid = opportunity(client)
    assessed(client, oid)
    for field in ["modality_scope", "channel_scope", "identity_scope"]:
        response = client.post(
            f"{BASE}/{oid}/convert-to-project",
            json={"expected_assessment_revision": 1, "idempotency_key": field, "brief_overrides": {field: [{}]}},
        )
        assert response.status_code == 422, response.text


def test_home_pending_decisions_not_limited_to_recent_project_cards(client, db_session):
    from app.models import ContentUnit

    persona = client.post("/api/v1/content-personas", json={"name": "persona"}).json()["id"]
    pid = client.post("/api/v1/content-projects", json={"title": "old unknown"}).json()["id"]
    unit = client.post(
        f"/api/v1/content-projects/{pid}/units", json={"title": "unknown", "persona_id": persona, "modality": "text"}
    )
    assert unit.status_code == 201, unit.text
    # Production status is a persisted fact, not Home-owned state.
    db_session.get(ContentUnit, unit.json()["id"]).status = "unknown"
    db_session.commit()
    for index in range(20):
        client.post("/api/v1/content-projects", json={"title": f"new {index}"})
    data = client.get("/api/v1/home").json()
    assert data["decisions"][0]["code"] == "unknown"
    assert data["decisions"][0]["project_id"] == pid


def test_concurrent_revision_and_conversion_use_independent_sessions(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    from fastapi import HTTPException
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    from app.models import User
    from app.routers.opportunities import ConversionIn, _convert_to_project
    from app.services import opportunities as service

    engine = create_engine(
        f"sqlite:///{tmp_path / 'race.db'}", connect_args={"check_same_thread": False, "timeout": 30}
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as db:
        user = User(email="race@studio.local", name="race", role="editor")
        db.add(user)
        db.flush()
        row = ContentOpportunity(owner_user_id=user.id, title="race", created_by=user.email)
        db.add(row)
        db.commit()
        uid, oid = user.id, row.id

    def save():
        with factory() as db:
            user = db.get(User, uid)
            try:
                service.save_assessment(
                    db, user, db.get(ContentOpportunity, oid), expected_revision=0, assessment={"why_now": "concurrent"}
                )
                return 201
            except HTTPException as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: save(), range(2))) == [201, 409]
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(service.ContentOpportunityAssessmentRevision)) == 1
        db.get(ContentOpportunity, oid).status = "qualified"
        db.commit()

    def convert(index):
        with factory() as db:
            try:
                return _convert_to_project(
                    ConversionIn(expected_assessment_revision=1, idempotency_key=f"race-{index}"),
                    oid,
                    db,
                    db.get(User, uid),
                )["project_id"]
            except Exception:
                db.rollback()
                raise

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert len(set(pool.map(convert, range(2)))) == 1
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(ContentProject)) == 1
        assert db.scalar(select(func.count()).select_from(OpportunityProjectConversion)) == 1
    engine.dispose()
