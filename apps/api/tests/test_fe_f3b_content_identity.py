"""FE-F3B identity hierarchy, revision, snapshot and production contracts."""

from sqlalchemy import inspect

from app.models import BrandVoiceVersion, ContentUnit, IdentitySnapshot


def test_identity_tables_exist_without_backfilling_legacy_rows(db_session):
    tables = set(inspect(db_session.bind).get_table_names())
    assert {
        "content_brand", "content_brand_revision", "content_persona_revision",
        "content_account", "content_account_revision", "content_series",
        "content_series_revision", "identity_snapshot",
        "account_workflow_default", "series_workflow_default",
    } <= tables


def test_legacy_persona_unit_run_identity_columns_are_nullable(db_session):
    inspector = inspect(db_session.bind)
    persona = {column["name"]: column for column in inspector.get_columns("content_persona")}
    unit = {column["name"]: column for column in inspector.get_columns("content_unit")}
    run = {column["name"]: column for column in inspector.get_columns("workflow_run")}
    assert persona["brand_id"]["nullable"]
    assert {"account_id", "series_id", "identity_snapshot_id"} <= set(unit)
    assert all(unit[name]["nullable"] for name in ("account_id", "series_id", "identity_snapshot_id"))
    assert run["identity_snapshot_id"]["nullable"]


def test_identity_hierarchy_revisions_and_effective_profile(client):
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    brand_response = client.post("/api/v1/content-brands", json={"name": "Studio"}, headers=alice)
    assert brand_response.status_code == 201, brand_response.text
    brand_id = brand_response.json()["id"]
    brand_revision = client.post(
        f"/api/v1/content-brands/{brand_id}/revisions",
        json={"expected_revision": 0, "profile": {"target_audience": ["开发者"], "expression_style": {"tone": "calm"}}},
        headers=alice,
    )
    assert brand_revision.status_code == 201, brand_revision.text
    assert client.post(f"/api/v1/content-brands/{brand_id}/revisions", json={"expected_revision": 0, "profile": {}}, headers=alice).status_code == 409
    assert client.post(f"/api/v1/content-brands/{brand_id}/revisions", json={"expected_revision": 1, "profile": {"unknown_field": "x"}}, headers=alice).status_code == 422
    persona_response = client.post(f"/api/v1/content-brands/{brand_id}/personas", json={"name": "创始人"}, headers=alice)
    assert persona_response.status_code == 201, persona_response.text
    persona_id = persona_response.json()["id"]
    account_response = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "主号"}, headers=alice)
    assert account_response.status_code == 201, account_response.text
    account_id = account_response.json()["id"]
    assert client.post(f"/api/v1/content-accounts/{account_id}/revisions", json={"expected_revision": 0, "profile": {"target_audience": None}}, headers=alice).status_code == 201
    series_response = client.post(f"/api/v1/content-accounts/{account_id}/series", json={"name": "周刊"}, headers=alice)
    assert series_response.status_code == 201, series_response.text
    series_id = series_response.json()["id"]
    effective = client.get(f"/api/v1/content-identities/effective?persona_id={persona_id}&account_id={account_id}&series_id={series_id}", headers=alice)
    assert effective.status_code == 200, effective.text
    assert effective.json()["effective_profile"]["target_audience"] is None
    assert effective.json()["field_origins"]["target_audience"] == "account"
    assert effective.json()["effective_profile"]["expression_style"] == {"tone": "calm"}
    assert effective.json()["field_origins"]["expression_style"] == "brand"
    assert client.post(f"/api/v1/content-series/{series_id}/revisions", json={"expected_revision": 0, "profile": {"expression_style": {"format": "weekly"}, "target_audience": ["读者"]}}, headers=alice).status_code == 201
    replaced = client.get(f"/api/v1/content-identities/effective?persona_id={persona_id}&account_id={account_id}&series_id={series_id}", headers=alice).json()
    assert replaced["effective_profile"]["expression_style"] == {"format": "weekly"}
    assert replaced["effective_profile"]["target_audience"] == ["读者"]
    assert replaced["field_origins"]["target_audience"] == "series"
    assert client.get(f"/api/v1/content-identities/effective?persona_id={persona_id}", headers=bob).status_code == 404


