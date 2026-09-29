"""Material Library（V1 PRD 2.0 D9 / capability: material-library-v1）。

覆盖：upload→MaterialRevision；同素材多稿复用；rights 撤权失效链；
approved 引用不可变（替换=新 Revision）；历史 DraftMedia 可读。
"""

import hashlib
import os
import subprocess
import sys

import pytest

from app.models import DraftMedia, Material, MaterialRevision
from app.services import materials as materials_service

EDITOR = {"X-Studio-User": "editor@studio.local"}

PNG = b"\x89PNG\r\n\x1a\n" + b"rest-of-png-bytes" * 8


def test_media_root_can_be_isolated_for_acceptance(tmp_path):
    isolated = tmp_path / "media"
    output = subprocess.check_output(
        [sys.executable, "-c", "from app.services.asset_media import MEDIA_ROOT; print(MEDIA_ROOT)"],
        env={**os.environ, "AI_STUDIO_MEDIA_ROOT": str(isolated)},
        text=True,
    ).strip()
    assert output == str(isolated)


def _upload(client, *, title="测试图", public=False, role="inline"):
    return client.post(
        "/api/v1/materials/upload",
        data={"kind": "image", "title": title, "rights_status": "cleared", "public_use_allowed": str(public)},
        files={"file": ("pic.png", PNG, "image/png")},
        headers=EDITOR,
    )


@pytest.fixture
def draft(db_session):
    """最小可挂素材的 Draft（绕过生成链，直接建 job+draft）。"""
    from app.models import ContentJob, Draft, FactPack, TopicBrief, User

    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    pack = FactPack(name="素材测试包", version=1, status="frozen", checksum="a" * 64)
    db_session.add(pack)
    db_session.flush()
    topic = TopicBrief(title="素材测试选题", fact_pack_id=pack.id, fact_pack_version=1)
    db_session.add(topic)
    db_session.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="xiaohongshu", status="succeeded")
    db_session.add(job)
    db_session.flush()
    draft = Draft(content_job_id=job.id, revision_no=1, title="t", body="第一段\n\n第二段", status="draft")
    db_session.add(draft)
    db_session.commit()
    return draft


def test_upload_creates_material_and_revision(client):
    resp = _upload(client)
    assert resp.status_code == 201, resp.json()
    body = resp.json()
    assert body["kind"] == "image"
    revision = body["revisions"][0]
    assert revision["source_kind"] == "upload"
    assert revision["content_hash"] == hashlib.sha256(PNG).hexdigest()
    # 上传默认未公开授权：web-found 规则的前置
    assert revision["public_use_allowed"] is False


def test_same_material_reused_across_drafts(client, db_session, draft):
    resp = _upload(client)
    revision_id = resp.json()["revisions"][0]["id"]
    r1 = client.post(f"/api/v1/drafts/{draft.id}/materials", json={"material_revision_id": revision_id}, headers=EDITOR)
    assert r1.status_code == 201, r1.json()
    # 第二个 draft 引用同一 revision
    from app.models import ContentJob, Draft

    job2 = ContentJob(topic_brief_id=draft.content_job.topic_brief_id, channel="wechat", status="succeeded")
    db_session.add(job2)
    db_session.flush()
    draft2 = Draft(content_job_id=job2.id, revision_no=1, title="t2", body="x", status="draft")
    db_session.add(draft2)
    db_session.commit()
    r2 = client.post(f"/api/v1/drafts/{draft2.id}/materials", json={"material_revision_id": revision_id}, headers=EDITOR)
    assert r2.status_code == 201
    uses = db_session.query(DraftMedia).filter(DraftMedia.material_revision_id == revision_id).all()
    assert {u.draft_id for u in uses} == {draft.id, draft2.id}
    assert all(u.file_path is None or u.file_path for u in uses)  # use 行可无独立文件


def test_revoke_public_use_marks_uses_stale(client, db_session, draft):
    resp = _upload(client, public=True)
    revision_id = resp.json()["revisions"][0]["id"]
    client.post(f"/api/v1/drafts/{draft.id}/materials", json={"material_revision_id": revision_id}, headers=EDITOR)
    resp2 = client.post(
        f"/api/v1/materials/{{}}/revisions/{revision_id}/revoke-public-use".format(resp.json()["id"]),
        json={"note": "版权存疑"},
        headers=EDITOR,
    )
    assert resp2.status_code == 200
    assert resp2.json()["affected_drafts"] == [draft.id]
    db_session.expire_all()
    assert draft.candidate_readiness == "stale"
    revision = db_session.get(MaterialRevision, revision_id)
    assert revision.status == "revoked"
    assert revision.public_use_allowed is False


