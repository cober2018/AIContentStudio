import pytest
from fastapi import HTTPException

from app.models import ContentAccount, PerformanceObservation, User
from app.services import account_metrics_import as imports
from app.services.creative_mcp import AccountMetricRow


def account(client, db_session, channel):
    persona = client.post("/api/v1/content-personas", json={"name": "复盘作者"}).json()["id"]
    user = db_session.query(User).filter_by(email="admin@studio.local").one()
    row = ContentAccount(owner_user_id=user.id, persona_id=persona, name="复盘号", platform_channel=channel, platform_account_id="acct" + "a" * 16)
    db_session.add(row)
    db_session.commit()
    return user, row


def test_wechat_channels_imports_with_its_object_id(client, db_session):
    user, acct = account(client, db_session, "wechat_channels")
    assert next(a for a in imports.list_accounts(db_session, user)["accounts"] if a["id"] == acct.id)["importable"]
    item = "export/UzFfBgAAxOOEPBVnGXqfk8zT4DCa7qx6KPAaB9mkdXpJUbv8LQ"
    row = AccountMetricRow(title="120个因子", published_at="2026-11-17 14:22:16", platform_item_id=item,
                           metrics={"plays": 472, "completion_rate": 0.036, "avg_play_seconds": 34.66, "likes": 5,
                                    "recommends": 2, "shares": 4, "followers_gained": 3}).model_dump()
    result = imports.import_metrics(db_session, user, acct.id, {"kind": "platform_page", "name": "视频号助手", "checksum": "c" * 64}, [row])
    assert result["counts"]["records_created"] == 1 and result["counts"]["observations"] == 7
    labels = {o.metric_key: o.payload_json["label"] for o in db_session.query(PerformanceObservation).all()}
    assert labels["recommends"] == "推荐/爱心" and labels["completion_rate"] == "完播率"


@pytest.mark.parametrize("channel,metrics", [
    ("xiaohongshu", {"impressions": 1460, "cover_ctr": 0.075, "completion_rate": 0.019, "bounce_rate_2s": 0.465, "followers_gained": 10}),
    ("wechat", {"favorites": 63, "followers_gained": 95, "avg_read_seconds": 75, "read_completion_rate": 0.957}),
    ("bilibili", {"avg_play_ratio": 0.579, "cover_ctr": 0.0591, "bounce_rate_3s": 0.2, "unfollows": 0}),
])
def test_backend_fields_are_accepted(client, db_session, channel, metrics):
    user, acct = account(client, db_session, channel)
    row = {"title": "作品", "published_at": "2026-11-17 14:20", "metrics": metrics}
    result = imports.import_metrics(db_session, user, acct.id, {"kind": "platform_page", "name": channel, "checksum": channel * 3}, [row])
    assert result["counts"]["observations"] == len(metrics)


def test_rates_still_refuse_percent_numbers(client, db_session):
    user, acct = account(client, db_session, "xiaohongshu")
    row = {"title": "作品", "published_at": "2026-11-17 14:20", "metrics": {"cover_ctr": 7.5}}
    with pytest.raises(HTTPException) as error:
        imports.import_metrics(db_session, user, acct.id, {"kind": "platform_page", "name": "x", "checksum": "d" * 64}, [row])
    assert error.value.detail["code"] == "account_import_rows_invalid"


def test_list_published_works_gives_china_time(client, db_session):
    user, acct = account(client, db_session, "bilibili")
    row = {"title": "作品", "published_at": "2026-11-17 18:22:16", "platform_item_id": "BV1x", "metrics": {"views": 1}}
    imports.import_metrics(db_session, user, acct.id, {"kind": "platform_page", "name": "b", "checksum": "e" * 64}, [row])
    works = imports.list_published_works(db_session, user, acct.id)["works"]
    assert next(w for w in works if w["platform_item_id"] == "BV1x")["published_at"] == "2026-11-17T18:22:16+08:00"


def test_craft_guides_pass_the_mcp_secret_filter():
    from pathlib import Path

    from app.services.creative_intents import contains_secret_text

    root = Path(__file__).resolve().parents[1] / "craft_skills"
    assert [str(p) for p in root.rglob("*.md") if contains_secret_text(p.read_text(encoding="utf-8"))] == []