def test_new_unit_pins_truthful_snapshot_and_legacy_unit_stays_null(client, db_session):
    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "旧角色"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "身份项目"}, headers=alice).json()["id"]
    created = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "新单元", "persona_id": persona_id, "modality": "text"}, headers=alice)
    assert created.status_code == 201, created.text
    snapshot_id = created.json()["identity_snapshot_id"]
    assert isinstance(snapshot_id, int)
    row = db_session.get(IdentitySnapshot, snapshot_id)
    assert row.persona_id == persona_id
    assert row.brand_id is None and row.persona_revision_id is None
    assert row.effective_profile_json == {}
    snapshot = client.get(f"/api/v1/identity-snapshots/{snapshot_id}", headers=alice)
    assert snapshot.status_code == 200
    assert snapshot.json()["checksum"] == row.checksum
    assert snapshot.json()["readiness"] == "incomplete"
    assert client.get(f"/api/v1/identity-snapshots/{snapshot_id}", headers={"X-Studio-User": "bob@studio.local"}).status_code == 404
    legacy = ContentUnit(project_id=project_id, persona_id=persona_id, modality="text", title="历史单元")
    db_session.add(legacy)
    db_session.commit()
    assert client.get(f"/api/v1/content-projects/{project_id}/units/{legacy.id}", headers=alice).json()["identity_state"] == "legacy_identity"


def test_run_copies_exact_snapshot_and_archived_identity_blocks_new_run(client):
    from test_fe_f2_workflows import _definition

    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "运行身份"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "文章", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    base = f"/api/v1/content-projects/{project_id}/units/{unit['id']}"
    assert client.post(f"{base}/workflow-override", json={"expected_revision": 0, "definition": _definition()}, headers=alice).status_code == 201
    first = client.post(f"{base}/runs", json={"params": {}}, headers=alice)
    assert first.status_code == 201, first.text
    assert first.json()["identity_snapshot_id"] == unit["identity_snapshot_id"]
    assert client.delete(f"/api/v1/content-personas/{persona_id}", headers=alice).status_code == 204
    assert client.get(f"{base}/runs/{first.json()['id']}", headers=alice).status_code == 200
    assert client.post(f"{base}/runs", json={"params": {}}, headers=alice).status_code == 409
    assert client.post(f"{base}/runs/{first.json()['id']}/nodes/a/rerun", headers=alice).status_code == 409
    assert client.post(f"/api/v1/workflow-runs/{first.json()['id']}/nodes/a/rerun", headers=alice).status_code == 409
    assert client.post(f"{base}/workflow-override", json={"expected_revision": 1, "definition": _definition()}, headers=alice).status_code == 409