def test_approved_candidate_blocks_delete_and_replace_creates_new_revision(client, db_session, draft):
    """approved 引用的 Revision 不可变：删除被拒；"替换"= 新 revision，旧 hash 可重建。"""
    resp = _upload(client, public=True)
    material_id = resp.json()["id"]
    revision_id = resp.json()["revisions"][0]["id"]
    from app.models import ContentAsset

    db_session.add(
        ContentAsset(
            draft_id=draft.id, topic_brief_id=draft.content_job.topic_brief_id, channel="xiaohongshu",
            title="t", final_body="b", fact_pack_id=1, fact_pack_version=1, approved_revision=1,
            approved_candidate_hash="h" * 64,
            candidate_manifest_json={"schema_version": 2, "media": [{"material_revision_id": revision_id, "hash": hashlib.sha256(PNG).hexdigest()}]},
        )
    )
    db_session.commit()
    # 挂到稿上再尝试删除
    client.post(f"/api/v1/drafts/{draft.id}/materials", json={"material_revision_id": revision_id}, headers=EDITOR)
    media_row = db_session.query(DraftMedia).filter_by(draft_id=draft.id).first()
    resp_del = client.delete(f"/api/v1/drafts/{draft.id}/materials/{media_row.id}", headers=EDITOR)
    assert resp_del.status_code == 409
    # 旧字节仍可校验重建（read_bytes_checked hash 一致）
    revision = db_session.get(MaterialRevision, revision_id)
    content = materials_service.read_bytes_checked(db_session, revision)
    assert hashlib.sha256(content).hexdigest() == revision.content_hash
    # 同一 material 追加新 revision = "替换"的合法路径
    new_revision = materials_service.create_revision(db_session, db_session.get(Material, material_id), content=PNG + b"v2", suffix=".png", declared_mime="image/png")
    assert new_revision.revision_no == 2
    assert new_revision.content_hash != revision.content_hash


def test_upload_validation_rejects_unknown_binary(client):
    resp = client.post(
        "/api/v1/materials/upload",
        data={"kind": "image", "title": "bad"},
        files={"file": ("evil.bin", b"\x00\x01\x02\x03not-an-image", "application/octet-stream")},
        headers=EDITOR,
    )
    assert resp.status_code == 422


def test_search_capability_unavailable(client):
    """无 provider：422 capability_unavailable，不返回假数据（§6.15）。"""
    resp = client.post("/api/v1/materials/search", json={"query": "城市夜景"}, headers=EDITOR)
    assert resp.status_code == 422
    assert "capability_unavailable" in resp.json()["detail"]


def test_legacy_draft_media_remains_readable(client, db_session, draft):
    """历史 DraftMedia（无 material_revision_id/file_path 兼容旧路径）仍可读写。"""
    legacy = DraftMedia(
        draft_id=draft.id, content_hash="c" * 64, role="inline", sort_order=0,
        mime_type="image/png", rights_status="cleared", public_use_allowed=True,
    )
    db_session.add(legacy)
    db_session.commit()
    rows = client.get(f"/api/v1/drafts/{draft.id}/materials", headers=EDITOR).json()
    assert rows[0]["material_revision_id"] is None
    # 显式 adoption：提升为 Material+Revision
    revision = materials_service.adopt_draft_media(db_session, legacy, created_by="editor@studio.local")
    db_session.commit()
    assert legacy.material_revision_id == revision.id
    assert revision.source_kind == "legacy"


def test_document_composition_sync_and_set(client, db_session, draft):
    """placement 变化：document 重建 / set 校验归属，draft 标 stale（artifact-composition）。"""
    resp = _upload(client, public=True)
    revision_id = resp.json()["revisions"][0]["id"]
    client.post(f"/api/v1/drafts/{draft.id}/materials", json={"material_revision_id": revision_id}, headers=EDITOR)
    doc = client.get(f"/api/v1/drafts/{draft.id}/document", headers=EDITOR).json()["document"]
    image_blocks = [b for b in doc["blocks"] if b["type"] == "image"]
    assert len(image_blocks) == 1
    assert image_blocks[0]["material_revision_id"] == revision_id

    # 引用他人素材被拒
    bad = client.put(
        f"/api/v1/drafts/{draft.id}/document",
        json={"blocks": [{"id": "x", "type": "image", "draft_media_id": 99999}]},
        headers=EDITOR,
    )
    assert bad.status_code == 422

    # 合法重排：段落 → 图片顺序变化，draft 标 stale
    draft.candidate_readiness = "ready"
    db_session.commit()
    ok = client.put(
        f"/api/v1/drafts/{draft.id}/document",
        json={"blocks": [{"id": "p1", "type": "paragraph", "text": "第一段"}, {"id": "img" + str(image_blocks[0]["draft_media_id"]), "type": "image", "draft_media_id": image_blocks[0]["draft_media_id"]}, {"id": "p2", "type": "paragraph", "text": "第二段"}]},
        headers=EDITOR,
    )
    assert ok.status_code == 200
    db_session.expire_all()
    assert draft.candidate_readiness == "stale"
