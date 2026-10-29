"""Task 4.6 identity contracts through real APIs and isolated SQLite services."""

import hashlib
import json
import socket
from copy import deepcopy

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models import AuditLog, IdentitySnapshot, ProjectEvent, User
from app.services import content_identity as identity
from app.services import studio_creative_catalog as catalog

STARTERS = ("starter.ai-tech-engineer.v1", "starter.lifestyle-observer.v1")
MODALITIES = ("text", "graphic", "video")
KINDS = ("persona", "account", "series")
ROUTES = {
    "brand": "content-brands",
    "persona": "content-personas",
    "account": "content-accounts",
    "series": "content-series",
}
ARCHIVE_CASES = [
    (kind, ancestor)
    for kind, ancestors in (
        ("persona", ("brand", "persona")),
        ("account", ("brand", "persona", "account")),
        ("series", ("brand", "persona", "account", "series")),
    )
    for ancestor in ancestors
]
PARAMETERS = {
    "text": {"length": "long", "candidate_count": 3},
    "graphic": {"density": "high", "instruction": "保留具体观察"},
    "video": {"aspect_ratio": "16:9", "instruction": "保留具体观察"},
}
REPLACEMENTS = {
    "text": {"length": "short"},
    "graphic": {"density": "low"},
    "video": {"aspect_ratio": "9:16"},
}


@pytest.fixture(autouse=True)
def _isolated_identity_contract(db_session, monkeypatch, tmp_path):
    from app.config import get_settings
    from app.services import asset_media

    assert db_session.get_bind().url.drivername == "sqlite"
    assert db_session.get_bind().url.database in (None, "", ":memory:")
    assert get_settings().llm_provider == "mock"
    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path / "media")

    def reject_network(*args, **kwargs):
        pytest.fail("Identity contracts must not open network connections")

    monkeypatch.setattr(socket.socket, "connect", reject_network)
    monkeypatch.setattr(socket, "create_connection", reject_network)


