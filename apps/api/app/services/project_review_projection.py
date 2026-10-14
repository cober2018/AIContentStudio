"""Read-only project review projection over existing persisted facts."""

import hashlib
from difflib import SequenceMatcher

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ChannelVariantRevision,
    ContentAsset,
    ContentProject,
    ContentUnit,
    DeliveryTarget,
    Draft,
    Review,
    WorkflowRun,
)
from .candidates import candidate_hash
from .channel_variant_documents import collection_key
from .project_evidence import current_boundary
from .project_projection_context import ProjectProjectionContext


def candidate_rows(db: Session, unit_id: int) -> list[ContentAsset]:
    return db.scalars(select(ContentAsset).where(ContentAsset.content_unit_id == unit_id).order_by(ContentAsset.id.desc())).all()


def unit_projection(db: Session, unit: ContentUnit, *, context: ProjectProjectionContext | None = None) -> dict:
    candidates = context.candidates.get(unit.id, []) if context is not None else candidate_rows(db, unit.id)
    current = candidates[0] if candidates else None
    legacy_current = next((row for row in candidates if row.channel_variant_revision_id is None), None)
    targets = (context.targets.get(current.id, []) if context is not None else db.scalars(select(DeliveryTarget).where(DeliveryTarget.content_asset_id == current.id).order_by(DeliveryTarget.id.desc())).all()) if current else []
    reviews = (context.reviews.get(current.id, []) if context is not None else db.scalars(select(Review).where(Review.content_asset_id == current.id).order_by(Review.id.desc())).all()) if current else []
    if context is not None:
        variant_keys = context.variant_keys
    else:
        variant_ids = {row.channel_variant_revision_id for row in candidates if row.channel_variant_revision_id is not None}
        keys = dict(db.execute(select(ChannelVariantRevision.id, ChannelVariantRevision.variant_key).where(
            ChannelVariantRevision.id.in_(variant_ids),
        )).all()) if variant_ids else {}
        variant_keys = {row.id: keys[row.channel_variant_revision_id] for row in candidates
                        if row.channel_variant_revision_id in keys}
    series_heads: dict[str, ContentAsset] = {}
    for candidate in candidates:
        key = variant_keys.get(candidate.id)
        if key is not None:
            series_heads.setdefault(key, candidate)
    series_candidate_ids = [row.id for row in series_heads.values()]
    series_targets = (context.targets if context is not None else {
        candidate_id: db.scalars(select(DeliveryTarget).where(DeliveryTarget.content_asset_id == candidate_id)).all()
        for candidate_id in series_candidate_ids
    })
    variant_series = []
    for key, row in series_heads.items():
        from .channel_variants import projected_variant_checks

        variant = db.get(ChannelVariantRevision, row.channel_variant_revision_id)
        series_reviews = context.reviews.get(row.id, []) if context is not None else db.scalars(select(Review).where(Review.content_asset_id == row.id)).all()
        series_approved = bool(row.status in {"approved", "exported"} and row.candidate_hash == row.approved_candidate_hash
                               and any(review.decision == "approved" and review.candidate_hash == row.candidate_hash for review in series_reviews))
        try:
            readiness = projected_variant_checks(db, variant) if variant is not None else None
            if readiness is None or readiness["drift_reasons"] or readiness["source_gate"]["status"] == "stale":
                status = "stale"
            elif readiness["ready"]:
                status = row.status
            else:
                status = "blocked"
        except (HTTPException, TypeError, ValueError):
            status = "blocked"
        variant_series.append({"variantKey": key, "candidateId": row.id, "candidateHash": row.candidate_hash,
                               "status": status, "channel": row.channel, "contentForm": row.content_form,
                               "approvalStatus": "approved" if series_approved else "waiting_review",
                               "targetStatuses": [target.status for target in series_targets.get(row.id, [])]})
    run = context.runs.get(unit.id) if context is not None else db.scalar(select(WorkflowRun).where(WorkflowRun.content_unit_id == unit.id).order_by(WorkflowRun.id.desc()).limit(1))

    def attempts(target):
        return context.attempts.get(target.id, []) if context is not None else target.attempts

    def receipts(target):
        return context.receipts.get(target.id, []) if context is not None else target.receipts

    live_db = context.live_reads(unit.project_id) if context is not None else db
    dimensions: dict[str, dict] = {}

    def dimension(name: str, status: str, reasons: list[str] | None = None) -> None:
        dimensions[name] = {"status": status, "reasons": reasons or []}

    dimension("content", "ready" if current else "blocked", [] if current else ["candidate_missing"])
    dimension("identity", "ready" if unit.identity_snapshot_id else "blocked", [] if unit.identity_snapshot_id else ["identity_unready"])
    boundary = context.boundaries.get(unit.project_id) if context is not None else current_boundary(db, unit.project_id)
    evidence = (current.candidate_manifest_json or {}).get("evidence", {}) if current else {}
    evidence_stale = bool(current and evidence.get("boundary_id") and boundary and evidence["boundary_id"] != boundary.id)
    from .project_review import live_evidence_reasons

    evidence_reasons = live_evidence_reasons(live_db, unit.project_id, current.candidate_manifest_json or {}) if current else ([] if boundary else ["evidence_unready"])
    dimension("evidence", "stale" if evidence_stale else ("blocked" if evidence_reasons else "ready"), evidence_reasons)
    media_reasons: list[str] = []
    if current:
        from .delivery import _live_media_rights

        for media in (current.candidate_manifest_json or {}).get("media", []):
            if _live_media_rights(live_db, media) is not True:
                media_reasons.append(f"media_rights_unready:{media.get('material_revision_id') or media.get('draft_media_id')}")
    dimension("media", "blocked" if media_reasons else "ready", media_reasons)
    checksum_ok = bool(current and current.candidate_hash and candidate_hash(current.candidate_manifest_json or {}) == current.candidate_hash)
    dimension("checks", "ready" if checksum_ok else "blocked", [] if checksum_ok else ["candidate_integrity_unready"])
    stale_revision = False
    if current and current.draft_id:
        draft = context.drafts.get(current.draft_id) if context is not None else db.get(Draft, current.draft_id)
        if draft:
            latest = context.draft_revisions.get(draft.content_job_id) if context is not None else db.scalar(select(Draft.revision_no).where(Draft.content_job_id == draft.content_job_id).order_by(Draft.revision_no.desc()).limit(1))
            stale_revision = latest != draft.revision_no
    dimension("candidate", "stale" if stale_revision else ("ready" if current else "blocked"), ["newer_draft_revision"] if stale_revision else ([] if current else ["freeze_required"]))
    v4_error = None
    if current and (current.candidate_manifest_json or {}).get("schema_version") == 4:
        from .production_validation import validate_live_v4_candidate

        try:
            validate_live_v4_candidate(db, current)
        except HTTPException as exc:
            v4_error = exc.detail if isinstance(exc.detail, dict) else {"code": "readiness_blocked", "reasons": [str(exc.detail)]}
            stale_revision = v4_error["code"] in {"stale_master", "historical_candidate"}
            dimension("candidate", "stale" if stale_revision else "blocked", v4_error.get("reasons", []))
            dimension("checks", "stale" if stale_revision else "blocked", [v4_error["code"], *v4_error.get("reasons", [])])
    approved = bool(current and current.status in {"approved", "exported"} and current.candidate_hash == current.approved_candidate_hash and any(row.decision == "approved" and row.candidate_hash == current.candidate_hash for row in reviews))
    pending_series = [series["variantKey"] for series in variant_series if series["approvalStatus"] != "approved"]
    unauthorized_series = [series["variantKey"] for series in variant_series
                           if series["approvalStatus"] == "approved" and not series["targetStatuses"]]
    dimension("approval", "waiting_review" if pending_series else "approved" if variant_series or approved else "waiting_review" if current else "blocked",
              [f"approval_pending:{key}" for key in pending_series] if pending_series else [] if current else ["candidate_missing"])
    has_series_target = any(series["targetStatuses"] for series in variant_series)
    dimension("delivery", "blocked" if unauthorized_series or not targets and not has_series_target else "ready",
              [f"authorization_missing:{key}" for key in unauthorized_series] if unauthorized_series else [] if targets or has_series_target else ["authorization_missing"])
    relevant_targets = {target.id: target for candidate_id in series_candidate_ids for target in series_targets.get(candidate_id, [])}
    relevant_targets.update({target.id: target for target in targets})
    unknown = any(target.status == "reconciliation_needed" or any(attempt.status == "unknown" and (attempt.response_metadata_json or {}).get("reconciled") is None for attempt in attempts(target)) for target in relevant_targets.values())
    if unknown:
        summary = "unknown"
    elif any(series["status"] == "blocked" for series in variant_series):
        summary = "blocked"
    elif any(series["status"] == "stale" for series in variant_series):
        summary = "stale"
    elif any(target.status == "blocked" for target in targets) or media_reasons or (evidence_reasons and not evidence_stale) or (not checksum_ok and current is not None) or (v4_error and not stale_revision):
        summary = "blocked"
    elif evidence_stale or stale_revision or (run and run.status == "stale" and current is None):
        summary = "stale"
    elif pending_series or current and not approved and not variant_series:
        summary = "waiting_review"
    elif unauthorized_series or current and not targets and not variant_series:
        summary = "approved"
    elif relevant_targets and all(target.status == "human_confirmed" for target in relevant_targets.values()):
        summary = "delivered"
    elif relevant_targets:
        summary = "delivery_ready"
    elif not unit.identity_snapshot_id or boundary is None:
        summary = "blocked"
    else:
        summary = "ready"
    return {
        "unit_id": unit.id, "project_id": unit.project_id, "title": unit.title, "modality": unit.modality,
        "persona_id": unit.persona_id, "account_id": unit.account_id, "channel_id": unit.channel_id,
        "identity_snapshot_id": unit.identity_snapshot_id,
        "unit_status": unit.status, "summary": summary, "dimensions": dimensions,
        "current_candidate": {"id": current.id, "hash": current.candidate_hash, "status": current.status, "title": current.title} if current else None,
        "legacy_current_candidate": {"id": legacy_current.id, "hash": legacy_current.candidate_hash, "status": legacy_current.status, "title": legacy_current.title} if legacy_current else None,
        "variantSeries": variant_series,
        "history": [{"id": row.id, "hash": row.candidate_hash, "status": row.status, "title": row.title} for row in candidates[1:]],
        "reviews": [{"id": row.id, "decision": row.decision, "candidate_hash": row.candidate_hash, "comment": row.comment} for row in reviews],
        "targets": [{"id": target.id, "status": target.status, "action": target.action, "account_ref": target.account_ref,
                     "content_account_id": target.content_account_id,
                     "attempts": [] if context is not None and context.summary_only else [{"id": attempt.id, "status": attempt.status, "remote_id": attempt.remote_id, "error": attempt.error} for attempt in attempts(target)],
                     "receipts": [{"id": receipt.id, "status": receipt.status, "evidence_ref": receipt.evidence_ref, "note": receipt.note} for receipt in receipts(target)]} for target in targets],
    }


