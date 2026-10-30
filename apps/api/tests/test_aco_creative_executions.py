"""Persisted R2 execution regressions; every byte and database lives under tmp_path."""

import hashlib
import io
import stat
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from PIL import Image
from sqlalchemy import create_engine, event, func, select, update
from sqlalchemy.orm import Session, sessionmaker

from app import db as app_db
from app.config import get_settings
from app.models import (
    AuditLog,
    CapabilityArtifact,
    CapabilityArtifactRevision,
    ContentMasterRevision,
    CreativeExecution,
    CreativeExecutionOutput,
    FactPack,
    Material,
    MaterialRevision,
    ProjectEvent,
    ProjectMaterialReference,
    User,
)
from app.services import asset_media, capability_memory, creative_packages, materials
from app.services import creative_execution_files as files
from app.services import creative_executions as executions
from app.services.creative_contracts import canonical_hash
from app.services.factpack_service import pack_snapshot_checksum
from app.services.material_storage import LocalMaterialStorage, provider

HEADERS = {"X-Studio-User": "aco-regression@studio.local"}
EXECUTOR = {"executor_kind": "agent", "executor_key": "isolated-test-agent", "executor_version": "1"}
PRIVATE_RIGHTS = {
    "rights_status": "restricted", "public_use_allowed": False,
    "model_use_allowed": False, "commercial_use_allowed": False,
}
METHOD = {"kind": "recipe", "name": "Review outputs", "content": {"steps": ["Inspect each required output."]}}
EFFECT_MODELS = (
    CreativeExecution, CreativeExecutionOutput, Material, MaterialRevision,
    ProjectMaterialReference, ProjectEvent, AuditLog, CapabilityArtifact, CapabilityArtifactRevision,
)
CONTENT_TABLES = (
    "content_master_revision", "channel_variant_revision", "content_asset",
    "delivery_target", "delivery_receipt", "published_content_record",
)


@pytest.fixture
def db_session(tmp_path, monkeypatch):
    # Shadow only this module's fixture so accidental module-engine writes are isolated too.
    media_root = tmp_path / "media"
    media_root.mkdir(mode=0o700)
    database_url = f"sqlite:///{tmp_path / 'studio.db'}"
    environment = {
        "DATABASE_URL": database_url, "LLM_PROVIDER": "mock", "REQUIRED_SCHEMA_HEAD": "",
        "APP_ENV": "test", "AUTH_MODE": "development_header", "MATERIAL_STORAGE_BACKEND": "local",
        "MINIO_ENABLED": "false", "TASK_QUEUE_ENABLED": "false", "AI_STUDIO_MEDIA_ROOT": str(media_root),
        "AICS_ENABLE_LOCAL_MLX_ASR": "false",
    }
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    settings = get_settings()
    monkeypatch.setattr(asset_media, "MEDIA_ROOT", media_root)
    from app import main

    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def enforce_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(app_db, "engine", engine)
    monkeypatch.setattr(app_db, "SessionLocal", factory)
    monkeypatch.setattr(main, "SessionLocal", factory)
    assert Path(settings.database_url.removeprefix("sqlite:///")) == tmp_path / "studio.db"
    assert settings.llm_provider == "mock" and settings.required_schema_head == ""
    storage = provider()
    assert isinstance(storage, LocalMaterialStorage) and storage.root == media_root
    app_db.Base.metadata.create_all(engine)
    with factory() as session:
        try:
            yield session
        finally:
            session.rollback()
    engine.dispose()
    get_settings.cache_clear()


def _post(client, path, body, status=200):
    response = client.post(path, json=body, headers=HEADERS)
    assert response.status_code == status, response.text
    return response.json()


def _png(color=0):
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), (color, 0, 0)).save(buffer, format="PNG")
    return buffer.getvalue()


def _role(role_id="image", *, kind="image", minimum=1, maximum=1, required=True):
    return {
        "role_id": role_id, "kind": kind, "required": required,
        "allowed_mime": ["image/png" if kind == "image" else "text/plain"],
        "min_count": minimum, "max_count": maximum, "max_bytes": 4096,
    }


