"""Canonical Master proposals for the versioned Creation Recipe stage."""

from __future__ import annotations

import asyncio
import math

from .generation.providers import (
    GenerateRequest,
    MockProvider,
    OpenAICompatibleProvider,
    effective_llm_config,
    input_hash,
    record_run,
    record_validated_stage_run,
)
from .stage_contracts import canonical, digest
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
        if modality != "text":
            raise StageProposalError("stage_proposal_candidate_invalid")
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
        record_run(db, request, None, error="stage_provider_failed", provider_name=provider.name,
                   model_name=model["model"], prompt_version="stage.master.propose.v1", route_provenance=route)
        raise StageProposalError("stage_provider_failed") from exc
    try:
        data = canonical(result.data, max_bytes=MAX_OUTPUT_BYTES)
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
        record_validated_stage_run(db, request, result, error="stage_proposal_output_invalid",
            provider_name=provider.name, model_name=getattr(provider, "model", None) or model.get("model"),
            prompt_version="stage.master.propose.v1", route_provenance=route)
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