def project_projection(db: Session, project: ContentProject, *, context: ProjectProjectionContext | None = None) -> dict:
    units = (context.units.get(project.id, []) if context is not None
             else db.scalars(select(ContentUnit).where(ContentUnit.project_id == project.id).order_by(ContentUnit.id)).all())
    return {"project_id": project.id, "title": project.title, "status": project.status, "units": [unit_projection(db, unit, context=context) for unit in units]}


def diff_variant_rows(before: list[dict], after: list[dict]) -> list[dict]:
    """Compare stable channel block/card/scene identities, keeping visual order distinct from content."""
    old = {row["id"]: row for row in before}
    new = {row["id"]: row for row in after}
    changes = [{"id": row["id"], "changes": ["remove"]} for row in before if row["id"] not in new]
    for row in after:
        prior = old.get(row["id"])
        if prior is None:
            changes.append({"id": row["id"], "changes": ["add"]})
            continue
        kinds = []
        if prior["order"] != row["order"]:
            kinds.append("move")
        if {key: value for key, value in prior.items() if key != "order"} != {key: value for key, value in row.items() if key != "order"}:
            kinds.append("modify")
        if kinds:
            changes.append({"id": row["id"], "changes": kinds})
    return changes


def candidate_diff(previous: ContentAsset | None, current: ContentAsset) -> dict:
    _verify_frozen_production(current)
    if previous is not None:
        _verify_frozen_production(previous)
    latest = current.candidate_manifest_json or {}
    if latest.get("schema_version") == 5:
        _verify_frozen_variant(current)
        if previous is not None:
            _verify_frozen_variant(previous)
            prior_key = (previous.candidate_manifest_json or {}).get("variant", {}).get("variant_key")
            if previous.content_unit_id != current.content_unit_id or prior_key != latest["variant"]["variant_key"]:
                previous = None
        prior = previous.candidate_manifest_json if previous else {}
        names = ("content", "source_master", "variant", "target", "brief", "assets", "evidence_refs",
                 "evidence", "identity", "production", "checks", "render", "citations", "declarations")
        changed = {name: {"changed": prior.get(name) != latest.get(name)} for name in names}
        kind = latest["target"]["artifact_kind"]
        before = (prior.get("render") or {}).get("text", "")
        after = latest["render"].get("text", "")
        text = ({"before_chars": len(before), "after_chars": len(after),
                 "similarity": round(SequenceMatcher(None, before, after).ratio(), 4)} if kind == "text" else None)
        rows_key = collection_key(latest["variant"]["payload_schema"])
        structured = diff_variant_rows((prior.get("content") or {}).get(rows_key, []), latest["content"][rows_key]) if rows_key else None
        return {"from_candidate_id": previous.id if previous else None, "to_candidate_id": current.id,
                "modality": latest["project"]["modality"], "changed_sections": changed,
                "structured": structured, "text": text}
    prior = previous.candidate_manifest_json or {} if previous else {}
    sections = ("content", "content_master", "brief", "assets", "evidence_refs", "media", "evidence", "identity", "production", "checks", "render", "channel", "content_form", "citations", "declarations")
    changed = {name: {"changed": prior.get(name) != latest.get(name)} for name in sections}
    modality = (latest.get("project") or {}).get("modality", "text")
    if modality != "text":
        structured = None
        if modality == "graphic" and previous and (prior.get("content_master") or {}).get("payload_schema") == "graphic.master.v2" and (latest.get("content_master") or {}).get("payload_schema") == "graphic.master.v2":
            from .graphic_master_diff import diff_graphic_documents

            structured = diff_graphic_documents(prior.get("content") or {}, latest.get("content") or {})
        elif modality == "video" and previous and (prior.get("content_master") or {}).get("payload_schema") == "video.master.v2" and (latest.get("content_master") or {}).get("payload_schema") == "video.master.v2":
            from .video_master_diff import diff_video_documents

            structured = diff_video_documents(prior["content"], latest["content"])
        return {"from_candidate_id": previous.id if previous else None, "to_candidate_id": current.id, "modality": modality, "changed_sections": changed, "structured": structured, "text": None}
    structured = None
    if previous and prior.get("schema_version") == 4 and latest.get("schema_version") == 4 and (prior.get("content_master") or {}).get("payload_schema") == "text.master.v2" and (latest.get("content_master") or {}).get("payload_schema") == "text.master.v2":
        before_list = ((prior.get("content") or {}).get("document") or {}).get("blocks", [])
        after_list = ((latest.get("content") or {}).get("document") or {}).get("blocks", [])
        before_blocks = {item.get("id"): item for item in before_list}
        after_blocks = {item.get("id"): item for item in after_list}
        before_order, after_order = list(before_blocks), list(after_blocks)
        structured = []
        for block_id in before_order:
            if block_id not in after_blocks:
                structured.append({"kind": "remove", "block_id": block_id})
        for block_id in after_order:
            if block_id not in before_blocks:
                structured.append({"kind": "add", "block_id": block_id})
            else:
                changes = []
                if before_order.index(block_id) != after_order.index(block_id):
                    changes.append("move")
                if before_blocks[block_id] != after_blocks[block_id]:
                    changes.append("modify")
                if changes:
                    structured.append({"kind": changes[-1], "changes": changes, "block_id": block_id})
    before = str(((prior.get("render") or {}).get("body_markdown") if prior.get("schema_version") == 4 else (prior.get("content") or {}).get("body_markdown")) or "")[:2000]
    after = str(((latest.get("render") or {}).get("body_markdown") if latest.get("schema_version") == 4 else (latest.get("content") or {}).get("body_markdown")) or "")[:2000]
    return {"from_candidate_id": previous.id if previous else None, "to_candidate_id": current.id,
            "changed_sections": changed, "structured": structured, "text": {"before_chars": len(before), "after_chars": len(after),
                                                 "similarity": round(SequenceMatcher(None, before, after).ratio(), 4)}}


