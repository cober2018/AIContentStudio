"""Account-bound official Publisher identity; remote effects remain contract gated."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ContentAccount, ContentBrand, ContentPersona, SystemSetting
from .content_harness.contracts import PublisherCapability, PublisherResult

KEY = "publisher.wechat.official"
VERSION = "1"
CONTRACT_VERSION = "wechat.official.article.v1-unresolved-body-limits"


def remote_contract_ready() -> bool:
    return False


def _short_draft_scope(scope: object) -> dict:
    fields = {"account_id", "appid", "candidate_id", "candidate_hash", "target_id", "attempt_id",
              "runtime_fingerprint", "actor", "action", "channel", "content_form"}
    if (not isinstance(scope, dict) or set(scope) != fields
            or any(type(scope[key]) is not int or scope[key] <= 0
                   for key in ("account_id", "candidate_id", "target_id", "attempt_id"))
            or (scope["channel"], scope["content_form"], scope["action"]) != ("wechat", "article", "auto_draft")
            or not isinstance(scope["appid"], str) or not re.fullmatch(r"wx[0-9a-f]{16}", scope["appid"])
            or any(not isinstance(scope[key], str) or not re.fullmatch(r"[0-9a-f]{64}", scope[key])
                   for key in ("candidate_hash", "runtime_fingerprint"))
            or not isinstance(scope["actor"], str) or not 1 <= len(scope["actor"]) <= 255
            or any(ord(char) < 32 for char in scope["actor"])):
        raise ValueError("official_experiment_authority_invalid")
    return dict(scope)


def _short_draft_signature(payload: dict) -> str:
    key = os.getenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", key):
        raise ValueError("official_experiment_authority_invalid")
    # Purpose separation prevents an experiment receipt from being treated as credential identity.
    purpose = b"aics.wechat.html-draft.authority.v1\0" if payload.get("schema") == "wechat.html-draft.authority.v1" else b"aics.wechat.short-draft.authority.v1\0"
    message = purpose + json.dumps(
        payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()
    return hmac.new(key.encode(), message, hashlib.sha256).hexdigest()


def sign_short_draft_authority(scope: dict, *, expires_at: int, now: int | None = None) -> dict:
    """Internal signing primitive; callers must establish owned approval and explicit experiment authority."""
    issued = int(time.time()) if now is None else now
    if type(issued) is not int or type(expires_at) is not int or not issued < expires_at <= issued + 900:
        raise ValueError("official_experiment_authority_invalid")
    payload = {"schema": "wechat.short-draft.authority.v1", "scope": _short_draft_scope(scope),
               "issued_at": issued, "expires_at": expires_at}
    return {**payload, "signature": _short_draft_signature(payload)}


def check_short_draft_authority(authority: object, scope: dict, *, now: int | None = None) -> bool:
    return check_draft_authority(authority, scope, now=now, schema="wechat.short-draft.authority.v1")


def sign_html_draft_authority(scope: dict, *, expires_at: int, now: int | None = None) -> dict:
    signed = sign_short_draft_authority(scope, expires_at=expires_at, now=now)
    payload = {key: value for key, value in signed.items() if key != "signature"}
    payload["schema"] = "wechat.html-draft.authority.v1"
    return {**payload, "signature": _short_draft_signature(payload)}


def check_draft_authority(authority: object, scope: dict, *, now: int | None = None, schema: str | None = None) -> bool:
    current = int(time.time()) if now is None else now
    try:
        if (not isinstance(authority, dict)
                or set(authority) != {"schema", "scope", "issued_at", "expires_at", "signature"}
                or authority["schema"] not in ({schema} if schema else {"wechat.short-draft.authority.v1", "wechat.html-draft.authority.v1"})
                or type(current) is not int or type(authority["issued_at"]) is not int
                or type(authority["expires_at"]) is not int
                or not authority["issued_at"] <= current < authority["expires_at"] <= authority["issued_at"] + 900
                or _short_draft_scope(authority["scope"]) != _short_draft_scope(scope)
                or not isinstance(authority["signature"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", authority["signature"])):
            return False
        payload = {key: value for key, value in authority.items() if key != "signature"}
        return hmac.compare_digest(authority["signature"], _short_draft_signature(payload))
    except (ValueError, TypeError, KeyError, RecursionError):
        return False


def implementation_fingerprint() -> str:
    digest = hashlib.sha256(CONTRACT_VERSION.encode())
    for filename in (Path(__file__), Path(__file__).with_name("capability_integrations.py"),
                     Path(__file__).with_name("wechat_official_transport.py"),
                     Path(__file__).with_name("wechat_official_delivery.py"),
                     Path(__file__).with_name("wechat_official_render.py")):
        digest.update(filename.name.encode())
        digest.update(filename.read_bytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class AccountRuntime:
    account_id: int
    appid: str
    fingerprint: str
    secret: str = field(repr=False)


def resolve_runtime(db: Session, account_id: int) -> AccountRuntime:
    account = db.get(ContentAccount, account_id, populate_existing=True)
    persona = db.get(ContentPersona, account.persona_id, populate_existing=True) if account else None
    brand = db.get(ContentBrand, persona.brand_id, populate_existing=True) if persona and persona.brand_id else None
    if (account is None or account.status != "active" or persona is None or persona.status != "active"
            or (persona.brand_id and (brand is None or brand.status != "active"))):
        raise HTTPException(409, "official_account_unavailable")
    if account.platform_channel != "wechat" or not re.fullmatch(r"wx[0-9a-f]{16}", account.platform_account_id or ""):
        raise HTTPException(409, "official_platform_binding_required")
    setting = db.get(SystemSetting, f"wechat.official.account.{account_id}", populate_existing=True)
    config = setting.value if setting else {}
    ref = f"AICS_WECHAT_ACCOUNT_{account_id}_APPSECRET"
    if (not isinstance(config, dict) or config.get("enabled") is not True
            or config.get("credential_ref") != ref or config.get("platform_account_id") != account.platform_account_id
            or type(config.get("revision")) is not int or config["revision"] < 1
            or not isinstance(config.get("credential_version"), str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", config["credential_version"])):
        raise HTTPException(409, "official_connection_unavailable")
    secret = os.getenv(ref, "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", secret) or os.getenv(ref + "_VERSION") != config["credential_version"]:
        raise HTTPException(409, "official_credentials_unavailable")
    identity_key = os.getenv("AICS_WECHAT_RUNTIME_IDENTITY_KEY", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", identity_key):
        raise HTTPException(409, "official_identity_key_unavailable")
    identity = {"implementation": implementation_fingerprint(), "account_id": account_id,
                "appid": account.platform_account_id, "revision": config["revision"],
                "credential_ref": ref, "credential_version": config["credential_version"],
                "credential_identity": hmac.new(identity_key.encode(), secret.encode(), hashlib.sha256).hexdigest()}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return AccountRuntime(account_id, account.platform_account_id, fingerprint, secret)


def scope_fingerprint(db: Session, scope: dict) -> str | None:
    if (scope.get("publisher_key"), scope.get("publisher_version"), scope.get("channel"), scope.get("content_form"), scope.get("action")) != (KEY, VERSION, "wechat", "article", "auto_draft"):
        return None
    if type(scope.get("content_account_id")) is not int:
        return None
    try:
        runtime = resolve_runtime(db, scope["content_account_id"])
    except HTTPException:
        return None
    return runtime.fingerprint if scope.get("account_ref") == runtime.appid else None


class TokenCache:
    def __init__(self) -> None:
        self._entries: dict[tuple[int, str, str], tuple[str, float]] = {}
        self._lock = RLock()

    def put(self, runtime: AccountRuntime, token: str, *, expires_in: int) -> None:
        if (not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,2048}", token)
                or type(expires_in) is not int or not 60 <= expires_in <= 7200):
            raise HTTPException(502, "official_token_response_invalid")
        with self._lock:
            now = time.monotonic()
            self._entries = {key: value for key, value in self._entries.items() if value[1] > now and key[0] != runtime.account_id}
            if len(self._entries) >= 256:
                raise HTTPException(429, "official_token_cache_capacity")
            self._entries[(runtime.account_id, runtime.appid, runtime.fingerprint)] = (token, now + expires_in - 30)

    def get(self, runtime: AccountRuntime, *, now: float | None = None) -> str | None:
        key = (runtime.account_id, runtime.appid, runtime.fingerprint)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry[1] <= (time.monotonic() if now is None else now):
                self._entries.pop(key, None)
                return None
            return entry[0]

    def revoke(self, runtime: AccountRuntime) -> None:
        with self._lock:
            self._entries = {key: value for key, value in self._entries.items() if key[0] != runtime.account_id}


class OfficialWechatPublisher:
    key = KEY
    version = VERSION

    def capability(self, channel: str, content_form: str, account_ref: str) -> PublisherCapability:
        return PublisherCapability(publisher_key=self.key, channel=channel, content_form=content_form,
                                   action="auto_draft", available=False, reason="official_contract_unresolved")

    def verified(self) -> bool:
        return False

    def deliver(self, manifest: dict, target, attempt) -> PublisherResult:
        return PublisherResult(status="failed", error="official_contract_unresolved")