def test_explicit_rebind_updates_in_place_then_replaces_after_run(client):
    from test_fe_f2_workflows import _definition

    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    account_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "主号"}, headers=alice).json()["id"]
    series_id = client.post(f"/api/v1/content-accounts/{account_id}/series", json={"name": "专栏"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "重绑"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    base = f"/api/v1/content-projects/{project_id}/units/{unit['id']}"
    in_place = client.patch(base, json={"account_id": account_id, "series_id": series_id, "rebind_identity": True}, headers=alice)
    assert in_place.status_code == 200, in_place.text
    assert in_place.json()["id"] == unit["id"]
    assert in_place.json()["identity_snapshot_id"] != unit["identity_snapshot_id"]
    assert in_place.json()["series_id"] == series_id
    assert client.post(f"{base}/workflow-override", json={"expected_revision": 0, "definition": _definition()}, headers=alice).status_code == 201
    run = client.post(f"{base}/runs", json={"params": {}}, headers=alice).json()
    old_snapshot = in_place.json()["identity_snapshot_id"]
    replacement = client.patch(base, json={"series_id": None, "rebind_identity": True}, headers=alice)
    assert replacement.status_code == 200, replacement.text
    assert replacement.json()["id"] != unit["id"]
    assert replacement.json()["account_id"] == account_id
    assert replacement.json()["series_id"] is None
    assert replacement.json()["identity_snapshot_id"] != old_snapshot
    assert client.get(base, headers=alice).json()["status"] == "archived"
    assert client.get(f"{base}/runs/{run['id']}", headers=alice).json()["identity_snapshot_id"] == old_snapshot
    assert client.patch(base, json={"rebind_identity": True}, headers=alice).status_code == 409
    events = client.get(f"/api/v1/content-projects/{project_id}/activity", headers=alice).json()["items"]
    replacement_event = next(event for event in events if event["event_type"] == "unit.replaced")
    assert replacement_event["payload"]["old_identity_snapshot_id"] == old_snapshot
    assert replacement_event["payload"]["new_identity_snapshot_id"] == replacement.json()["identity_snapshot_id"]


def test_hierarchical_defaults_pin_new_units_and_preserve_old_ones(client):
    portable = {"nodes": [{"id": "gate", "kind": "Human", "plugin": "builtin.approve", "config": {}}], "edges": [], "visual_order": ["gate"]}
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    account_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "主号"}, headers=alice).json()["id"]
    series_id = client.post(f"/api/v1/content-accounts/{account_id}/series", json={"name": "周刊"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "工作流"}, headers=alice).json()["id"]
    persona = client.post(f"/api/v1/content-personas/{persona_id}/default-workflows/text", json={"expected_revision": 0, "definition": portable}, headers=alice)
    assert persona.status_code == 201, persona.text
    old = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "早期", "persona_id": persona_id, "modality": "text", "account_id": account_id, "series_id": series_id}, headers=alice).json()
    assert old["pinned_workflow_id"] == persona.json()["workflow_id"]
    account = client.post(f"/api/v1/content-accounts/{account_id}/default-workflows/text", json={"expected_revision": 0, "definition": portable}, headers=alice)
    assert account.status_code == 201, account.text
    assert client.post(f"/api/v1/content-accounts/{account_id}/default-workflows/text", json={"expected_revision": 0, "definition": portable}, headers=alice).status_code == 409
    middle = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "中期", "persona_id": persona_id, "modality": "text", "account_id": account_id, "series_id": series_id}, headers=alice).json()
    assert middle["pinned_workflow_id"] == account.json()["workflow_id"]
    series = client.post(f"/api/v1/content-series/{series_id}/default-workflows/text", json={"expected_revision": 0, "definition": portable}, headers=alice)
    assert series.status_code == 201, series.text
    newest = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "近期", "persona_id": persona_id, "modality": "text", "account_id": account_id, "series_id": series_id}, headers=alice).json()
    assert newest["pinned_workflow_id"] == series.json()["workflow_id"]
    assert client.get(f"/api/v1/content-projects/{project_id}/units/{old['id']}", headers=alice).json()["pinned_workflow_id"] == persona.json()["workflow_id"]
    effective = client.get(f"/api/v1/content-identities/effective-workflow?persona_id={persona_id}&account_id={account_id}&series_id={series_id}&modality=text", headers=alice)
    assert effective.status_code == 200 and effective.json()["source"] == "series"
    assert client.get(f"/api/v1/workflows/{series.json()['workflow_id']}", headers=bob).status_code == 404


