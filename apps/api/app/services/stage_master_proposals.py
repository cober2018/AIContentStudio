"""Canonical Master proposals for the versioned Creation Recipe stage."""

from __future__ import annotations

import asyncio
import math
import re

from .generation.providers import (
    provider_failure,
    GenerateRequest,
    MockProvider,
    OpenAICompatibleProvider,
    effective_llm_config,
    input_hash,
    record_run,
    record_validated_stage_run,
)
from .stage_contracts import canonical, digest, remember_validation_code
from .text_documents import convert_legacy_text, resolve_proposal_citations

MAX_CANDIDATES = 5
MAX_OUTPUT_BYTES = 128 * 1024
MASTER_SCHEMAS = {modality: f"{modality}.master.v2" for modality in ("text", "graphic", "video")}


class StageProposalError(ValueError):
    pass


def master_modality(resolved: dict) -> str:
    modality = (resolved.get("context") or {}).get("modality", "text")
    if not isinstance(modality, str) or modality not in MASTER_SCHEMAS:
        raise StageProposalError("stage_modality_unavailable")
    return modality


def canonical_master_payload(modality: str, payload: dict, asset_refs: list, evidence_refs: list) -> dict:
    from . import graphic_documents, text_documents, video_documents
    from .production_modalities import validate_master_references

    documents = {"text": text_documents, "graphic": graphic_documents, "video": video_documents}
    if modality not in documents:
        raise StageProposalError("stage_modality_unavailable")
    if any(not isinstance(refs, list) or any(not isinstance(ref, dict) for ref in refs)
           for refs in (asset_refs, evidence_refs)):
        raise StageProposalError("stage_proposal_reference_invalid")
    document = documents[modality]
    payload = document.canonical_payload(payload)
    document.validate_references(payload, asset_refs, evidence_refs)
    if validate_master_references(payload, asset_refs, evidence_refs):
        raise StageProposalError("stage_proposal_reference_invalid")
    return canonical(payload)


def planned_shots(upstream: dict | None) -> list[dict] | None:
    """Shots of the accepted shot plan upstream, in order, or None when the stage has no plan."""
    for value in (upstream or {}).values():
        if (isinstance(value, dict) and str(value.get("output_schema") or "").startswith("video.shot-plan.")
                and isinstance(value.get("selected_content"), dict)):
            shots = value["selected_content"].get("shots")
            if isinstance(shots, list) and shots:
                return sorted(shots, key=lambda shot: shot["order"])
    return None


MAX_BOARD_ROWS = 30


def _beat_text(beat: dict, key: str) -> str:
    value = beat.get(key)
    return value.strip() if isinstance(value, str) else ""


