"""Learning decision and Memory gates against a real isolated database."""

import pytest
from sqlalchemy import func, select

from app.models import (
    ContentBrandRevision,
    ContentInsight,
    ContentMemoryEntry,
    ContentMemoryRevision,
    LearningCandidate,
    LearningCandidateEvidence,
    PerformanceObservation,
    PublishedContentRecord,
    User,
    utcnow,
)

BASE = "/api/v1"
OTHER = {"X-Studio-User": "other@studio.local"}


def published(client, db_session, other=False):
    owner = db_session.scalar(
        select(User).where(User.email == ("other@studio.local" if other else "admin@studio.local"))
    )
    if owner is None:
        owner = User(email="other@studio.local" if other else "admin@studio.local", name="test", role="editor")
        db_session.add(owner)
        db_session.commit()
    row = PublishedContentRecord(owner_user_id=owner.id, origin="external_import", channel="wechat", title="样本")
    db_session.add(row)
    db_session.commit()
    obs = PerformanceObservation(
        published_content_id=row.id,
        observation_kind="metric",
        numeric_value=10,
        metric_namespace="wechat",
        metric_key="reads",
        observed_at=utcnow(),
    )
    db_session.add(obs)
    db_session.commit()
    return row.id, obs.id


def candidate(client, **overrides):
    result = client.post(
        BASE + "/learning-candidates",
        json={"category": "topic", "title": "假设", "proposition": "具体假设", **overrides},
    )
    assert result.status_code == 201, result.text
    return result.json()


def evidence(client, row, entity_id, evidence_type="published_content", role="support"):
    result = client.post(
        f"{BASE}/learning-candidates/{row['id']}/evidence",
        json={
            "expected_revision": row["revision_no"],
            "evidence_type": evidence_type,
            "entity_id": entity_id,
            "role": role,
        },
    )
    assert result.status_code == 201, result.text
    return client.get(f"{BASE}/learning-candidates/{row['id']}").json()


def ready(client, row):
    result = client.post(
        f"{BASE}/learning-candidates/{row['id']}/submit-review", json={"expected_revision": row["revision_no"]}
    )
    assert result.status_code == 200, result.text
    return result.json()


def validate(client, row, **overrides):
    return client.post(
        f"{BASE}/learning-candidates/{row['id']}/validate",
        json={
            "expected_revision": row["revision_no"],
            "decision": "accepted",
            "validation_method": "human",
            "validation_summary": {"rationale": "人工核对证据"},
            **overrides,
        },
    )


def accepted(client, db_session, validation_summary=None, **overrides):
    pid, _ = published(client, db_session)
    row = ready(client, evidence(client, candidate(client, **overrides), pid))
    result = validate(client, row, **({"validation_summary": validation_summary} if validation_summary else {}))
    assert result.status_code == 200, result.text
    return result.json()


def promotion(**overrides):
    return {
        "idempotency_key": "explicit",
        "scope_type": "owner",
        "memory_type": "topic_learning",
        "statement": "具体假设",
        "applicability": {"channel": "wechat"},
        "limitations": ["single_sample", "仅适用于当前样本"],
        **overrides,
    }


def test_insights_owner_refs_immutable_and_unavailable(client, db_session):
    pid, oid = published(client, db_session)
    foreign, _ = published(client, db_session, other=True)
    payload = {
        "statement": "人工分析",
        "supporting_refs": [{"evidence_type": "performance_observation", "entity_id": oid}],
        "contradicting_refs": [{"evidence_type": "published_content", "entity_id": pid}],
        "limitations": ["一个样本"],
    }
    result = client.post(BASE + "/learning/insights", json=payload)
    assert result.status_code == 201, result.text
    insight = result.json()
    assert insight["coverage"]["published_content_count"] == 1
    assert client.get(f"{BASE}/learning/insights/{insight['id']}", headers=OTHER).status_code == 404
    assert client.patch(f"{BASE}/learning/insights/{insight['id']}", json={"statement": "修改"}).status_code == 405
    for refs in ["supporting_refs", "contradicting_refs"]:
        assert (
            client.post(
                BASE + "/learning/insights",
                json={**payload, refs: [{"evidence_type": "published_content", "entity_id": foreign}]},
            ).status_code
            == 404
        )
    assert client.post(BASE + "/learning/insights", json={**payload, "analysis_source": "model"}).status_code == 422
    assert (
        client.post(
            BASE + "/learning/insights", json={**payload, "coverage": {"published_content_count": 99}}
        ).status_code
        == 422
    )
    second = client.post(BASE + "/learning/insights", json={**payload, "supersedes_id": insight["id"]})
    assert second.status_code == 201
    assert (
        client.post(
            BASE + "/learning/insights", headers=OTHER, json={"statement": "foreign", "supersedes_id": insight["id"]}
        ).status_code
        == 404
    )
    before = db_session.scalar(select(func.count()).select_from(ContentInsight))
    assert client.post(BASE + "/learning/insights/analyze").json()["status"] == "capability_unavailable"
    assert db_session.scalar(select(func.count()).select_from(ContentInsight)) == before


