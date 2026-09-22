"""Canonical candidate manifest for approval and manual handoff."""

import hashlib
import json

from ..models import Draft


def build_manifest(draft: Draft) -> dict:
    media = [
        {
            "id": row.id,
            "hash": row.content_hash,
            "role": row.role,
            "sort_order": row.sort_order,
            "public_use_allowed": row.public_use_allowed,
            "rights_status": row.rights_status,
        }
        for row in draft.media
    ]
    return {
        "schema_version": 1,
        "draft_id": draft.id,
        "revision_no": draft.revision_no,
        "title": draft.title,
        "body_markdown": draft.body,
        "structured": draft.structured_json,
        "thread_posts": draft.thread_posts_json,
        "media": media,
        "citations": (draft.structured_json or {}).get("citations") or (draft.structured_json or {}).get("claim_fact_map") or [],
        "declarations": (draft.structured_json or {}).get("declarations") or [],
        "fact_check": draft.fact_check_json,
        "mother_revision_id": draft.mother_revision_id,
        "input_hash": draft.input_hash,
    }


def readiness_reasons(draft: Draft) -> list[str]:
    reasons: list[str] = []
    fact_check = draft.fact_check_json or {}
    if not fact_check:
        reasons.append("missing_fact_check")
    elif fact_check.get("result") == "blocker":
        reasons.append("blocking_fact_check")
    if draft.input_hash and fact_check.get("input_hash") not in {None, draft.input_hash}:
        reasons.append("stale_fact_check")
    for media in draft.media:
        if media.public_use_allowed is not True or not media.rights_status or media.public_use_revoked_at:
            reasons.append(f"media_rights_incomplete:{media.id}")
    if draft.content_job.channel == "wechat" and not any(media.role == "cover" for media in draft.media):
        reasons.append("missing_required_cover")
    if draft.content_job.channel == "x_thread" and not draft.thread_posts_json:
        reasons.append("missing_thread_boundaries")
    return reasons


def candidate_hash(manifest: dict) -> str:
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def draft_input_hash(title: str, body: str, thread_posts: list | None, media: list | None = None) -> str:
    payload = {"title": title, "body": body, "thread_posts": thread_posts or [], "media": media or []}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
