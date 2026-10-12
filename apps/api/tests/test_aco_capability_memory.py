"""Persisted R2 capability-memory regressions using only isolated local resources."""

import copy
import hashlib
import json
from functools import partial

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app import runtime_config
from app.db import Base
from app.models import (
    CapabilityArtifact,
    CapabilityArtifactRevision,
    CapabilityUse,
    ContentAccount,
    ContentMasterRevision,
    ContentPersona,
    ContentProject,
    ContentSeries,
    ContentUnit,
    CreativeExecution,
    CreativeExecutionOutput,
    CreativeExecutionPackage,
    IdentitySnapshot,
    Material,
    MaterialRevision,
    SystemSetting,
    User,
)
from app.services import asset_media, capability_memory, plugin_registry


@pytest.fixture
def capability_db(tmp_path, monkeypatch):
    media = tmp_path / "media"
    skills = tmp_path / "skills"
    media.mkdir()
    skills.mkdir()
    monkeypatch.setenv("AI_STUDIO_MEDIA_ROOT", str(media))
    monkeypatch.setattr(asset_media, "MEDIA_ROOT", media)
    monkeypatch.setattr(runtime_config, "_OVERRIDES", {})
    # scan_skills binds its default directories at definition time.
    monkeypatch.setattr(plugin_registry, "scan_skills", partial(plugin_registry.scan_skills, dirs=(skills,)))
    engine = create_engine(f"sqlite:///{tmp_path / 'capability.db'}")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    try:
        with Session(engine, autoflush=False, expire_on_commit=False) as db:
            user = User(email="capability-r2@studio.local", name="R2 owner", role="editor")
            db.add(user)
            db.commit()
            yield db, user
    finally:
        engine.dispose()


@pytest.fixture
def scope_context(capability_db):
    db, user = capability_db
    persona = ContentPersona(owner_user_id=user.id, name="R2 persona")
    db.add(persona)
    db.flush()
    account = ContentAccount(persona_id=persona.id, name="R2 account")
    db.add(account)
    db.flush()
    series = ContentSeries(account_id=account.id, name="R2 series")
    project = ContentProject(owner_user_id=user.id, title="R2 project")
    db.add_all([series, project])
    db.flush()
    snapshot = IdentitySnapshot(
        owner_user_id=user.id, persona_id=persona.id, account_id=account.id,
        series_id=series.id, checksum="a" * 64,
    )
    db.add(snapshot)
    db.flush()
    unit = ContentUnit(
        project_id=project.id, persona_id=persona.id, account_id=account.id,
        series_id=series.id, identity_snapshot_id=snapshot.id,
        modality="text", channel_id="wechat", title="R2 unit",
    )
    db.add(unit)
    db.commit()
    return {
        "project_id": project.id, "unit_id": unit.id,
        "scopes": {
            "owner": {"id": user.id}, "persona": {"id": persona.id},
            "account": {"id": account.id}, "series": {"id": series.id},
            "project": {"id": project.id}, "channel": {"channel_id": unit.channel_id},
        },
    }


def _artifact(**overrides):
    return {
        "kind": "prompt_skill", "name": "Shared title method",
        "content": {"prompt": "Write a calm title about {{topic}}."},
        "args_schema": {
            "type": "object", "properties": {"topic": {"type": "string", "maxLength": 100}},
            "required": ["topic"], "additionalProperties": False,
        },
        **overrides,
    }


def _promote(db, user, candidate, status="saved"):
    response = capability_memory.lifecycle(db, user, candidate["id"], {
        "expected_revision": candidate["current_revision"]["revision_no"], "status": status,
    })
    persisted = _read_artifact(db, user.id, candidate["id"])
    assert response["status"] == persisted["status"] == status
    assert response["current_revision"]["content_hash"] == persisted["current_revision"]["content_hash"]
    return persisted


def _read_artifact(db, owner_id, artifact_id):
    # SQLite reloads timestamps without their original timezone annotation.
    with Session(db.get_bind()) as persisted:
        return capability_memory.get_artifact(persisted, persisted.get(User, owner_id), artifact_id)


