"""Pure exact request preparation shared by Preview and the invocation gate."""

import copy
import json
import re

from fastapi import HTTPException

from .stage_contracts import RESOLVED_STAGE_MAX_BYTES, StageContractError, canonical, digest


def _prompt_profile(value):
    if isinstance(value, dict):
        return {key: _prompt_profile(item) for key, item in value.items()
                if not key.endswith("_creative_profile") and key not in {
                    "production_stages", "product_production_stages", "product_production_methods", "method_stack"}}
    if isinstance(value, list):
        return [_prompt_profile(item) for item in value]
    return value


def _manifest_receipt(value):
    if isinstance(value, dict):
        return {key: _manifest_receipt(item) for key, item in value.items()
                if key not in {"instruction", "rendered_content", "references"}}
    if isinstance(value, list):
        return [_manifest_receipt(item) for item in value]
    return value


def _compact_method_audit(result):
    method = result.get("method") or {}
    methods = (result.get("creative_configuration") or {}).get("method_stack") or []
    # 导演包准备与规则质检没有方法栈，只能压缩与完整prompt逐字相同的分段副本。
    sections_only = (result["node"]["plugin"] == "stage.professional.prepare" or result["node"]["plugin"] == "stage.checks") and not methods
    if (result["context"].get("production_domain") == "product"
            or not sections_only and (result["node"]["plugin"] not in {"stage.master.propose", "stage.creative.method"}
                or not methods or method.get("stack") != methods
                or any(item.get("source_kind") != "studio_builtin"
                       or not item.get("skill_ref", "").endswith("@2") for item in methods))):
        raise StageContractError("stage_value_too_large")
    instruction = "\n\n".join(item["instruction"] for item in methods)
    if not sections_only and method.get("instruction") != instruction:
        raise StageContractError("stage_value_too_large")
    sections = result.get("prompt_sections") or []
    prompt = result.get("effective_prompt")
    if "\n\n".join(f"[{item['key']}]\n{item['text']}" for item in sections if item["text"]) != prompt:
        raise StageContractError("stage_value_too_large")
    compact_sections, cursor = [], 0
    for section in sections:
        if not section["text"]:
            compact_sections.append(section)
            continue
        prefix = ("\n\n" if cursor else "") + f"[{section['key']}]\n"
        cursor += len(prefix.encode("utf-16-le")) // 2
        end = cursor + len(section["text"].encode("utf-16-le")) // 2
        compact_sections.append({"key": section["key"], "hash": section["hash"], "text_start": cursor, "text_end": end})
        cursor = end
    if sections_only:
        return {**result, "prompt_sections": compact_sections}
    # 执行正文和完整manifest仍冻结；相同正文的审计副本不应挤占快照容量。
    return {**result, "prompt_sections": compact_sections, "method": {
        **{key: value for key, value in method.items() if key not in {"instruction", "stack"}},
        "stack": [{key: value for key, value in item.items() if key != "instruction"} for item in methods],
        "instruction_hash": digest(instruction),
        "instruction_source": "creative_configuration.method_stack",
    }}