@pytest.fixture
def flow(client, db_session, tmp_path):
    persona = _post(client, "/api/v1/content-personas", {"name": "Regression author"}, 201)
    project = _post(client, "/api/v1/content-projects", {"title": "Isolated R2"}, 201)
    unit = _post(client, f"/api/v1/content-projects/{project['id']}/units", {
        "title": "Current source", "persona_id": persona["id"], "modality": "text",
    }, 201)
    project_path = f"/api/v1/content-projects/{project['id']}"
    base = f"{project_path}/units/{unit['id']}"
    _post(client, f"{project_path}/brief/revisions", {"objective": "Review exact outputs", "expected_revision": 0}, 201)
    pack = FactPack(name="Empty frozen evidence boundary", version=1, status="frozen",
                    checksum=pack_snapshot_checksum([]))
    db_session.add(pack)
    db_session.commit()
    _post(client, f"{project_path}/fact-boundary", {"fact_pack_id": pack.id, "expected_revision": 0}, 201)
    user = db_session.scalar(select(User).where(User.email == HEADERS["X-Studio-User"]))
    return SimpleNamespace(client=client, db=db_session, tmp_path=tmp_path, user=user,
                           project=project["id"], unit=unit["id"], base=base, project_path=project_path)


def _source(flow, *, input_revision=None, expected=0):
    refs = [] if input_revision is None else [{
        "material_revision_id": input_revision.id, "content_hash": input_revision.content_hash, "role": "inline",
    }]
    source = _post(flow.client, f"{flow.base}/master-revisions", {
        "idempotency_key": f"source-{expected + 1}", "expected_revision": expected,
        "payload_schema": "text.master.v1", "payload": {"title": "Current source", "markdown": f"Revision {expected + 1}"},
        "asset_refs": refs,
    })
    assert source["readiness"] == {"state": "current", "reasons": []}
    return source


def _package(flow, source, roles=None):
    return creative_packages.create_package(flow.db, project_id=flow.project, unit_id=flow.unit,
        user=flow.user, payload={"source_master_revision_id": source["id"], "objective": "Produce exact outputs",
                                "output_contract": {"roles": roles or [_role()]}})


def _prepare(flow, package, key="execution", **extra):
    result = executions.prepare_execution(flow.db, flow.project, flow.unit, {
        **EXECUTOR, "package_id": package["id"], "idempotency_key": key, **extra,
    }, flow.user)
    return _read(flow, result)


def _transition(flow, execution, action, **extra):
    result = executions.transition_execution(flow.db, flow.project, flow.unit, execution["id"], {
        **EXECUTOR, "expected_revision": execution["revision_no"], "action": action, **extra,
    }, flow.user)
    return _read(flow, result)


def _submit(flow, execution, *, role="image", index=1, attempt=1, content=None, mime="image/png"):
    content = _png(index + attempt) if content is None else content
    key = f"outputs/{role}-{index}-{attempt}.bin"
    output_file = files.work_root(flow.user.id, execution["id"]) / key
    assert output_file.is_relative_to(flow.tmp_path / "media")
    output_file.write_bytes(content)
    output_file.chmod(0o600)
    result = executions.submit_output(flow.db, flow.project, flow.unit, execution["id"], {
        **EXECUTOR, "expected_revision": execution["revision_no"], "role_id": role, "output_index": index,
        "attempt_no": attempt, "relative_path": key, "mime_type": mime,
        "content_hash": hashlib.sha256(content).hexdigest(),
    }, flow.user)
    return _read(flow, result)


def _decision_path(flow, execution, output_id):
    return f"{flow.base}/creative-executions/{execution['id']}/outputs/{output_id}/decision"


def _decide(flow, execution, output_id, decision="accept", **extra):
    return _post(flow.client, _decision_path(flow, execution, output_id), {
        "expected_revision": execution["revision_no"], "decision": decision,
        "rights": PRIVATE_RIGHTS, **extra,
    })