def test_versions_overview_and_typed_brief_identity_scope(client, db_session):
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    foreign_persona_id = client.post("/api/v1/content-personas", json={"name": "外部"}, headers=bob).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "身份回读"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    legacy = ContentUnit(project_id=project_id, persona_id=persona_id, modality="text", title="旧稿")
    db_session.add(legacy)
    db_session.commit()
    versions = client.get(f"/api/v1/content-projects/{project_id}/versions", headers=alice).json()
    assert any(row["id"] == str(unit["identity_snapshot_id"]) and row["unitId"] == unit["id"] for row in versions["identitySnapshots"])
    assert any(row["unitId"] == legacy.id and row["status"] == "legacy_identity" for row in versions["identityStates"])
    overview = client.get(f"/api/v1/content-projects/{project_id}/overview", headers=alice).json()
    assert {risk["code"] for risk in overview["risks"]} == {"identity_unready"}
    brief_url = f"/api/v1/content-projects/{project_id}/brief/revisions"
    invalid = client.post(brief_url, json={"expected_revision": 0, "objective": "写文章", "identity_scope": [{"persona_id": foreign_persona_id}]}, headers=alice)
    assert invalid.status_code in {404, 422}
    valid = client.post(brief_url, json={"expected_revision": 0, "objective": "写文章", "identity_scope": [{"persona_id": persona_id}, "传统标签"]}, headers=alice)
    assert valid.status_code == 201, valid.text
    assert valid.json()["identity_scope"] == [{"persona_id": persona_id}, "传统标签"]


def test_snapshot_remains_immutable_after_profile_and_voice_revision(client, db_session):
    alice = {"X-Studio-User": "alice@studio.local"}
    voice = BrandVoiceVersion(name="全局语气", version=1, status="published")
    draft_voice = BrandVoiceVersion(name="未发布", version=1, status="draft")
    db_session.add_all([voice, draft_voice]); db_session.commit()
    brand_id = client.post("/api/v1/content-brands", json={"name": "Studio"}, headers=alice).json()["id"]
    brand_revisions = f"/api/v1/content-brands/{brand_id}/revisions"
    assert client.post(brand_revisions, json={"expected_revision": 0, "profile": {"positioning": "可靠写作", "brand_voice_version_id": voice.id}}, headers=alice).status_code == 201
    assert client.post(brand_revisions, json={"expected_revision": 1, "profile": {"brand_voice_version_id": draft_voice.id}}, headers=alice).status_code == 422
    persona_id = client.post(f"/api/v1/content-brands/{brand_id}/personas", json={"name": "主编"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "快照"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "第一版", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    first = client.get(f"/api/v1/identity-snapshots/{unit['identity_snapshot_id']}", headers=alice).json()
    assert first["brand_voice_version_id"] == voice.id and first["effective_profile"]["positioning"] == "可靠写作"
    assert client.post(brand_revisions, json={"expected_revision": 1, "profile": {"positioning": "新定位", "brand_voice_version_id": voice.id}}, headers=alice).status_code == 201
    assert client.get(f"/api/v1/identity-snapshots/{unit['identity_snapshot_id']}", headers=alice).json() == first
    assert client.get(f"/api/v1/content-identities/effective?persona_id={persona_id}", headers=alice).json()["effective_profile"]["positioning"] == "新定位"
    refreshed = client.patch(f"/api/v1/content-projects/{project_id}/units/{unit['id']}", json={"rebind_identity": True}, headers=alice)
    assert refreshed.status_code == 200
    assert refreshed.json()["identity_snapshot_id"] != first["id"]
    second = client.get(f"/api/v1/identity-snapshots/{refreshed.json()['identity_snapshot_id']}", headers=alice).json()
    assert second["checksum"] != first["checksum"] and second["effective_profile"]["positioning"] == "新定位"
    account_voice = BrandVoiceVersion(name="账号语气", version=1, status="published")
    db_session.add(account_voice); db_session.commit()
    account_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "主号"}, headers=alice).json()["id"]
    assert client.post(f"/api/v1/content-accounts/{account_id}/revisions", json={"expected_revision": 0, "profile": {"brand_voice_version_id": account_voice.id}}, headers=alice).status_code == 201
    account_unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "账号稿", "persona_id": persona_id, "account_id": account_id, "modality": "text"}, headers=alice).json()
    account_snapshot = client.get(f"/api/v1/identity-snapshots/{account_unit['identity_snapshot_id']}", headers=alice).json()
    assert account_snapshot["brand_voice_version_id"] == account_voice.id
    assert account_snapshot["field_origins"]["brand_voice_version_id"] == "account"


