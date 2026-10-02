"""Opt-in real PG transactions; only outward transport is an isolated fixture."""

import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from test_f7_wechat_official_delivery import _authorize
from test_f7_wechat_official_delivery import (
    ready as ready,  # noqa: PLC0414 -- pytest must discover the imported fixture.
)

from app.db import Base
from app.models import (
    CapabilityRegistration,
    ChannelTemplateVersion,
    ChannelVariantRevision,
    ContentAsset,
    DeliveryAttempt,
    User,
)
from app.routers.delivery import GenericTargetIn
from app.services import capability_integrations, delivery, wechat_official_delivery, wechat_official_transport


def _isolated_url(value):
    parsed = make_url(value)
    assert parsed.drivername == "postgresql+psycopg" and not parsed.query
    assert parsed.host == "127.0.0.1" and parsed.port == 15439 and parsed.database == "aics_account_test"
    return parsed


@pytest.mark.parametrize("suffix", ["?host=elsewhere", "?port=5432", "?dbname=other", "?service=other", "?options=-csearch_path=public"])
def test_pg_fixture_rejects_connection_overrides(suffix):
    with pytest.raises(AssertionError):
        _isolated_url("postgresql+psycopg://postgres@127.0.0.1:15439/aics_account_test" + suffix)


@pytest.mark.parametrize("value", ["postgresql://postgres@127.0.0.1:15439/aics_account_test", "sqlite:///aics_account_test"])
def test_pg_fixture_rejects_other_drivers(value):
    with pytest.raises(AssertionError):
        _isolated_url(value)


@pytest.fixture
def pg_engine():
    value = os.getenv("AICS_ACCOUNT_TEST_DATABASE_URL")
    if not value:
        pytest.skip("opt-in isolated PostgreSQL delivery gate")
    parsed = _isolated_url(value)
    schema = "official_delivery_gate_" + uuid.uuid4().hex
    admin = create_engine(parsed, connect_args={"connect_timeout": 5, "options": "-cstatement_timeout=15000 -clock_timeout=10000"})
    with admin.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA {schema}"))
    scoped = parsed.set(query={**parsed.query, "options": f"-csearch_path={schema} -cstatement_timeout=15000 -clock_timeout=10000"})
    engine = create_engine(scoped, connect_args={"connect_timeout": 5})
    try:
        Base.metadata.create_all(engine)
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        admin.dispose()