def _verify_frozen_production(asset: ContentAsset) -> None:
    manifest = asset.candidate_manifest_json or {}
    schema = (manifest.get("content_master") or {}).get("payload_schema")
    if manifest.get("schema_version") != 4 or schema not in {"text.master.v2", "graphic.master.v2", "video.master.v2"}:
        return
    render = manifest.get("render") or {}
    if candidate_hash(manifest) != asset.candidate_hash or render.get("status") != "ready":
        raise HTTPException(409, {"code": "frozen_candidate_integrity_failed"})
    if schema == "text.master.v2":
        body = render.get("body_markdown")
        if not isinstance(body, str) or render.get("content_hash") != hashlib.sha256(body.encode()).hexdigest():
            raise HTTPException(409, {"code": "frozen_candidate_integrity_failed"})
    elif schema == "graphic.master.v2":
        from .graphic_documents import GraphicDocumentError, canonical_payload

        try:
            document = canonical_payload(manifest.get("content") or {})
        except GraphicDocumentError as exc:
            raise HTTPException(409, {"code": "frozen_candidate_integrity_failed"}) from exc
        outputs = render.get("outputs")
        if not isinstance(outputs, list) or [item.get("canvas_id") for item in outputs if isinstance(item, dict)] != [canvas["id"] for canvas in document["canvases"]] or len(outputs) != len(document["canvases"]):
            raise HTTPException(409, {"code": "frozen_candidate_integrity_failed"})
    else:
        from .production_modalities import _canonical_hash, frozen_video_render_input_hash
        from .video_documents import VideoDocumentError, canonical_payload, validate_references

        try:
            content = manifest["content"]
            if canonical_payload(content) != content or _canonical_hash(content) != manifest["content_master"]["payload_hash"]:
                raise ValueError("frozen_video_payload_mismatch")
            assets = manifest["assets"]
            validate_references(content, [
                {key: ref[key] for key in ("material_revision_id", "content_hash", "role", "slot_key", "sort_order", "placement")}
                for ref in assets
            ], manifest["evidence_refs"])
            output_refs = [ref for ref in assets if ref["role"] == "render_output"]
            outputs = render["outputs"]
            if len(output_refs) != 1 or not isinstance(outputs, list) or len(outputs) != 1:
                raise ValueError("frozen_video_render_count_invalid")
            ref, output = output_refs[0], outputs[0]
            if not isinstance(output, dict) or output.get("material_revision_id") != ref["material_revision_id"] or output.get("content_hash") != ref["content_hash"] or output.get("mime_type") != "video/mp4" or output.get("rights_snapshot") != ref["rights_snapshot"] or output.get("canvas_id") is not None:
                raise ValueError("frozen_video_render_binding_invalid")
            profile = render["video_profile"]
            if not isinstance(profile, dict) or profile.get("source") != "profile" or type(profile.get("version_id")) is not int or profile.get("artifact_kind") != "video":
                raise ValueError("frozen_video_profile_invalid")
            input_hash = frozen_video_render_input_hash(manifest)
            attestation = manifest["production"]["edit_summary"]["render_attestation"]
            if not isinstance(attestation, dict) or attestation.get("origin") != "manual" or attestation.get("confirmed") is not True or not attestation.get("attested_by"):
                raise ValueError("frozen_video_render_attestation_invalid")
            expected_output = {"material_revision_id": ref["material_revision_id"], "content_hash": ref["content_hash"], "canvas_id": None}
            if render.get("origin") != "manual" or render.get("attested_by") != attestation["attested_by"] or render.get("render_input_hash") != input_hash or attestation.get("render_input_hash") != input_hash or attestation.get("outputs") != [expected_output]:
                raise ValueError("frozen_video_render_attestation_invalid")
        except (KeyError, TypeError, ValueError, VideoDocumentError) as exc:
            raise HTTPException(409, {"code": "frozen_candidate_integrity_failed"}) from exc