def _video_plan(data: dict, plan: list[dict] | None = None) -> dict:
    """Turn a storyboard table into video.master.v2 without inventing footage."""
    from .video_documents import BOARD_CAMERA, BOARD_SPEAKER

    title = data.get("title") or "未命名视频"
    if not isinstance(title, str) or not title.strip():
        raise StageProposalError("stage_proposal_candidate_invalid")
    beats = data.get("beats")
    if not isinstance(beats, list) or not (len(beats) == len(plan) if plan else 1 <= len(beats) <= MAX_BOARD_ROWS):
        raise StageProposalError("stage_proposal_candidate_invalid")
    blocks, shots, items, cursor = [], [], [], 0
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            raise StageProposalError("stage_proposal_candidate_invalid")
        planned = plan[index] if plan else {}
        line = _beat_text(beat, "line") or _beat_text(beat, "narration")
        speaker = beat.get("speaker") if beat.get("speaker") in BOARD_SPEAKER else ("narration" if line or planned.get("script") else "none")
        if speaker != "none":
            line = line or (planned.get("script") or "").strip()
        visual = _beat_text(beat, "visual") or (planned.get("visual") or "").strip()
        if not visual or (speaker != "none" and not line):
            raise StageProposalError("stage_proposal_candidate_invalid")
        seconds = planned.get("duration_seconds")
        duration = (min(15_000, max(200, round(seconds * 1000))) if type(seconds) in (int, float) and seconds > 0
                    else beat.get("duration_ms", 1500))
        if type(duration) is not int or not 200 <= duration <= 15_000:
            raise StageProposalError("stage_proposal_candidate_invalid")
        # Shot ids come from the plan so shot-slot material stays attached to the same shot.
        key = planned["id"] if plan else str(index + 1)
        block_id, shot_id = f"script-{key}", planned["id"] if plan else f"shot-{key}"
        message = _beat_text(beat, "message") or (planned.get("purpose") or "").strip()
        shot = {"id": shot_id, "order": index, "label": visual[:200], "purpose": (message or visual)[:1000], "duration_ms": duration,
                "board": {"message": message[:500], "visual": visual[:1000],
                          "camera": beat.get("camera") if beat.get("camera") in BOARD_CAMERA else "fixed", "speaker": speaker,
                          "sound": _beat_text(beat, "sound")[:500], "notes": _beat_text(beat, "notes")[:500]}}
        if speaker != "none":
            blocks.append({"id": block_id, "order": len(blocks), "text": line[:10_000]})
            shot["script_block_id"] = block_id
        shots.append(shot)
        items.append({"id": f"item-{key}", "order": index, "shot_id": shot_id,
                      "start_ms": cursor, "end_ms": cursor + duration})
        cursor += duration
    return {"title": title.strip()[:500], "aspect_ratio": [9, 16], "script": {"blocks": blocks}, "shots": shots,
            "timeline": {"duration_ms": cursor, "tracks": [{"id": "video-1", "order": 0, "kind": "video", "items": items}]},
            "voice": {"mode": "none"}, "subtitles": {"cues": []}, "overlays": [], "music": {}, "cover": {}}


def _markdown(data: dict) -> tuple[str, str]:
    title = data.get("title") or (data.get("titles") or [""])[0] or "未命名内容"
    if isinstance(data.get("body"), str):
        body = data["body"]
    elif isinstance(data.get("sections"), list):
        body = "\n\n".join(
            f"## {item.get('heading', '')}\n{item.get('body', '')}" for item in data["sections"]
            if isinstance(item, dict) and isinstance(item.get("body"), str)
        )
    elif isinstance(data.get("spoken_script"), str):
        body = data["spoken_script"]
    else:
        raise StageProposalError("stage_proposal_candidate_invalid")
    if not body.strip():
        raise StageProposalError("stage_proposal_candidate_invalid")
    return str(title)[:500], f"# {str(title)[:500]}\n\n{body}"


_INTACT_FIELDS = ("payload", "payload_schema", "asset_refs", "evidence_refs", "citation_selections")
_TEXT_FIELDS = ("title", "body", "spoken_script")


def project_proposal_input(data, modality: str):
    """Drop echoed siblings before the depth bound.

    A declared payload or reference is kept verbatim so an invented ref still fails.
    Simple title and body fields are kept only when no payload was supplied.
    """
    if not isinstance(data, dict):
        return data
    if isinstance(data.get("candidates"), list):
        return {"candidates": [_project_proposal_candidate(item, modality) for item in data["candidates"]]}
    return _project_proposal_candidate(data, modality)


def _project_proposal_candidate(item, modality: str):
    if not isinstance(item, dict):
        return item
    projected = {}
    for key in _INTACT_FIELDS:
        if key not in item:
            continue
        value = item[key]
        if _within_depth(value):
            projected[key] = value
            continue
        reduced = _reduced_refs(key, value)
        if reduced is not None and _within_depth(reduced):
            projected[key] = reduced
    if "payload" in projected:
        return projected
    if modality == "video":
        projected.update(_video_fields(item))
    elif modality == "text":
        projected.update(_text_fields(item))
        if "body" not in projected and isinstance(item.get("payload"), dict):
            projected.update(_text_fields(item["payload"]))
    return projected


def _within_depth(value, at: int = 3) -> bool:
    """A candidate field is visited three levels under the proposal envelope."""
    from .stage_contracts import MAX_DEPTH

    return _max_depth(value, at) <= MAX_DEPTH


