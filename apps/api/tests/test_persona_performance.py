from app.services import account_metrics_import as imports
from tests.test_account_metrics_import import account


def _rows(views):
    return [{"title": f"作品{i}", "published_at": f"2026-10-{i + 1:02d} 10:00", "platform_item_id": f"w{i}",
             "metrics": {"plays": v, "comments": 2, "likes": 1, "followers_gained": 1}} for i, v in enumerate(views)]


def test_timeline_flags_breakout_and_cold_start_within_a_platform(client, db_session):
    user, acct = account(client, db_session, "douyin")
    imports.import_metrics(db_session, user, acct.id, {"kind": "platform_page", "name": "抖音", "checksum": "1" * 64},
                           _rows([100, 100, 100, 100, 20, 900]))
    data = client.get(f"/api/v1/learning/personas/{acct.persona_id}/timeline?days=0").json()
    assert [w["title"] for w in data["works"]] == [f"作品{i}" for i in range(6)]
    kinds = {(e["title"], e["type"]) for e in data["events"]}
    assert ("作品5", "breakout") in kinds and ("作品4", "cold_start") in kinds and ("作品0", "new_channel") in kinds
    assert ("作品0", "breakout") not in kinds
    assert data["channels"][0]["median_views"] == 100


def test_too_few_works_give_no_relative_events(client, db_session):
    user, acct = account(client, db_session, "douyin")
    imports.import_metrics(db_session, user, acct.id, {"kind": "platform_page", "name": "抖音", "checksum": "2" * 64}, _rows([10, 5000]))
    data = client.get(f"/api/v1/learning/personas/{acct.persona_id}/timeline?days=0").json()
    assert not {e["type"] for e in data["events"]} & {"breakout", "cold_start"}


def test_works_list_filters_by_persona(client, db_session):
    user, acct = account(client, db_session, "douyin")
    imports.import_metrics(db_session, user, acct.id, {"kind": "platform_page", "name": "抖音", "checksum": "3" * 64}, _rows([10]))
    assert client.get(f"/api/v1/published-content?persona_id={acct.persona_id}").json()["total"] == 1
    other = client.post("/api/v1/content-personas", json={"name": "别的角色"}).json()["id"]
    assert client.get(f"/api/v1/published-content?persona_id={other}").json()["total"] == 0


def test_followers_sum_latest_per_account_and_same_day_replaces(client, db_session):
    from app.models import AccountFollowerSnapshot, ContentAccount
    from app.services.account_metrics_import import record_followers

    user, douyin = account(client, db_session, "douyin")
    wechat = ContentAccount(owner_user_id=user.id, persona_id=douyin.persona_id, name="公众号", platform_channel="wechat", platform_account_id="gh" + "b" * 16)
    silent = ContentAccount(owner_user_id=user.id, persona_id=douyin.persona_id, name="知乎", platform_channel="zhihu", platform_account_id="zh" + "c" * 16)
    db_session.add_all([wechat, silent])
    db_session.commit()
    db_session.add(AccountFollowerSnapshot(owner_user_id=user.id, content_account_id=douyin.id, followers=200,
                                           observed_on="2026-11-01", source_name="旧"))
    db_session.commit()
    record_followers(db_session, user, douyin.id, 260, "抖音首页")
    result = record_followers(db_session, user, douyin.id, 275, "抖音首页")
    assert result["previous"] == {"followers": 200, "observed_on": "2026-11-01"}
    record_followers(db_session, user, wechat.id, 1076, "公众号首页")
    followers = client.get(f"/api/v1/learning/personas/{douyin.persona_id}/timeline?days=0").json()["followers"]
    assert followers["total"] == 1351 and followers["recorded"] == 2 and followers["missing"] == 1
    row = next(a for a in followers["accounts"] if a["account_id"] == douyin.id)
    assert row["followers"] == 275 and row["change"] == 75 and len(row["history"]) == 2
    assert followers["trend"][-1]["followers"] == 1351


def test_record_followers_is_an_mcp_review_tool():
    from app.services.creative_mcp import TOOLS
    from app.services.mcp_settings import GROUPS

    assert "record_account_followers" in TOOLS
    assert any("record_account_followers" in tools for _label, tools in GROUPS.values())
