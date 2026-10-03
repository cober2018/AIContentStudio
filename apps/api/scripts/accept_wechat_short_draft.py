"""Opt-in real draft acceptance over an existing, approved isolated product database.

Default: rollback-only preflight, no HTTP. --execute is an external-effect action.
No database creation/migration, Candidate synthesis, gate override or legacy CLI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path


class AcceptanceRefused(ValueError):
    pass


@dataclass(frozen=True)
class ApprovedCredentials:
    appid: str
    secret: str = field(repr=False)


def credentials_from_documents(documents):
    pairs = []
    for document in documents:
        config = document.get("wechat") if isinstance(document, dict) else None
        appid = config.get("appid") if isinstance(config, dict) else None
        secret = config.get("secret") if isinstance(config, dict) else None
        if (not isinstance(appid, str) or not re.fullmatch(r"wx[0-9a-f]{16}", appid)
                or not isinstance(secret, str) or not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", secret)):
            raise AcceptanceRefused("acceptance_credentials_invalid")
        pairs.append((appid, secret))
    if len(pairs) != 2 or pairs[0] != pairs[1]:
        raise AcceptanceRefused("acceptance_credentials_invalid")
    return ApprovedCredentials(*pairs[0])


def load_approved_credentials():
    import yaml

    paths = (Path("/Users/mshengran/.wewrite/config.yaml"),
             Path("/Users/mshengran/Project/new_media/config/accounts.yaml"))
    try:
        documents = []
        for path in paths:
            with path.open("rb") as handle:
                raw = handle.read(512 * 1024 + 1)
            if len(raw) > 512 * 1024:
                raise AcceptanceRefused("acceptance_credentials_invalid")
            documents.append(yaml.safe_load(raw))
        return credentials_from_documents(documents)
    except (OSError, ValueError, yaml.YAMLError):
        # YAML and OS errors can include source text; never surface their messages.
        raise AcceptanceRefused("acceptance_credentials_invalid") from None


def private_database_path(value):
    path = Path(value)
    try:
        resolved = path.resolve(strict=True)
        roots = (Path("/private/tmp"), Path(tempfile.gettempdir()).resolve())
        if (not path.is_absolute() or path.is_symlink() or path.parent.is_symlink()
                or not resolved.is_file() or not any(resolved.is_relative_to(root) for root in roots)):
            raise AcceptanceRefused("acceptance_database_invalid")
        for item in (resolved, resolved.parent):
            info = item.stat()
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise AcceptanceRefused("acceptance_database_invalid")
        return resolved
    except (OSError, ValueError):
        raise AcceptanceRefused("acceptance_database_invalid") from None


@contextmanager
def credential_environment(account_id, version, credentials):
    values = {f"AICS_WECHAT_ACCOUNT_{account_id}_APPSECRET": credentials.secret,
              f"AICS_WECHAT_ACCOUNT_{account_id}_APPSECRET_VERSION": version}
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_acceptance(db, *, candidate_id, candidate_hash, account_id, actor, expires_at, execute=False, mode="short"):
    from fastapi import HTTPException
    from sqlalchemy import select

    from app.models import ContentAccount, ContentAsset, DeliveryAttempt, DeliveryTarget, SystemSetting, User
    from app.routers.delivery import GenericTargetIn
    from app.services import wechat_official, wechat_official_delivery
    from app.services.content_harness.publishers import bootstrap_publishers
    from app.services.wechat_official_render import validate_html_draft_render_bound, validate_short_draft_render_bound

    now = int(time.time())
    if (type(candidate_id) is not int or candidate_id < 1 or type(account_id) is not int or account_id < 1
            or not isinstance(candidate_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", candidate_hash)
            or not isinstance(actor, str) or not 1 <= len(actor) <= 255 or any(ord(c) < 32 for c in actor)
            or type(expires_at) is not int or not now < expires_at <= now + 900 or type(execute) is not bool or mode not in {"short", "html"}):
        raise AcceptanceRefused("acceptance_scope_invalid")
    try:
        asset = db.get(ContentAsset, candidate_id)
        user = db.scalar(select(User).where(User.email == actor))
        account = db.get(ContentAccount, account_id)
        if (asset is None or asset.candidate_hash != candidate_hash or user is None
                or user.is_active is not True or user.role != "admin" or account is None):
            raise AcceptanceRefused("acceptance_scope_invalid")
        existing = db.scalar(select(DeliveryTarget.id).where(
            DeliveryTarget.content_asset_id == candidate_id, DeliveryTarget.publisher_key == wechat_official.KEY))
        if existing is not None:
            raise AcceptanceRefused("acceptance_already_claimed")
        credentials = load_approved_credentials()
        if account.platform_account_id != credentials.appid or account.platform_channel != "wechat":
            raise AcceptanceRefused("acceptance_account_mismatch")
        setting = db.get(SystemSetting, f"wechat.official.account.{account_id}")
        version = (setting.value or {}).get("credential_version") if setting else None
        if not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", version):
            raise AcceptanceRefused("acceptance_connection_invalid")
        payload = GenericTargetIn(channel="wechat", content_form="article", action="auto_draft",
            content_account_id=account_id, account_ref=credentials.appid, authorization_version=f"{mode}-draft.v1")
        authority = {"account_id": account_id, "appid": credentials.appid, "candidate_id": candidate_id,
                     "candidate_hash": candidate_hash, "actor": actor, "expires_at": expires_at}
        if mode == "html":
            authority["mode"] = mode
        with credential_environment(account_id, version, credentials):
            bootstrap_publishers()
            transient = DeliveryTarget(content_asset_id=candidate_id, channel="wechat", content_form="article",
                action="auto_draft", content_account_id=account_id, account_ref=credentials.appid,
                approved_candidate_hash=candidate_hash, authorized_by=actor,
                publisher_key=wechat_official.KEY, publisher_version="1", authorization_version=f"{mode}-draft.v1")
            manifest, runtime = wechat_official_delivery.validate_target(db, transient, user,
                                                                        _short_draft_request=authority)
            bound = (validate_html_draft_render_bound if mode == "html" else validate_short_draft_render_bound)(manifest["official_render"])
            summary = {"schema": f"wechat.{mode}-draft.acceptance.v1", "candidate_id": candidate_id,
                "candidate_hash": candidate_hash, "account_id": account_id,
                "account_identity_hash": hashlib.sha256(credentials.appid.encode()).hexdigest(),
                "runtime_fingerprint": runtime.fingerprint, "render_hash": manifest["official_render"]["render_hash"],
                "body_utf8_bytes": bound, "general_contract_ready": wechat_official.remote_contract_ready(),
                "status": "preflight_only", "dispatched": False, "public_publication": False}
            db.rollback()
            if not execute:
                return summary
            target_id, attempt_id, claim = wechat_official_delivery.prepare_short_draft_experiment(
                db, asset, payload, user, authority=authority)
            summary.update(target_id=target_id, attempt_id=attempt_id, retry_allowed=False)
            try:
                result = wechat_official_delivery.execute_prepared(db, target_id, attempt_id, claim, user)
                attempt = db.get(DeliveryAttempt, attempt_id, populate_existing=True)
                metadata = attempt.response_metadata_json or {}
                completed = metadata.get("completed_steps", [])
                summary.update(status=result["status"], target_status=result["target_status"],
                    dispatched=True if completed else None,
                    completed_steps=[step for step in completed if step in {"token", "create", "read"} or re.fullmatch(r"asset_[0-9]{1,2}", step)],
                    remote_id_hash=hashlib.sha256(attempt.remote_id.encode()).hexdigest() if attempt.remote_id else None,
                    readback_hash=metadata.get("readback_hash"))
            except Exception:  # noqa: BLE001 - committed preparation or effects cannot be called a refusal.
                db.rollback()
                summary.update(status="unconfirmed", dispatched=None,
                    reason="acceptance_failed_inspect_existing_attempt_do_not_retry")
            return summary
    except HTTPException:
        db.rollback()
        raise AcceptanceRefused("acceptance_product_gate_refused") from None
    finally:
        db.rollback()


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise AcceptanceRefused("acceptance_arguments_invalid")


def parse_arguments(argv=None):
    parser = SafeArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--candidate-id", required=True, type=int)
    parser.add_argument("--candidate-hash", required=True)
    parser.add_argument("--account-id", required=True, type=int)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--expires-at", required=True, type=int)
    parser.add_argument("--execute", action="store_true", help="Explicit one-shot external draft effect; never public publish")
    parser.add_argument("--mode", choices=("short", "html"), default="short")
    return parser.parse_args(argv)


def main(argv=None):
    try:
        arguments = parse_arguments(argv)
        database = private_database_path(arguments.database)
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from sqlalchemy import URL, create_engine
        from sqlalchemy.orm import Session

        # mode=rw refuses accidental database creation if the checked file disappears.
        url = URL.create("sqlite", database=database.as_uri(), query={"mode": "rw", "uri": "true"})
        os.environ["DATABASE_URL"] = str(url)
        engine = create_engine(url, echo=False)
        try:
            with engine.connect() as connection:
                rows = connection.exec_driver_sql("PRAGMA database_list").all()
                actual = next((row[2] for row in rows if row[1] == "main"), None)
                if not actual or Path(actual).resolve() != database or private_database_path(database) != database:
                    raise AcceptanceRefused("acceptance_database_invalid")
            with Session(engine, expire_on_commit=False) as db:
                result = run_acceptance(db, **{key: getattr(arguments, key) for key in
                    ("candidate_id", "candidate_hash", "account_id", "actor", "expires_at", "execute", "mode")})
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] in {"preflight_only", "succeeded"} else 2
        finally:
            engine.dispose()
    except AcceptanceRefused as error:
        print(json.dumps({"status": "refused", "reason": str(error)}))
        return 2
    except Exception:  # noqa: BLE001 - CLI boundary must not print secret-bearing exception text.
        # Leave persisted Attempt authoritative, even if evidence projection fails after dispatch.
        print(json.dumps({"status": "unconfirmed", "reason": "acceptance_failed_inspect_existing_attempt_do_not_retry"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
