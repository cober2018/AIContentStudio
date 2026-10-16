"""Pure exact request preparation shared by Preview and the invocation gate."""

import copy
import json
import re

from fastapi import HTTPException

from .stage_contracts import StageContractError, canonical, digest


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
    for key in metadata["input_contract"].get("required_context", []):
        if not context.get(key):
            blockers.append(f"{key}_required")
    if method and method.get("source_kind") not in metadata["method_sources"]:
        raise StageContractError("stage_method_source_unsupported")
    sections = []
    prompt_identity = context.get("identity")
    prompt_creative = creative
    if creative is not None and creative.get("production_stage"):
        # Raw profile history contains disabled instructions; only the manifest is task input.
        prompt_identity = copy.deepcopy(prompt_identity)
        if prompt_identity and isinstance(prompt_identity.get("content"), dict):
            prompt_identity["content"] = {key: value for key, value in prompt_identity["content"].items()
                                          if not key.endswith("_creative_profile")}
        prompt_creative = {key: value for key, value in creative.items()
                           if key not in {"profile", "method_stack"}}
    values = (
        ("method", method.get("instruction", "") if method else ""),
        ("identity", prompt_identity),
        ("stage_instruction", effective.get("instruction", "")),
        ("execution_controls", {
            key: effective.get(key) for key in metadata["tunable_fields"] if key != "instruction"
        }),
        ("brief", context.get("brief")), ("intent", context.get("intent")),
        ("evidence", context.get("boundary")), ("upstream", upstream), ("task_override", override),
    )
    if creative is not None:
        values = (*values, ("persona_creative_configuration", prompt_creative))
    if context.get("knowledge_context") is not None:
        values = (*values, ("selected_knowledge_and_style", context["knowledge_context"]))
    if "shared_asset_refs" in context:
        values = (*values, ("project_shared_assets", {"exact_refs": context["shared_asset_refs"],
            "coverage": context.get("shared_assets_coverage"),
            "rule": "Use only supplied exact MaterialRevision IDs/hashes; unavailable photos must not be invented."}))
    for key, value in values:
        value = canonical(value)
        text = value if type(value) is str else json.dumps(value, ensure_ascii=False, sort_keys=True,
                                                          separators=(",", ":")) if value else ""
        sections.append({"key": key, "text": text, "hash": digest(value)})
    prompt = "\n\n".join(f"[{item['key']}]\n{item['text']}" for item in sections if item["text"])
    output_contract = dict(metadata["output_contract"])
    if node.get("plugin") == "stage.master.propose" and context.get("modality") == "text":
        from .text_documents import TEXT_PAYLOAD_SCHEMA, proposal_response_schema

        output_contract.update(payload_schema=TEXT_PAYLOAD_SCHEMA,
            response_schema=proposal_response_schema(effective["candidate_count"]),
            reference_rules=[
                "Block IDs are unique; list item IDs are unique within each list; citation IDs are unique.",
                "Copy only supplied exact asset IDs/content hashes and FactPackItem IDs/snapshot checksums.",
                "For new citations return citation_selections: id, block_id, optional list_item_id, quote, fact_pack_item_id.",
                "quote must occur exactly once in its text block/list item; use only supplied FactPackItem IDs.",
                "With citation_selections keep document.citations and evidence_refs empty; the service derives exact offsets/hashes/refs.",
                "Never calculate or invent selected_text_hash; pre-existing canonical citations still require exact matching evidence_refs.",
                "Every image/chart requires its exact asset_ref; omit unproven references, not invent them.",
                "Do not return Markdown/ProseMirror JSON or server-owned candidate/provenance hashes.",
            ])
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
            output_contract["content_rule"] = "Every candidate.content MUST match the supplied content_schema; do not return it as a wrapper."
        preset = (creative or {}).get("style_preset") or {}
        preset_config = preset.get("config") or {}
        if (effective["output_schema"] in {"graphic.visual-direction.v1", "graphic.card-plan.v1"}
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
    result = canonical({
        "schema": "resolved.stage.execution.v1", "workflow": workflow,
        "node": {key: node.get(key) for key in ("id", "kind", "plugin", "plugin_version", "stage_schema")},
        "stage_contract_hash": digest(metadata), "base_config": base, "base_config_hash": digest(base),
        "override": override, "effective_config": effective, "config_hash": digest(effective),
        "context": context, "context_hash": digest(context), "upstream": upstream, "method": method, "model": model,
        "prompt_sections": sections, "effective_prompt": prompt, "system_prompt": system_prompt,
        "prompt_hash": digest({"system": system_prompt, "user": prompt}),
        "output_contract": output_contract, "blockers": sorted(set(blockers)),
        "ready": not blockers,
    })
    if creative is not None:
        result["creative_configuration"] = canonical(creative)
    result["resolution_hash"] = digest(result)
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