def _read(flow, execution):
    return executions.get_execution(flow.db, flow.project, flow.unit, execution["id"], flow.user)


def _effects(flow):
    # A fresh reader proves committed state, rather than the writer's identity map.
    with Session(flow.db.get_bind()) as reader:
        return {model.__tablename__: reader.scalar(select(func.count()).select_from(model)) for model in EFFECT_MODELS}


def _content_counts(flow):
    return {name: flow.db.scalar(select(func.count()).select_from(app_db.Base.metadata.tables[name]))
            for name in CONTENT_TABLES}


def _http_error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json() == {"detail": {"code": code}}


@pytest.mark.parametrize("drift", ["new_master", "new_brief"])
@pytest.mark.parametrize("action", ["claim", "start"])
def test_stale_package_remains_readable_but_cannot_claim_or_start(flow, drift, action):
    source = _source(flow)
    package = _package(flow, source)
    execution = _prepare(flow, package)
    if action == "start":
        execution = _transition(flow, execution, "claim")
    if drift == "new_master":
        _source(flow, expected=1)
    else:
        _post(flow.client, f"{flow.project_path}/brief/revisions", {
            "objective": "Changed current context", "expected_revision": 1,
        }, 201)
    old = creative_packages.get_package(flow.db, flow.project, flow.unit, package["id"], flow.user)
    assert old["package"] == package["package"] and old["package_hash"] == package["package_hash"]
    assert old["is_current"] is False and old["reasons"] == ["creative_source_not_current"]
    before = _effects(flow)
    with pytest.raises(HTTPException) as denied:
        _transition(flow, execution, action)
    assert denied.value.status_code == 409 and denied.value.detail == {"code": "creative_source_not_current"}
    assert _read(flow, execution) == execution
    assert _effects(flow) == before
    _http_error(flow.client.post(f"{flow.base}/creative-executions", headers=HEADERS, json={
        **EXECUTOR, "package_id": package["id"], "idempotency_key": "stale-resend",
    }), 409, "creative_source_not_current")
    assert _effects(flow) == before


def test_unknown_blocks_restart_resend_and_requires_bound_explicit_reconciliation(flow):
    package = _package(flow, _source(flow))
    execution = _prepare(flow, package)
    sibling = _prepare(flow, package, "already-prepared")
    execution = _transition(flow, execution, "claim")
    execution = _transition(flow, execution, "start")
    execution = _transition(flow, execution, "fail", safe_reason="dispatch_uncertain")
    assert execution["state"] == "unknown" and execution["dispatch_certainty"] == "possibly_dispatched"
    before = _effects(flow)
    assert _prepare(flow, package) == execution
    for action in ("claim", "start", "fail", "cancel"):
        _http_error(flow.client.post(f"{flow.base}/creative-executions/{execution['id']}/transition",
            headers=HEADERS, json={**EXECUTOR, "expected_revision": execution["revision_no"], "action": action}),
            409, "creative_execution_reconciliation_required")
    for extra in ({}, {"retry_of_id": execution["id"]}):
        _http_error(flow.client.post(f"{flow.base}/creative-executions", headers=HEADERS, json={
            **EXECUTOR, "package_id": package["id"], "idempotency_key": "resend", **extra,
        }), 409, "creative_execution_reconciliation_required")
    with pytest.raises(HTTPException) as denied:
        _transition(flow, sibling, "claim")
    assert denied.value.detail == {"code": "creative_execution_reconciliation_required"}
    for operation in ("materialize-inputs", "outputs"):
        body = {**EXECUTOR, "expected_revision": execution["revision_no"]}
        if operation == "outputs":
            body.update(role_id="image", output_index=1, relative_path="outputs/no-send.png", mime_type="image/png")
        _http_error(flow.client.post(f"{flow.base}/creative-executions/{execution['id']}/{operation}",
            headers=HEADERS, json=body), 409, "creative_execution_reconciliation_required")
    observation = canonical_hash({"execution_id": execution["id"], "observed": "existing work only"})
    reconciliation = {**EXECUTOR, "expected_revision": execution["revision_no"], "action": "reconcile",
        "observation_hash": observation, "summary": "", "resolution": "in_progress",
        "dispatch_certainty": "confirmed_dispatched"}
    path = f"{flow.base}/creative-executions/{execution['id']}/transition"
    _http_error(flow.client.post(path, headers=HEADERS, json=reconciliation),
                422, "creative_execution_observation_required")
    _http_error(flow.client.post(path, headers=HEADERS, json={
        **reconciliation, "summary": "Existing work observed", "executor_version": "other",
    }), 409, "creative_execution_executor_mismatch")
    assert _read(flow, execution) == execution and _effects(flow) == before
    continued = _post(flow.client, path, {**reconciliation, "summary": "Existing work observed"})
    assert continued["id"] == execution["id"] and continued["revision_no"] == execution["revision_no"] + 1
    assert continued["state"] == "in_progress" and continued["dispatch_certainty"] == "confirmed_dispatched"
    assert continued["retry_of_id"] is None
    assert continued["recovery"] == {"observation_hash": observation, "summary": "Existing work observed",
                                    "recovery_action": "in_progress", "readback_status": "observed"}
    audit = flow.db.scalars(select(ProjectEvent).where(ProjectEvent.entity_type == "creative_execution",
        ProjectEvent.entity_id == str(execution["id"])).order_by(ProjectEvent.id)).all()[-1]
    assert audit.payload_json["recovery"] == continued["recovery"]
    assert _effects(flow)["creative_execution"] == 2


