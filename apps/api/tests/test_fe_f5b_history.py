def imported(client, key="history-1"):
    response = client.post(
        "/api/v1/published-content/import",
        json={
            "records": [
                {"external_key": key, "channel": "youtube", "title": "旧内容", "content_snapshot": {"body": "历史正文"}}
            ]
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["items"][0]


def test_project_recovery_records_registered_event_atomically(client, db_session):
    from app.models import ContentAsset, DeliveryTarget, ProjectEvent

    persona = client.post("/api/v1/content-personas", json={"name": "回收身份"}).json()["id"]
    project = client.post("/api/v1/content-projects", json={"title": "回收项目"}).json()["id"]
    unit = client.post(
        f"/api/v1/content-projects/{project}/units", json={"title": "稿件", "persona_id": persona, "modality": "text"}
    ).json()["id"]
    asset = ContentAsset(
        project_id=project,
        content_unit_id=unit,
        channel="wechat",
        title="项目稿件",
        final_body="正文",
        candidate_hash="a" * 64,
    )
    db_session.add(asset)
    db_session.flush()
    target = DeliveryTarget(
        content_asset_id=asset.id,
        channel="wechat",
        content_form="article",
        account_ref="acct",
        authorization_version="v1",
        approved_candidate_hash="a" * 64,
        authorized_by="admin@studio.local",
        status="human_confirmed",
    )
    db_session.add(target)
    db_session.commit()
    payload = {"target_id": target.id, "publication_attestation": "人工核对", "idempotency_key": "project-recovery"}
    response = client.post("/api/v1/published-content/confirm-reconciled", json=payload)
    assert response.status_code == 201, response.text
    assert client.post("/api/v1/published-content/confirm-reconciled", json=payload).status_code == 201
    assert (
        db_session.query(ProjectEvent)
        .filter_by(project_id=project, event_type="delivery.publication_confirmed")
        .count()
        == 1
    )


def test_snapshot_timezone_order_and_cutoff_coverage(client):
    row = imported(client)
    for value, instant in [(100, "2026-09-28T08:00:00+08:00"), (150, "2026-09-28T01:00:00Z")]:
        response = client.post(
            f"/api/v1/published-content/{row['id']}/observations",
            json={
                "observation_kind": "metric",
                "metric_namespace": "youtube",
                "metric_key": "views",
                "numeric_value": value,
                "unit": "count",
                "observed_at": instant,
            },
        )
        assert response.status_code == 201
    result = client.get("/api/v1/learning/analysis").json()
    assert result["groups"][0]["sum"] == 150
    empty = client.get("/api/v1/learning/analysis?cutoff=2026-09-27T00:00:00Z").json()
    assert empty["observation_count"] == 0
    assert empty["coverage"]["metrics"]["missing"] == 1


def test_metric_correction_cannot_replace_number_with_text(client):
    row = imported(client)
    payload = {"metric_namespace": "youtube", "metric_key": "views", "unit": "count"}
    first = client.post(
        f"/api/v1/published-content/{row['id']}/observations",
        json={**payload, "observation_kind": "metric", "numeric_value": 100},
    ).json()
    result = client.post(
        f"/api/v1/published-content/{row['id']}/observations",
        json={**payload, "observation_kind": "correction", "text_value": "撤回", "supersedes_id": first["id"]},
    )
    assert result.status_code == 422


def test_external_account_reference_is_known_without_fake_identity_snapshot(client, db_session):
    from app.models import ContentAccount, ContentBrand, ContentPersona, User

    client.get("/api/v1/home")
    user = db_session.query(User).filter_by(email="admin@studio.local").one()
    brand = ContentBrand(owner_user_id=user.id, name="品牌")
    db_session.add(brand)
    db_session.flush()
    persona = ContentPersona(owner_user_id=user.id, brand_id=brand.id, name="角色")
    db_session.add(persona)
    db_session.flush()
    account = ContentAccount(persona_id=persona.id, name="账号")
    db_session.add(account)
    db_session.commit()
    response = client.post(
        "/api/v1/published-content",
        json={"external_key": "account-history", "channel": "youtube", "content_account_id": account.id},
    )
    assert response.status_code == 201
    assert response.json()["coverage"]["account"] == "known"
    assert response.json()["identity_snapshot_id"] is None


def test_metric_granularity_and_asof_are_persisted(client):
    row = imported(client)
    response = client.post(
        f"/api/v1/published-content/{row['id']}/observations",
        json={
            "observation_kind": "metric",
            "metric_namespace": "youtube",
            "metric_key": "views",
            "unit": "count",
            "numeric_value": 10,
            "granularity": "daily",
            "cutoff": "2026-09-27T23:00:00+08:00",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["payload"]["granularity"] == "daily"
    assert response.json()["payload"]["cutoff"] == "2026-09-27T15:00:00+00:00"


def test_incompatible_interval_granularities_are_not_coalesced(client):
    row = imported(client)
    for granularity in ["daily", "weekly"]:
        result = client.post(
            f"/api/v1/published-content/{row['id']}/observations",
            json={
                "observation_kind": "metric",
                "metric_namespace": "youtube",
                "metric_key": "views",
                "unit": "count",
                "numeric_value": 10,
                "granularity": granularity,
                "measurement_mode": "interval",
                "period_start": "2026-09-26T00:00:00Z",
                "period_end": "2026-09-27T00:00:00Z",
            },
        )
        assert result.status_code == 201
    analysis = client.get("/api/v1/learning/analysis").json()
    assert {group["granularity"] for group in analysis["groups"]} == {"daily", "weekly"}


def test_import_flush_collision_is_retried_atomically(client, db_session, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    client.get("/api/v1/home")
    flush = db_session.flush
    calls = 0

    def collision_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise IntegrityError("INSERT", {}, Exception("unique collision"))
        return flush(*args, **kwargs)

    monkeypatch.setattr(db_session, "flush", collision_once)
    row = imported(client)
    assert row["id"] is not None
    assert client.get("/api/v1/published-content").json()["total"] == 1


def test_publication_import_normalizes_equivalent_offsets_and_scoped_missing_dates(client):
    base = {"external_key": "dated", "channel": "wechat", "published_at": "2026-09-28T08:00:00+08:00"}
    first = client.post("/api/v1/published-content", json=base)
    repeat = client.post("/api/v1/published-content", json={**base, "published_at": "2026-09-28T00:00:00Z"})
    assert first.status_code == repeat.status_code == 201
    assert first.json()["id"] == repeat.json()["id"]
    imported(client)
    assert client.get("/api/v1/learning/analysis?channel=wechat").json()["missing_date_count"] == 0
    assert client.get("/api/v1/learning/analysis?cutoff=2026-09-28T00:00:00").status_code == 422


def test_over_bound_analysis_does_not_return_obsolete_latest(client, db_session):
    from datetime import UTC, datetime, timedelta

    from app.models import PerformanceObservation

    row = imported(client)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    db_session.add_all(
        PerformanceObservation(
            published_content_id=row["id"],
            observation_kind="metric",
            metric_namespace="youtube",
            metric_key="views",
            unit="count",
            numeric_value=i,
            observed_at=start + timedelta(seconds=i),
            payload_json={"measurement_mode": "snapshot"},
        )
        for i in range(10001)
    )
    db_session.commit()
    result = client.get("/api/v1/learning/analysis").json()
    assert result["incomplete"] is True and result["computed"] is False
    assert result["groups"] == [] and any("unavailable" in item for item in result["limitations"])
    assert result["coverage"]["metrics"]["unknown"] == 1


def test_recovery_reuses_qualifying_receipt_from_another_entry(client, db_session):
    from app.models import AuditLog, ContentAsset, DeliveryReceipt, DeliveryTarget, utcnow

    client.get("/api/v1/home")
    asset = ContentAsset(channel="wechat", title="既有回执", final_body="正文", candidate_hash="a" * 64)
    db_session.add(asset)
    db_session.flush()
    target = DeliveryTarget(
        content_asset_id=asset.id,
        channel="wechat",
        content_form="article",
        account_ref="acct",
        authorization_version="v1",
        approved_candidate_hash="a" * 64,
        authorized_by="admin@studio.local",
        status="human_confirmed",
    )
    db_session.add(target)
    db_session.flush()
    receipt = DeliveryReceipt(
        target_id=target.id,
        approved_candidate_hash="a" * 64,
        action=target.action,
        idempotency_key="old-api",
        status="human_confirmed",
        operator="admin@studio.local",
        delivered_at=utcnow(),
    )
    db_session.add(receipt)
    db_session.commit()
    payload = {
        "target_id": target.id,
        "publication_attestation": "复核已有人工发布回执",
        "idempotency_key": "recovery-reuse",
    }
    response = client.post("/api/v1/published-content/confirm-reconciled", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["delivery_receipt_id"] == receipt.id
    assert db_session.query(DeliveryReceipt).count() == 1
    asset.candidate_hash = "b" * 64
    db_session.commit()
    assert client.post("/api/v1/published-content/confirm-reconciled", json=payload).status_code == 409
    asset.candidate_hash = "a" * 64
    db_session.commit()
    db_session.query(AuditLog).filter_by(event="publication.recovery_attested").delete()
    db_session.commit()
    assert (
        client.post(
            "/api/v1/published-content/confirm-reconciled", json={**payload, "publication_attestation": "conflicting"}
        ).status_code
        == 409
    )


def test_observation_rechecks_active_status_under_write_lock(client, db_session, monkeypatch):
    from app.services import published_history

    record = imported(client)
    original = published_history.owned_record

    def archived_between_check_and_lock(db, user, record_id, **kwargs):
        row = original(db, user, record_id, **kwargs)
        row.status = "archived"
        db.commit()
        return row

    monkeypatch.setattr(published_history, "owned_record", archived_between_check_and_lock)
    result = client.post(
        f"/api/v1/published-content/{record['id']}/observations",
        json={"observation_kind": "feedback", "text_value": "不能写入已归档内容"},
    )
    assert result.status_code == 409


def test_external_import_is_idempotent_and_date_is_unknown(client):
    row = imported(client)
    assert row["origin"] == "external_import"
    assert row["published_at"] is None
    assert row["coverage"]["published_at"] in {"missing", "unknown"}
    assert imported(client)["id"] == row["id"]
    response = client.get(f"/api/v1/published-content/{row['id']}", headers={"X-Studio-User": "other@studio.local"})
    assert response.status_code == 404


def test_cumulative_snapshots_use_latest_not_sum(client):
    row = imported(client)
    for value, date in [(100, "2026-09-26T10:00:00Z"), (150, "2026-09-27T10:00:00Z")]:
        response = client.post(
            f"/api/v1/published-content/{row['id']}/observations",
            json={
                "observation_kind": "metric",
                "metric_namespace": "youtube",
                "metric_key": "views",
                "numeric_value": value,
                "unit": "count",
                "observed_at": date,
                "measurement_mode": "snapshot",
            },
        )
        assert response.status_code == 201, response.text
    analysis = client.get("/api/v1/learning/analysis?metric_namespace=youtube&metric_key=views").json()
    assert analysis["groups"][0]["sum"] == 150
    assert analysis["observation_count"] == 2


def test_correction_retains_window_and_replaces_prior_value(client):
    row = imported(client)
    payload = {
        "observation_kind": "metric",
        "metric_namespace": "youtube",
        "metric_key": "views",
        "numeric_value": 100,
        "unit": "count",
        "period_start": "2026-09-25T00:00:00Z",
        "period_end": "2026-09-26T00:00:00Z",
        "measurement_mode": "interval",
    }
    first = client.post(f"/api/v1/published-content/{row['id']}/observations", json=payload)
    assert first.status_code == 201, first.text
    corrected = client.post(
        f"/api/v1/published-content/{row['id']}/observations",
        json={**payload, "observation_kind": "correction", "numeric_value": 120, "supersedes_id": first.json()["id"]},
    )
    assert corrected.status_code == 201, corrected.text
    analysis = client.get("/api/v1/learning/analysis").json()
    assert analysis["groups"][0]["sum"] == 120


def test_home_learning_candidates_are_owned_and_have_distinct_links(client, db_session):
    from app.models import LearningCandidate, User

    client.get("/api/v1/home")
    user = db_session.query(User).filter_by(email="admin@studio.local").first()
    assert user is not None
    first = LearningCandidate(
        owner_user_id=user.id, category="topic", title="第一条", proposition="主张", status="ready_for_review"
    )
    second = LearningCandidate(
        owner_user_id=user.id, category="topic", title="第二条", proposition="主张", status="ready_for_review"
    )
    db_session.add_all([first, second])
    db_session.commit()
    decisions = client.get("/api/v1/home").json()["decisions"]
    learning = [item for item in decisions if item["code"] == "learning_validation"]
    assert {item["learning_candidate_id"] for item in learning} == {first.id, second.id}
    assert all(item["project_id"] is None and "tab=candidates" in item["href"] for item in learning)
    other = client.get("/api/v1/home", headers={"X-Studio-User": "other@studio.local"}).json()
    assert not [item for item in other["decisions"] if item["code"] == "learning_validation"]


def test_reconciled_target_needs_explicit_attestation_and_retries_are_idempotent(client, db_session):
    from app.models import ContentAsset, DeliveryReceipt, DeliveryTarget, PublishedContentRecord

    client.get("/api/v1/home")
    asset = ContentAsset(channel="wechat", title="人工确认", final_body="正文", candidate_hash="a" * 64)
    db_session.add(asset)
    db_session.flush()
    target = DeliveryTarget(
        content_asset_id=asset.id,
        channel="wechat",
        content_form="article",
        account_ref="acct",
        authorization_version="v1",
        approved_candidate_hash="a" * 64,
        authorized_by="admin@studio.local",
        status="human_confirmed",
    )
    db_session.add(target)
    db_session.commit()
    sync = client.post("/api/v1/published-content/sync-studio").json()
    assert sync["items"] == [] and target.id in sync["missing_confirmation_target_ids"]
    payload = {"target_id": target.id, "publication_attestation": "已经核对公开文章", "idempotency_key": "confirm-one"}
    assert (
        client.post(
            "/api/v1/published-content/confirm-reconciled", json={**payload, "publication_attestation": " "}
        ).status_code
        == 422
    )
    first = client.post("/api/v1/published-content/confirm-reconciled", json=payload)
    assert first.status_code == 201, first.text
    assert first.json()["published_at"] is None
    repeat = client.post("/api/v1/published-content/confirm-reconciled", json=payload)
    assert repeat.status_code == 201 and repeat.json()["id"] == first.json()["id"]
    assert (
        client.post(
            "/api/v1/published-content/confirm-reconciled", json={**payload, "publication_attestation": "changed"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/v1/published-content/confirm-reconciled",
            json=payload,
            headers={"X-Studio-User": "other@studio.local"},
        ).status_code
        == 404
    )
    assert db_session.query(DeliveryReceipt).count() == 1
    assert db_session.query(PublishedContentRecord).count() == 1
    db_session.refresh(target)
    assert target.status == "human_confirmed"
    feedback = client.post(f"/api/v1/delivery-targets/{target.id}/feedback", json={"body": "人工反馈，无指标"})
    assert feedback.status_code == 201
    observation = {
        "observation_kind": "feedback",
        "source_type": "delivery_feedback",
        "source_ref": str(feedback.json()["id"]),
    }
    result = client.post(f"/api/v1/published-content/{first.json()['id']}/observations", json=observation)
    assert result.status_code == 201 and result.json()["numeric_value"] is None
    external = imported(client)
    assert client.post(f"/api/v1/published-content/{external['id']}/observations", json=observation).status_code == 422


def test_import_conflict_rolls_back_whole_batch_and_archived_is_read_only(client):
    row = imported(client)
    response = client.post(
        "/api/v1/published-content/import",
        json={
            "records": [
                {"external_key": "new-before-conflict", "channel": "youtube"},
                {"external_key": "history-1", "channel": "youtube", "title": "different"},
            ]
        },
    )
    assert response.status_code == 409
    assert client.get("/api/v1/published-content").json()["total"] == 1
    assert client.delete(f"/api/v1/published-content/{row['id']}").status_code == 204
    assert client.get(f"/api/v1/published-content/{row['id']}").status_code == 200
    assert (
        client.post(
            f"/api/v1/published-content/{row['id']}/observations",
            json={"observation_kind": "feedback", "text_value": "评论"},
        ).status_code
        == 409
    )


def test_units_are_not_merged_and_zero_is_known(client):
    row = imported(client)
    for unit, value in [("count", 0), ("seconds", 10)]:
        response = client.post(
            f"/api/v1/published-content/{row['id']}/observations",
            json={
                "observation_kind": "metric",
                "metric_namespace": "youtube",
                "metric_key": "views",
                "numeric_value": value,
                "unit": unit,
            },
        )
        assert response.status_code == 201
    result = client.get("/api/v1/learning/analysis").json()
    assert len(result["groups"]) == 2
    assert {group["unit"]: group["sum"] for group in result["groups"]} == {"count": 0, "seconds": 10}
    assert client.get(f"/api/v1/published-content/{row['id']}").json()["coverage"]["metrics"] == "known"
    assert (
        client.post(
            f"/api/v1/published-content/{row['id']}/observations",
            json={"observation_kind": "metric", "numeric_value": 2},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/v1/published-content/{row['id']}/observations",
            json={"observation_kind": "feedback", "text_value": "未经连接", "source_type": "connector"},
        ).status_code
        == 409
    )
