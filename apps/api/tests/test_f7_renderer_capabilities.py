"""Actual deterministic render probes do not mutate Studio content."""

import hashlib
import io
from copy import deepcopy
from datetime import UTC, datetime, timedelta

import pytest
from PIL import Image
from sqlalchemy import select

from app.models import CapabilityRegistration, CapabilityVerification, ContentMasterRevision, User
from app.services import capability_integrations

ADMIN = {"X-Studio-User": "renderer-admin@studio.local"}
VIEWER = {"X-Studio-User": "renderer-viewer@studio.local"}


@pytest.fixture
def renderer_setup(client, db_session):
    db_session.add_all([User(email=ADMIN["X-Studio-User"], role="admin", name="Renderer admin"),
                       User(email=VIEWER["X-Studio-User"], role="viewer", name="Viewer")])
    db_session.commit()
    persona = client.post("/api/v1/content-personas", headers=ADMIN, json={"name": "作者"}).json()["id"]
    project = client.post("/api/v1/content-projects", headers=ADMIN, json={"title": "渲染项目"}).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", headers=ADMIN, json={
        "title": "文章", "modality": "text", "persona_id": persona, "channel_id": "wechat"}).json()["id"]
    path = f"/api/v1/content-projects/{project}/units/{unit}/master-revisions"
    response = client.post(path, headers=ADMIN, json={"payload_schema": "text.master.v1", "payload": {"markdown": "## 精确正文\n\n不修改原文"}, "idempotency_key": "renderer-initial"})
    assert response.status_code == 200, response.text
    master = response.json()
    body = {"project_id": project, "unit_id": unit, "master_id": master["id"],
            "renderer_key": "text.markdown.v1", "renderer_version": "1", "expected_payload_hash": master["payload_hash"],
            "expected_context_hash": master["context_hash"]}
    return {"body": body, "master": master, "path": path}


def probe(client, setup, **overrides):
    return client.post("/api/v1/settings/renderer-probes", headers=ADMIN, json={**setup["body"], **overrides})


def test_actual_text_probe_persists_scoped_hash_evidence_without_master_write(client, db_session, renderer_setup):
    result = probe(client, renderer_setup)
    assert result.status_code == 201, result.text
    row = db_session.get(CapabilityVerification, result.json()["verification_id"])
    assert row.scope_kind == "renderer_output"
    assert row.scope_json["payload_schema"] == "text.master.v1"
    assert row.scope_json["channel"] == "wechat" and row.scope_json["content_form"] == "article"
    assert row.evidence_json["output_hash"] == hashlib.sha256(renderer_setup["master"]["payload"]["markdown"].encode()).hexdigest()
    assert len(row.evidence_json["input_hash"]) == 64
    assert "精确正文" not in str(row.evidence_json)
    assert db_session.query(ContentMasterRevision).count() == 1
    assert db_session.get(ContentMasterRevision, renderer_setup["master"]["id"]).payload_hash == renderer_setup["master"]["payload_hash"]
    inventory = client.get("/api/v1/settings/capabilities", headers=ADMIN).json()
    found = next(item for item in inventory["renderers"] if item.get("registration_id") == row.registration_id)
    assert found["verified"] and found["mode"] == "deterministic"


@pytest.mark.parametrize("change", [{"expected_payload_hash": "0" * 64}, {"expected_context_hash": "0" * 64},
                                   {"renderer_version": "99"}, {"renderer_key": "manual.graphic.master.v2"}])
def test_invalid_probe_creates_no_evidence(client, db_session, renderer_setup, change):
    assert probe(client, renderer_setup, **change).status_code in {409, 422}
    assert db_session.query(CapabilityVerification).count() == 0