def _verify_frozen_variant(asset: ContentAsset) -> dict:
    from .candidates_v5 import build_manifest_v5

    manifest = asset.candidate_manifest_json or {}
    legacy_fields = (asset.draft_id, asset.topic_brief_id, asset.mother_revision_id,
                     asset.content_master_revision_id, asset.workflow_run_id)
    try:
        intact = (manifest.get("schema_version") == 5 and candidate_hash(manifest) == asset.candidate_hash
                  and build_manifest_v5({key: value for key, value in manifest.items() if key != "schema_version"}) == manifest
                  and asset.channel_variant_revision_id == manifest["variant"]["id"]
                  and asset.project_id == manifest["project"]["id"]
                  and asset.content_unit_id == manifest["project"]["unit_id"]
                  and asset.identity_snapshot_id == manifest["identity"]["id"]
                  and all(value is None for value in legacy_fields)
                  and asset.channel == manifest["target"]["channel"]
                  and asset.content_form == manifest["target"]["content_form"]
                  and asset.artifact_kind == manifest["target"]["artifact_kind"])
    except (KeyError, TypeError, ValueError):
        intact = False
    if not intact:
        raise HTTPException(409, {"code": "frozen_candidate_integrity_failed"})
    return manifest


def candidate_preview(asset: ContentAsset) -> dict:
    """Preview the frozen snapshot, never the mutable current Master payload."""
    _verify_frozen_production(asset)
    manifest = asset.candidate_manifest_json or {}
    if manifest.get("schema_version") == 5:
        manifest = _verify_frozen_variant(asset)
        target = manifest["target"]
        render = manifest["render"]
        preview = {"modality": manifest["project"]["modality"], "title": asset.title,
                "target": {"channel": asset.channel, "content_form": asset.content_form, "artifact_kind": asset.artifact_kind},
                "render": render, "content": manifest["content"], "checks": manifest["checks"],
                "external_execution": (manifest.get("production") or {}).get("external_execution", [])}
        from .channel_form_descriptors import form_descriptor_for

        preview["payload_schema"] = manifest["variant"]["payload_schema"]
        preview["form_descriptor"] = form_descriptor_for(preview["payload_schema"], asset.channel, asset.content_form)
        preview["target_account"] = target.get("account")
        preview["delivery_notice"] = "本地包供人工交付；公众号草稿不是公开发布。"
        if "official_render" in manifest:
            preview["official_render"] = manifest["official_render"]
        if target["artifact_kind"] == "text":
            body = render["text"]
            preview.update({"markdown": body[:20_000], "truncated": len(body) > 20_000})
        elif target["artifact_kind"] == "image":
            cards = render["cards"]
            preview.update({"canvas_count": len(cards), "cards": cards})
        else:
            scenes = render["scenes"]
            preview.update({"shot_count": len(scenes), "shots": scenes,
                            "estimated_srt": render.get("estimated_srt"), "finished_video": False})
        return preview
    content = manifest.get("content") or {}
    modality = (manifest.get("project") or {}).get("modality", "text")
    preview = {"modality": modality, "title": asset.title, "render": manifest.get("render") or {},
               "external_execution": (manifest.get("production") or {}).get("external_execution", [])}
    if manifest.get("schema_version") != 4:
        markdown = str(content.get("body_markdown") or "")
        return {**preview, "modality": "text", "source_modality": modality, "markdown": markdown[:20_000], "truncated": len(markdown) > 20_000}
    if modality == "text":
        markdown = str((manifest.get("render") or {}).get("body_markdown") if manifest.get("schema_version") == 4 else content.get("body_markdown") or "")
        preview.update({"markdown": markdown[:20_000], "truncated": len(markdown) > 20_000, "document_present": isinstance(content.get("document"), dict)})
    elif modality == "graphic":
        canvases = content.get("canvases") or []
        if (manifest.get("content_master") or {}).get("payload_schema") == "graphic.master.v2":
            from .graphic_documents import canonical_payload

            canvases = canonical_payload(content)["canvases"]
            outputs = {(item.get("canvas_id")): item for item in (manifest.get("render") or {}).get("outputs", [])}
            preview.update({"canvas_count": len(canvases), "canvases": [{"id": row["id"], "order": row["order"], "width": row["width"], "height": row["height"], "role": row.get("role"), "text": "\n".join("".join(run["text"] for run in layer["runs"]) for layer in row["layers"] if layer["type"] == "text" and layer["visible"])[:4000], "layers": [{"id": layer["id"], "order": layer["order"], "type": layer["type"], "visible": layer["visible"], "material_revision_id": layer.get("material_revision_id")} for layer in row["layers"][:100]], "render_output": outputs.get(row["id"])} for row in canvases[:50]], "checks": [{"check_kind": item.get("kind") or item.get("check_kind"), "status": item.get("status"), "input_hash": item.get("input_hash")} for item in (manifest.get("checks") or [])[:50]]})
        else:
            preview.update({"canvas_count": len(canvases), "canvases": [{"id": row.get("id"), "order": row.get("order"), "width": row.get("width"), "height": row.get("height")} for row in canvases[:50]]})
    elif modality == "video":
        if (manifest.get("content_master") or {}).get("payload_schema") == "video.master.v2":
            from .video_documents import canonical_payload

            document = canonical_payload(content)
            preview.update({"shot_count": len(document["shots"]), "script_blocks": document["script"]["blocks"], "shots": document["shots"], "timeline": document["timeline"], "voice": document["voice"], "subtitles": document["subtitles"], "overlays": document["overlays"], "music": document["music"], "cover": document["cover"], "checks": [{"check_kind": item.get("kind") or item.get("check_kind"), "status": item.get("status"), "input_hash": item.get("input_hash")} for item in (manifest.get("checks") or [])[:50]]})
        else:
            shots = content.get("shots") or []
            script = content.get("script") or ""
            preview.update({"shot_count": len(shots), "script": script[:20_000] if isinstance(script, str) else {"structured": True}, "shots": [{"id": row.get("id"), "order": row.get("order"), "duration": row.get("duration")} for row in shots[:50]], "timeline_present": bool(content.get("timeline"))})
    return preview