def test_hierarchy_rejects_mismatched_children_and_archived_parent(client):
    alice = {"X-Studio-User": "alice@studio.local"}
    bob = {"X-Studio-User": "bob@studio.local"}
    brand_id = client.post("/api/v1/content-brands", json={"name": "品牌"}, headers=alice).json()["id"]
    first = client.post(f"/api/v1/content-brands/{brand_id}/personas", json={"name": "甲"}, headers=alice).json()["id"]
    second = client.post(f"/api/v1/content-brands/{brand_id}/personas", json={"name": "乙"}, headers=alice).json()["id"]
    account_id = client.post(f"/api/v1/content-personas/{first}/accounts", json={"name": "账号"}, headers=alice).json()["id"]
    series_id = client.post(f"/api/v1/content-accounts/{account_id}/series", json={"name": "栏目"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "项目"}, headers=alice).json()["id"]
    units = f"/api/v1/content-projects/{project_id}/units"
    assert client.post(units, json={"title": "错层级", "persona_id": second, "account_id": account_id, "series_id": series_id, "modality": "text"}, headers=alice).status_code == 404
    assert client.post(units, json={"title": "外部", "persona_id": first, "account_id": account_id, "modality": "text"}, headers=bob).status_code == 404
    assert client.get(units, headers=alice).json() == []
    assert client.delete(f"/api/v1/content-brands/{brand_id}", headers=alice).status_code == 204
    assert client.get(f"/api/v1/content-identities/effective?persona_id={first}", headers=alice).status_code == 200
    assert client.post(units, json={"title": "已归档", "persona_id": first, "modality": "text"}, headers=alice).status_code == 409
    assert client.post(f"/api/v1/content-personas/{first}/accounts", json={"name": "新号"}, headers=alice).status_code == 409


def test_revision_unique_race_returns_409_without_partial_revision(client, monkeypatch):
    from app.services import content_identity

    alice = {"X-Studio-User": "alice@studio.local"}
    brand_id = client.post("/api/v1/content-brands", json={"name": "竞态"}, headers=alice).json()["id"]
    url = f"/api/v1/content-brands/{brand_id}/revisions"
    assert client.post(url, json={"expected_revision": 0, "profile": {"positioning": "第一版"}}, headers=alice).status_code == 201
    original = content_identity.current_revision
    monkeypatch.setattr(content_identity, "current_revision", lambda *_args: None)
    assert client.post(url, json={"expected_revision": 0, "profile": {"positioning": "冲突版"}}, headers=alice).status_code == 409
    monkeypatch.setattr(content_identity, "current_revision", original)
    revisions = client.get(url, headers=alice).json()
    assert len(revisions) == 1 and revisions[0]["profile"]["positioning"] == "第一版"


def test_account_default_portability_gate_and_old_unit_pin(client):
    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    account_id = client.post(f"/api/v1/content-personas/{persona_id}/accounts", json={"name": "号"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "默认"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "旧单元", "persona_id": persona_id, "account_id": account_id, "modality": "text"}, headers=alice).json()
    url = f"/api/v1/content-accounts/{account_id}/default-workflows/text"
    project_bound = {"nodes": [{"id": "gate", "kind": "Rule", "plugin": "builtin.fact_check", "config": {"project_id": project_id}}], "edges": [], "visual_order": ["gate"]}
    assert client.post(url, json={"expected_revision": 0, "definition": project_bound}, headers=alice).status_code == 422
    assert client.get(url, headers=alice).json()["workflow_id"] is None
    portable = {"nodes": [{"id": "gate", "kind": "Human", "plugin": "builtin.approve", "config": {}}], "edges": [], "visual_order": ["gate"]}
    saved = client.post(url, json={"expected_revision": 0, "definition": portable}, headers=alice)
    assert saved.status_code == 201
    assert client.get(f"/api/v1/content-projects/{project_id}/units/{unit['id']}", headers=alice).json()["pinned_workflow_id"] is None


