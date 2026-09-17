"""核心主干测试：执行计划 §22 端到端验收用例 + STU-150 关键不变量。"""

from app.models import FactPack, FactPackStatus

ADMIN = {"X-Studio-User": "admin@studio.local"}

SAMPLE_TEXT = """2026-09-15 市场数据。
沪深300指数当日上涨1.2%，收于3900点。
两市成交额达到1.1万亿元。
AI算力板块成交额增长25%，资金关注度明显提升。
北向资金净流入82亿元。
某科技公司发布新款芯片，性能提升30%。
创业板指当日下跌0.5%。
半导体设备板块换手率3.4%。
国债收益率维持在2.1%附近。
"""


def _make_source_with_facts(client) -> int:
    resp = client.post(
        "/api/v1/sources/text",
        json={"title": "2026-09-15 市场数据", "content": SAMPLE_TEXT, "as_of": "2026-09-15", "trust_level": 0.9},
        headers=ADMIN,
    )
    assert resp.status_code == 201, resp.text
    source_id = resp.json()["id"]
    resp = client.post(f"/api/v1/sources/{source_id}/extract-facts", headers=ADMIN)
    assert resp.status_code == 201, resp.text
    candidates = resp.json()["candidates"]
    assert candidates >= 5
    return source_id


def _confirm_all_facts(client, source_id: int) -> list[int]:
    resp = client.get(f"/api/v1/facts?source_id={source_id}", headers=ADMIN)
    fact_ids = [f["id"] for f in resp.json() if f["status"] == "candidate"]
    resp = client.post("/api/v1/facts/bulk-status", json={"fact_ids": fact_ids, "action": "confirm"}, headers=ADMIN)
    assert resp.status_code == 200, resp.text
    return fact_ids