def test_candidate_cas_lifecycle_and_freeze(client, db_session):
    pid, oid = published(client, db_session)
    row = candidate(client)
    assert validate(client, row).status_code == 409
    row = evidence(client, row, oid, "performance_observation")
    row = evidence(client, row, pid, role="contradict")
    before = row["revision_no"]
    assert (
        client.patch(
            f"{BASE}/learning-candidates/{row['id']}", json={"expected_revision": 1, "proposition": "race"}
        ).status_code
        == 409
    )
    row = ready(client, row)
    assert (
        client.post(
            f"{BASE}/learning-candidates/{row['id']}/evidence",
            json={
                "expected_revision": row["revision_no"],
                "evidence_type": "published_content",
                "entity_id": pid,
                "role": "support",
            },
        ).status_code
        == 409
    )
    assert validate(client, row, validation_summary={}).status_code == 422
    assert validate(client, row, validation_method="rule").status_code == 409
    result = validate(client, row)
    assert result.status_code == 200, result.text
    frozen = result.json()["validation_summary"]
    assert frozen["proposition"] == "具体假设"
    assert len(frozen["evidence"]) == 2
    assert frozen["evidence"][1]["role"] == "contradict"
    assert frozen["evidence"][0]["snapshot_checksum"]
    assert db_session.scalar(select(func.count()).select_from(ContentMemoryEntry)) == 0
    db_session.get(PerformanceObservation, oid).numeric_value = 999
    db_session.commit()
    assert client.get(f"{BASE}/learning-candidates/{row['id']}").json()["validation_summary"] == frozen
    assert (
        client.patch(
            f"{BASE}/learning-candidates/{row['id']}", json={"expected_revision": before + 2, "proposition": "改历史"}
        ).status_code
        == 409
    )
    assert validate(client, result.json(), decision="collecting").status_code == 409
    assert client.get(f"{BASE}/learning-candidates/{row['id']}", headers=OTHER).status_code == 404


def test_support_and_independent_samples_required(client, db_session):
    pid, oid = published(client, db_session)
    row = ready(client, evidence(client, candidate(client), pid, role="context"))
    assert validate(client, row).status_code == 422
    row = ready(client, evidence(client, evidence(client, candidate(client), pid), oid, "performance_observation"))
    assert (
        validate(
            client,
            row,
            validation_method="multi_sample",
            validation_summary={"sample_definition": "independent published items"},
        ).status_code
        == 422
    )
    other, _ = published(client, db_session)
    result = validate(client, row, decision="collecting")
    assert result.status_code == 200, result.text
    row = ready(client, evidence(client, result.json(), other))
    assert (
        validate(
            client,
            row,
            validation_method="multi_sample",
            validation_summary={"sample_definition": "independent published items"},
        ).status_code
        == 200
    )


@pytest.mark.parametrize("kind", ["published_content", "performance_observation", "insight", "delivery_feedback"])
def test_evidence_foreign_rejected(client, db_session, kind):
    pid, oid = published(client, db_session, other=True)
    foreign_insight = client.post(
        BASE + "/learning/insights",
        headers=OTHER,
        json={"statement": "foreign", "supporting_refs": [{"evidence_type": "published_content", "entity_id": pid}]},
    ).json()
    entity_id = {
        "published_content": pid,
        "performance_observation": oid,
        "insight": foreign_insight.get("id", 999),
        "delivery_feedback": 999,
    }[kind]
    row = candidate(client)
    response = client.post(
        f"{BASE}/learning-candidates/{row['id']}/evidence",
        json={"expected_revision": 1, "evidence_type": kind, "entity_id": entity_id, "role": "support"},
    )
    assert response.status_code == 404, response.text
    db_session.commit()
    assert db_session.get(LearningCandidate, row["id"]).revision_no == 1
    assert db_session.scalar(select(func.count()).select_from(LearningCandidateEvidence)) == 0