def test_identity_refresh_keeps_compatible_project_override_and_workflow_rebind_refreshes_snapshot(client):
    from test_fe_f2_workflows import _definition

    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "刷新"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    base = f"/api/v1/content-projects/{project_id}/units/{unit['id']}"
    override = client.post(f"{base}/workflow-override", json={"expected_revision": 0, "definition": _definition()}, headers=alice).json()
    assert client.post(f"/api/v1/content-personas/{persona_id}/revisions", json={"expected_revision": 0, "profile": {"positioning": "新定位"}}, headers=alice).status_code == 201
    refreshed = client.patch(base, json={"rebind_identity": True}, headers=alice)
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["id"] == unit["id"]
    assert refreshed.json()["identity_snapshot_id"] != unit["identity_snapshot_id"]
    assert refreshed.json()["pinned_workflow_id"] == override["workflow_id"]
    assert client.get(f"{base}/workflow-override", headers=alice).json()["workflow_id"] == override["workflow_id"]
    assert client.post(f"/api/v1/content-personas/{persona_id}/revisions", json={"expected_revision": 1, "profile": {"positioning": "再更新"}}, headers=alice).status_code == 201
    changed = client.patch(base, json={"modality": "graphic"}, headers=alice)
    assert changed.status_code == 200, changed.text
    assert changed.json()["identity_snapshot_id"] != refreshed.json()["identity_snapshot_id"]
    assert changed.json()["pinned_workflow_id"] is None
    assert client.get(f"{base}/workflow-override", headers=alice).json()["workflow_id"] is None


def test_identity_refresh_after_run_forks_and_keeps_compatible_project_override(client):
    from test_fe_f2_workflows import _definition

    alice = {"X-Studio-User": "alice@studio.local"}
    persona_id = client.post("/api/v1/content-personas", json={"name": "作者"}, headers=alice).json()["id"]
    project_id = client.post("/api/v1/content-projects", json={"title": "历史刷新"}, headers=alice).json()["id"]
    unit = client.post(f"/api/v1/content-projects/{project_id}/units", json={"title": "稿件", "persona_id": persona_id, "modality": "text"}, headers=alice).json()
    base = f"/api/v1/content-projects/{project_id}/units/{unit['id']}"
    override = client.post(f"{base}/workflow-override", json={"expected_revision": 0, "definition": _definition()}, headers=alice).json()
    run = client.post(f"{base}/runs", json={"params": {}}, headers=alice)
    assert run.status_code == 201, run.text
    old_snapshot_id = run.json()["identity_snapshot_id"]
    assert client.post(f"/api/v1/content-personas/{persona_id}/revisions", json={"expected_revision": 0, "profile": {"positioning": "更新"}}, headers=alice).status_code == 201
    replacement = client.patch(base, json={"rebind_identity": True}, headers=alice)
    assert replacement.status_code == 200, replacement.text
    replacement = replacement.json()
    assert replacement["id"] != unit["id"]
    assert replacement["identity_snapshot_id"] != old_snapshot_id
    assert replacement["pinned_workflow_id"] == override["workflow_id"]
    new_base = f"/api/v1/content-projects/{project_id}/units/{replacement['id']}"
    assert client.get(f"{new_base}/workflow-override", headers=alice).json()["workflow_id"] == override["workflow_id"]
    assert client.get(f"{base}/runs/{run.json()['id']}", headers=alice).json()["identity_snapshot_id"] == old_snapshot_id