def test_required_distinct_indexes_replacement_and_capture_wait_for_all_outputs(flow):
    source = _source(flow)
    package = _package(flow, source, [
        _role(minimum=2, maximum=3), _role("subtitles", kind="other"),
        _role("notes", kind="other", minimum=0, required=False),
    ])
    content_before = _content_counts(flow)
    execution = _transition(flow, _prepare(flow, package), "claim")
    execution = _submit(flow, execution)
    first = execution["outputs"][0]
    assert execution["state"] == "in_progress"
    assert execution["output_counts"][0]["staged_count"] == 1
    execution = _decide(flow, execution, first["id"], reusable_artifact=METHOD)
    assert execution["state"] == "in_progress"
    assert execution["capability_capture"] == {"status": "deferred", "code": "execution_not_fully_accepted"}
    assert _effects(flow)["capability_artifact"] == 0
    with pytest.raises(HTTPException) as denied:
        capability_memory.capture_execution(flow.db, flow.user, {**METHOD, "execution_id": execution["id"]})
    assert denied.value.status_code == 409
    assert denied.value.detail == {"code": "capability_execution_not_fully_accepted"}
    execution = _submit(flow, execution, index=2)
    second = execution["outputs"][-1]
    assert execution["state"] == "in_progress"
    assert execution["output_counts"][0]["staged_count"] == 2
    assert next(count for count in execution["output_counts"] if count["role_id"] == "subtitles")["staged_count"] == 0
    execution = _submit(flow, execution, role="subtitles", content=b"Exact subtitles", mime="text/plain")
    subtitle = execution["outputs"][-1]
    assert execution["state"] == "result_ready"
    execution = _decide(flow, execution, second["id"], "reject")
    assert execution["state"] == "blocked" and execution["safe_reason"] == "needs_output_replacement"
    rejected = deepcopy(next(output for output in _read(flow, execution)["outputs"] if output["id"] == second["id"]))
    before = _effects(flow)
    for index, attempt, code in (
        (1, 2, "creative_execution_output_replacement_denied"),
        (2, 1, "creative_execution_output_attempt_invalid"),
        (4, 1, "creative_execution_output_count_exceeded"),
    ):
        with pytest.raises(HTTPException) as denied:
            _submit(flow, execution, index=index, attempt=attempt)
        assert denied.value.detail == {"code": code}
        assert _effects(flow) == before
    with pytest.raises(HTTPException) as denied:
        _transition(flow, execution, "start")
    assert denied.value.detail == {"code": "creative_execution_output_replacement_required"}
    execution = _submit(flow, execution, index=2, attempt=2)
    replacement = execution["outputs"][-1]
    assert execution["state"] == "result_ready"
    assert (replacement["output_index"], replacement["attempt_no"]) == (2, 2)
    assert replacement["id"] != rejected["id"] and replacement["content_hash"] != rejected["content_hash"]
    assert next(output for output in execution["outputs"] if output["id"] == rejected["id"]) == rejected
    assert execution["output_counts"][0]["staged_count"] == 2
    execution = _decide(flow, execution, replacement["id"], reusable_artifact=METHOD)
    assert execution["state"] == "result_ready" and execution["output_counts"][0]["accepted_count"] == 2
    assert execution["capability_capture"]["status"] == "deferred"
    assert _effects(flow)["capability_artifact_revision"] == 0
    execution = _decide(flow, execution, subtitle["id"], reusable_artifact=METHOD)
    assert execution["state"] == "accepted" and execution["capability_capture"]["status"] == "candidate"
    assert {count["role_id"]: count["accepted_count"] for count in execution["output_counts"]} == {
        "image": 2, "subtitles": 1, "notes": 0,
    }
    assert next(output for output in execution["outputs"] if output["id"] == rejected["id"]) == rejected
    with Session(flow.db.get_bind()) as reader:
        rows = reader.scalars(select(CreativeExecutionOutput).order_by(CreativeExecutionOutput.id)).all()
        assert [(row.output_index, row.attempt_no, row.state) for row in rows if row.role_id == "image"] == [
            (1, 1, "accepted"), (2, 1, "rejected"), (2, 2, "accepted"),
        ]
        artifact = reader.get(CapabilityArtifact, execution["capability_capture"]["artifact_id"])
        method = reader.get(CapabilityArtifactRevision, artifact.current_revision_id)
        assert artifact.status == "candidate" and method.source_execution_id == execution["id"]
        accepted_ids = {output["id"] for output in method.metadata_json["provenance"]["accepted_outputs"]}
        assert accepted_ids == {first["id"], replacement["id"], subtitle["id"]}
    assert _effects(flow)["material_revision"] == 3
    assert _content_counts(flow) == content_before
    assert flow.db.get(ContentMasterRevision, source["id"]).payload_json == source["payload"]


