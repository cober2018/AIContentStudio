from sqlalchemy import select

from app.models import (
    ContentAccount,
    ContentAsset,
    ContentPersona,
    ContentProject,
    ContentUnit,
    DeliveryReceipt,
    DeliveryTarget,
    PerformanceObservation,
    PublishedContentRecord,
    User,
    utcnow,
)
from app.services import account_metrics_import as imports
from app.services import published_history as history


def env(client, db_session, channel="wechat_channels"):
    client.get("/api/v1/published-content")
    user = db_session.query(User).filter_by(email="admin@studio.local").one()
    persona = ContentPersona(owner_user_id=user.id, name="作者")
    project = ContentProject(owner_user_id=user.id, title="P")
    db_session.add_all([persona, project])
    db_session.flush()
    unit = ContentUnit(project_id=project.id, persona_id=persona.id, modality="video", title="决定AI量化生死的4根数据支柱")
    db_session.add(unit)
    db_session.flush()
    asset = ContentAsset(project_id=project.id, content_unit_id=unit.id, channel="unassigned", title=unit.title,
                         final_body="b", candidate_hash="c" * 64, approved_candidate_hash="c" * 64)
    account = ContentAccount(owner_user_id=user.id, persona_id=persona.id, name="号", platform_channel=channel,
                             platform_account_id="acct" + "b" * 16)
    db_session.add_all([asset, account])
    db_session.flush()
    target = DeliveryTarget(content_asset_id=asset.id, channel=channel, content_form="short_video", account_ref="号",
                            authorization_version="v1", approved_candidate_hash="c" * 64, authorized_by=user.email,
                            status="target_authorized", action="copy_package")
    db_session.add(target)
    db_session.commit()
    return user, unit, asset, account, target


def imported(db_session, user, account, plays, checksum):
    row = {"title": "接口悄悄返回空数组…四根支柱", "published_at": "2026-11-11 20:15:23", "platform_item_id": "export/abc",
           "metrics": {"plays": plays}}
    imports.import_metrics(db_session, user, account.id, {"kind": "platform_page", "name": "视频号", "checksum": checksum}, [row])
    return db_session.scalar(select(PublishedContentRecord).where(PublishedContentRecord.external_key == "item:export/abc"))


def test_match_keeps_data_and_later_imports_follow(client, db_session):
    user, unit, asset, account, target = env(client, db_session)
    record = imported(db_session, user, account, 100, "a" * 64)
    assert any(c["content_unit_id"] == unit.id and c["has_target"]
               for c in history.match_candidates(db_session, user, record.id)["items"])
    response = client.post(f"/api/v1/published-content/{record.id}/match", json={"content_unit_id": unit.id})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == record.id and body["matched_work"]["content_unit_id"] == unit.id
    assert body["content_asset_id"] == asset.id and body["delivery_target_id"] == target.id
    assert body["title"] == "接口悄悄返回空数组…四根支柱"
    again = imported(db_session, user, account, 150, "b" * 64)
    assert again.id == record.id
    assert db_session.query(PublishedContentRecord).filter_by(channel="wechat_channels", status="active").count() == 1
    # 之后补上回执也接到这一条，不重复统计。
    receipt = DeliveryReceipt(target_id=target.id, approved_candidate_hash="c" * 64, action="copy_package",
                              idempotency_key="k", status="human_confirmed", delivered_at=utcnow(), operator=user.email)
    db_session.add(receipt)
    db_session.flush()
    assert history.sync_receipt(db_session, user, receipt).id == record.id
    assert db_session.query(PublishedContentRecord).filter_by(channel="wechat_channels").count() == 1


def test_match_merges_into_existing_record(client, db_session):
    user, unit, asset, account, target = env(client, db_session)
    studio = PublishedContentRecord(owner_user_id=user.id, origin="studio", content_asset_id=asset.id,
                                    delivery_target_id=target.id, channel="wechat_channels", title=unit.title,
                                    content_snapshot_json={}, coverage_json={})
    db_session.add(studio)
    db_session.commit()
    record = imported(db_session, user, account, 100, "c" * 64)
    response = client.post(f"/api/v1/published-content/{record.id}/match", json={"content_unit_id": unit.id})
    assert response.status_code == 200, response.text
    assert response.json()["id"] == studio.id
    db_session.expire_all()
    assert db_session.get(PublishedContentRecord, record.id).status == "archived"
    assert {o.published_content_id for o in db_session.query(PerformanceObservation)} == {studio.id}
    assert imported(db_session, user, account, 120, "d" * 64).id == studio.id
    assert db_session.query(PublishedContentRecord).filter_by(channel="wechat_channels", status="active").count() == 1


def test_only_external_records_match(client, db_session):
    user, unit, asset, _, _ = env(client, db_session)
    studio = PublishedContentRecord(owner_user_id=user.id, origin="studio", content_asset_id=asset.id,
                                    channel="wechat_channels", content_snapshot_json={}, coverage_json={})
    db_session.add(studio)
    db_session.commit()
    assert client.post(f"/api/v1/published-content/{studio.id}/match", json={"content_unit_id": unit.id}).status_code == 409