@pytest.fixture
def db_session(pg_engine):
    with Session(pg_engine, autoflush=False, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def pg_wire(monkeypatch):
    calls, article = [], {}
    lock = threading.Lock()

    class Transport:
        def __init__(self, **kwargs):
            pass

        def token(self, runtime):
            with lock:
                calls.append("token")
            return "isolated-pg-token"

        def upload_cover(self, token, data, mime, filename):
            assert token == "isolated-pg-token" and mime == "image/png"
            assert filename == "原始封面.png"
            with lock:
                calls.append("cover")
            return "pg-cover"

        def create_draft(self, token, value):
            with lock:
                calls.append("create")
                article.update(value)
            return "pg-draft"

        def read_draft(self, token, remote_id):
            assert remote_id == "pg-draft"
            with lock:
                calls.append("read")
                return dict(article)

    monkeypatch.setattr(wechat_official_transport, "OfficialTransport", Transport)
    return calls


@pytest.mark.parametrize("ready", ["short"], indirect=True)
@pytest.mark.parametrize("operation", ["prepare_experiment", "execute_prepared"])
def test_pg_short_experiment_one_durable_claim(client, db_session, pg_engine, ready, pg_wire, operation):
    owner_id, asset_id = ready["owner"].id, ready["candidate"]["id"]
    authority = {"account_id": ready["account"].id, "appid": ready["account"].platform_account_id,
                 "candidate_id": asset_id, "candidate_hash": ready["candidate"]["candidate_hash"],
                 "actor": ready["owner"].email, "expires_at": int(time.time()) + 600}
    prepared = None
    if operation == "execute_prepared":
        prepared = wechat_official_delivery.prepare_short_draft_experiment(db_session,
            db_session.get(ContentAsset, asset_id), GenericTargetIn(**ready["auth"]), ready["owner"], authority=authority)
    db_session.commit()
    barrier = threading.Barrier(2)

    def worker():
        with Session(pg_engine, expire_on_commit=False) as session:
            user = session.get(User, owner_id)
            barrier.wait(timeout=10)
            try:
                if operation == "prepare_experiment":
                    wechat_official_delivery.prepare_short_draft_experiment(session,
                        session.get(ContentAsset, asset_id), GenericTargetIn(**ready["auth"]), user, authority=authority)
                else:
                    target_id, attempt_id, claim = prepared
                    result = wechat_official_delivery.execute_prepared(session, target_id, attempt_id, claim, user)
                    assert result["status"] == "succeeded"
                return "winner"
            except HTTPException as exc:
                assert exc.status_code == 409
                return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        assert sorted(future.result(timeout=25) for future in futures) == ["blocked", "winner"]
    with Session(pg_engine) as session:
        attempts = session.scalars(select(DeliveryAttempt)).all()
        assert len(attempts) == 1 and attempts[0].attempt_no == 1
        assert attempts[0].status == ("prepared" if operation == "prepare_experiment" else "succeeded")
    assert pg_wire == ([] if operation == "prepare_experiment" else ["token", "cover", "create"])


@pytest.mark.parametrize("operation", ["prepare", "execute"])
def test_pg_two_workers_have_one_dispatch_claim(client, db_session, pg_engine, ready, pg_wire, operation):
    target = _authorize(client, ready)
    owner_id = ready["owner"].id
    db_session.commit()
    barrier = threading.Barrier(2)

    def worker():
        with Session(pg_engine, expire_on_commit=False) as session:
            user = session.get(User, owner_id)
            barrier.wait(timeout=10)
            try:
                if operation == "prepare":
                    wechat_official_delivery.prepare(session, target, user)
                else:
                    assert wechat_official_delivery.execute(session, target, user)["status"] == "succeeded"
                return "winner"
            except HTTPException as exc:
                assert exc.status_code == 409
                return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        assert sorted(future.result(timeout=25) for future in futures) == ["blocked", "winner"]
    with Session(pg_engine) as session:
        attempts = session.scalars(select(DeliveryAttempt)).all()
        assert len(attempts) == 1 and attempts[0].attempt_no == 1
        assert attempts[0].status == ("prepared" if operation == "prepare" else "succeeded")
    assert pg_wire == ([] if operation == "prepare" else ["token", "cover", "create"])


def test_pg_authorization_and_execute_do_not_reverse_locks(client, db_session, pg_engine, ready, pg_wire):
    target = _authorize(client, ready)
    owner_id, asset_id = ready["owner"].id, ready["candidate"]["id"]
    db_session.commit()
    barrier = threading.Barrier(2)

    def worker(authorize):
        with Session(pg_engine, expire_on_commit=False) as session:
            user = session.get(User, owner_id)
            barrier.wait(timeout=10)
            if authorize:
                result = delivery.authorize_target(session, session.get(ContentAsset, asset_id), GenericTargetIn(**ready["auth"]), user)
                return result.id
            assert wechat_official_delivery.execute(session, target, user)["status"] == "succeeded"
            return target

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker, item) for item in [False, True]]
        assert [future.result(timeout=25) for future in futures] == [target, target]
    assert pg_wire == ["token", "cover", "create"]