def _materialized_execution(flow, *, rights_status="cleared"):
    material = materials.create_material(flow.db, kind="image", title="Exact private input", created_by=flow.user.email)
    revision = materials.create_revision(flow.db, material, content=_png(100), declared_mime="image/png",
        rights_status=rights_status, public_use_allowed=False, model_use_allowed=True, commercial_use_allowed=False,
        attribution_text="Input author must remain credited", metadata={"license": "CC-BY-4.0"}, created_by=flow.user.email)
    flow.db.add(ProjectMaterialReference(project_id=flow.project, material_revision_id=revision.id,
        origin="manual", status="active", attached_by=flow.user.email))
    flow.db.commit()
    package = _package(flow, _source(flow, input_revision=revision))
    execution = _transition(flow, _prepare(flow, package), "claim")
    execution = executions.materialize_inputs(flow.db, flow.project, flow.unit, execution["id"], {
        **EXECUTOR, "expected_revision": execution["revision_no"], "material_revision_ids": [revision.id],
    }, flow.user)
    root = Path(execution.pop("work_root"))
    transported = execution.pop("files")
    assert root.is_relative_to(flow.tmp_path / "media")
    assert root == files.work_root(flow.user.id, execution["id"])
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    for directory in ("inputs", "outputs", "staging"):
        assert stat.S_IMODE((root / directory).stat().st_mode) == 0o700
    input_file = root / transported[0]["relative_path"]
    assert input_file.read_bytes() == _png(100) and stat.S_IMODE(input_file.stat().st_mode) == 0o600
    assert execution["materialized_inputs"][0]["rights"]["attribution_text"] == revision.attribution_text
    return _submit(flow, execution), revision


