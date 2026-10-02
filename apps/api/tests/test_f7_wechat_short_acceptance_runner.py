"""Offline runner safeguards; none of these tests proves real WeChat acceptance."""

import json
import os
import sqlite3
import time

import pytest
from sqlalchemy import func, select
from test_f7_wechat_official_delivery import ready as ready_fixture
from test_f7_wechat_official_delivery import wire as wire_fixture

from app.models import ContentAsset, DeliveryAttempt, DeliveryTarget

ready = ready_fixture
wire = wire_fixture


def runner():
    from scripts import accept_wechat_short_draft

    return accept_wechat_short_draft


def test_credentials_require_identical_approved_sources():
    module = runner()
    doc = {"wechat": {"appid": "wx" + "a" * 16, "secret": "a" * 32}}
    credentials = module.credentials_from_documents([doc, doc])
    assert credentials.appid == doc["wechat"]["appid"]
    assert doc["wechat"]["secret"] not in repr(credentials)


@pytest.mark.parametrize("second", [None, {}, {"wechat": {}},
    {"wechat": {"appid": "wx" + "b" * 16, "secret": "a" * 32}},
    {"wechat": {"appid": "wx" + "a" * 16, "secret": "private-secret-sentinel"}},
    {"wechat": {"appid": True, "secret": "a" * 32}}])
def test_credentials_refuse_missing_malformed_or_mismatched(second):
    module = runner()
    with pytest.raises(module.AcceptanceRefused, match="acceptance_credentials_invalid") as error:
        module.credentials_from_documents([
            {"wechat": {"appid": "wx" + "a" * 16, "secret": "a" * 32}}, second])
    assert "private-secret-sentinel" not in str(error.value)


def test_private_existing_database_only(tmp_path):
    module = runner()
    tmp_path.chmod(0o700)
    database = tmp_path / "acceptance.sqlite"
    database.touch(mode=0o600)
    assert module.private_database_path(database) == database.resolve()
    database.chmod(0o644)
    with pytest.raises(module.AcceptanceRefused):
        module.private_database_path(database)
    database.chmod(0o600)
    linked = tmp_path / "linked.sqlite"
    linked.symlink_to(database)
    with pytest.raises(module.AcceptanceRefused):
        module.private_database_path(linked)
    with pytest.raises(module.AcceptanceRefused):
        module.private_database_path(tmp_path / "missing.sqlite")


def test_cli_defaults_to_no_dispatch():
    module = runner()
    arguments = module.parse_arguments([
        "--database", "/private/tmp/acceptance.sqlite", "--candidate-id", "1",
        "--candidate-hash", "a" * 64, "--account-id", "2", "--actor", "operator@example.test",
        "--expires-at", str(int(time.time()) + 120)])
    assert arguments.execute is False


def test_cli_existing_empty_database_does_not_create_schema(tmp_path, capsys, monkeypatch):
    module = runner()
    tmp_path.chmod(0o700)
    database = tmp_path / "isolated.sqlite"
    with sqlite3.connect(database):
        pass
    database.chmod(0o600)
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    code = module.main(["--database", str(database), "--candidate-id", "1",
        "--candidate-hash", "a" * 64, "--account-id", "1", "--actor", "operator@example.test",
        "--expires-at", str(int(time.time()) + 120)])
    assert code == 2
    output = capsys.readouterr()
    assert not output.err and "Traceback" not in output.out
    assert str(database) not in output.out
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []


def test_cli_uri_fragment_never_opens_an_unvalidated_file(tmp_path, capsys, monkeypatch):
    module = runner()
    tmp_path.chmod(0o700)
    database = tmp_path / "actual.sqlite#validated-file"
    with sqlite3.connect(database):
        pass
    database.chmod(0o600)
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    assert module.main(["--database", str(database), "--candidate-id", "1",
        "--candidate-hash", "a" * 64, "--account-id", "1", "--actor", "operator@example.test",
        "--expires-at", str(int(time.time()) + 120)]) == 2
    assert not (tmp_path / "actual.sqlite").exists()
    assert "Traceback" not in capsys.readouterr().err


def test_cli_parser_errors_do_not_echo_raw_input(capsys):
    module = runner()
    try:
        code = module.main(["--candidate-id", "private-argument-sentinel", "--unknown", "other-private-sentinel"])
    except SystemExit as error:
        code = error.code
    assert code == 2
    captured = capsys.readouterr()
    assert "private-argument-sentinel" not in captured.out + captured.err
    assert "other-private-sentinel" not in captured.out + captured.err
    assert not captured.err


@pytest.mark.parametrize("ready", ["short"], indirect=True)
@pytest.mark.parametrize("partial", [False, True])
def test_post_prepare_failure_keeps_ids_and_no_retry(db_session, ready, wire, monkeypatch, partial):
    from fastapi import HTTPException

    from app.services import wechat_official_delivery

    module = runner()
    monkeypatch.setattr(module, "load_approved_credentials", lambda: module.ApprovedCredentials(
        ready["account"].platform_account_id, "a" * 32))
    original = wechat_official_delivery.execute_prepared

    def fail(db, target_id, attempt_id, claim, user):
        if partial:
            original(db, target_id, attempt_id, claim, user)
        raise HTTPException(409, "private-post-prepare-sentinel")

    monkeypatch.setattr(wechat_official_delivery, "execute_prepared", fail)
    result = module.run_acceptance(db_session, **inputs(ready), execute=True)
    assert result["status"] == "unconfirmed"
    assert result["dispatched"] is None and result["retry_allowed"] is False
    assert result["target_id"] > 0 and result["attempt_id"] > 0
    attempt = db_session.get(DeliveryAttempt, result["attempt_id"])
    assert attempt is not None
    if partial:
        assert attempt.remote_id == "exact-draft-id"
    assert "private-post-prepare-sentinel" not in json.dumps(result)
    with pytest.raises(module.AcceptanceRefused, match="acceptance_already_claimed"):
        module.run_acceptance(db_session, **inputs(ready), execute=True)