def test_memory_gate_idempotency_unique_revisions_and_archive(client, db_session):
    row = candidate(client)
    endpoint = f"{BASE}/learning-candidates/{row['id']}/promote-to-memory"
    assert client.post(endpoint, json=promotion()).status_code == 409
    assert (
        client.post(
            BASE + "/content-memory", json={**promotion(), "source_learning_candidate_id": row["id"]}
        ).status_code
        == 409
    )
    accepted_row = accepted(client, db_session)
    endpoint = f"{BASE}/learning-candidates/{accepted_row['id']}/promote-to-memory"
    stable_before = db_session.scalar(select(func.count()).select_from(ContentBrandRevision))
    result = client.post(endpoint, json=promotion())
    assert result.status_code == 201, result.text
    detail = result.json()
    mid = detail["id"]
    assert detail["current_revision"]["evidence_snapshot"]["candidate"] == accepted_row["validation_summary"]
    assert client.post(endpoint, json=promotion()).json() == detail
    assert (
        client.post(
            BASE + "/content-memory", json={**promotion(), "source_learning_candidate_id": accepted_row["id"]}
        ).json()
        == detail
    )
    assert client.post(endpoint, json=promotion(statement="changed")).status_code == 409
    assert client.post(endpoint, json=promotion(idempotency_key="another-key")).status_code == 409
    assert db_session.scalar(select(func.count()).select_from(ContentMemoryEntry)) == 1
    assert db_session.scalar(select(func.count()).select_from(ContentMemoryRevision)) == 1
    assert client.get(f"{BASE}/content-memory/{mid}", headers=OTHER).status_code == 404
    revision = {
        "expected_revision": 1,
        "statement": "refined",
        "source_learning_candidate_id": accepted_row["id"],
        "applicability": promotion()["applicability"],
        "limitations": promotion()["limitations"],
    }
    assert (
        client.post(
            f"{BASE}/content-memory/{mid}/revisions", json={**revision, "source_learning_candidate_id": row["id"]}
        ).status_code
        == 409
    )
    assert client.post(f"{BASE}/content-memory/{mid}/revisions", json=revision).status_code == 409
    matching = accepted(client, db_session, proposition="refined")
    revision["source_learning_candidate_id"] = matching["id"]
    assert client.post(f"{BASE}/content-memory/{mid}/revisions", json=revision).status_code == 201
    assert client.post(f"{BASE}/content-memory/{mid}/revisions", json=revision).status_code == 409
    history = client.get(f"{BASE}/content-memory/{mid}/revisions").json()
    assert history["total"] == 2
    assert history["items"][1] == detail["current_revision"]
    assert client.delete(f"{BASE}/content-memory/{mid}").status_code == 204
    assert (
        client.post(f"{BASE}/content-memory/{mid}/revisions", json={**revision, "expected_revision": 2}).status_code
        == 409
    )
    assert (
        client.delete(
            f"{BASE}/learning-candidates/{accepted_row['id']}?expected_revision={accepted_row['revision_no']}"
        ).status_code
        == 204
    )
    assert client.post(endpoint, json=promotion()).status_code == 409
    assert db_session.scalar(select(func.count()).select_from(ContentBrandRevision)) == stable_before


def test_typed_bounded_payloads_and_lists(client):
    assert (
        client.post(
            BASE + "/learning-candidates",
            json={"category": "topic", "title": "x", "proposition": "p", "status": "accepted"},
        ).status_code
        == 422
    )
    assert client.get(BASE + "/learning-candidates?limit=101").status_code == 422
    for path in ["learning-candidates", "content-memory", "learning/insights"]:
        response = client.get(BASE + "/" + path)
        assert response.status_code == 200, response.text
        assert response.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_insight_cannot_save_unbacked_claim_or_spoof_provider(client, db_session):
    assert client.post(BASE + "/learning/insights", json={"statement": "无证据最佳实践"}).status_code == 422
    pid, _ = published(client, db_session)
    payload = {"statement": "人工", "supporting_refs": [{"evidence_type": "published_content", "entity_id": pid}]}
    assert client.post(BASE + "/learning/insights", json={**payload, "provider_key": ""}).status_code == 422
    assert (
        client.post(
            BASE + "/learning/insights", json={**payload, "cohort": {"published_content_ids": [999]}}
        ).status_code
        == 404
    )
    assert (
        client.post(BASE + "/learning/insights", json={**payload, "scope": {"owner_user_id": 999}}).status_code == 404
    )


def test_validation_summary_cannot_impersonate_human_review(client, db_session):
    pid, _ = published(client, db_session)
    row = ready(client, evidence(client, candidate(client), pid))
    assert validate(client, row, validation_summary={"verified": True}).status_code == 422
    assert validate(client, row, validation_summary={"rationale": "   "}).status_code == 422
    assert validate(client, row, validation_summary={"rationale": "real", "insight_id": 999}).status_code == 404