def test_viewer_and_foreign_admin_cannot_probe_other_project(client, db_session, renderer_setup):
    path = "/api/v1/settings/renderer-probes"
    assert client.post(path, headers=VIEWER, json=renderer_setup["body"]).status_code == 403
    db_session.add(User(email="foreign-admin@studio.local", role="admin", name="Other"))
    db_session.commit()
    assert client.post(path, headers={"X-Studio-User": "foreign-admin@studio.local"}, json=renderer_setup["body"]).status_code == 404
    assert db_session.query(CapabilityVerification).count() == 0


def test_historical_or_stale_master_does_not_verify(client, db_session, renderer_setup):
    assert client.post(renderer_setup["path"], headers=ADMIN, json={"expected_revision": 1, "payload": {"markdown": "新版"}, "idempotency_key": "renderer-next"}).status_code == 200
    assert probe(client, renderer_setup).status_code == 409
    assert db_session.query(CapabilityVerification).count() == 0


def test_renderer_verification_expiry_and_code_change_invalidate_scope(client, db_session, renderer_setup, monkeypatch):
    result = probe(client, renderer_setup)
    assert result.status_code == 201, result.text
    from app.services import renderer_capabilities
    from app.services.content_harness.registry import registry

    event = db_session.get(CapabilityVerification, result.json()["verification_id"])
    registration = db_session.get(CapabilityRegistration, event.registration_id)
    fingerprint = event.config_fingerprint
    assert capability_integrations.is_verified_for_scope(db_session, registration, event.scope_json, fingerprint, registry)
    changed = {**event.scope_json, "output_mime": "text/html"}
    assert not capability_integrations.is_verified_for_scope(db_session, registration, changed, fingerprint, registry)
    monkeypatch.setattr(renderer_capabilities, "code_fingerprint", lambda: "b" * 64)
    assert not next(item for item in renderer_capabilities.inventory(db_session) if item.get("registration_id") == event.registration_id)["verified"]
    event.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()
    assert not capability_integrations.is_verified_for_scope(db_session, registration, event.scope_json, fingerprint, registry)


def test_renderer_inventory_does_not_render_or_read_bytes(client, renderer_setup, monkeypatch):
    assert probe(client, renderer_setup).status_code == 201
    from app.services import renderer_capabilities

    def forbidden(*_args, **_kwargs):
        raise AssertionError("inventory must not render")

    monkeypatch.setattr(renderer_capabilities.ProductionRenderer, "render_master", forbidden)
    inventory = client.get("/api/v1/settings/capabilities", headers=VIEWER)
    assert inventory.status_code == 200, inventory.text
    manual = [item for item in inventory.json()["renderers"] if item["mode"] == "manual"]
    assert manual and all(not item["verified"] and not item["executable"] for item in manual)


def test_renderer_scope_cannot_accept_client_supplied_provenance(client, db_session, renderer_setup):
    assert probe(client, renderer_setup, output_hash="a" * 64).status_code == 422
    assert db_session.query(CapabilityVerification).count() == 0


def test_renderer_revocation_is_append_only(client, db_session, renderer_setup):
    verified = probe(client, renderer_setup)
    assert verified.status_code == 201, verified.text
    revoked = probe(client, renderer_setup, result="revoked")
    assert revoked.status_code == 201, revoked.text
    assert db_session.get(CapabilityVerification, verified.json()["verification_id"]).result == "verified"
    inventory = client.get("/api/v1/settings/capabilities", headers=ADMIN).json()
    assert not next(item for item in inventory["renderers"] if item.get("registration_id") == verified.json()["registration_id"])["verified"]


