"""Exact published-form capability boundary for F6E ChannelAdapters."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from ..models import ChannelTemplateVersion
from .content_harness.channel_registry import ChannelRegistryError, resolve_content_form


class AdapterUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class AdapterContract:
    key: str
    version: str
    accepted_master_schemas: frozenset[str]
    channel: str
    content_form: str
    artifact_kind: str
    payload_schema: str


class ChannelAdapter(Protocol):
    contract: AdapterContract

    def capabilities(self) -> dict: ...

    def canonicalize(self, payload: object) -> dict: ...

    def validate(self, payload: dict, asset_refs: list[dict], evidence_refs: list[dict]) -> None: ...

    def adapt(self, source_payload: dict) -> dict: ...

    def preview(self, payload: dict) -> dict: ...

    def render(self, payload: dict) -> dict: ...

    def required_checks(self, payload: dict) -> tuple[str, ...]: ...

    def package_projection(self, payload: dict) -> dict: ...


FIRST_BATCH: dict[tuple[str, str], AdapterContract] = {
    ("wechat", "article"): AdapterContract("wechat.article", "1", frozenset({"text.master.v2"}), "wechat", "article", "text", "wechat.article.v1"),
    ("x", "thread"): AdapterContract("x.thread", "1", frozenset({"text.master.v2"}), "x", "thread", "text", "x.thread.v1"),
    ("x", "single"): AdapterContract("x.single", "1", frozenset({"text.master.v2"}), "x", "single", "text", "x.single.v1"),
    ("xiaohongshu", "image_note"): AdapterContract("xiaohongshu.image_note", "1", frozenset({"graphic.master.v2"}), "xiaohongshu", "image_note", "image", "xiaohongshu.image_note.v1"),
    ("douyin", "spoken_script"): AdapterContract("douyin.spoken_script", "1", frozenset({"video.master.v2"}), "douyin", "spoken_script", "script", "douyin.spoken_script.v1"),
}


# Registration means the executable implementation passed its own acceptance gates.
_EXECUTABLE_ADAPTERS: dict[tuple[str, str], ChannelAdapter] = {}


def capability_for(db: Session, source_schema: str, channel: str, content_form: str) -> dict:
    contract = FIRST_BATCH.get((channel, content_form))
    if contract is None or source_schema not in contract.accepted_master_schemas:
        return {
            "configured": False,
            "supported_source": False,
            "executable": False,
            "verified": False,
            "reason": "unsupported_source_or_target",
        }
    try:
        form = resolve_content_form(db, channel, content_form)
    except ChannelRegistryError:
        return {
            "configured": False,
            "supported_source": True,
            "executable": False,
            "verified": False,
            "reason": "published_profile_missing",
        }
    if form.source != "profile" or form.profile_version_id is None:
        return {
            "configured": False,
            "supported_source": True,
            "executable": False,
            "verified": False,
            "reason": "published_profile_missing",
        }
    if form.artifact_kind != contract.artifact_kind:
        raise AdapterUnavailable("artifact_kind_mismatch")
    template = db.get(ChannelTemplateVersion, form.profile_version_id)
    if template is None or template.status != "published":
        raise AdapterUnavailable("published_profile_missing")
    profile = (template.profile_json or {}).get("content_forms", {}).get(content_form)
    if not isinstance(profile, dict):
        raise AdapterUnavailable("published_profile_missing")
    profile_hash = hashlib.sha256(json.dumps(profile, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    adapter = _EXECUTABLE_ADAPTERS.get((channel, content_form))
    executable = adapter is not None and adapter.contract == contract
    return {
        "configured": True,
        "supported_source": True,
        "executable": executable,
        "verified": False,
        "reason": None if executable else "adapter_not_implemented",
        "profile_version_id": template.id,
        "profile_version": template.version,
        "profile_hash": profile_hash,
        "artifact_kind": contract.artifact_kind,
        "adapter_key": contract.key,
        "adapter_version": contract.version,
        "payload_schema": contract.payload_schema,
    }