def _max_depth(value, depth: int) -> int:
    if isinstance(value, dict):
        return max([depth, *(_max_depth(child, depth + 1) for child in value.values())], default=depth)
    if isinstance(value, list):
        return max([depth, *(_max_depth(child, depth + 1) for child in value)], default=depth)
    return depth


def _reduced_refs(key: str, value):
    fields = {
        "asset_refs": ("material_revision_id", "content_hash", "role", "slot_key", "sort_order", "canvas_id"),
        "evidence_refs": ("fact_pack_item_id", "snapshot_checksum", "role", "sort_order", "item_id", "checksum"),
    }.get(key)
    if fields is None or not isinstance(value, list):
        return None
    reduced = []
    for ref in value:
        if isinstance(ref, dict):
            reduced.append({name: ref[name] for name in fields if name in ref and not isinstance(ref[name], (dict, list))})
        else:
            reduced.append(ref)
    return reduced


def _text_fields(item: dict) -> dict:
    projected = {}
    for key in _TEXT_FIELDS:
        if isinstance(item.get(key), str):
            projected[key] = item[key]
    if isinstance(item.get("alt_titles"), list):
        projected["alt_titles"] = [entry for entry in item["alt_titles"] if isinstance(entry, str)][:2]
    if isinstance(item.get("titles"), list):
        titles = [entry for entry in item["titles"] if isinstance(entry, str)]
        if titles:
            projected["titles"] = titles
    if isinstance(item.get("sections"), list):
        sections = []
        for section in item["sections"]:
            if isinstance(section, dict):
                kept = {name: section[name] for name in ("heading", "body") if isinstance(section.get(name), str)}
                if kept:
                    sections.append(kept)
        if sections:
            projected["sections"] = sections
    if "body" not in projected and isinstance(item.get("body"), list) and item["body"] and all(isinstance(part, str) for part in item["body"]):
        projected["body"] = "\n\n".join(item["body"])
    return projected


def _video_fields(item: dict) -> dict:
    projected = {}
    if isinstance(item.get("title"), str):
        projected["title"] = item["title"]
    if isinstance(item.get("beats"), list):
        beats = []
        for beat in item["beats"]:
            if not isinstance(beat, dict):
                beats.append(beat)
                continue
            kept = {key: beat[key] for key in ("narration", "line", "message", "visual", "camera", "speaker", "sound", "notes")
                    if isinstance(beat.get(key), str)}
            if type(beat.get("duration_ms")) is int:
                kept["duration_ms"] = beat["duration_ms"]
            beats.append(kept)
        projected["beats"] = beats
    return projected


def _candidate(raw: dict, index: int, modality: str = "text", resolved: dict | None = None) -> dict:
    if not isinstance(raw, dict):
        raise StageProposalError("stage_proposal_candidate_invalid")
    schema = MASTER_SCHEMAS[modality]
    if raw.get("payload_schema", schema) != schema:
        raise StageProposalError("stage_proposal_schema_invalid")
    payload = raw.get("payload")
    asset_refs = raw.get("asset_refs", [])
    evidence_refs = raw.get("evidence_refs", [])
    if any(not isinstance(refs, list) or any(not isinstance(ref, dict) for ref in refs)
           for refs in (asset_refs, evidence_refs)):
        raise StageProposalError("stage_proposal_reference_invalid")
    citation_resolution = None
    if "citation_selections" in raw:
        if modality != "text" or payload is None or evidence_refs or resolved is None:
            raise StageProposalError("stage_proposal_citation_form_invalid")
        catalog = ((resolved.get("context") or {}).get("boundary") or {}).get("items", [])
        payload, evidence_refs = resolve_proposal_citations(payload, raw["citation_selections"], catalog)
        citation_resolution = {"version": "text.proposal.citations.v1", "selector_hash": digest(raw["citation_selections"])}
    if payload is None:
        if modality == "video":
            payload = _video_plan(raw, planned_shots((resolved or {}).get("upstream")))
        elif modality != "text":
            raise StageProposalError("stage_proposal_candidate_invalid")
        else:
            title, markdown = _markdown(raw)
            converted = convert_legacy_text({"title": title, "markdown": markdown}, asset_refs=asset_refs, evidence_refs=evidence_refs)
            payload = converted["payload"]
            asset_refs, evidence_refs = converted["asset_refs"], converted["evidence_refs"]
    payload = canonical_master_payload(modality, payload, asset_refs, evidence_refs)
    payload_hash = digest(payload)
    candidate = {"candidate_id": f"candidate-{index:02d}-{payload_hash[:16]}", "payload_schema": schema,
                 "payload": payload, "payload_hash": payload_hash, "asset_refs": canonical(asset_refs),
                 "evidence_refs": canonical(evidence_refs)}
    if citation_resolution is not None:
        candidate["citation_resolution"] = citation_resolution
    # Alternative titles ride with the candidate for the user to swap in; the master keeps only the chosen title.
    alt_titles = [entry.strip()[:200] for entry in raw.get("alt_titles") or [] if isinstance(entry, str) and entry.strip()][:2]
    if modality == "text" and alt_titles:
        candidate["alt_titles"] = alt_titles
    return {**candidate, "candidate_hash": digest(candidate)}


