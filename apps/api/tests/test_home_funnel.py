from app.services import account_metrics_import as imports
from tests.test_account_metrics_import import account


def test_funnel_counts_posts_and_latest_metrics(client, db_session):
    user, acct = account(client, db_session, "douyin")
    source = {"kind": "platform_page", "name": "抖音", "checksum": "f" * 64}
    imports.import_metrics(db_session, user, acct.id, source, [
        {"title": "甲", "published_at": "2026-11-17 10:00", "platform_item_id": "a1", "metrics": {"plays": 100, "likes": 5, "comments": 2, "followers_gained": 3}},
        {"title": "乙", "published_at": "2026-11-17 11:00", "platform_item_id": "a2", "metrics": {"plays": 40}},
    ])
    data = client.get("/api/v1/home/funnel?days=0").json()
    assert data["totals"]["posts"] == 2 and data["totals"]["views"] == 140
    assert data["totals"]["engagements"] == 7 and data["totals"]["followers_gained"] == 3
    assert [w["title"] for w in data["top_works"]] == ["甲", "乙"]
    row = next(p for p in data["personas"] if p["persona_id"] == acct.persona_id)
    assert row["posts"] == 2 and row["posts_studio"] == 0
    assert data["channels"][0] == {"channel": "douyin", "channel_label": "抖音", "posts": 2, "views": 140, "engagements": 7, "followers_gained": 3}


def test_sku_list_reports_total(client):
    assert client.get("/api/v1/product-skus?limit=1").json()["total"] >= 0