def test_memory_scope_ancestors_exact_siblings_and_frozen_labels(client, db_session):
    brand = client.post(BASE + "/content-brands", json={"name": "原始品牌"}).json()["id"]
    persona = client.post(f"{BASE}/content-brands/{brand}/personas", json={"name": "角色"}).json()["id"]
    account = client.post(f"{BASE}/content-personas/{persona}/accounts", json={"name": "账号"}).json()["id"]
    sibling = client.post(f"{BASE}/content-personas/{persona}/accounts", json={"name": "同级账号"}).json()["id"]
    ids = []
    for kind, entity_id in [("owner", None), ("brand", brand), ("account", account), ("account", sibling)]:
        row = accepted(client, db_session)
        response = client.post(
            f"{BASE}/learning-candidates/{row['id']}/promote-to-memory",
            json=promotion(idempotency_key=f"scope-{row['id']}", scope_type=kind, scope_id=entity_id),
        )
        assert response.status_code == 201, response.text
        ids.append(response.json()["id"])
    result = client.get(f"{BASE}/content-memory?scope_type=account&scope_id={account}&include_ancestors=true").json()
    assert {item["id"] for item in result["items"]} == set(ids[:3])
    assert {item["id"]: item["scope_origin"]["relationship"] for item in result["items"]} == {
        ids[0]: "ancestor",
        ids[1]: "ancestor",
        ids[2]: "exact",
    }
    assert client.get(f"{BASE}/content-memory?scope_type=account&scope_id={account}").json()["total"] == 1
    assert client.get(f"{BASE}/content-memory?scope_type=account&scope_id={account}", headers=OTHER).status_code == 404
    detail = client.get(f"{BASE}/content-memory/{ids[1]}").json()
    assert detail["scope_origin"]["label"] == "原始品牌"
    client.patch(f"{BASE}/content-brands/{brand}", json={"name": "新品牌"})
    assert client.get(f"{BASE}/content-memory/{ids[1]}").json()["scope_origin"]["label"] == "原始品牌"
    row = accepted(client, db_session)
    assert (
        client.post(
            f"{BASE}/learning-candidates/{row['id']}/promote-to-memory",
            headers=OTHER,
            json=promotion(scope_type="brand", scope_id=brand),
        ).status_code
        == 404
    )
    client.delete(f"{BASE}/content-brands/{brand}")
    assert (
        client.post(
            f"{BASE}/learning-candidates/{row['id']}/promote-to-memory",
            json=promotion(idempotency_key="archived", scope_type="brand", scope_id=brand),
        ).status_code
        == 409
    )


def test_real_delivery_feedback_owner_boundary(client, db_session):
    from app.models import ContentAsset, DeliveryFeedback, DeliveryTarget

    client.get(BASE + "/learning-candidates")
    asset = ContentAsset(channel="wechat", title="legacy", final_body="body")
    db_session.add(asset)
    db_session.flush()
    target = DeliveryTarget(
        content_asset_id=asset.id,
        channel="wechat",
        content_form="article",
        account_ref="legacy",
        authorization_version="v1",
        approved_candidate_hash="h",
        authorized_by="other@studio.local",
    )
    db_session.add(target)
    db_session.flush()
    feedback = DeliveryFeedback(target_id=target.id, body="定性反馈")
    db_session.add(feedback)
    db_session.commit()
    ref = {"evidence_type": "delivery_feedback", "entity_id": feedback.id}
    assert (
        client.post(
            BASE + "/learning/insights", json={"statement": "不可引用别人的反馈", "supporting_refs": [ref]}
        ).status_code
        == 404
    )
    row = candidate(client)
    assert (
        client.post(
            f"{BASE}/learning-candidates/{row['id']}/evidence", json={**ref, "role": "support", "expected_revision": 1}
        ).status_code
        == 404
    )
    target.authorized_by = "admin@studio.local"
    db_session.commit()
    assert (
        client.post(
            BASE + "/learning/insights", json={"statement": "只作定性依据", "supporting_refs": [ref]}
        ).status_code
        == 201
    )