def _run(provider, request):
    return asyncio.run(provider.generate_json(request))


def _validate_supplied_refs(candidate: dict, resolved: dict) -> None:
    context = resolved.get("context") or {}
    supplied = [context, context.get("master") or {}, *(resolved.get("upstream") or {}).values()]
    assets = {(item["material_revision_id"], item["content_hash"])
              for source in supplied for item in source.get("asset_refs", [])}
    assets.update((item["material_revision_id"], item["content_hash"]) for item in context.get("shared_asset_refs", []))
    evidence = {(item["item_id"], item["checksum"])
                for item in (context.get("boundary") or {}).get("items", [])}
    evidence.update((item["fact_pack_item_id"], item["snapshot_checksum"])
                    for source in supplied for item in source.get("evidence_refs", []))
    for ref in candidate["asset_refs"]:
        if (ref["material_revision_id"], ref.get("content_hash")) not in assets:
            raise StageProposalError("stage_proposal_foreign_ref")
    for ref in candidate["evidence_refs"]:
        if (ref["fact_pack_item_id"], ref.get("snapshot_checksum")) not in evidence:
            raise StageProposalError("stage_proposal_foreign_ref")


def build_master_request(resolved: dict) -> GenerateRequest:
    config = resolved.get("effective_config") or {}
    modality = master_modality(resolved)
    count = config.get("candidate_count", 3)
    length = config.get("length", "medium")
    if type(count) is not int or not 1 <= count <= MAX_CANDIDATES:
        raise StageProposalError("stage_proposal_count_invalid")
    if not isinstance(length, str) or length not in {"short", "medium", "long"}:
        raise StageProposalError("stage_proposal_length_invalid")
    parameters = {}
    if "temperature" in config:
        temperature = config["temperature"]
        if type(temperature) not in (int, float) or not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise StageProposalError("stage_proposal_temperature_invalid")
        parameters["temperature"] = temperature
    return GenerateRequest(
        purpose="generate", channel=(resolved.get("context") or {}).get("channel"),
        system_prompt=resolved["system_prompt"], user_prompt=resolved["effective_prompt"],
        schema_hint="stage.master.proposal.v1",
        context={"stage_schema": "stage.master.proposal.v1", "candidate_count": count,
                 "length": length, "modality": modality, "payload_schema": MASTER_SCHEMAS[modality]},
        max_tokens=((resolved.get("creative_configuration") or {}).get("chat_limits") or {}).get("max_tokens"),
        timeout_seconds=((resolved.get("creative_configuration") or {}).get("chat_limits") or {}).get("timeout_seconds"),
        **parameters,
    )


def build_text_request(resolved: dict) -> GenerateRequest:
    return build_master_request(resolved)