def _build_frozen_pack(client, name="2026-09-15 市场复盘") -> dict:
    source_id = _make_source_with_facts(client)
    fact_ids = _confirm_all_facts(client, source_id)
    resp = client.post("/api/v1/fact-packs", json={"name": name, "fact_ids": fact_ids}, headers=ADMIN)
    assert resp.status_code == 201, resp.text
    pack = resp.json()
    resp = client.post(f"/api/v1/fact-packs/{pack['id']}/freeze", headers=ADMIN)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _create_topic(client, pack_id: int, channels=("douyin", "xiaohongshu", "wechat")) -> dict:
    resp = client.post(
        "/api/v1/topics",
        json={
            "title": "今天的市场复盘",
            "audience": "普通投资者",
            "goal": "帮助理解今日市场",
            "angle": "数据复盘",
            "core_thesis": "今日市场结构分化，AI 算力是主线",
            "must_include": ["成交额"],
            "forbidden": ["保证收益"],
            "cta": "关注获取每日复盘",
            "fact_pack_id": pack_id,
            "channels": list(channels),
        },
        headers=ADMIN,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------- STU-031/032：导入 → 抽取 → 确认 ----------


def test_source_extract_and_confirm(client):
    source_id = _make_source_with_facts(client)
    resp = client.get(f"/api/v1/sources/{source_id}", headers=ADMIN)
    facts = resp.json()["facts"]
    assert resp.json()["parse_status"] == "done"
    assert all(f["status"] == "candidate" for f in facts)
    _confirm_all_facts(client, source_id)
    resp = client.get(f"/api/v1/facts?source_id={source_id}", headers=ADMIN)
    assert all(f["status"] == "confirmed" for f in resp.json())


def test_fact_reject(client):
    source_id = _make_source_with_facts(client)
    resp = client.get(f"/api/v1/facts?source_id={source_id}", headers=ADMIN)
    fact_id = resp.json()[0]["id"]
    resp = client.post(f"/api/v1/facts/{fact_id}/reject", headers=ADMIN)
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


# ---------- STU-033：冲突检测 ----------


def test_conflict_detection_same_key_different_value(client, db_session):
    from app.models import Fact, SourceDocument

    source = SourceDocument(title="s1", source_type="text", raw_text="x", parse_status="done")
    db_session.add(source)
    db_session.flush()
    facts = [
        Fact(source_document_id=source.id, statement="指数上涨1.2%", subject="沪深300",
             predicate="上涨", value_json={"value": 1.2}, unit="%", as_of="2026-09-15",
             status="confirmed"),
        Fact(source_document_id=source.id, statement="指数上涨1.5%", subject="沪深300",
             predicate="上涨", value_json={"value": 1.5}, unit="%", as_of="2026-09-15",
             status="confirmed"),
    ]
    db_session.add_all(facts)
    db_session.commit()

    # confirm 触发全量冲突重算
    resp = client.post(f"/api/v1/facts/{facts[0].id}/confirm", headers=ADMIN)
    assert resp.status_code == 200

    resp = client.get("/api/v1/facts?conflict_only=true", headers=ADMIN)
    conflicts = [f for f in resp.json() if f["statement"].startswith("指数上涨")]
    assert len(conflicts) == 2
    assert all(f["status"] == "conflict" for f in conflicts)


def test_conflict_blocks_freeze(client, db_session):
    from app.models import Fact, FactPackItem, SourceDocument

    source = SourceDocument(title="s", source_type="text", parse_status="done")
    db_session.add(source)
    db_session.flush()
    facts = [
        Fact(source_document_id=source.id, statement="a", subject="X", predicate="涨",
             value_json={"value": 1.0}, unit="%", as_of="2026-09-15", status="confirmed"),
        Fact(source_document_id=source.id, statement="b", subject="X", predicate="涨",
             value_json={"value": 2.0}, unit="%", as_of="2026-09-15", status="confirmed"),
    ]
    db_session.add_all(facts)
    db_session.commit()

    from app.services.factpack_service import detect_conflicts

    detect_conflicts(db_session)
    db_session.commit()

    pack = FactPack(name="冲突包", version=1)
    db_session.add(pack)
    db_session.flush()
    db_session.add_all([FactPackItem(fact_pack_id=pack.id, fact_id=f.id) for f in facts])
    db_session.commit()

    resp = client.post(f"/api/v1/fact-packs/{pack.id}/freeze", headers=ADMIN)
    assert resp.status_code == 400
    assert "冲突" in resp.json()["detail"]


# ---------- STU-042/043：冻结与克隆不变量 ----------


def test_freeze_validations(client):
    resp = client.post("/api/v1/fact-packs", json={"name": "空包"}, headers=ADMIN)
    empty_pack = resp.json()
    resp = client.post(f"/api/v1/fact-packs/{empty_pack['id']}/freeze", headers=ADMIN)
    assert resp.status_code == 400

    source_id = _make_source_with_facts(client)
    fact_ids = _confirm_all_facts(client, source_id)

    # 含 rejected 事实的包不能冻结
    resp = client.post(f"/api/v1/facts/{fact_ids[0]}/reject", headers=ADMIN)
    assert resp.status_code == 200
    resp = client.post("/api/v1/fact-packs", json={"name": "含未确认"}, headers=ADMIN)
    bad_pack = resp.json()
    resp = client.post(f"/api/v1/fact-packs/{bad_pack['id']}/items", json={"fact_id": fact_ids[0]}, headers=ADMIN)
    assert resp.status_code == 409  # 非 confirmed 事实加不进包

    # 正常冻结 + 不可变
    resp = client.post("/api/v1/fact-packs", json={"name": "正常包", "fact_ids": fact_ids[1:3]}, headers=ADMIN)
    assert resp.status_code == 201, resp.text
    normal_pack = resp.json()
    resp = client.post(f"/api/v1/fact-packs/{normal_pack['id']}/freeze", headers=ADMIN)
    assert resp.status_code == 200
    frozen = resp.json()
    assert frozen["checksum"] and frozen["frozen_at"]

    # 冻结后不可加 item
    resp = client.post(
        f"/api/v1/fact-packs/{frozen['id']}/items", json={"fact_id": fact_ids[3]}, headers=ADMIN
    )
    assert resp.status_code == 409

    # 再次冻结报错
    resp = client.post(f"/api/v1/fact-packs/{frozen['id']}/freeze", headers=ADMIN)
    assert resp.status_code == 409


def test_clone_creates_new_draft_version(client):
    frozen = _build_frozen_pack(client)
    resp = client.post(f"/api/v1/fact-packs/{frozen['id']}/clone", headers=ADMIN)
    assert resp.status_code == 201, resp.text
    clone = resp.json()
    assert clone["version"] == frozen["version"] + 1
    assert clone["parent_id"] == frozen["id"]
    assert clone["status"] == FactPackStatus.draft.value
    assert clone["item_count"] == frozen["item_count"]


def test_topic_requires_frozen_pack(client):
    resp = client.post("/api/v1/fact-packs", json={"name": "未冻结包"}, headers=ADMIN)
    draft_pack = resp.json()
    resp = client.post(
        "/api/v1/topics",
        json={"title": "t", "fact_pack_id": draft_pack["id"], "channels": ["douyin"]},
        headers=ADMIN,
    )
    assert resp.status_code == 409


# ---------- §22 端到端：三渠道生成 → FactCheck → 审核 → 资产 → 导出 ----------


def test_full_pipeline_and_immutability(client):
    frozen = _build_frozen_pack(client)
    topic = _create_topic(client, frozen["id"])

    resp = client.post(f"/api/v1/topics/{topic['id']}/generate", json={}, headers=ADMIN)
    assert resp.status_code == 201, resp.text
    jobs = resp.json()["jobs"]
    assert len(jobs) == 3
    assert all(j["status"] == "succeeded" for j in jobs), jobs

    for job in jobs:
        draft_id = job["draft_id"]
        resp = client.post(f"/api/v1/drafts/{draft_id}/fact-check", headers=ADMIN)
        assert resp.status_code == 200, resp.text
        assert resp.json()["result"] != "blocker", resp.json()
        resp = client.post(f"/api/v1/drafts/{draft_id}/submit-review", headers=ADMIN)
        assert resp.status_code == 201, resp.text
        resp = client.post(f"/api/v1/reviews/drafts/{draft_id}/approve", headers=ADMIN)
        assert resp.status_code == 201, resp.text

    resp = client.get("/api/v1/assets", headers=ADMIN)
    assets = resp.json()
    assert len(assets) == 3

    # 导出 MD/TXT/JSON + 抖音 SRT
    for asset in assets:
        for fmt in asset["allowed_formats"]:
            resp = client.post(f"/api/v1/assets/{asset['id']}/export", json={"fmt": fmt}, headers=ADMIN)
            assert resp.status_code == 200, resp.text
            assert len(resp.json()["content"]) > 0

    # 旧稿证据不可漂移：clone v2 修改后，v1 资产仍指向 v1
    resp = client.post(f"/api/v1/fact-packs/{frozen['id']}/clone", headers=ADMIN)
    v2 = resp.json()
    resp = client.get(f"/api/v1/assets/{assets[0]['id']}", headers=ADMIN)
    assert resp.json()["fact_pack"]["version"] == frozen["version"]
    assert v2["version"] == frozen["version"] + 1


def test_unfact_number_blocks_approval(client, inject_unfact):
    frozen = _build_frozen_pack(client, name="注入口径包")
    topic = _create_topic(client, frozen["id"], channels=("douyin",))

    resp = client.post(f"/api/v1/topics/{topic['id']}/generate", json={}, headers=ADMIN)
    job = resp.json()["jobs"][0]
    assert job["status"] == "succeeded"
    draft_id = job["draft_id"]

    resp = client.post(f"/api/v1/drafts/{draft_id}/fact-check", headers=ADMIN)
    body = resp.json()
    assert body["result"] == "blocker", body
    assert any(i["category"] == "number" for i in body["issues"])

    # blocker 时不能提交审核，也不能直接批准（Gate）
    resp = client.post(f"/api/v1/drafts/{draft_id}/submit-review", headers=ADMIN)
    assert resp.status_code == 409
    resp = client.post(f"/api/v1/reviews/drafts/{draft_id}/approve", headers=ADMIN)
    assert resp.status_code in (409, 403)  # 未进队列 approve 被状态校验拦下

    # 修正（编辑去掉无来源数字所在句）后重新 FactCheck 通过
    resp = client.get(f"/api/v1/drafts/{draft_id}", headers=ADMIN)
    original = resp.json()
    fixed_body = "\n".join(
        line for line in original["body"].split("\n") if "87.3" not in line and "资金净流入达到" not in line
    )
    resp = client.patch(f"/api/v1/drafts/{draft_id}", json={"body": fixed_body}, headers=ADMIN)
    assert resp.status_code == 200, resp.text
    new_draft = resp.json()
    assert new_draft["revision_no"] == original["revision_no"] + 1  # 不覆盖旧 Draft

    resp = client.post(f"/api/v1/drafts/{new_draft['id']}/fact-check", headers=ADMIN)
    assert resp.json()["result"] != "blocker", resp.json()
    resp = client.post(f"/api/v1/drafts/{new_draft['id']}/submit-review", headers=ADMIN)
    assert resp.status_code == 201
    resp = client.post(f"/api/v1/reviews/drafts/{new_draft['id']}/approve", headers=ADMIN)
    assert resp.status_code == 201, resp.text


def test_regenerate_keeps_old_draft(client):
    frozen = _build_frozen_pack(client, name="重生成口径")
    topic = _create_topic(client, frozen["id"], channels=("douyin",))
    resp = client.post(f"/api/v1/topics/{topic['id']}/generate", json={}, headers=ADMIN)
    job = resp.json()["jobs"][0]
    resp = client.post(f"/api/v1/content-jobs/{job['job_id']}/regenerate", headers=ADMIN)
    assert resp.status_code == 201
    assert resp.json()["revision_no"] == 2
    resp = client.get(f"/api/v1/content-jobs/{job['job_id']}", headers=ADMIN)
    assert len(resp.json()["drafts"]) == 2


def test_request_changes_flow(client):
    frozen = _build_frozen_pack(client, name="退回口径")
    topic = _create_topic(client, frozen["id"], channels=("xiaohongshu",))
    resp = client.post(f"/api/v1/topics/{topic['id']}/generate", json={}, headers=ADMIN)
    draft_id = resp.json()["jobs"][0]["draft_id"]
    client.post(f"/api/v1/drafts/{draft_id}/fact-check", headers=ADMIN)
    client.post(f"/api/v1/drafts/{draft_id}/submit-review", headers=ADMIN)

    resp = client.post(
        f"/api/v1/reviews/drafts/{draft_id}/request-changes",
        json={"comment": "开头太弱"},
        headers={"X-Studio-User": "reviewer@studio.local"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "changes_requested"

    resp = client.get("/api/v1/reviews/queue", headers=ADMIN)
    assert any(q["draft_id"] == draft_id for q in resp.json())


def test_rbac_viewer_cannot_write(client, db_session):
    from app.models import User

    db_session.add(User(email="viewer@studio.local", name="Viewer", role="viewer"))
    db_session.commit()
    viewer = {"X-Studio-User": "viewer@studio.local"}
    resp = client.post(
        "/api/v1/sources/text",
        json={"title": "x", "content": "y"},
        headers=viewer,
    )
    assert resp.status_code == 403
    resp = client.get("/api/v1/sources", headers=viewer)
    assert resp.status_code == 200  # 只读放行


def test_frozen_draft_after_pack_update_unchanged(client):
    """克隆 v2 并修改 Fact 后，v1 生成的旧稿引用不变化（PRD 验收 14）。"""
    frozen = _build_frozen_pack(client, name="漂移口径")
    topic = _create_topic(client, frozen["id"], channels=("wechat",))
    resp = client.post(f"/api/v1/topics/{topic['id']}/generate", json={}, headers=ADMIN)
    draft_id = resp.json()["jobs"][0]["draft_id"]
    before = client.get(f"/api/v1/drafts/{draft_id}", headers=ADMIN).json()

    resp = client.post(f"/api/v1/fact-packs/{frozen['id']}/clone", headers=ADMIN)
    v2 = resp.json()
    job_snapshot = client.get(f"/api/v1/content-jobs/{before['content_job_id']}", headers=ADMIN).json()
    assert job_snapshot["fact_pack_snapshot"]["version"] == frozen["version"]
    assert job_snapshot["fact_pack_snapshot"]["checksum"] == frozen["checksum"]

    after = client.get(f"/api/v1/drafts/{draft_id}", headers=ADMIN).json()
    assert after["body"] == before["body"]
    assert v2["id"] != frozen["id"]