def inputs(ready):
    return {"candidate_id": ready["candidate"]["id"],
            "candidate_hash": ready["candidate"]["candidate_hash"],
            "account_id": ready["account"].id, "actor": ready["owner"].email,
            "expires_at": int(time.time()) + 120}


@pytest.mark.parametrize("ready", ["short"], indirect=True)
def test_preflight_no_transport_no_durable_target(db_session, ready, wire, monkeypatch):
    module = runner()
    monkeypatch.setattr(module, "load_approved_credentials", lambda: module.ApprovedCredentials(
        ready["account"].platform_account_id, "a" * 32))
    result = module.run_acceptance(db_session, **inputs(ready))
    assert result["status"] == "preflight_only" and result["dispatched"] is False
    assert result["body_utf8_bytes"] < 2048
    assert not wire[0]
    assert db_session.scalar(select(func.count()).select_from(DeliveryTarget)) == 0
    assert db_session.scalar(select(func.count()).select_from(DeliveryAttempt)) == 0
    assert "a" * 32 not in json.dumps(result)


@pytest.mark.parametrize("ready", ["short"], indirect=True)
@pytest.mark.parametrize("field,value", [("candidate_hash", "b" * 64), ("account_id", 9999),
    ("actor", "foreign@example.test"), ("expires_at", 0), ("expires_at", 99999999999)])
def test_bad_scope_no_transport_no_write(db_session, ready, wire, monkeypatch, field, value):
    module = runner()
    monkeypatch.setattr(module, "load_approved_credentials", lambda: module.ApprovedCredentials(
        ready["account"].platform_account_id, "a" * 32))
    request = {**inputs(ready), field: value}
    with pytest.raises(module.AcceptanceRefused):
        module.run_acceptance(db_session, **request, execute=True)
    assert not wire[0]
    assert db_session.scalar(select(func.count()).select_from(DeliveryAttempt)) == 0
    assert db_session.scalar(select(func.count()).select_from(DeliveryTarget)) == 0


@pytest.mark.parametrize("ready", ["short"], indirect=True)
def test_explicit_execute_uses_product_attempt_and_cannot_repeat(db_session, ready, wire, monkeypatch):
    module = runner()
    monkeypatch.setattr(module, "load_approved_credentials", lambda: module.ApprovedCredentials(
        ready["account"].platform_account_id, "a" * 32))
    request = inputs(ready)
    result = module.run_acceptance(db_session, **request, execute=True)
    assert result["status"] == "succeeded"
    assert result["target_status"] == "awaiting_manual_receipt"
    assert result["completed_steps"] == ["token", "asset_0", "create"]
    assert result["general_contract_ready"] is False
    assert result["public_publication"] is False
    assert wire[0] == ["token", "cover", "create"]
    frozen = db_session.get(ContentAsset, request["candidate_id"])
    assert frozen.candidate_hash == request["candidate_hash"]
    assert "secret-token" not in json.dumps(result)
    with pytest.raises(module.AcceptanceRefused, match="acceptance_already_claimed"):
        module.run_acceptance(db_session, **request, execute=True)
    assert len(wire[0]) == 3
    assert db_session.scalar(select(func.count()).select_from(DeliveryAttempt)) == 1


@pytest.mark.parametrize("ready", ["short"], indirect=True)
def test_unknown_create_preserves_partial_evidence_and_never_retries(db_session, ready, wire, monkeypatch):
    module = runner()
    monkeypatch.setattr(module, "load_approved_credentials", lambda: module.ApprovedCredentials(
        ready["account"].platform_account_id, "a" * 32))

    def uncertain_create(self, token, article):
        wire[0].append("create")
        raise OSError("private-create-sentinel")

    monkeypatch.setattr(wire[1], "create_draft", uncertain_create)
    request = inputs(ready)
    result = module.run_acceptance(db_session, **request, execute=True)
    assert result["status"] == "unknown" and result["target_status"] == "reconciliation_needed"
    assert result["retry_allowed"] is False
    assert result["completed_steps"] == ["token", "asset_0"]
    assert result["remote_id_hash"] is None and result["readback_hash"] is None
    attempt = db_session.get(DeliveryAttempt, result["attempt_id"])
    assert len(attempt.response_metadata_json["resource_mapping"]) == 1
    assert "private-create-sentinel" not in json.dumps(result)
    with pytest.raises(module.AcceptanceRefused, match="acceptance_already_claimed"):
        module.run_acceptance(db_session, **request, execute=True)
    assert wire[0] == ["token", "cover", "create"]


def test_credential_environment_restores_values(monkeypatch):
    module = runner()
    key = "AICS_WECHAT_ACCOUNT_7_APPSECRET"
    monkeypatch.setenv(key, "existing-private-value")
    monkeypatch.delenv(key + "_VERSION", raising=False)
    with module.credential_environment(7, "v1", module.ApprovedCredentials("wx" + "a" * 16, "a" * 32)):
        assert os.environ[key] == "a" * 32
        assert os.environ[key + "_VERSION"] == "v1"
    assert os.environ[key] == "existing-private-value"
    assert key + "_VERSION" not in os.environ