def execute_master_proposal(db, ctx, resolved: dict, user) -> dict:
    from .creation_recipes import _model, _model_projection

    config = resolved.get("effective_config") or {}
    modality = master_modality(resolved)
    request = build_master_request(resolved)
    from .creative_configuration import validate_execution
    validate_execution(db, resolved)
    model = resolved.get("model") or {}
    current, blockers = _model(config)
    if blockers or current != model:
        raise StageProposalError("stage_model_runtime_changed")
    actual = effective_llm_config(request.purpose, profile=model["profile_id"] if model["profile_id"] != "default" else None)
    if _model_projection(actual) != model:
        raise StageProposalError("stage_model_runtime_changed")
    route = {"provider": model["provider"], "model": model["model"], "profile": model["profile_id"],
             "configuration_revision": model.get("configuration_revision"), "runtime_hash": model["runtime_hash"]}
    provider = (MockProvider() if actual["provider"] == "mock" else OpenAICompatibleProvider(
        actual["base_url"], actual["api_key"], actual["model"],
        registered_provider=actual.get("registered_provider"), route_provenance=route,
    ))
    try:
        result = _run(provider, request)
    except Exception as exc:
        failure = provider_failure(exc)
        record_run(db, request, None, error=f"stage_provider_failed:{failure['reason']}:{failure['status'] or ''}", provider_name=provider.name,
                   model_name=model["model"], prompt_version="stage.master.propose.v1", route_provenance=route)
        error = StageProposalError("stage_provider_rejected" if failure["answered"] else "stage_provider_failed")
        error.failure = failure
        raise error from exc
    try:
        data = canonical(project_proposal_input(result.data, modality), max_bytes=MAX_OUTPUT_BYTES)
        if not isinstance(data, dict):
            raise StageProposalError("stage_proposal_output_invalid")
        raws = data.get("candidates") if isinstance(data.get("candidates"), list) else [data]
        if not 1 <= len(raws) <= MAX_CANDIDATES or len(raws) != request.context["candidate_count"]:
            raise StageProposalError("stage_proposal_count_invalid")
        candidates = [_candidate(item, index + 1, modality, resolved) for index, item in enumerate(raws)]
        for candidate in candidates:
            _validate_supplied_refs(candidate, resolved)
        output = canonical({"schema": "stage.master.proposal.v1", "candidates": candidates,
                            "candidate_count": len(candidates),
                            "input_hash": input_hash(request), "prompt_hash": resolved.get("prompt_hash"),
                            "model": {"provider": provider.name, "model": getattr(provider, "model", None) or model.get("model")}},
                           max_bytes=MAX_OUTPUT_BYTES)
    except Exception as exc:
        recorded = record_validated_stage_run(db, request, result, error="stage_proposal_output_invalid",
            provider_name=provider.name, model_name=getattr(provider, "model", None) or model.get("model"),
            prompt_version="stage.master.propose.v1", route_provenance=route)
        remember_validation_code(recorded, exc)
        if str(exc) == "stage_value_too_deep":
            recorded.usage_json = {**(recorded.usage_json or {}), "validation_shape": _shape(result.data)}
        raise StageProposalError("stage_proposal_output_invalid") from exc
    llm_run = record_validated_stage_run(db, request, result,
        validated_data={"schema": "stage.master.proposal.v1", "candidates": candidates},
        provider_name=provider.name, model_name=getattr(provider, "model", None) or model.get("model"),
        prompt_version="stage.master.propose.v1", route_provenance=route)
    output["llm_run_id"] = llm_run.id
    output["proposal_hash"] = digest(output)
    return output


def execute_text_proposal(db, ctx, resolved: dict, user) -> dict:
    return execute_master_proposal(db, ctx, resolved, user)


def _shape(value, depth: int = 0):
    """Key and type fingerprint only. String values stay out of the failure record."""
    if isinstance(value, dict):
        if depth >= 4:
            return {"type": "dict", "keys": len(value)}
        kept = {}
        for key in list(value)[:12]:
            if type(key) is str and re.fullmatch(r"[A-Za-z0-9_.:-]{1,40}", key):
                kept[key] = _shape(value[key], depth + 1)
        return kept
    if isinstance(value, list):
        return {"type": "list", "len": len(value), "first": _shape(value[0], depth + 1) if value and depth < 4 else None}
    if isinstance(value, str):
        return f"str:{min(len(value), 100000)}"
    return type(value).__name__