@pytest.mark.parametrize("permission", ["public_use_allowed", "model_use_allowed", "commercial_use_allowed"])
def test_derived_rights_cannot_escalate_and_inherited_attribution_license_survive(flow, permission):
    status = "restricted" if permission == "model_use_allowed" else "cleared"
    execution, source_input = _materialized_execution(flow, rights_status=status)
    output = execution["outputs"][0]
    before = _effects(flow)
    _http_error(flow.client.post(_decision_path(flow, execution, output["id"]), headers=HEADERS, json={
        "expected_revision": execution["revision_no"], "decision": "accept", "attach_to_project": True,
        "rights": {**PRIVATE_RIGHTS, "rights_status": "cleared", permission: True},
    }), 403, "creative_execution_rights_escalation")
    assert _read(flow, execution) == execution and _effects(flow) == before
    _http_error(flow.client.post(_decision_path(flow, execution, output["id"]), headers=HEADERS, json={
        "expected_revision": execution["revision_no"], "decision": "accept",
        "rights": {**PRIVATE_RIGHTS, "license": {"license": "CC0"}},
    }), 403, "creative_execution_license_conflict")
    assert _effects(flow) == before
    accepted = _decide(flow, execution, output["id"], attach_to_project=True,
                       rights={**PRIVATE_RIGHTS, "attribution_text": "Only output author supplied"})
    assert accepted["state"] == "accepted"
    with Session(flow.db.get_bind()) as reader:
        material = reader.get(MaterialRevision, accepted["outputs"][0]["material_revision_id"])
        assert material.source_kind == "external_execution" and material.content_hash == output["content_hash"]
        assert material.public_use_allowed is False and material.model_use_allowed is False
        assert material.commercial_use_allowed is False and material.rights_status == "restricted"
        assert material.attribution_text == "Input author must remain credited\nOnly output author supplied"
        provenance = material.source_metadata_json
        snapshot = execution["materialized_inputs"][0]
        assert provenance["inherited_inputs"] == [{key: snapshot[key] for key in ("material_revision_id", "content_hash", "rights")}]
        assert provenance["license_obligations"] == [{"material_revision_id": source_input.id,
            "content_hash": source_input.content_hash, "license": {"license": "CC-BY-4.0"}}]
        assert provenance["input_manifest_hash"] == canonical_hash(execution["materialized_inputs"])
        assert (provenance["execution_id"], provenance["output_id"], provenance["output_index"], provenance["attempt_no"]) == (
            execution["id"], output["id"], 1, 1,
        )
    assert files.read_material(material) == _png(2)


@pytest.mark.parametrize("revocation,code,status", [
    ("model_permission", "creative_input_model_use_denied", 403),
    ("material_archived", "creative_input_unavailable", 409),
    ("project_reference_detached", "creative_input_unavailable", 409),
])
def test_live_revoked_materialized_input_acceptance_fails_without_partial_writes(flow, revocation, code, status):
    execution, source_input = _materialized_execution(flow)
    if revocation == "model_permission":
        source_input.model_use_allowed = False
    elif revocation == "material_archived":
        source_input.material.status = "archived"
    else:
        reference = flow.db.scalar(select(ProjectMaterialReference).where(
            ProjectMaterialReference.material_revision_id == source_input.id))
        reference.status = "detached"
    flow.db.commit()
    before = _effects(flow)
    output = execution["outputs"][0]
    _http_error(flow.client.post(_decision_path(flow, execution, output["id"]), headers=HEADERS, json={
        "expected_revision": execution["revision_no"], "decision": "accept", "rights": PRIVATE_RIGHTS,
        "attach_to_project": True, "reusable_artifact": METHOD,
    }), status, code)
    assert _read(flow, execution) == execution
    assert _effects(flow) == before
    with Session(flow.db.get_bind()) as reader:
        persisted = reader.get(CreativeExecutionOutput, output["id"])
        assert persisted.state == "staged" and persisted.material_revision_id is None
        assert persisted.decided_at is None and persisted.decided_by is None