def _digest(value):
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _json(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def _hierarchy(client):
    headers = {"X-Studio-User": "creative-identity@studio.test"}
    brand = _json(client.post("/api/v1/content-brands", headers=headers, json={"name": "共享品牌"}), 201)
    persona = _json(client.post(
        f"/api/v1/content-brands/{brand['id']}/personas", headers=headers, json={"name": "创作角色"},
    ), 201)
    account = _json(client.post(
        f"/api/v1/content-personas/{persona['id']}/accounts", headers=headers, json={"name": "发布账号"},
    ), 201)
    series = _json(client.post(
        f"/api/v1/content-accounts/{account['id']}/series", headers=headers, json={"name": "观察栏目"},
    ), 201)
    ids = {kind: row["id"] for kind, row in zip(("brand", *KINDS), (brand, persona, account, series))}
    return headers, ids


def _path(ids, kind):
    return f"/api/v1/{ROUTES[kind]}/{ids[kind]}"


def _save(client, headers, ids, kind, expected_revision, profile):
    saved = _json(client.post(
        f"{_path(ids, kind)}/revisions", headers=headers,
        json={"expected_revision": expected_revision, "profile": profile},
    ), 201)
    assert saved["revision_no"] == expected_revision + 1
    assert saved["profile"] == profile
    assert saved["checksum"] == _digest(profile)
    assert saved["created_by"] == headers["X-Studio-User"]
    return saved


def _effective(client, headers, ids):
    return _json(client.get("/api/v1/content-identities/effective", headers=headers, params={
        "persona_id": ids["persona"], "account_id": ids["account"], "series_id": ids["series"],
    }))


def _profile(key, modality, scope="persona"):
    profile = deepcopy(catalog.BLUEPRINTS[key][f"{modality}_creative_profile"])
    profile["parameters"] = deepcopy(PARAMETERS[modality])
    profile["stage_instruction"] = f"保留 {scope} 的独立观察"
    profile["provenance"].update(blueprint_key=key, blueprint_version="1")
    return profile


def _profiles(key, scope="persona"):
    return {f"{modality}_creative_profile": _profile(key, modality, scope) for modality in MODALITIES}


def _replacement(key, modality):
    source = catalog.BLUEPRINTS[key][f"{modality}_creative_profile"]
    required = ("schema", "mode", "skill_ref", "style_preset_ref", "quality_profile_ref", "capability")
    return {**{field: source[field] for field in required}, "parameters": deepcopy(REPLACEMENTS[modality])}


def _freeze(client, db_session, headers, ids):
    resolved = _effective(client, headers, ids)
    user = db_session.scalar(select(User).where(User.email == headers["X-Studio-User"]))
    snapshot = identity.create_snapshot(
        db_session, user, persona_id=ids["persona"], account_id=ids["account"], series_id=ids["series"],
    )
    db_session.commit()
    # Compare persisted SQLite values, whose datetime storage drops the UTC offset.
    db_session.refresh(snapshot)
    value = _json(client.get(f"/api/v1/identity-snapshots/{snapshot.id}", headers=headers))
    assert value["effective_profile"] == resolved["effective_profile"]
    assert value["field_origins"] == resolved["field_origins"]
    assert value["checksum"] == _digest({**resolved, "owner_user_id": user.id})
    for kind, revision_id in resolved["revision_ids"].items():
        assert value[f"{kind}_revision_id"] == revision_id
    return deepcopy(value)


def _assert_frozen(client, db_session, headers, *snapshots):
    db_session.expire_all()
    for snapshot in snapshots:
        assert _json(client.get(f"/api/v1/identity-snapshots/{snapshot['id']}", headers=headers)) == snapshot


def _database_state(db_session):
    assert not db_session.new
    assert not db_session.dirty
    models = [model for pair in identity.REVISION_MODELS.values() for model in pair[:2]]
    models.extend((IdentitySnapshot, ProjectEvent, AuditLog))
    return {
        model.__tablename__: deepcopy([
            dict(row) for row in db_session.execute(select(model.__table__).order_by(model.id)).mappings()
        ])
        for model in models
    }


@pytest.mark.parametrize("key", STARTERS)
@pytest.mark.parametrize("modality", MODALITIES)
@pytest.mark.parametrize("kind", KINDS)
def test_creative_revisions_fresh_cas_stale_atomicity_and_frozen_history(client, db_session, key, modality, kind):
    headers, ids = _hierarchy(client)
    field = f"{modality}_creative_profile"
    _save(client, headers, ids, "persona", 0, _profiles(key))
    initial_no = 1 if kind == "persona" else 0
    original = _profiles(key, kind)
    original["positioning"] = "最初定位"
    first = _save(client, headers, ids, kind, initial_no, original)
    frozen = _freeze(client, db_session, headers, ids)
    assert frozen["effective_profile"][field] == original[field]
    assert frozen["field_origins"][field] == kind

    updated = deepcopy(original)
    updated[field] = _replacement(key, modality)
    updated["positioning"] = "保存新定位"
    second = _save(client, headers, ids, kind, first["revision_no"], updated)
    assert second["id"] != first["id"]
    assert second["checksum"] != first["checksum"]
    assert _json(client.get(_path(ids, kind), headers=headers))["current_revision"] == second["revision_no"]
    resolved = _effective(client, headers, ids)
    assert resolved["effective_profile"][field] == updated[field]
    assert resolved["creative_profile_origins"][field] == kind
    assert resolved["revision_ids"][kind] == second["id"]
    fresh_snapshot = _freeze(client, db_session, headers, ids)
    assert fresh_snapshot["checksum"] != frozen["checksum"]
    assert fresh_snapshot[f"{kind}_revision_id"] == second["id"]

    before = _database_state(db_session)
    stale = deepcopy(original)
    stale["positioning"] = "不得保存的旧编辑"
    stale[field]["stage_instruction"] = "不得进入历史的内容"
    response = client.post(f"{_path(ids, kind)}/revisions", headers=headers, json={
        "expected_revision": first["revision_no"], "profile": stale,
    })
    assert response.status_code == 409, response.text
    assert _database_state(db_session) == before
    assert _json(client.get(f"{_path(ids, kind)}/revisions/{first['id']}", headers=headers)) == first
    assert _json(client.get(f"{_path(ids, kind)}/revisions", headers=headers))[:2] == [second, first]
    _assert_frozen(client, db_session, headers, frozen, fresh_snapshot)

    recovered = _save(client, headers, ids, kind, second["revision_no"], stale)
    assert recovered["id"] not in (first["id"], second["id"])
    assert _effective(client, headers, ids)["effective_profile"][field] == stale[field]
    _assert_frozen(client, db_session, headers, frozen, fresh_snapshot)


@pytest.mark.parametrize("key", STARTERS)
@pytest.mark.parametrize("modality", MODALITIES)
def test_missing_inherits_whole_object_replaces_and_null_clears_each_scope(client, db_session, key, modality):
    headers, ids = _hierarchy(client)
    field = f"{modality}_creative_profile"

    def assert_effective(value, origin):
        resolved = _effective(client, headers, ids)
        if origin is None:
            assert field not in resolved["effective_profile"]
            assert field not in resolved["field_origins"]
            assert field not in resolved["creative_profile_origins"]
        else:
            assert resolved["effective_profile"][field] == value
            assert resolved["field_origins"][field] == origin
            assert resolved["creative_profile_origins"][field] == origin

    assert_effective(None, None)
    persona_profile = _profile(key, modality)
    persona_revision = _save(client, headers, ids, "persona", 0, {field: persona_profile})
    _save(client, headers, ids, "account", 0, {"positioning": "账号继承"})
    _save(client, headers, ids, "series", 0, {"positioning": "栏目继承"})
    assert_effective(persona_profile, "persona")
    persona_snapshot = _freeze(client, db_session, headers, ids)

    account_profile = _replacement(key, modality)
    account_revision = _save(client, headers, ids, "account", 1, {field: account_profile})
    assert_effective(account_profile, "account")
    assert "stage_instruction" not in account_profile and "provenance" not in account_profile
    account_snapshot = _freeze(client, db_session, headers, ids)

    series_profile = {**deepcopy(account_profile), "parameters": {}, "stage_instruction": "栏目独立观察"}
    series_revision = _save(client, headers, ids, "series", 1, {field: series_profile})
    assert_effective(series_profile, "series")
    series_snapshot = _freeze(client, db_session, headers, ids)
    changed_persona = {**deepcopy(persona_profile), "stage_instruction": "新的角色观察"}
    _save(client, headers, ids, "persona", 1, {field: changed_persona})
    assert_effective(series_profile, "series")

    _save(client, headers, ids, "series", 2, {field: None})
    assert_effective(None, "series")
    cleared_snapshot = _freeze(client, db_session, headers, ids)
    _save(client, headers, ids, "series", 3, {"positioning": "栏目恢复继承"})
    assert_effective(account_profile, "account")
    _save(client, headers, ids, "account", 2, {field: None})
    assert_effective(None, "account")
    _save(client, headers, ids, "account", 3, {"positioning": "账号恢复继承"})
    assert_effective(changed_persona, "persona")
    _save(client, headers, ids, "persona", 2, {field: None})
    assert_effective(None, "persona")
    _save(client, headers, ids, "persona", 3, {"positioning": "无创作默认"})
    assert_effective(None, None)

    for kind, revision in zip(KINDS, (persona_revision, account_revision, series_revision)):
        assert _json(client.get(f"{_path(ids, kind)}/revisions/{revision['id']}", headers=headers)) == revision
    _assert_frozen(client, db_session, headers, persona_snapshot, account_snapshot, series_snapshot, cleared_snapshot)
    assert len({snapshot["checksum"] for snapshot in (
        persona_snapshot, account_snapshot, series_snapshot, cleared_snapshot,
    )}) == 4


@pytest.mark.parametrize("key", STARTERS)
@pytest.mark.parametrize("kind,archived_kind", ARCHIVE_CASES)
def test_archived_self_or_ancestor_blocks_writes_but_preserves_creative_history(
    client, db_session, key, kind, archived_kind,
):
    headers, ids = _hierarchy(client)
    _save(client, headers, ids, "brand", 0, {"content_boundaries": ["共享品牌约束"]})
    for scope in KINDS:
        _save(client, headers, ids, scope, 0, _profiles(key, scope))
    current = _save(client, headers, ids, kind, 1, _profiles(key, "最新编辑"))
    snapshot = _freeze(client, db_session, headers, ids)
    historical = {
        scope: _json(client.get(f"{_path(ids, scope)}/revisions", headers=headers))
        for scope in ("brand", *KINDS)
    }
    resolved = _effective(client, headers, ids)
    response = client.delete(_path(ids, archived_kind), headers=headers)
    assert response.status_code == 204, response.text
    assert _json(client.get(_path(ids, archived_kind), headers=headers))["status"] == "archived"
    if kind != archived_kind:
        assert _json(client.get(_path(ids, kind), headers=headers))["status"] == "active"
    before = _database_state(db_session)

    response = client.post(f"{_path(ids, kind)}/revisions", headers=headers, json={
        "expected_revision": current["revision_no"], "profile": _profiles(key, "不得保存"),
    })
    assert response.status_code == 409, response.text
    assert _database_state(db_session) == before
    response = client.patch(_path(ids, kind), headers=headers, json={"name": "不得重命名"})
    assert response.status_code == 409, response.text
    assert _database_state(db_session) == before
    child_path = {"persona": "accounts", "account": "series"}.get(kind)
    if child_path:
        response = client.post(f"{_path(ids, kind)}/{child_path}", headers=headers, json={"name": "不得新建"})
        assert response.status_code == 409, response.text
        assert _database_state(db_session) == before

    user = db_session.scalar(select(User).where(User.email == headers["X-Studio-User"]))
    with pytest.raises(HTTPException) as rejected:
        identity.create_snapshot(
            db_session, user, persona_id=ids["persona"], account_id=ids["account"], series_id=ids["series"],
        )
    assert rejected.value.status_code == 409
    assert _database_state(db_session) == before
    response = client.delete(_path(ids, archived_kind), headers=headers)
    assert response.status_code == 204, response.text
    assert _database_state(db_session) == before
    assert _effective(client, headers, ids) == resolved
    for scope, revisions in historical.items():
        assert _json(client.get(f"{_path(ids, scope)}/revisions", headers=headers)) == revisions
        for revision in revisions:
            assert _json(client.get(f"{_path(ids, scope)}/revisions/{revision['id']}", headers=headers)) == revision
    _assert_frozen(client, db_session, headers, snapshot)


@pytest.mark.parametrize("key", STARTERS)
@pytest.mark.parametrize("modality", MODALITIES)
@pytest.mark.parametrize("clear", (False, True), ids=("object", "null"))
def test_brand_rejects_every_creative_field_on_revision_even_when_null(client, db_session, key, modality, clear):
    headers, ids = _hierarchy(client)
    original = _save(client, headers, ids, "brand", 0, {"content_boundaries": ["原有品牌约束"]})
    _save(client, headers, ids, "persona", 0, _profiles(key))
    snapshot = _freeze(client, db_session, headers, ids)
    before = _database_state(db_session)
    field = f"{modality}_creative_profile"
    value = None if clear else deepcopy(catalog.BLUEPRINTS[key][field])
    response = client.post(f"{_path(ids, 'brand')}/revisions", headers=headers, json={
        "expected_revision": 1, "profile": {"content_boundaries": ["不得部分保存"], field: value},
    })
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == "brand_creative_profile_forbidden"
    assert _database_state(db_session) == before
    assert _json(client.get(_path(ids, "brand"), headers=headers))["current_revision"] == 1
    assert _json(client.get(f"{_path(ids, 'brand')}/revisions", headers=headers)) == [original]
    assert _effective(client, headers, ids)["creative_profile_origins"] == {
        f"{item}_creative_profile": "persona" for item in MODALITIES
    }
    _assert_frozen(client, db_session, headers, snapshot)