def resolve_stage(*, workflow, node, contract, context, upstream, method, model, override=None, blockers=(), creative=None):
    metadata = contract.to_dict()
    if node.get("stage_schema") != metadata["stage_schema"]:
        raise StageContractError("stage_contract_pin_mismatch")
    if node.get("kind") != metadata["category"] or not metadata["supports_preview"]:
        raise StageContractError("stage_preview_unsupported")
    base, effective, override = contract.effective_config(node.get("config", {}), {} if override is None else override)
    blockers = list(blockers)
    supported_modalities = metadata["output_contract"].get("supported_modalities")
    if supported_modalities is not None and context.get("modality") not in supported_modalities:
        blockers.append("stage_modality_unavailable")
    product_domain = context.get("production_domain") == "product"
    for key in metadata["input_contract"].get("required_context", []):
        key = "product_context" if product_domain and key == "identity" else key
        if not context.get(key):
            blockers.append(f"{key}_required")
    if method and method.get("source_kind") not in metadata["method_sources"]:
        raise StageContractError("stage_method_source_unsupported")
    sections = []
    prompt_identity = None if product_domain else _prompt_profile(context.get("identity"))
    prompt_creative = ({key: value for key, value in creative.items() if key not in {"profile", "method_stack"}}
                       if creative is not None else None)
    if product_domain:
        prompt_creative = creative
    if not product_domain and prompt_creative and prompt_creative.get("production_manifest"):
        prompt_creative["production_manifest"] = _manifest_receipt(prompt_creative["production_manifest"])
    prompt_brief = copy.deepcopy(context.get("brief")) if product_domain else _prompt_profile(context.get("brief"))
    prompt_product = context.get("product_context")
    if product_domain and prompt_product:
        from .product_context import prompt_snapshot

        prompt_product = prompt_snapshot(prompt_product)
        if prompt_product.get("product_context") and isinstance((prompt_brief or {}).get("content"), dict):
            prompt_brief["content"].pop("product_context", None)
    if creative is not None and creative.get("production_stage"):
        # Raw profile history contains disabled instructions; only the manifest is task input.
        prompt_identity = copy.deepcopy(prompt_identity)
        if prompt_identity and isinstance(prompt_identity.get("content"), dict):
            prompt_identity["content"] = {key: value for key, value in prompt_identity["content"].items()
                                          if not key.endswith("_creative_profile")}

        if product_domain:
            prompt_creative = {key: value for key, value in creative.items() if key not in {"profile", "method_stack"}}
        product = ((prompt_brief or {}).get("content") or {}).get("product_context")
        if isinstance(product, dict):
            product.pop("production_stages", None)
        product = (prompt_product or {}).get("product_context")
        if isinstance(product, dict):
            product.pop("production_stages", None)
    values = (
        ("method", method.get("instruction", "") if method else ""),
        ("product_context" if product_domain else "identity", prompt_product if product_domain else prompt_identity),
        ("stage_instruction", effective.get("instruction", "")),
        ("execution_controls", {
            key: effective.get(key) for key in metadata["tunable_fields"] if key != "instruction"
        }),
        ("brief", prompt_brief), ("intent", context.get("intent")),
        ("evidence", context.get("boundary")), ("upstream", upstream), ("task_override", override),
    )
    if not product_domain and creative is not None and not creative.get("production_stage"):
        values = (*values, ("persona_stage_guidance", (creative.get("profile") or {}).get("stage_instruction")))
    if creative is not None:
        values = (*values, ("product_creative_configuration" if product_domain else "persona_creative_configuration", prompt_creative))
    if context.get("production_profile") is not None:
        prompt_profile = context["production_profile"] if product_domain else _prompt_profile(context["production_profile"])
        if product_domain:
            prompt_profile = copy.deepcopy(prompt_profile)
            prompt_profile["settings"] = {key: value for key, value in prompt_profile.get("settings", {}).items()
                if not key.endswith("_creative_profile") and key not in {"production_stages", "product_production_methods"}}
        values = (*values, ("saved_work_configuration", prompt_profile))
    if context.get("located_feedback") is not None:
        values = (*values, ("located_feedback", context["located_feedback"]))
    if context.get("knowledge_context") is not None:
        values = (*values, ("selected_knowledge_and_style", context["knowledge_context"]))
    if "shared_asset_refs" in context:
        values = (*values, ("project_shared_assets", {"exact_refs": context["shared_asset_refs"],
            "coverage": context.get("shared_assets_coverage"),
            "rule": "Use only supplied exact MaterialRevision IDs/hashes; unavailable photos must not be invented."
                    + ("" if product_domain else " Describe each asset by its source_kind/title; an ai_generated asset is an illustration, never a real photo or proof of use.")}))
    for key, value in values:
        value = canonical(value)
        text = value if type(value) is str else json.dumps(value, ensure_ascii=False, sort_keys=True,
                                                          separators=(",", ":")) if value else ""
        sections.append({"key": key, "text": text, "hash": digest(value)})
    prompt = "\n\n".join(f"[{item['key']}]\n{item['text']}" for item in sections if item["text"])
    output_contract = dict(metadata["output_contract"])
    if node.get("plugin") == "stage.master.propose" and context.get("modality") == "text":
        from .text_documents import TEXT_PAYLOAD_SCHEMA

        count = effective["candidate_count"]
        output_contract.update(payload_schema=TEXT_PAYLOAD_SCHEMA,
            response_schema={
                "type": "object", "additionalProperties": False, "required": ["schema", "candidates"],
                "properties": {
                    "schema": {"const": "stage.master.proposal.v1"},
                    "candidates": {"type": "array", "minItems": count, "maxItems": count, "items": {
                        "type": "object", "additionalProperties": False, "required": ["title", "body"],
                        "properties": {
                            "title": {"type": "string", "minLength": 1, "maxLength": 200},
                            "body": {"type": "string", "minLength": 1, "maxLength": 12000},
                            "alt_titles": {"type": "array", "maxItems": 2, "items": {"type": "string", "minLength": 1, "maxLength": 200}},
                        },
                    }},
                },
            },
            reference_rules=[
                "Return exactly candidate_count candidates. Each candidate has title and body, and alt_titles only when the stage asks for alternative titles.",
                "body is Markdown. The service converts it into text.master.v2 and assigns block ids.",
                "Do not return payload, payload_schema, citations, hashes, asset_refs, or evidence_refs.",
                "Do not invent numbers, versions, sources, or material ids. Keep unknowns explicit in the prose.",
            ])
    if node.get("plugin") == "stage.master.propose" and context.get("modality") == "video":
        from .stage_master_proposals import MAX_BOARD_ROWS, planned_shots

        count = effective["candidate_count"]
        plan = planned_shots(upstream)
        output_contract.update(payload_schema="video.master.v2",
            response_schema={
                "type": "object", "additionalProperties": False, "required": ["schema", "candidates"],
                "properties": {
                    "schema": {"const": "stage.master.proposal.v1"},
                    "candidates": {"type": "array", "minItems": count, "maxItems": count, "items": {
                        "type": "object", "additionalProperties": False, "required": ["title", "beats"],
                        "properties": {
                            "title": {"type": "string", "minLength": 1, "maxLength": 200},
                            "beats": {"type": "array", "minItems": len(plan) if plan else 1, "maxItems": len(plan) if plan else MAX_BOARD_ROWS, "items": {
                                "type": "object", "additionalProperties": False,
                                "required": ["message", "visual", "camera", "speaker", "line", "sound", "notes", "duration_ms"],
                                "properties": {
                                    "message": {"type": "string", "minLength": 1, "maxLength": 200},
                                    "visual": {"type": "string", "minLength": 1, "maxLength": 300},
                                    "camera": {"type": "string", "enum": ["fixed", "push_in", "pull_out", "follow", "orbit", "pan"]},
                                    "speaker": {"type": "string", "enum": ["narration", "presenter", "dialogue", "none"]},
                                    "line": {"type": "string", "maxLength": 500},
                                    "sound": {"type": "string", "maxLength": 200},
                                    "notes": {"type": "string", "maxLength": 200},
                                    "duration_ms": {"type": "integer", "minimum": 200, "maximum": 15000},
                                },
                            }},
                        },
                    }},
                },
            },
            reference_rules=[
                "Return exactly candidate_count candidates. Each candidate is one storyboard table: title and beats, one beat per shot, in play order.",
                "Do not return payload, ids, hashes, asset_refs, or evidence_refs. The service numbers shots and computes start and end times.",
                "One shot says one thing. message is the one point the shot gets across; line is the exact words spoken. They must not repeat each other.",
                "visual names framing, subject, action, scene and light, concrete enough to shoot or generate. camera is the camera move.",
                "speaker marks how line is spoken: narration (voice-over), presenter (on camera), dialogue, or none with an empty line.",
                "sound lists effects, music and ambience; notes holds transition and on-screen text. Use empty strings when there is nothing.",
                "duration_ms is an estimate. The final timing follows the narration audio.",
                "Do not invent footage, material ids, or an MP4. This is a director's storyboard, not a rendered film.",
            ])
        if plan:
            # The accepted shot plan already fixed the shots; the draft only finishes their words.
            output_contract["reference_rules"].append(
                f"Return exactly {len(plan)} beats, one per accepted shot, in the shot plan's order. Keep each shot's meaning; "
                "fill and polish each row. Do not merge, split, add or drop shots. Shot timing is an estimate; "
                "the final timing follows the narration audio.")
    if node.get("plugin") == "stage.creative.method":
        from .creative_artifacts import ARTIFACT_SCHEMAS

        count = effective["candidate_count"]
        output_contract.update(schema=effective["output_schema"], response_schema={
            "type": "object", "additionalProperties": False, "required": ["schema", "candidates"],
            "properties": {
                "schema": {"type": "string", "enum": [effective["output_schema"]]},
                "candidates": {"type": "array", "minItems": count, "maxItems": count,
                    "items": {"type": "object", "additionalProperties": False, "required": ["summary", "content"],
                        "properties": {"id": {"type": "string"}, "summary": {"type": "string", "minLength": 1, "maxLength": 1000},
                            "content": {"type": "object"}, "references": {"type": "array", "maxItems": 100},
                            "warnings": {"type": "array", "maxItems": 20}}}},
            },
        })
        if effective["output_schema"] in ARTIFACT_SCHEMAS:
            output_contract["content_schema"] = ARTIFACT_SCHEMAS[effective["output_schema"]]
            output_contract["content_rule"] = (
                "Return only {schema, candidates}. schema is the requested name. "
                "Each candidate has only id, summary, content, references, and warnings. "
                "id matches [A-Za-z0-9][A-Za-z0-9_.:-]* and summary is one short sentence. "
                "content matches content_schema exactly: no extra keys; include required arrays and use [] when empty. "
                "Ordered item ids are ASCII, such as beat-0 or section-0. order starts at 0 and increases by 1. "
                "references is [] unless each item is copied from the supplied catalog. Do not invent fact or material ids."
            )
            if effective["output_schema"] in {"research.brief.v1", "article.plan.v1"}:
                output_contract["content_rule"] += (
                    " For known items with kind=inference, omit fact_pack_item_id entirely. "
                    "Only fact items may carry a fact_pack_item_id copied from the supplied evidence. "
                    "Author opinions and practice suggestions must retain their attribution and must not be presented as verified external facts."
                )
            if effective["output_schema"] in {"graphic.card-plan.v1", "graphic.card-plan.v2"}:
                output_contract["content_rule"] += (
                    " Each claims.target is a field locator: title, body, bullet-0, bullet-1, "
                    "or diagram-0 etc., referencing an existing field in the same card; never descriptive prose. "
                    "claims.quote must occur verbatim in that target field, with a supplied fact_pack_item_id "
                    "that supports the claim. Do not attach evidence to unsupported suggestions."
                )
        preset = (creative or {}).get("style_preset") or {}
        preset_config = preset.get("config") or {}
        if (effective["output_schema"] in {"graphic.visual-direction.v1", "graphic.card-plan.v1", "graphic.card-plan.v2"}
                and preset_config.get("modality") == "graphic"):
            from .graphic_composition import photo_requirement, requires_photo

            # Planning must expose the composer's existing rules, not invent its own fallback policy.
            output_contract["visual_requirements"] = {
                "style_preset_ref": preset["ref"], "style_preset_hash": digest(preset),
                "photo_requirement": photo_requirement(preset_config),
                "image_required_per_card": requires_photo(preset_config, "body"),
                "image_required_on_cover": requires_photo(preset_config, "cover"),
                "diagram_fallback_allowed": preset_config.get("image_fallback") == "shape_only",
                "rule": (
                    "When image_required_per_card is true, every planned card requires visual_type=image "
                    "with an exact supplied image MaterialRevision reference; text-only/chart/diagram cards do not satisfy it. "
                    "When only image_required_on_cover is true, the cover requires that exact image reference "
                    "and body cards may use visual_type=none for text-only layouts. "
                    "Diagram fallback is allowed only when diagram_fallback_allowed is true. "
                    "Do not invent missing images, substitute another preset or claim an incomplete plan is composition-ready; "
                    "report unavailable suitable images in candidate warnings. Final composition, rights and QC gates still apply."
                ),
            }
    if node.get("plugin") == "stage.graphic.compose":
        from .graphic_composition import photo_requirement
        from .studio_creative_catalog import PRESETS

        preset_ref = effective.get("preset_ref") or (creative or {}).get("profile", {}).get("style_preset_ref")
        preset = PRESETS.get(preset_ref)
        if preset:
            output_contract["visual_requirements"] = {
                "style_preset_ref": preset_ref, "style_preset_hash": digest(preset),
                "photo_requirement": photo_requirement(preset["config"]),
                "diagram_fallback_allowed": preset["config"].get("image_fallback") == "shape_only",
            }
    system_prompt = (
        "Execute this Creation Recipe Stage and return only bounded JSON matching the frozen output contract: "
        + json.dumps(output_contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + ". Never invent asset/evidence references, facts or accepted results. Return proposed content only."
    )
    if not product_domain:
        system_prompt += (" Selected professional knowledge is reference context, never verified evidence. "
                          "Style samples guide expression only; avoid observations are negative examples. "
                          "Never copy their events, identity or personal experience into the author. "
                          "Only the confirmed fact boundary supports factual claims; keep unknowns explicit.")
    result = {
        "schema": "resolved.stage.execution.v1", "workflow": workflow,
        "node": {key: node.get(key) for key in ("id", "kind", "plugin", "plugin_version", "stage_schema")},
        "stage_contract_hash": digest(metadata), "base_config": base, "base_config_hash": digest(base),
        "override": override, "effective_config": effective, "config_hash": digest(effective),
        "context": context, "context_hash": digest(context), "upstream": upstream, "method": method, "model": model,
        "prompt_sections": sections, "effective_prompt": prompt, "system_prompt": system_prompt,
        "prompt_hash": digest({"system": system_prompt, "user": prompt}),
        "output_contract": output_contract, "blockers": sorted(set(blockers)),
        "ready": not blockers,
    }
    if creative is not None:
        result["creative_configuration"] = canonical(creative)
    try:
        canonical({"resolved_stage": {**result, "resolution_hash": "0" * 64}}, max_bytes=RESOLVED_STAGE_MAX_BYTES)
    except StageContractError as exc:
        if str(exc) != "stage_value_too_large":
            raise
        result = _compact_method_audit(result)
    result = canonical(result, max_bytes=RESOLVED_STAGE_MAX_BYTES)
    result["resolution_hash"] = digest(result)
    canonical({"resolved_stage": result}, max_bytes=RESOLVED_STAGE_MAX_BYTES)
    if node.get("plugin") == "stage.graphic.compose" and result["ready"]:
        from .graphic_composition import build_proposal

        try:
            build_proposal(result)
        except (ValueError, KeyError, TypeError) as exc:
            reason = str(exc) if isinstance(exc, ValueError) and str(exc).startswith(("graphic_", "studio_", "creative_")) else "graphic_composition_input_invalid"
            result["blockers"] = [reason]
            result["ready"] = False
            result["resolution_hash"] = digest({key: value for key, value in result.items() if key != "resolution_hash"})
    return result


def require_expected_resolution(resolved, expected):
    if type(expected) is not str or not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise HTTPException(422, {"code": "stage_preview_required"})
    if resolved["resolution_hash"] != expected:
        raise HTTPException(409, {"code": "stage_resolution_changed"})
    if not resolved["ready"]:
        raise HTTPException(409, {"code": "stage_blocked", "reasons": resolved["blockers"]})