def test_late_input_revocation_rolls_back_material_reference_decision_and_events(flow):
    execution, source_input = _materialized_execution(flow)
    output = execution["outputs"][0]
    before = _effects(flow)
    inserted = []

    def revoke_after_material_insert(_mapper, connection, revision):
        if revision.source_kind == "external_execution":
            inserted.append(revision.id)
            connection.execute(update(MaterialRevision).where(MaterialRevision.id == source_input.id)
                               .values(model_use_allowed=False))

    # Exercise the second live check after actual SQL writes, without replacing a guard.
    event.listen(MaterialRevision, "after_insert", revoke_after_material_insert)
    try:
        _http_error(flow.client.post(_decision_path(flow, execution, output["id"]), headers=HEADERS, json={
            "expected_revision": execution["revision_no"], "decision": "accept", "rights": PRIVATE_RIGHTS,
            "attach_to_project": True, "reusable_artifact": METHOD,
        }), 403, "creative_input_model_use_denied")
    finally:
        event.remove(MaterialRevision, "after_insert", revoke_after_material_insert)
    assert len(inserted) == 1
    assert _read(flow, execution) == execution and _effects(flow) == before
    with Session(flow.db.get_bind()) as reader:
        assert reader.get(MaterialRevision, inserted[0]) is None
        assert reader.get(MaterialRevision, source_input.id).model_use_allowed is True
        persisted = reader.get(CreativeExecutionOutput, output["id"])
        assert persisted.state == "staged" and persisted.material_revision_id is None


def test_video_chain_output_path_stays_in_the_project_folder(tmp_path, monkeypatch):
    from app.services import project_folders

    export = tmp_path / "项目" / "导出" / "小样"
    work = tmp_path / "项目" / "工作" / "作品-1" / "任务7"
    export.mkdir(parents=True)
    work.mkdir(parents=True)
    monkeypatch.setattr(project_folders, "export_dir", lambda _db, _project, _phase: export)
    monkeypatch.setattr(project_folders, "work_dir", lambda _db, _project, _unit, _execution: work)
    row = SimpleNamespace(project_id=1, content_unit_id=1, id=7)
    package = SimpleNamespace(package_json={"director": {"postproduction": {"phase": "rough_cut"}}})
    cut, project_file, outside = export / "小样.mp4", work / "工程.drp", tmp_path / "别处.mp4"
    for path in (cut, project_file, outside, tmp_path / "别处.drp"):
        path.write_bytes(b"x")
    assert executions._project_output(None, row, package, "rough_cut", str(cut)) == cut
    assert executions._project_output(None, row, package, "resolve_project", str(project_file)) == project_file
    (export / "快捷方式.mp4").symlink_to(outside)
    (work / "链接目录").symlink_to(tmp_path)
    refused = [(outside, "rough_cut"), (project_file, "rough_cut"), (cut, "resolve_project"),
               (export / ".." / ".." / ".." / "别处.mp4", "rough_cut"), (export / "快捷方式.mp4", "rough_cut"),
               (work / "链接目录" / "别处.drp", "resolve_project"), ("小样.mp4", "rough_cut")]
    for path, role in refused:
        with pytest.raises(HTTPException) as error:
            executions._project_output(None, row, package, role, str(path))
        assert error.value.detail["code"] == "video_chain_output_path_outside"
        assert str(export if role == "rough_cut" else work) in error.value.detail["message"]


def test_video_chain_output_changed_after_submission_is_refused(tmp_path):
    cut = tmp_path / "小样.mp4"
    cut.write_bytes(b"first")
    digest = hashlib.sha256(b"first").hexdigest()
    executions.check_output(1, 7, str(cut), 5, digest)
    cut.write_bytes(b"other")
    with pytest.raises(HTTPException) as error:
        executions.check_output(1, 7, str(cut), 5, digest)
    assert error.value.detail == {"code": "video_chain_output_changed", "message": "文件已变化，请重新交付"}