def test_qualitative_observation_does_not_claim_metric_coverage(client, db_session):
    _, oid = published(client, db_session)
    observation = db_session.get(PerformanceObservation, oid)
    observation.observation_kind = "feedback"
    observation.numeric_value = None
    observation.metric_key = None
    observation.metric_namespace = None
    observation.text_value = "读者觉得有用"
    db_session.commit()
    response = client.post(
        BASE + "/learning/insights",
        json={
            "statement": "定性样本",
            "supporting_refs": [{"evidence_type": "performance_observation", "entity_id": oid}],
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["coverage"]["observation_count"] == 1
    assert response.json()["coverage"]["metrics"] == "unknown"


def test_snapshot_bound(client, db_session):
    pid, _ = published(client, db_session)
    record = db_session.get(PublishedContentRecord, pid)
    record.content_snapshot_json = {"body": "x" * 200001}
    db_session.commit()
    row = candidate(client)
    response = client.post(
        f"{BASE}/learning-candidates/{row['id']}/evidence",
        json={"expected_revision": 1, "evidence_type": "published_content", "entity_id": pid, "role": "support"},
    )
    assert response.status_code == 422, response.text[:300]


def test_candidate_frozen_scope_labels(client, db_session):
    pid, _ = published(client, db_session)
    brand = client.post(BASE + "/content-brands", json={"name": "验证时的品牌"}).json()["id"]
    row = ready(client, evidence(client, candidate(client, scope={"brand_id": brand}), pid))
    result = validate(client, row)
    assert result.status_code == 200, result.text
    frozen = result.json()["validation_summary"]
    assert frozen["scope_origins"][0]["label"] == "验证时的品牌"
    client.patch(f"{BASE}/content-brands/{brand}", json={"name": "后来的名字"})
    assert client.get(f"{BASE}/learning-candidates/{row['id']}").json()["validation_summary"] == frozen


def test_learning_and_promotion_never_write_stable_domains(client, db_session):
    from sqlalchemy import event

    brand = client.post(BASE + "/content-brands", json={"name": "稳定品牌"}).json()["id"]
    saved = client.post(
        f"{BASE}/content-brands/{brand}/revisions",
        json={"expected_revision": 0, "profile": {"positioning": "人工设定"}},
    )
    assert saved.status_code == 201, saved.text
    stable_tables = {
        "content_brand",
        "content_brand_revision",
        "content_persona",
        "content_persona_revision",
        "content_account",
        "content_account_revision",
        "content_series",
        "content_series_revision",
        "persona_workflow_default",
        "account_workflow_default",
        "series_workflow_default",
        "workflow",
        "channel_template",
    }
    writes = []

    def capture(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            tokens = {word.strip('"') for word in statement.split()}
            if stable_tables & tokens:
                writes.append(statement)

    event.listen(db_session.bind, "before_cursor_execute", capture)
    try:
        row = accepted(client, db_session)
        result = client.post(
            f"{BASE}/learning-candidates/{row['id']}/promote-to-memory",
            json=promotion(scope_type="brand", scope_id=brand),
        )
        assert result.status_code == 201, result.text
        assert writes == []
        assert db_session.get(ContentBrandRevision, saved.json()["id"]).profile_json == {"positioning": "人工设定"}
    finally:
        event.remove(db_session.bind, "before_cursor_execute", capture)


@pytest.mark.parametrize("direct", [False, True])
def test_initial_memory_requires_frozen_claim_match(client, db_session, direct):
    row = accepted(client, db_session, proposition="WeChat 读者偏好短文")
    path = BASE + "/content-memory" if direct else f"{BASE}/learning-candidates/{row['id']}/promote-to-memory"
    extra = {"source_learning_candidate_id": row["id"]} if direct else {}
    unsupported = client.post(path, json={**promotion(statement="所有平台都适合长视频"), **extra})
    assert unsupported.status_code == 409, unsupported.text
    assert db_session.scalar(select(func.count()).select_from(ContentMemoryEntry)) == 0
    response = client.post(path, json={**promotion(statement="  WｅChat\t读者偏好短文\n"), **extra})
    assert response.status_code == 201, response.text


def test_revision_changed_claim_requires_matching_new_candidate(client, db_session):
    original = accepted(client, db_session, proposition="WeChat读者偏好短文")
    initial = client.post(
        f"{BASE}/learning-candidates/{original['id']}/promote-to-memory",
        json=promotion(statement=original["proposition"]),
    )
    assert initial.status_code == 201, initial.text
    mid = initial.json()["id"]
    revision = {
        "expected_revision": 1,
        "source_learning_candidate_id": original["id"],
        "statement": "所有平台都适合长视频",
        "applicability": promotion()["applicability"],
        "limitations": promotion()["limitations"],
    }
    denied = client.post(f"{BASE}/content-memory/{mid}/revisions", json=revision)
    assert denied.status_code == 409, denied.text
    assert db_session.scalar(select(func.count()).select_from(ContentMemoryRevision)) == 1
    matching = accepted(client, db_session, proposition="所有平台都适合长视频")
    allowed = client.post(
        f"{BASE}/content-memory/{mid}/revisions", json={**revision, "source_learning_candidate_id": matching["id"]}
    )
    assert allowed.status_code == 201, allowed.text


def test_memory_cannot_expand_frozen_scope_or_erase_validated_limits(client, db_session):
    row = accepted(
        client,
        db_session,
        scope={"channel": "wechat"},
        validation_summary={
            "rationale": "文章样本已核对",
            "applicability": {"content_form": "article"},
            "limitations": ["仅限中文读者"],
        },
    )
    endpoint = f"{BASE}/learning-candidates/{row['id']}/promote-to-memory"
    valid = promotion(
        applicability={"channel": "wechat", "content_form": "article"},
        limitations=["single_sample", "仅限中文读者", "手工附加限制"],
    )
    for bad in [
        dict(valid, applicability={"channel": "all", "content_form": "article"}),
        dict(valid, applicability={"channel": "wechat"}),
        dict(valid, limitations=["single_sample"]),
    ]:
        result = client.post(endpoint, json=bad)
        assert result.status_code == 409, result.text
    response = client.post(endpoint, json=valid)
    assert response.status_code == 201, response.text
    mid = response.json()["id"]
    revision = {
        "expected_revision": 1,
        "statement": row["proposition"],
        "source_learning_candidate_id": row["id"],
        "applicability": valid["applicability"],
        "limitations": valid["limitations"],
    }
    for bad in [
        dict(revision, applicability={"content_form": "article"}),
        dict(revision, limitations=["single_sample", "仅限中文读者"]),
    ]:
        assert client.post(f"{BASE}/content-memory/{mid}/revisions", json=bad).status_code == 409
    assert client.post(f"{BASE}/content-memory/{mid}/revisions", json=revision).status_code == 201


def test_identity_scoped_claim_cannot_promote_to_owner_or_sibling(client, db_session):
    brand = client.post(BASE + "/content-brands", json={"name": "品牌范围"}).json()["id"]
    other = client.post(BASE + "/content-brands", json={"name": "同所有者另一品牌"}).json()["id"]
    row = accepted(client, db_session, scope={"brand_id": brand})
    endpoint = f"{BASE}/learning-candidates/{row['id']}/promote-to-memory"
    assert client.post(endpoint, json=promotion()).status_code == 409
    assert client.post(endpoint, json=promotion(scope_type="brand", scope_id=other)).status_code == 409
    assert client.post(endpoint, json=promotion(scope_type="brand", scope_id=brand)).status_code == 201


def test_frozen_promotable_claim_matches_readonly_ui_and_memory_gate(client, db_session):
    pid, _ = published(client, db_session)
    insight = client.post(
        BASE + "/learning/insights",
        json={
            "statement": "来源分析",
            "supporting_refs": [{"evidence_type": "published_content", "entity_id": pid}],
            "limitations": ["来源仅限当前样本"],
        },
    ).json()
    row = ready(client, evidence(client, candidate(client, scope={"channel": "wechat"}), insight["id"], "insight"))
    response = validate(
        client,
        row,
        validation_summary={
            "rationale": "人工验证",
            "applicability": {"content_form": "article"},
            "limitations": ["必须人工复核", "来源仅限当前样本"],
        },
    )
    assert response.status_code == 200, response.text
    frozen = response.json()["validation_summary"]
    claim = frozen["promotable_claim"]
    assert claim == {
        "statement": row["proposition"],
        "applicability": {"channel": "wechat", "content_form": "article"},
        "limitations": ["single_sample", "必须人工复核", "来源仅限当前样本"],
    }
    assert db_session.get(LearningCandidate, row["id"]).validation_summary_json == frozen
    assert (
        client.get(f"{BASE}/learning-candidates/{row['id']}").json()["validation_summary"]["promotable_claim"] == claim
    )
    assert (
        client.get(BASE + "/learning-candidates").json()["items"][0]["validation_summary"]["promotable_claim"] == claim
    )
    promoted = client.post(
        f"{BASE}/learning-candidates/{row['id']}/promote-to-memory",
        json={"idempotency_key": "readonly-ui", "scope_type": "owner", "memory_type": "topic_learning", **claim},
    )
    assert promoted.status_code == 201, promoted.text
    memory = promoted.json()["current_revision"]
    assert {key: memory[key] for key in claim} == claim
    assert memory["evidence_snapshot"]["candidate"]["promotable_claim"] == claim
    revision = client.post(
        f"{BASE}/content-memory/{promoted.json()['id']}/revisions",
        json={"expected_revision": 1, "source_learning_candidate_id": row["id"], **claim},
    )
    assert revision.status_code == 201, revision.text


def test_conflicting_frozen_applicability_cannot_offer_promotable_claim(client, db_session):
    pid, _ = published(client, db_session)
    row = ready(client, evidence(client, candidate(client, scope={"channel": "wechat"}), pid))
    result = validate(
        client, row, validation_summary={"rationale": "冲突的条件", "applicability": {"channel": "youtube"}}
    )
    assert result.status_code == 409, result.text
    db_session.commit()
    saved = db_session.get(LearningCandidate, row["id"])
    assert saved.status == "ready_for_review"
    assert saved.revision_no == row["revision_no"]
    assert saved.validation_summary_json == {}


@pytest.mark.parametrize("trusted", [True, False])
def test_legacy_accepted_claim_read_projection_preserves_frozen_history(client, db_session, trusted):
    import copy

    from app.services import content_learning as service

    row = accepted(client, db_session, scope={"channel": "wechat"})
    stored = db_session.get(LearningCandidate, row["id"])
    legacy = copy.deepcopy(stored.validation_summary_json)
    legacy.pop("promotable_claim")
    legacy.pop("checksum")
    legacy["checksum"] = service.checksum(legacy) if trusted else "untrusted"
    stored.validation_summary_json = copy.deepcopy(legacy)
    db_session.commit()
    response = client.get(f"{BASE}/learning-candidates/{row['id']}")
    assert response.status_code == 200, response.text
    summary = response.json()["validation_summary"]
    assert summary["checksum"] == legacy["checksum"]
    if trusted:
        claim = summary["promotable_claim"]
        assert claim == {
            "statement": row["proposition"],
            "applicability": {"channel": "wechat"},
            "limitations": ["single_sample"],
        }
        assert response.json()["validation_summary_projection"] == {
            "derived_fields": ["promotable_claim"],
            "source_checksum": legacy["checksum"],
        }
        assert (
            client.get(BASE + "/learning-candidates").json()["items"][0]["validation_summary"]["promotable_claim"]
            == claim
        )
        promoted = client.post(
            f"{BASE}/learning-candidates/{row['id']}/promote-to-memory",
            json={
                "idempotency_key": "legacy-projection",
                "scope_type": "owner",
                "memory_type": "topic_learning",
                **claim,
            },
        )
        assert promoted.status_code == 201, promoted.text
        assert promoted.json()["current_revision"]["evidence_snapshot"]["candidate"] == legacy
        assert (
            client.post(
                f"{BASE}/learning-candidates/{row['id']}/promote-to-memory",
                json=promotion(statement="未经验证的新声明"),
            ).status_code
            == 409
        )
    else:
        assert "promotable_claim" not in summary
        assert (
            client.post(f"{BASE}/learning-candidates/{row['id']}/promote-to-memory", json=promotion()).status_code
            == 409
        )
    db_session.expire_all()
    assert db_session.get(LearningCandidate, row["id"]).validation_summary_json == legacy
    assert db_session.get(LearningCandidate, row["id"]).revision_no == row["revision_no"]


@pytest.mark.parametrize(
    "scope",
    [
        {"published_content_id": []},
        {"scope_type": {}},
        {"published_content_ids": [{}]},
        {"performance_observation_id": True},
        {"insight_id": 0},
        {"delivery_feedback_id": -1},
        {"account_ids": [False]},
        {"brand_id": "1"},
        {"scope_type": "owner", "scope_id": []},
        {"owner_user_id": True},
        {"evidence_type": "published_content", "entity_id": {}},
    ],
)
def test_recognized_context_ids_and_scope_types_reject_malformed_values(client, scope):
    result = client.post(
        BASE + "/learning-candidates",
        json={"category": "topic", "title": "类型边界", "proposition": "p", "scope": scope},
    )
    assert result.status_code == 422, result.text


@pytest.mark.parametrize(
    "path,payload",
    [
        (
            "/learning/insights",
            {"statement": "p", "supporting_refs": [{"evidence_type": "published_content", "entity_id": True}]},
        ),
        ("/learning/insights", {"statement": "p", "supersedes_id": True}),
        (
            "/learning-candidates",
            {"category": "topic", "title": "p", "proposition": "p", "created_from_insight_id": True},
        ),
        ("/content-memory", {**promotion(), "source_learning_candidate_id": True}),
    ],
)
def test_typed_reference_ids_do_not_coerce_boolean(client, path, payload):
    response = client.post(BASE + path, json=payload)
    assert response.status_code == 422, response.text


def test_recursive_insight_coverage_includes_contradictions_and_deduplicates(client, db_session):
    pid, oid = published(client, db_session)
    negative_pid, negative_oid = published(client, db_session)
    support = {"evidence_type": "performance_observation", "entity_id": oid}
    contradiction = {"evidence_type": "performance_observation", "entity_id": negative_oid}
    first = client.post(
        BASE + "/learning/insights",
        json={"statement": "内层结论", "supporting_refs": [support], "contradicting_refs": [contradiction]},
    ).json()
    second = client.post(
        BASE + "/learning/insights",
        json={"statement": "二层结论", "supporting_refs": [{"evidence_type": "insight", "entity_id": first["id"]}]},
    ).json()
    assert second["coverage"]["observation_count"] == 2
    assert second["coverage"]["published_content_count"] == 2
    assert second["coverage"]["metrics"] == "known"
    third = client.post(
        BASE + "/learning/insights",
        json={
            "statement": "重复引用归并",
            "supporting_refs": [support, {"evidence_type": "insight", "entity_id": second["id"]}],
            "contradicting_refs": [contradiction, {"evidence_type": "insight", "entity_id": first["id"]}],
        },
    ).json()
    assert third["coverage"]["observation_count"] == 2
    assert third["coverage"]["published_content_count"] == 2
    assert set(third["coverage"]["source_coverage"]) == {str(pid), str(negative_pid)}


def test_memory_writers_take_candidate_identity_memory_locks_in_same_order(client, db_session):
    from sqlalchemy import event

    brand = client.post(BASE + "/content-brands", json={"name": "顺序"}).json()["id"]
    row = accepted(client, db_session)
    statements = []

    def capture(_connection, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)

    event.listen(db_session.bind, "before_cursor_execute", capture)
    try:
        response = client.post(
            f"{BASE}/learning-candidates/{row['id']}/promote-to-memory",
            json=promotion(scope_type="brand", scope_id=brand),
        )
        assert response.status_code == 201, response.text
        mid = response.json()["id"]
        statements.clear()
        response = client.post(
            f"{BASE}/content-memory/{mid}/revisions",
            json={
                "expected_revision": 1,
                "statement": row["proposition"],
                "source_learning_candidate_id": row["id"],
                "applicability": promotion()["applicability"],
                "limitations": promotion()["limitations"],
            },
        )
        assert response.status_code == 201, response.text
        candidate_lock = next(
            index for index, statement in enumerate(statements) if statement.startswith("UPDATE learning_candidate")
        )
        identity_lock = next(index for index, statement in enumerate(statements) if "FROM content_brand" in statement)
        memory_lock = next(
            index for index, statement in enumerate(statements) if statement.startswith("UPDATE content_memory_entry")
        )
        assert candidate_lock < identity_lock < memory_lock
    finally:
        event.remove(db_session.bind, "before_cursor_execute", capture)


@pytest.mark.parametrize("driver_error", ["deadlock", "serialization", "unrelated"])
def test_memory_database_conflicts_rollback_only_known_errors(client, db_session, driver_error):
    from psycopg.errors import DeadlockDetected, SerializationFailure, UndefinedTable
    from sqlalchemy import event
    from sqlalchemy.exc import OperationalError

    row = accepted(client, db_session)
    error = {"deadlock": DeadlockDetected, "serialization": SerializationFailure, "unrelated": UndefinedTable}[
        driver_error
    ]("driver failure")

    def fail_revision(_connection, _cursor, statement, parameters, _context, _executemany):
        if statement.startswith("INSERT INTO content_memory_revision"):
            raise OperationalError(statement, parameters, error)

    event.listen(db_session.bind, "before_cursor_execute", fail_revision)
    try:
        if driver_error == "unrelated":
            with pytest.raises(OperationalError):
                client.post(f"{BASE}/learning-candidates/{row['id']}/promote-to-memory", json=promotion())
        else:
            result = client.post(f"{BASE}/learning-candidates/{row['id']}/promote-to-memory", json=promotion())
            assert result.status_code == 409, result.text
    finally:
        event.remove(db_session.bind, "before_cursor_execute", fail_revision)
    assert db_session.scalar(select(func.count()).select_from(ContentMemoryEntry)) == 0
    assert db_session.scalar(select(func.count()).select_from(ContentMemoryRevision)) == 0


def test_concurrent_promotion_and_candidate_cas(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from fastapi import HTTPException
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.db import Base as DatabaseBase
    from app.routers.learning import CandidateInput, PromotionInput
    from app.services import content_learning as service

    engine = create_engine(f"sqlite:///{tmp_path / 'learning-races.db'}", connect_args={"timeout": 10})
    DatabaseBase.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        user = User(email="race@studio.local", name="race", role="editor")
        db.add(user)
        db.commit()
        user_id = user.id
        record = PublishedContentRecord(owner_user_id=user.id, origin="external_import", channel="wechat")
        db.add(record)
        db.commit()
        candidate_row = service.create_candidate(
            db, user, CandidateInput(category="topic", title="race", proposition="p").model_dump()
        )
        cid = candidate_row["id"]
        service.add_evidence(
            db,
            user,
            cid,
            {
                "expected_revision": 1,
                "evidence_type": "published_content",
                "entity_id": record.id,
                "role": "support",
                "note": None,
            },
        )
        service.submit(db, user, cid, 2)
        service.decide(
            db,
            user,
            cid,
            {
                "expected_revision": 3,
                "decision": "accepted",
                "validation_method": "human",
                "validation_summary": {"rationale": "reviewed"},
            },
        )
        collecting_row = service.create_candidate(
            db, user, CandidateInput(category="topic", title="collect", proposition="p").model_dump()
        )
        collecting_id = collecting_row["id"]
    barrier = Barrier(2)

    def promote_same(_):
        with Session(engine, expire_on_commit=False) as db:
            user = db.get(User, user_id)
            barrier.wait()
            return service.promote(db, user, cid, PromotionInput(**promotion(statement="p")).model_dump())["id"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(promote_same, range(2)))
    assert results[0] == results[1]
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(ContentMemoryEntry)) == 1
        assert db.scalar(select(func.count()).select_from(ContentMemoryRevision)) == 1
    barrier = Barrier(2)

    def edit_same(index):
        with Session(engine, expire_on_commit=False) as db:
            user = db.get(User, user_id)
            barrier.wait()
            try:
                service.patch_candidate(db, user, collecting_id, {"expected_revision": 1, "proposition": str(index)})
                return 200
            except HTTPException as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(edit_same, range(2))) == [200, 409]
    engine.dispose()