def test_pg_cross_project_profile_lock_precedes_registration(client, db_session, pg_engine, ready, pg_wire, tmp_path, monkeypatch):
    second = globals()["ready"].__wrapped__(client, db_session, tmp_path, monkeypatch,
        SimpleNamespace(platform_account_id="wx" + "b" * 16, fact_pack_name="跨项目独立事实边界"))
    target = _authorize(client, second)
    asset_a = db_session.get(ContentAsset, ready["candidate"]["id"])
    asset_b = db_session.get(ContentAsset, second["candidate"]["id"])
    assert asset_a.project_id != asset_b.project_id
    profile_a = db_session.get(ChannelVariantRevision, asset_a.channel_variant_revision_id).profile_template_version_id
    profile_b = db_session.get(ChannelVariantRevision, asset_b.channel_variant_revision_id).profile_template_version_id
    assert profile_a == profile_b
    assert ready["registration"].id == second["registration"].id
    owner_id, asset_id, registration_id = ready["owner"].id, asset_a.id, ready["registration"].id
    db_session.commit()
    worker_started, worker_pid = threading.Event(), []

    def execute():
        with Session(pg_engine, expire_on_commit=False) as executor:
            user = executor.get(User, owner_id)
            worker_pid.append(executor.scalar(text("SELECT pg_backend_pid()")))
            worker_started.set()
            return wechat_official_delivery.execute(executor, target, user)

    with Session(pg_engine) as authorizer, ThreadPoolExecutor(max_workers=1) as pool:
        authorizer_pid = authorizer.scalar(text("SELECT pg_backend_pid()"))
        authorizer.get(ChannelTemplateVersion, profile_a, with_for_update=True)
        future = pool.submit(execute)
        try:
            assert worker_started.wait(timeout=5)
            _assert_blocked_by(pg_engine, worker_pid[0], authorizer_pid)
            assert pg_wire == []
            with Session(pg_engine) as observer:
                waiting_query = observer.scalar(text("SELECT query FROM pg_stat_activity WHERE pid=:pid"), {"pid": worker_pid[0]})
                assert "channel_template_version" in waiting_query.lower()
                # A reversed executor would hold registration while waiting for the shared profile.
                observer.get(CapabilityRegistration, registration_id, with_for_update={"nowait": True})
            result = delivery.authorize_target(authorizer, authorizer.get(ContentAsset, asset_id),
                GenericTargetIn(**ready["auth"]), authorizer.get(User, owner_id))
            assert result.content_asset_id == asset_id
        finally:
            authorizer.commit()
        assert future.result(timeout=25)["status"] == "succeeded"
    assert pg_wire == ["token", "cover", "create"]
    with Session(pg_engine) as session:
        attempts = session.scalars(select(DeliveryAttempt)).all()
        assert len(attempts) == 1 and attempts[0].target_id == target and attempts[0].status == "succeeded"


def test_pg_revocation_committed_before_step_prevents_dispatch(client, db_session, pg_engine, ready, pg_wire):
    target = _authorize(client, ready)
    attempt_id, claim = wechat_official_delivery.prepare(db_session, target, ready["owner"])
    owner_id, registration_id = ready["owner"].id, ready["registration"].id
    with Session(pg_engine) as revoker:
        registration = revoker.get(CapabilityRegistration, registration_id)
        capability_integrations.append_verification(revoker, registration, scope_kind="publisher_action",
            scope=ready["scope"], result="revoked", actor=ready["owner"].email, evidence={"kind": "revocation"})
        revoker.commit()
    with Session(pg_engine) as executor:
        user = executor.get(User, owner_id)
        with pytest.raises(HTTPException, match="official_publisher_unverified"):
            wechat_official_delivery._step(executor, target, attempt_id, claim, user, "token",
                lambda *args: wechat_official_transport.OfficialTransport().token(None), lambda *args: None)
    assert pg_wire == []
    with Session(pg_engine) as session:
        attempt = session.get(DeliveryAttempt, attempt_id)
        assert attempt.status == "prepared" and attempt.response_metadata_json["in_flight"] is None


def _assert_blocked_by(engine, waiting_pid, holding_pid):
    deadline = time.monotonic() + 5
    with engine.connect() as observer:
        while time.monotonic() < deadline:
            blockers = observer.scalar(text("SELECT pg_blocking_pids(:pid)"), {"pid": waiting_pid})
            if holding_pid in blockers:
                return
    pytest.fail("native PostgreSQL blocking relationship was not observed")


