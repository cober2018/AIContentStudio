"""Account-bound official Publisher identity for WeChat draft-box delivery."""

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
CONTRACT_VERSION = "wechat.official.draft.v2"
# draft/add takes these two forms; publication and mass sending are never offered.
DRAFT_FORMS = frozenset({"article", "image_message"})


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
    if ((scope.get("publisher_key"), scope.get("publisher_version"), scope.get("channel"), scope.get("action")) != (KEY, VERSION, "wechat", "auto_draft")
            or scope.get("content_form") not in DRAFT_FORMS):
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
        available = channel == "wechat" and content_form in DRAFT_FORMS
        return PublisherCapability(publisher_key=self.key, channel=channel, content_form=content_form,
                                   action="auto_draft", available=available, reason=None if available else "official_form_unsupported")

    def verified(self) -> bool:
        return False

    def deliver(self, manifest: dict, target, attempt) -> PublisherResult:
        # Official drafts run through wechat_official_delivery's claimed steps, never this generic hook.
        return PublisherResult(status="failed", error="official_delivery_path_required")