def test_renderer_probe_uses_v2_canonical_document_renderer(client, db_session, renderer_setup):
    from app.services import text_documents

    # An explicit upgrade remains the only path out of a legacy v1 Master.
    master = renderer_setup["master"]
    path = renderer_setup["path"]
    response = client.post(f"{path}/{master['id']}/text-v2-upgrade", headers=ADMIN, json={
        "expected_revision": 1, "expected_payload_hash": master["payload_hash"], "expected_context_hash": master["context_hash"], "idempotency_key": "render-v2-upgrade"})
    assert response.status_code == 200, response.text
    upgraded = response.json()
    setup = deepcopy(renderer_setup)
    setup["body"].update(master_id=upgraded["id"], renderer_key="text.studio.document.v1", renderer_version="2",
                         expected_payload_hash=upgraded["payload_hash"], expected_context_hash=upgraded["context_hash"])
    result = probe(client, setup)
    assert result.status_code == 201, result.text
    event = db_session.get(CapabilityVerification, result.json()["verification_id"])
    rendered = text_documents.render_markdown(upgraded["payload"]["document"])
    assert event.evidence_json["output_hash"] == hashlib.sha256(rendered.encode()).hexdigest()
    assert db_session.query(ContentMasterRevision).count() == 2


@pytest.mark.parametrize("value", [{}, [], True, None])
def test_renderer_scope_invalid_mime_is_typed_rejection(value):
    scope = {"renderer_key": "text.markdown.v1", "renderer_version": "1", "modality": "text", "payload_schema": "text.master.v1",
             "channel": "wechat", "content_form": "article", "output_mime": value}
    with pytest.raises(ValueError, match="capability_scope_invalid"):
        capability_integrations._scope("renderer_output", scope)


def test_channel_neutral_master_cannot_verify_a_channel_scope(client, db_session, renderer_setup):
    from app.models import ContentUnit

    db_session.get(ContentUnit, renderer_setup["body"]["unit_id"]).channel_id = None
    db_session.commit()
    response = client.post(renderer_setup["path"], headers=ADMIN, json={"expected_revision": 1, "idempotency_key": "neutral", "payload": {"markdown": "中立正文"}})
    assert response.status_code == 200, response.text
    master = response.json()
    assert probe(client, renderer_setup, master_id=master["id"], expected_payload_hash=master["payload_hash"], expected_context_hash=master["context_hash"]).status_code in {409, 422}
    assert db_session.query(CapabilityVerification).count() == 0


def test_upstream_context_change_does_not_verify_old_render(client, db_session, renderer_setup):
    project = renderer_setup["body"]["project_id"]
    result = client.post(f"/api/v1/content-projects/{project}/brief/revisions", headers=ADMIN, json={"expected_revision": 0, "objective": "新上下文"})
    assert result.status_code == 201, result.text
    assert probe(client, renderer_setup).status_code == 409
    assert db_session.query(CapabilityVerification).count() == 0


def test_two_channel_scopes_remain_verified_independently(client, db_session, renderer_setup):
    assert probe(client, renderer_setup).status_code == 201
    persona = client.post("/api/v1/content-personas", headers=ADMIN, json={"name": "第二作者"}).json()["id"]
    project = renderer_setup["body"]["project_id"]
    unit = client.post(f"/api/v1/content-projects/{project}/units", headers=ADMIN, json={
        "title": "线程", "modality": "text", "persona_id": persona, "channel_id": "x_thread"}).json()["id"]
    master = client.post(f"/api/v1/content-projects/{project}/units/{unit}/master-revisions", headers=ADMIN,
        json={"payload_schema": "text.master.v1", "payload": {"markdown": "第二渠道"}, "idempotency_key": "second-scope"}).json()
    result = probe(client, renderer_setup, unit_id=unit, master_id=master["id"],
        expected_payload_hash=master["payload_hash"], expected_context_hash=master["context_hash"])
    assert result.status_code == 201, result.text
    rows = client.get("/api/v1/settings/capabilities", headers=ADMIN).json()["renderers"]
    scopes = [row for row in rows if row["renderer_key"] == "text.markdown.v1" and "scope" in row]
    assert len(scopes) == 2 and all(row["verified"] for row in scopes)