def test_pg_revocation_lock_winner_blocks_waiting_step(client, db_session, pg_engine, ready, pg_wire):
    target = _authorize(client, ready)
    attempt_id, claim = wechat_official_delivery.prepare(db_session, target, ready["owner"])
    owner_id, registration_id = ready["owner"].id, ready["registration"].id
    worker_started = threading.Event()
    worker_pid = []

    def worker():
        with Session(pg_engine) as executor:
            user = executor.get(User, owner_id)
            worker_pid.append(executor.scalar(text("SELECT pg_backend_pid()")))
            worker_started.set()
            with pytest.raises(HTTPException, match="official_publisher_unverified"):
                wechat_official_delivery._step(executor, target, attempt_id, claim, user, "token",
                    lambda *args: wechat_official_transport.OfficialTransport().token(None), lambda *args: None)

    with Session(pg_engine) as revoker, ThreadPoolExecutor(max_workers=1) as pool:
        holding_pid = revoker.scalar(text("SELECT pg_backend_pid()"))
        capability_integrations.append_verification(revoker, revoker.get(CapabilityRegistration, registration_id),
            scope_kind="publisher_action", scope=ready["scope"], result="revoked",
            actor=ready["owner"].email, evidence={"kind": "revocation"})
        future = pool.submit(worker)
        try:
            assert worker_started.wait(timeout=5)
            _assert_blocked_by(pg_engine, worker_pid[0], holding_pid)
        finally:
            revoker.commit()
        future.result(timeout=20)
    assert pg_wire == []


def test_pg_bounded_step_holds_registration_until_effect_finishes(client, db_session, pg_engine, ready):
    target = _authorize(client, ready)
    attempt_id, claim = wechat_official_delivery.prepare(db_session, target, ready["owner"])
    owner_id, registration_id = ready["owner"].id, ready["registration"].id
    effect_entered, release_effect, revoker_started = (threading.Event() for _ in range(3))
    execution_pid, revocation_pid, effects = [], [], []

    def execute_step():
        with Session(pg_engine) as executor:
            user = executor.get(User, owner_id)
            execution_pid.append(executor.scalar(text("SELECT pg_backend_pid()")))

            def effect(*args):
                effects.append("token")
                effect_entered.set()
                assert release_effect.wait(timeout=10)
                return "fixture-token"

            wechat_official_delivery._step(executor, target, attempt_id, claim, user, "token", effect, lambda *args: None)

    def revoke():
        with Session(pg_engine) as revoker:
            revocation_pid.append(revoker.scalar(text("SELECT pg_backend_pid()")))
            revoker_started.set()
            capability_integrations.append_verification(revoker, revoker.get(CapabilityRegistration, registration_id),
                scope_kind="publisher_action", scope=ready["scope"], result="revoked",
                actor=ready["owner"].email, evidence={"kind": "revocation"})
            revoker.commit()

    with ThreadPoolExecutor(max_workers=2) as pool:
        executing = pool.submit(execute_step)
        try:
            assert effect_entered.wait(timeout=5)
            revoking = pool.submit(revoke)
            assert revoker_started.wait(timeout=5)
            _assert_blocked_by(pg_engine, revocation_pid[0], execution_pid[0])
        finally:
            release_effect.set()
        executing.result(timeout=20)
        revoking.result(timeout=20)
    with Session(pg_engine) as executor, pytest.raises(HTTPException, match="official_publisher_unverified"):
        wechat_official_delivery._step(executor, target, attempt_id, claim, executor.get(User, owner_id), "cover",
            lambda *args: effects.append("cover"), lambda *args: None)
    assert effects == ["token"]
    with Session(pg_engine) as session:
        attempt = session.get(DeliveryAttempt, attempt_id)
        assert attempt.status == "running"
        assert attempt.response_metadata_json["completed_steps"] == ["token"]
        assert attempt.response_metadata_json["in_flight"] is None