def _memory_snapshot(db):
    with Session(db.get_bind()) as persisted:
        return {
            model.__tablename__: copy.deepcopy(persisted.execute(
                select(model.__table__).order_by(model.id),
            ).mappings().all())
            for model in (CapabilityArtifact, CapabilityArtifactRevision, CapabilityUse)
        }


@pytest.mark.parametrize("status", ["saved", "pinned"])
def test_candidate_hidden_until_explicit_promotion_preserves_exact_hash(capability_db, scope_context, status):
    db, user = capability_db
    request = _artifact()
    candidate = capability_memory.create_artifact(db, user, request)
    captured = _read_artifact(db, user.id, candidate["id"])["current_revision"]
    expected_hash = hashlib.sha256(json.dumps({
        "kind": request["kind"], "content": request["content"], "args_schema": request["args_schema"],
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    context = {key: scope_context[key] for key in ("project_id", "unit_id")}

    with Session(db.get_bind()) as persisted:
        owner = persisted.get(User, user.id)
        assert capability_memory.get_artifact(persisted, owner, candidate["id"])["status"] == "candidate"
        assert capability_memory.discover(persisted, owner, context)["items"] == []
        explicit = capability_memory.list_artifacts(persisted, owner, {"status": "candidate"})
        assert [item["id"] for item in explicit["items"]] == [candidate["id"]]
    with pytest.raises(HTTPException) as rejected:
        capability_memory.use_artifact(db, user, candidate["id"], {
            "artifact_revision_id": captured["id"], "arguments": {"topic": "gardens"}, **context,
        })
    assert (rejected.value.status_code, rejected.value.detail) == (
        409, {"code": "capability_not_discoverable"},
    )
    assert _memory_snapshot(db)["capability_use"] == []

    promoted = _promote(db, user, candidate, status)
    with Session(db.get_bind()) as persisted:
        owner = persisted.get(User, user.id)
        detail = capability_memory.get_artifact(persisted, owner, candidate["id"])
        current = detail["current_revision"]
        assert detail["status"] == status
        assert current["id"] != captured["id"]
        assert current["revision_no"] == 2
        assert current["content_hash"] == captured["content_hash"] == expected_hash
        assert current["content"] == captured["content"] == request["content"]
        assert current["args_schema"] == captured["args_schema"] == request["args_schema"]
        assert current["metadata"]["status"] == status
        assert current["metadata"]["provenance"] == captured["metadata"]["provenance"]
        assert current["source_execution_id"] == captured["source_execution_id"]
        assert current["source_learning_candidate_id"] == captured["source_learning_candidate_id"]
        assert capability_memory.revisions(persisted, owner, candidate["id"])["items"] == [current, captured]
        assert capability_memory.discover(persisted, owner, context)["items"][0]["current_revision"] == current
        assert promoted["current_revision"] == current


def test_discovery_returns_all_conflicting_applicable_scopes_without_merging(
    capability_db, scope_context, partial_execution,
):
    db, user = capability_db
    expected = {}
    scopes = [*scope_context["scopes"].items(), ("executor", {
        key: getattr(partial_execution, key) for key in ("executor_kind", "executor_key", "executor_version")
    }), ("owner", {"id": user.id})]
    for index, (scope_type, scope) in enumerate(scopes):
        candidate = capability_memory.create_artifact(db, user, _artifact(
            content={"prompt": f"Use conflicting approach {index} for {{{{topic}}}}."},
            scope_type=scope_type, scope=scope,
        ))
        saved = _promote(db, user, candidate, "pinned" if index % 2 else "saved")
        expected[saved["id"]] = saved
    for status in ("candidate", "archived", "deprecated"):
        excluded = capability_memory.create_artifact(db, user, _artifact())
        if status != "candidate":
            _promote(db, user, excluded, status)
    other_project = ContentProject(owner_user_id=user.id, title="Other project")
    db.add(other_project)
    db.commit()
    _promote(db, user, capability_memory.create_artifact(db, user, _artifact(
        scope_type="project", scope={"id": other_project.id},
    )))
    before = _memory_snapshot(db)
    context = {key: scope_context[key] for key in ("project_id", "unit_id")}
    context["execution_id"] = partial_execution.id

    with Session(db.get_bind()) as persisted:
        owner = persisted.get(User, user.id)
        result = capability_memory.discover(persisted, owner, context)
        assert result["total"] == len(expected)
        assert len(result["items"]) == len(expected)
        assert {item["id"] for item in result["items"]} == set(expected)
        for item in result["items"]:
            saved = expected[item["id"]]
            assert item == {
                **saved, "matched_scope": {"scope_type": saved["scope_type"], "scope": saved["scope"]},
            }
        assert capability_memory.discover(persisted, owner, context) == result
    assert _memory_snapshot(db) == before


@pytest.mark.parametrize("operation", ["create", "import", "update"])
@pytest.mark.parametrize("location", ["content", "args_schema"])
@pytest.mark.parametrize("secret", [
    "sk-r2syntheticcredential123456789",
    "https://example.invalid/object?X-Amz-Signature=r2-synthetic",
], ids=["credential", "signed-url"])
def test_secret_content_or_arguments_rejects_entire_write_atomically(capability_db, operation, location, secret):
    db, user = capability_db
    retained = _promote(db, user, capability_memory.create_artifact(db, user, _artifact()))
    before = _memory_snapshot(db)
    payload = _artifact()
    if location == "content":
        payload["content"]["notes"] = ["Keep this benign sibling.", {"hint": secret}]
    else:
        payload["args_schema"]["properties"]["topic"]["enum"] = ["benign sibling", secret]

    with pytest.raises(HTTPException) as rejected:
        if operation == "create":
            capability_memory.create_artifact(db, user, payload)
        elif operation == "import":
            capability_memory.import_artifact(db, user, {"schema": "capability.memory.export.v1", **payload})
        else:
            capability_memory.update_revision(db, user, retained["id"], {
                "expected_revision": retained["current_revision"]["revision_no"],
                "content": payload["content"], "args_schema": payload["args_schema"],
            })
    assert (rejected.value.status_code, rejected.value.detail) == (
        422, {"code": "capability_unsafe_payload"},
    )
    assert secret not in str(rejected.value.detail)
    assert _memory_snapshot(db) == before
    with Session(db.get_bind()) as persisted:
        owner = persisted.get(User, user.id)
        assert capability_memory.get_artifact(persisted, owner, retained["id"]) == retained


@pytest.mark.parametrize("enabled", [[], ["Unrelated installed skill"]], ids=["disabled", "other-enabled"])
def test_same_name_installed_skill_stays_separate_and_promotion_has_no_side_effects(
    capability_db, tmp_path, enabled,
):
    db, user = capability_db
    skills = tmp_path / "skills"
    for directory, name in (("same-name", "Shared title method"), ("unrelated", "Unrelated installed skill")):
        target = skills / directory
        target.mkdir()
        (target / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Local R2 fixture\nversion: 1.0\n---\n"
            "Keep installed instructions separate.\n", encoding="utf-8",
        )
    files_before = {path.relative_to(skills): path.read_bytes() for path in skills.rglob("*") if path.is_file()}
    plugins = {"skill_dirs": [str(skills)], "skills_enabled": enabled, "mcp": []}
    setting = SystemSetting(key="plugins", value=copy.deepcopy(plugins), updated_by=user.email)
    db.add(setting)
    db.commit()
    runtime_config.load_from_db(db)
    with Session(db.get_bind()) as persisted:
        baseline = persisted.get(SystemSetting, "plugins")
        setting_before = (copy.deepcopy(baseline.value), baseline.updated_at, baseline.updated_by)
    candidate = capability_memory.create_artifact(db, user, _artifact())
    inventory = capability_memory.installed_skills(db, user)
    installed = next(item for item in inventory["items"] if item["name"] == candidate["name"])
    expected_id = hashlib.sha256(json.dumps({
        "path": str(skills / "same-name"), "name": candidate["name"],
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    assert len(inventory["items"]) == 2
    assert installed["source_kind"] == "installed_agent_skill"
    assert installed["id"] == expected_id
    assert candidate["source_kind"] == "capability_memory"
    assert installed["id"] != candidate["id"]
    assert len(_memory_snapshot(db)["capability_artifact"]) == 1
    saved = _promote(db, user, candidate)
    pinned = _promote(db, user, saved, "pinned")

    with Session(db.get_bind()) as persisted:
        owner = persisted.get(User, user.id)
        assert capability_memory.installed_skills(persisted, owner) == inventory
        memory = capability_memory.list_artifacts(persisted, owner, {"status": "pinned"})["items"]
        assert memory == [pinned]
        assert memory[0]["id"] == candidate["id"]
        assert memory[0]["name"] == installed["name"]
        assert memory[0]["source_kind"] != installed["source_kind"]
        assert pinned["current_revision"]["content_hash"] == candidate["current_revision"]["content_hash"]
        persisted_setting = persisted.get(SystemSetting, "plugins")
        assert (persisted_setting.value, persisted_setting.updated_at, persisted_setting.updated_by) == setting_before
        assert len(persisted.scalars(select(SystemSetting)).all()) == 1
        assert len(persisted.scalars(select(CapabilityArtifact)).all()) == 1
    assert runtime_config.get_runtime("plugins") == plugins
    assert {path.relative_to(skills): path.read_bytes() for path in skills.rglob("*") if path.is_file()} == files_before


@pytest.fixture
def partial_execution(capability_db, scope_context):
    db, user = capability_db
    project_id, unit_id = scope_context["project_id"], scope_context["unit_id"]
    source = ContentMasterRevision(
        project_id=project_id, content_unit_id=unit_id, revision_no=1, modality="text",
        payload_schema="text.master.v1", payload_json={"text": "R2 fixture"}, payload_hash="a" * 64,
        context_hash="b" * 64, source_kind="user_edit", idempotency_key="r2-source",
        request_fingerprint="c" * 64,
    )
    db.add(source)
    db.flush()
    package = CreativeExecutionPackage(
        owner_user_id=user.id, project_id=project_id, content_unit_id=unit_id,
        source_master_revision_id=source.id, package_schema="creative.execution.v1",
        package_json={"output_contract": {"roles": [{"role_id": "illustrations", "required": True,
            "kind": "image", "min_count": 2, "max_count": 2, "allowed_mime": ["image/png"], "max_bytes": 1000}]}},
        package_hash="d" * 64, source_payload_hash=source.payload_hash, source_context_hash=source.context_hash,
    )
    db.add(package)
    db.flush()
    execution = CreativeExecution(
        owner_user_id=user.id, project_id=project_id, content_unit_id=unit_id, package_id=package.id,
        idempotency_key="r2-partial", request_fingerprint="e" * 64, executor_kind="agent",
        executor_key="r2-local", executor_version="1", state="result_ready", revision_no=5,
        dispatch_certainty="confirmed_dispatched",
    )
    material = Material(kind="image", title="R2 accepted illustration")
    db.add_all([execution, material])
    db.flush()
    revision = MaterialRevision(material_id=material.id, content_hash="f" * 64, status="ready")
    db.add(revision)
    db.flush()
    output = CreativeExecutionOutput(
        execution_id=execution.id, role_id="illustrations", kind="image", output_index=1,
        attempt_no=1, staging_key="r2-illustration.png", mime_type="image/png", content_hash="f" * 64,
        size_bytes=100, state="accepted", material_revision_id=revision.id,
    )
    db.add(output)
    db.commit()
    return execution


def test_capture_rejects_partially_accepted_execution_without_changing_accepted_output(
    capability_db, partial_execution,
):
    db, user = capability_db
    before = _memory_snapshot(db)
    retained_models = (CreativeExecution, CreativeExecutionOutput, MaterialRevision)
    with Session(db.get_bind()) as persisted:
        source_before = {model.__tablename__: persisted.execute(select(model.__table__)).mappings().all()
                         for model in retained_models}

    with pytest.raises(HTTPException) as rejected:
        capability_memory.capture_execution(db, user, {"execution_id": partial_execution.id, **_artifact()})
    assert (rejected.value.status_code, rejected.value.detail) == (
        409, {"code": "capability_execution_not_fully_accepted"},
    )
    assert _memory_snapshot(db) == before
    with Session(db.get_bind()) as persisted:
        assert {model.__tablename__: persisted.execute(select(model.__table__)).mappings().all()
                for model in retained_models} == source_before