def test_replaced_loaded_adapter_invalidates_verification(client, db_session, renderer_setup, monkeypatch):
    from app.services import production_modalities

    assert probe(client, renderer_setup).status_code == 201
    adapter = production_modalities.adapter_for("text", "text.master.v1")
    monkeypatch.setattr(adapter, "build_render_snapshot", lambda db, master: {"status": "ready", "markdown": "改稿"})
    rows = client.get("/api/v1/settings/capabilities", headers=ADMIN).json()["renderers"]
    assert not next(row for row in rows if row.get("scope", {}).get("channel") == "wechat")["verified"]


@pytest.mark.parametrize("change", ["rights", "detach", "hash"])
def test_render_probe_rechecks_exact_project_material(client, db_session, renderer_setup, change):
    from app.models import MaterialRevision, ProjectMaterialReference

    image = io.BytesIO()
    Image.new("RGB", (8, 8), "blue").save(image, format="PNG")
    result = client.post("/api/v1/materials/upload?kind=image&public_use_allowed=true&model_use_allowed=true&rights_status=cleared",
        headers=ADMIN, files={"file": ("source.png", image.getvalue(), "image/png")})
    assert result.status_code == 201, result.text
    source = result.json()["revisions"][0]
    project = renderer_setup["body"]["project_id"]
    assert client.post(f"/api/v1/content-projects/{project}/materials/references", headers=ADMIN,
        json={"material_revision_id": source["id"]}).status_code == 201
    result = client.post(renderer_setup["path"], headers=ADMIN, json={"expected_revision": 1,
        "payload": {"markdown": "引用真实素材"}, "idempotency_key": "renderer-media",
        "asset_refs": [{"material_revision_id": source["id"], "content_hash": source["content_hash"], "role": "inline"}]})
    assert result.status_code == 200, result.text
    master = result.json()
    revision = db_session.get(MaterialRevision, source["id"])
    if change == "rights":
        revision.public_use_allowed = False
    elif change == "hash":
        revision.content_hash = "0" * 64
    else:
        db_session.scalar(select(ProjectMaterialReference).where(ProjectMaterialReference.material_revision_id == source["id"])).status = "detached"
    db_session.commit()
    result = probe(client, renderer_setup, master_id=master["id"], expected_payload_hash=master["payload_hash"], expected_context_hash=master["context_hash"])
    assert result.status_code == 409, result.text
    assert db_session.query(CapabilityVerification).count() == 0


def test_evidence_lock_and_commit_boundary_recheck(client, db_session, monkeypatch):
    from sqlalchemy import event
    from test_f6e_freeze_v5 import HEADERS, _ready_source

    from app.services import renderer_capabilities

    project, unit, master = _ready_source(client, db_session, cited=True)
    user = db_session.scalar(select(User).where(User.email == HEADERS["X-Studio-User"]))
    user.role = "admin"
    db_session.commit()
    statements = []
    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())
    event.listen(db_session.bind, "before_cursor_execute", record)
    def revoke_after_check(renderer, db, row):
        from app import models
        from app.services import production_modalities

        rendered = production_modalities.adapter_for(row.modality, row.payload_schema).build_render_snapshot(db, row)
        item = db.scalar(select(models.FactPackItem))
        item.public_use_allowed = False
        db.flush()
        return rendered
    monkeypatch.setattr(renderer_capabilities.ProductionRenderer, "render_master", revoke_after_check)
    try:
        response = client.post("/api/v1/settings/renderer-probes", headers=HEADERS, json={
            "project_id": project, "unit_id": unit, "master_id": master["id"], "renderer_key": "text.studio.document.v1",
            "renderer_version": "2", "expected_payload_hash": master["payload_hash"], "expected_context_hash": master["context_hash"]})
    finally:
        event.remove(db_session.bind, "before_cursor_execute", record)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "renderer_evidence_unavailable", response.text
    assert any(statement.startswith("update fact_pack set") for statement in statements), statements
    assert any(statement.startswith("update fact_pack_item set") for statement in statements)
    assert db_session.query(CapabilityVerification).count() == 0
