"""外部内容入库协议测试（dsh/Agent skills → Studio 汇聚）。"""

EDITOR = {"X-Studio-User": "editor@studio.local"}


def _ingest(client, **overrides):
    payload = {
        "title": "一次 \\b 漏判的复盘",
        "body": "正文内容……",
        "channel": "wechat",
        "origin": "dsh",
        "origin_ref": "runs/20260917-131219-c0dbd3/draft.md",
        "tags": ["工程复盘"],
    }
    payload.update(overrides)
    return client.post("/api/v1/assets/ingest", json=payload, headers=EDITOR)


def test_ingest_creates_content(client, db_session):
    from app.models import User

    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()

    resp = _ingest(client)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "draft"
    assert data["origin"] == "dsh"

    # 列表可见
    listing = client.get("/api/v1/external-contents", headers=EDITOR).json()
    assert any(c["id"] == data["id"] for c in listing)


def test_ingest_idempotent_on_origin_ref(client, db_session):
    from app.models import User

    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()

    first = _ingest(client).json()
    again = client.post(
        "/api/v1/assets/ingest",
        json={"title": "改了标题再报一次", "body": "x", "channel": "wechat", "origin": "dsh",
              "origin_ref": "runs/20260917-131219-c0dbd3/draft.md"},
        headers=EDITOR,
    )
    assert again.status_code == 200
    assert again.json()["deduplicated"] is True
    assert again.json()["id"] == first["id"]

    # 无 origin_ref 不去重
    third = _ingest(client, origin_ref=None, title="无引用")
    assert third.status_code == 201


def test_ingest_validates_channel_and_origin(client, db_session):
    from app.models import User

    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()
    assert _ingest(client, channel="twitter").status_code == 400
    assert _ingest(client, origin="chatgpt").status_code == 400


def test_external_status_transition(client, db_session):
    from app.models import User

    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()
    content_id = _ingest(client).json()["id"]

    resp = client.patch(f"/api/v1/external-contents/{content_id}", json={"status": "published"}, headers=EDITOR)
    assert resp.json()["status"] == "published"
    detail = client.get(f"/api/v1/external-contents/{content_id}", headers=EDITOR).json()
    assert detail["body"] == "正文内容……"

    assert client.patch(
        f"/api/v1/external-contents/{content_id}", json={"status": "bogus"}, headers=EDITOR
    ).status_code == 400
