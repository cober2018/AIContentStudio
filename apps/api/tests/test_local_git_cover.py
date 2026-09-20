"""local_git 开发文档 Connector 与资产封面 测试。"""

import pytest

from app.config import get_settings
from app.models import ContentAsset

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}


@pytest.fixture
def seed_users(db_session):
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()


@pytest.fixture
def docs_repo(tmp_path, monkeypatch):
    """临时「仓库」：两个 md 文件，无需真 git（git_log best-effort）。"""
    root = tmp_path / "myrepo"
    (root / "docs").mkdir(parents=True)
    (root / "CHANGELOG.md").write_text("# Changelog\n\n- fix: 修复看板日期解析", encoding="utf-8")
    (root / "docs" / "architecture.md").write_text("# 架构\n\n三层结构：web/api/worker。", encoding="utf-8")
    monkeypatch.setenv("LOCAL_DOCS_ALLOWLIST", str(tmp_path))
    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def _make_local_git(client, root, path="**/*.md", params=None):
    c = client.post(
        "/api/v1/connectors", headers=ADMIN,
        json={"name": "开发文档", "base_url": str(root), "auth_style": "none", "connector_type": "local_git"},
    )
    assert c.status_code == 201, c.text
    cid = c.json()["id"]
    e = client.post(
        f"/api/v1/connectors/{cid}/endpoints", headers=ADMIN,
        json={
            "name": "全部文档", "path": path, "title_template": "开发文档汇总 {today}",
            "trust_level": 0.8, "fact_mapping": {"statement": "x", "fields": {"value": "{v}"}},
            "params": params or {},
        },
    )
    assert e.status_code == 201, e.text
    return cid, e.json()["id"]


def test_local_git_pull_combines_docs(client, seed_users, docs_repo):
    _, ep = _make_local_git(client, docs_repo)
    resp = client.post(f"/api/v1/endpoints/{ep}/pull", headers=EDITOR)
    assert resp.status_code == 200, resp.text
    sid = resp.json()["source_id"]
    src = client.get(f"/api/v1/sources/{sid}", headers=EDITOR).json()
    assert src["source_type"] == "local_git"
    assert "修复看板日期解析" in src["raw_text"]
    assert "三层结构" in src["raw_text"]
    assert src["parse_status"] == "done"


def test_local_git_outside_allowlist_rejected(client, seed_users, docs_repo):
    _, ep = _make_local_git(client, docs_repo)
    # 把 allowlist 换成别的前缀
    import os
    os.environ["LOCAL_DOCS_ALLOWLIST"] = "/nonexistent"
    get_settings.cache_clear()
    try:
        resp = client.post(f"/api/v1/endpoints/{ep}/pull", headers=EDITOR)
        assert resp.status_code == 400 or resp.status_code == 500
        assert "ALLOWLIST" in str(resp.json())
    finally:
        del os.environ["LOCAL_DOCS_ALLOWLIST"]
        get_settings.cache_clear()


def test_local_git_allowlist_empty_disabled(client, seed_users, docs_repo, monkeypatch):
    monkeypatch.setenv("LOCAL_DOCS_ALLOWLIST", "")
    get_settings.cache_clear()
    _, ep = _make_local_git(client, docs_repo)
    resp = client.post(f"/api/v1/endpoints/{ep}/pull", headers=EDITOR)
    assert resp.status_code in (400, 500)
    assert "LOCAL_DOCS_ALLOWLIST" in str(resp.json())


def test_asset_cover_svg(client, seed_users, db_session):
    asset = ContentAsset(
        draft_id=0, topic_brief_id=0, channel="douyin", title="9·17复盘：油价与加息下的A股",
        final_body="正文", fact_pack_id=1, fact_pack_version=3, approved_revision=1,
        reviewer="r@studio.local", model_name="MiniMax-M3",
    )
    db_session.add(asset)
    db_session.commit()
    # 封面端点无 Header 鉴权（<img> 直接引用），内容是 SVG
    resp = client.get(f"/api/v1/assets/{asset.id}/cover.svg")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/svg+xml")
    assert resp.text.startswith("<svg")
    assert "9·17复盘" in resp.text
    assert client.get("/api/v1/assets/99999/cover.svg").status_code == 404

def test_pull_dedupe_same_content(client, seed_users, docs_repo):
    """同一端点内容未变化时二次拉取不新建 Source（来源库不再被刷屏）。"""
    _, ep = _make_local_git(client, docs_repo)
    first = client.post(f"/api/v1/endpoints/{ep}/pull", headers=EDITOR)
    assert first.status_code == 200
    sid1 = first.json()["source_id"]
    before = client.get("/api/v1/sources", headers=EDITOR).json()
    second = client.post(f"/api/v1/endpoints/{ep}/pull", headers=EDITOR)
    assert second.status_code == 200
    sid2 = second.json()["source_id"]
    assert sid2 == sid1  # 返回既有 Source
    after = client.get("/api/v1/sources", headers=EDITOR).json()
    assert len(after) == len(before)  # 没有新建


def test_patch_endpoint_interval(client, seed_users, docs_repo):
    _, ep = _make_local_git(client, docs_repo)
    resp = client.patch(
        f"/api/v1/endpoints/{ep}", headers=ADMIN,
        json={
            "name": "改过名的端点", "path": "**/*.md", "title_template": "t {today}",
            "trust_level": 0.8,
            "fact_mapping": {"statement": "x", "fields": {"value": "{v}"}},
            "interval_minutes": 60,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "改过名的端点"
    assert body["interval_minutes"] == 60
    # interval=0 → 仅手动
    resp = client.patch(
        f"/api/v1/endpoints/{ep}", headers=ADMIN,
        json={"name": "手动", "path": "**/*.md", "title_template": "t {today}",
              "trust_level": 0.8, "fact_mapping": {"statement": "x", "fields": {"value": "{v}"}},
              "interval_minutes": 0},
    )
    assert resp.json()["interval_minutes"] is None


def test_patch_endpoint_requires_admin(client, seed_users, docs_repo):
    _, ep = _make_local_git(client, docs_repo)
    resp = client.patch(f"/api/v1/endpoints/{ep}", headers=EDITOR, json={"name": "x", "path": "a.md", "title_template": "t", "fact_mapping": {"statement": "x", "fields": {"value": "{v}"}}})
    assert resp.status_code == 403
