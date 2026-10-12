"""Task 18.7 contract fixtures; no providers, rendered-output or aesthetic claims."""

import hashlib
import io
import json
import socket
from copy import deepcopy

import pytest
from fastapi import HTTPException
from PIL import Image

from app.config import get_settings
from app.models import (
    ContentMasterAssetRef,
    ContentMasterRevision,
    ContentPersona,
    ContentProject,
    ContentUnit,
    IdentitySnapshot,
    ProjectMaterialReference,
    User,
)
from app.services import asset_media, content_masters, graphic_composition, materials, stage_master_proposals
from app.services import studio_creative_catalog as catalog
from app.services.creative_artifacts import validate_artifact
from app.services.graphic_documents import GraphicDocumentError, canonical_payload, document_hash, validate_references
from app.services.graphic_master_checks import run_graphic_checks
from app.services.production_modalities import adapter_for, render_input_hash
from app.services.stage_contracts import digest


@pytest.fixture(autouse=True)
def local_only(monkeypatch, tmp_path):
    settings = get_settings()
    for key, value in {"app_env": "test", "llm_provider": "mock", "material_storage_backend": "local",
                       "minio_enabled": False}.items():
        monkeypatch.setattr(settings, key, value)
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("Graphic contract fixtures must not dispatch providers or connect to a network")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(stage_master_proposals, "_run", forbidden)


def _plan():
    return {
        "title": "本地图卡夹具", "aspect_ratio": "3:4",
        "cards": [
            {"id": "cover", "order": 0, "role": "cover", "title": "可验证的观察",
             "body": "这里是本地夹具，不对应外部事实。", "visual_type": "image", "material_revision_id": 101,
             "claims": [{"target": "body", "quote": "本地夹具", "fact_pack_item_id": 7}]},
            {"id": "details", "order": 1, "role": "body", "title": "保留具体细节",
             "body": "图卡保留明确的素材和引用。", "bullets": ["检查引用", "检查布局"],
             "visual_type": "image", "material_revision_id": 102},
        ],
    }


@pytest.fixture(params=[
    pytest.param("starter.ai-tech-engineer.v1", id="tech"),
    pytest.param("starter.lifestyle-observer.v1", id="lifestyle"),
])
def graphic_case(request):
    profile = deepcopy(catalog.BLUEPRINTS[request.param]["graphic_creative_profile"])
    return {
        "blueprint_key": request.param, "profile": profile, "preset_ref": profile["style_preset_ref"], "plan": _plan(),
        "assets": [{"material_revision_id": 101, "content_hash": "a" * 64, "kind": "image"},
                   {"material_revision_id": 102, "content_hash": "b" * 64, "kind": "image"}],
        "evidence": [{"item_id": 7, "checksum": "c" * 64}],
    }


def _compose(case, **kwargs):
    return graphic_composition.compose(case["plan"], preset_ref=case["preset_ref"],
                                       asset_catalog=case["assets"], evidence_catalog=case["evidence"], **kwargs)


def _resolved(case):
    package = catalog.load_skill("studio.graphic.layout-compose@1")
    return {
        "node": {"plugin": "stage.graphic.compose"}, "model": None,
        "method": {"skill_ref": "studio.graphic.layout-compose@1", "package_hash": package["package_hash"]},
        "context": {"modality": "graphic", "shared_asset_refs": deepcopy(case["assets"]),
                    "boundary": {"items": deepcopy(case["evidence"])}},
        "upstream": {"plan": {"output_schema": "graphic.card-plan.v1", "selected_content": deepcopy(case["plan"]),
                              "accepted_hash": digest(validate_artifact("graphic.card-plan.v1", case["plan"]))}},
        "effective_config": {"preset_ref": case["preset_ref"]},
        "resolution_hash": "d" * 64, "prompt_hash": "e" * 64,
    }


@pytest.mark.parametrize("aspect, dimensions", [
    ("1:1", (1080, 1080)), ("4:3", (1440, 1080)), ("3:4", (1080, 1440)),
    ("16:9", (1920, 1080)), ("9:16", (1080, 1920)),
])
def test_composition_is_canonical_deterministic_and_keeps_stable_ids(graphic_case, aspect, dimensions):
    graphic_case["plan"]["aspect_ratio"] = aspect
    before = deepcopy(graphic_case)
    first = _compose(graphic_case)
    reordered = deepcopy(graphic_case)
    reordered["plan"]["cards"].reverse()
    reordered["assets"].reverse()
    reordered["plan"] = dict(reversed(list(reordered["plan"].items())))
    assert first == _compose(reordered) == _compose(deepcopy(graphic_case))
    assert graphic_case == before
    payload = first["payload"]
    assert first["payload_schema"] == "graphic.master.v2"
    assert payload == canonical_payload(payload)
    assert adapter_for("graphic", "graphic.master.v2").validate_payload(payload) == []
    assert document_hash(payload) == hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest() == first["quality"]["payload_hash"]
    assert first["composition"]["plan_hash"] == digest(validate_artifact("graphic.card-plan.v1", before["plan"]))
    assert first["composition"]["preset_hash"] == catalog.digest(catalog.PRESETS[graphic_case["preset_ref"]])
    assert first["composition"]["density"] == catalog.PRESETS[graphic_case["preset_ref"]]["config"]["density"]
    assert [canvas["id"] for canvas in payload["canvases"]] == ["cover", "details"]
    for canvas, card in zip(payload["canvases"], before["plan"]["cards"], strict=True):
        assert (canvas["width"], canvas["height"]) == dimensions
        assert canvas["role"] == card["role"]
        ids = [layer["id"] for layer in canvas["layers"]]
        assert ids == (["cover-accent", "cover-title", "cover-visual", "cover-body"] if card["order"] == 0 else
                       ["details-accent", "details-title", "details-visual", "details-body",
                        "details-bullet-0", "details-bullet-1"])
        assert len(ids) == len(set(ids))
        title = next(layer for layer in canvas["layers"] if layer["id"] == f"{card['id']}-title")
        assert "".join(run["text"] for run in title["runs"]) == card["title"]
        assert all(24 <= layer["x"] and 24 <= layer["y"] and
                   layer["x"] + layer["width"] <= canvas["width"] - 24 and
                   layer["y"] + layer["height"] <= canvas["height"] - 24 for layer in canvas["layers"])
    assert first["quality"]["status"] == "pass"
    assert first["quality"]["issues"] == []
    assert first["quality"]["coverage"] == {
        "geometry": "axis_aligned", "text_fit": "estimated", "bytes": "not_rendered",
        "contrast": "text_vs_solid_canvas_only", "aesthetic_quality": "human_review_required",
    }
    assert first["quality"]["human_review_required"] is True
    assert "render_asset_ref" not in payload


@pytest.mark.parametrize("template", ["editorial", "split", "cards"])
@pytest.mark.parametrize("density", ["low", "medium", "high"])
def test_build_proposal_consumes_template_density_and_binds_exact_canonical_candidate(graphic_case, template, density):
    resolved = _resolved(graphic_case)
    resolved["effective_config"].update(template=template, density=density)
    before = deepcopy(resolved)
    first = graphic_composition.build_proposal(resolved)
    assert first == graphic_composition.build_proposal(deepcopy(resolved))
    assert resolved == before
    assert first["schema"] == "stage.master.proposal.v1"
    assert first["candidate_count"] == len(first["candidates"]) == 1
    assert first["llm_run_id"] is first["model"] is None
    assert first["input_hash"] == digest({"resolution_hash": resolved["resolution_hash"],
        "accepted_plan_hash": resolved["upstream"]["plan"]["accepted_hash"],
        "tool_package_hash": resolved["method"]["package_hash"]})
    assert first["prompt_hash"] == resolved["prompt_hash"]
    candidate = first["candidates"][0]
    composed = _compose(graphic_case, template=template, density=density)
    for key in ("payload_schema", "payload", "asset_refs", "evidence_refs"):
        assert candidate[key] == composed[key]
    assert candidate["payload_hash"] == document_hash(candidate["payload"])
    assert candidate["candidate_id"] == f"candidate-01-{candidate['payload_hash'][:16]}"
    assert candidate["candidate_hash"] == digest({k: v for k, v in candidate.items() if k != "candidate_hash"})
    assert first["proposal_hash"] == digest({k: v for k, v in first.items() if k != "proposal_hash"})

    def layers(payload, canvas_id):
        return {layer["id"]: layer for canvas in payload["canvases"] if canvas["id"] == canvas_id
                for layer in canvas["layers"]}

    templates = {key: _compose(graphic_case, template=key, density=density)["payload"]
                 for key in ("editorial", "split", "cards")}
    assert len({document_hash(payload) for payload in templates.values()}) == 3
    editorial, split = (layers(templates[key], "cover") for key in ("editorial", "split"))
    assert editorial["cover-visual"]["height"] == 403
    assert split["cover-visual"]["height"] == 461
    assert split["cover-body"]["y"] - editorial["cover-body"]["y"] == 58
    for key, spacing in (("editorial", 24), ("split", 24), ("cards", 32)):
        detail = layers(templates[key], "details")
        left, right = detail["details-bullet-0"], detail["details-bullet-1"]
        assert right["y"] - (left["y"] + left["height"]) == pytest.approx(spacing)
    densities = {key: _compose(graphic_case, template=template, density=key)["payload"]
                 for key in ("low", "medium", "high")}
    assert len({document_hash(payload) for payload in densities.values()}) == 3
    for key, size in (("low", 38), ("medium", 34), ("high", 30)):
        detail = layers(densities[key], "details")
        for lid in ("details-body", "details-bullet-0", "details-bullet-1"):
            assert detail[lid]["runs"][0]["style"]["font_size"] == size
            assert detail[lid]["height"] == pytest.approx(size * 1.4)
    assert layers(densities["low"], "details")["details-bullet-1"]["y"] > layers(
        densities["medium"], "details")["details-bullet-1"]["y"] > layers(
        densities["high"], "details")["details-bullet-1"]["y"]
    changed = deepcopy(resolved)
    changed["upstream"]["plan"]["selected_content"]["cards"][0]["title"] = "另一个明确标题"
    changed["upstream"]["plan"]["accepted_hash"] = digest(changed["upstream"]["plan"]["selected_content"])
    second = graphic_composition.build_proposal(changed)
    assert first["input_hash"] != second["input_hash"]
    assert candidate["payload_hash"] != second["candidates"][0]["payload_hash"]
    assert candidate["candidate_id"] != second["candidates"][0]["candidate_id"]
    assert first["proposal_hash"] != second["proposal_hash"]


@pytest.mark.parametrize("template", ["editorial", "split", "cards"])
@pytest.mark.parametrize("density", ["low", "medium", "high"])
def test_graphic_tunables_flow_through_frozen_stage_and_real_resolver(
        db_session, graphic_case, template, density):
    from types import SimpleNamespace

    from app.services import creative_configuration, stage_resolver, starter_personas
    from app.services.content_harness.nodes import bootstrap_builtin_nodes
    from app.services.content_harness.registry import registry

    bootstrap_builtin_nodes()
    node = starter_personas._definition("graphic", graphic_case["blueprint_key"])["nodes"][2]
    saved_config = deepcopy(node["config"])
    override = {"template": template, "density": density}
    contract = registry.descriptor("node", node["plugin"], node["plugin_version"]).stage_contract
    context = {
        "modality": "graphic",
        "identity": {"content": {"graphic_creative_profile": deepcopy(graphic_case["profile"])}},
        "shared_asset_refs": deepcopy(graphic_case["assets"]),
        "boundary": {"items": deepcopy(graphic_case["evidence"])},
    }
    upstream = {"plan": {
        "output_schema": "graphic.card-plan.v1", "selected_content": deepcopy(graphic_case["plan"]),
        "accepted_hash": digest(validate_artifact("graphic.card-plan.v1", graphic_case["plan"])),
    }}
    effective_node, method, creative, blockers = creative_configuration.frozen_stage(
        db_session, SimpleNamespace(id=1), SimpleNamespace(id=1, project_id=1, modality="graphic"),
        node, contract, context, override)
    assert not blockers, blockers
    assert node["config"] == saved_config
    resolved = stage_resolver.resolve_stage(
        workflow={"id": 1, "version": 1, "checksum": "c" * 64}, node=effective_node,
        contract=contract, context=context, upstream=upstream, method=method, model=None,
        override=override, creative=creative)
    assert resolved["ready"], resolved["blockers"]
    assert resolved["override"] == override
    assert resolved["effective_config"]["template"] == template
    assert resolved["effective_config"]["density"] == density
    proposal = graphic_composition.build_proposal(resolved)
    assert proposal["composition"]["template"] == template
    assert proposal["composition"]["density"] == density
    assert proposal["candidates"][0]["payload_hash"] == document_hash(proposal["candidates"][0]["payload"])


@pytest.mark.parametrize("invalid, reason", [
    ("preset_version", "creative_resource_ref_unavailable"),
    ("preset_format", "creative_resource_ref_invalid"),
    ("preset_modality", "graphic_composition_preset_invalid"),
    ("missing_asset", "graphic_composition_asset_not_supplied"),
    ("asset_kind", "graphic_composition_asset_kind_mismatch"),
    ("conflicting_asset", "graphic_composition_conflicting_asset_hash"),
    ("missing_evidence", "graphic_composition_claim_unproven"),
    ("claim_target", "graphic_composition_claim_target_invalid"),
    ("text_overflow", "graphic_composition_text_overflow"),
    ("pixel_plan", "stage_config_unknown_field"),
    ("template", "graphic_composition_preset_invalid"),
    ("density", "graphic_composition_density_invalid"),
    ("model", "graphic_composition_stage_invalid"),
    ("method", "graphic_composition_method_invalid"),
    ("package", "graphic_composition_tool_changed"),
    ("unaccepted_plan", "graphic_composition_one_accepted_plan_required"),
    ("multiple_plans", "graphic_composition_one_accepted_plan_required"),
])
def test_invalid_presets_assets_and_proposal_bindings_fail_closed(graphic_case, invalid, reason):
    if invalid in {"template", "density"}:
        with pytest.raises(ValueError, match=f"^{reason}$"):
            _compose(graphic_case, **{invalid: "unsupported"})
        return
    if invalid in {"model", "method", "package", "unaccepted_plan", "multiple_plans"}:
        resolved = _resolved(graphic_case)
        if invalid == "model":
            resolved["model"] = {"provider": "mock", "model": "unused"}
        elif invalid == "method":
            resolved["method"]["skill_ref"] = "studio.graphic.qc@1"
        elif invalid == "package":
            resolved["method"]["package_hash"] = "f" * 64
        elif invalid == "unaccepted_plan":
            resolved["upstream"]["plan"]["selected_content"] = None
        else:
            resolved["upstream"]["duplicate"] = deepcopy(resolved["upstream"]["plan"])
        with pytest.raises(ValueError, match=f"^{reason}$"):
            graphic_composition.build_proposal(resolved)
        return
    if invalid == "preset_version":
        graphic_case["preset_ref"] = graphic_case["preset_ref"].replace("@1", "@99")
    elif invalid == "preset_format":
        graphic_case["preset_ref"] = "warm-magazine"
    elif invalid == "preset_modality":
        graphic_case["preset_ref"] = "studio.text.deep-technical@1"
    elif invalid == "missing_asset":
        graphic_case["assets"] = graphic_case["assets"][1:]
    elif invalid == "asset_kind":
        graphic_case["assets"][0]["kind"] = "chart"
    elif invalid == "conflicting_asset":
        graphic_case["assets"].append({**graphic_case["assets"][0], "content_hash": "f" * 64})
    elif invalid == "missing_evidence":
        graphic_case["evidence"] = []
    elif invalid == "claim_target":
        graphic_case["plan"]["cards"][0]["claims"][0]["target"] = "missing-layer"
    elif invalid == "text_overflow":
        graphic_case["plan"]["cards"][1]["body"] = "长" * 1200
    else:
        graphic_case["plan"]["cards"][0]["x"] = 72
    with pytest.raises(ValueError, match=f"^{reason}$"):
        _compose(graphic_case)


@pytest.mark.parametrize("preset, visual, reason", [
    ("studio.graphic.warm-magazine@1", "none", "graphic_composition_requested_photo_missing"),
    ("studio.graphic.documentary-photo@1", "diagram", "graphic_composition_requested_photo_missing"),
    ("studio.graphic.technical-editorial@1", "diagram", "graphic_composition_shape_fallback_unavailable"),
    ("studio.graphic.architecture-diagram@1", "diagram", None),
    ("studio.graphic.lifestyle-cards@1", "diagram", None),
    ("studio.graphic.technical-editorial@1", "none", None),
])
def test_required_photos_and_declared_shape_only_fallback(preset, visual, reason):
    plan = _plan()
    for card in plan["cards"]:
        card["visual_type"] = visual
        card.pop("material_revision_id")
        card.pop("claims", None)
        if visual == "diagram":
            card["diagram_nodes"] = ["输入", "输出"]
    if reason:
        with pytest.raises(ValueError, match=f"^{reason}$"):
            graphic_composition.compose(plan, preset_ref=preset)
    else:
        result = graphic_composition.compose(plan, preset_ref=preset)
        assert result["quality"]["status"] == "pass"
        assert result["asset_refs"] == []
        assert not any(layer["type"] in {"image", "chart"}
                       for canvas in result["payload"]["canvases"] for layer in canvas["layers"])
        if visual == "diagram":
            assert any(layer["id"] == "cover-node-0" for layer in result["payload"]["canvases"][0]["layers"])


@pytest.mark.parametrize("mutation, status, reason", [
    ("left_margin", "blocker", "graphic_minimum_margin"),
    ("right_bound", "blocker", "graphic_minimum_margin"),
    ("overflow", "blocker", "graphic_estimated_text_overflow"),
    ("overlap", "blocker", "graphic_text_overlap"),
    ("contrast", "blocker", "graphic_low_contrast"),
    ("small_type", "warning", "graphic_small_type"),
    ("alpha", "warning", "graphic_contrast_unmeasured"),
    ("hidden", "pass", None),
])
def test_geometry_qc_detects_bounds_fit_overlap_and_supported_contrast(graphic_case, mutation, status, reason):
    payload = _compose(graphic_case)["payload"]
    canvas = payload["canvases"][0]
    title = next(layer for layer in canvas["layers"] if layer["id"] == "cover-title")
    title["x"] = 24
    assert graphic_composition.geometry_quality(payload)["status"] == "pass"
    before_hash = document_hash(payload)
    if mutation == "left_margin":
        title["x"] = 23
    elif mutation == "right_bound":
        title["x"] = canvas["width"] - title["width"] - 23
    elif mutation == "overflow":
        title["height"] = 10
    elif mutation == "overlap":
        body = next(layer for layer in canvas["layers"] if layer["id"] == "cover-body")
        body["y"] = title["y"]
    elif mutation == "contrast":
        title["runs"][0]["style"]["color"] = canvas["background"]["color"]
    elif mutation == "small_type":
        title["runs"][0]["style"]["font_size"] = 23
    elif mutation == "alpha":
        title["runs"][0]["style"]["color"] += "80"
    else:
        title.update(x=-100, y=-100, height=1, visible=False)
    before = deepcopy(payload)
    report = graphic_composition.geometry_quality(payload)
    assert payload == before
    assert report["status"] == status
    assert report["payload_hash"] == document_hash(payload) != before_hash
    assert {issue["reason"] for issue in report["issues"]} == ({reason} if reason else set())
    if reason:
        assert all(issue["canvas_id"] == "cover" and issue["layer_id"] == "cover-title"
                   for issue in report["issues"])
    assert report["human_review_required"] is True


@pytest.mark.parametrize("mutation", ["none", "quality_hash", "preset_hash", "hidden_photo", "cover_role"])
def test_actual_graphic_structure_checks_use_exact_persona_profiles(graphic_case, mutation):
    result = _compose(graphic_case)
    profile = graphic_case["profile"]
    ref = profile["quality_profile_ref"]
    persona = {"ref": ref, "hash": catalog.digest(catalog.QUALITY[ref]),
               "style_preset_ref": graphic_case["preset_ref"],
               "style_preset_hash": catalog.digest(catalog.PRESETS[graphic_case["preset_ref"]])}
    if mutation == "quality_hash":
        persona["hash"] = "f" * 64
    elif mutation == "preset_hash":
        persona["style_preset_hash"] = "f" * 64
    elif mutation == "hidden_photo":
        next(layer for layer in result["payload"]["canvases"][0]["layers"]
             if layer["type"] == "image")["visible"] = False
    elif mutation == "cover_role":
        result["payload"]["canvases"][0]["role"] = "body"
    master = ContentMasterRevision(payload_schema="graphic.master.v2", payload_json=result["payload"])
    checks = run_graphic_checks(None, master, {"assets": result["asset_refs"], "evidence": result["evidence_refs"]},
                               {"graphic_structure": {"metadata": {"persona_quality": persona}}})
    status, report = checks["graphic_structure"]
    if mutation in {"quality_hash", "preset_hash"}:
        assert status == "incomplete"
        assert report["reasons"] == ["graphic_persona_quality_unavailable"]
    else:
        qc = report["persona_quality"]["report"]
        expected = ({"graphic_studio_canvas_contract"} if mutation == "cover_role" else
                    {"graphic_requested_photo_missing"} if mutation == "hidden_photo" and
                    graphic_case["preset_ref"] == "studio.graphic.warm-magazine@1" else set())
        assert status == ("blocker" if expected else "pass")
        assert {issue["reason"] for issue in qc["issues"]} == expected
        assert qc["payload_hash"] == document_hash(result["payload"])
        assert qc["human_review_required"] is True
        assert report["coverage"]["live_bytes_rights"] == "separate_required_render_rights_checks"


@pytest.mark.parametrize("mutation", [
    "none", "missing_asset", "duplicate_asset", "wrong_revision", "wrong_slot", "wrong_canvas",
    "missing_evidence", "duplicate_evidence", "wrong_checksum", "wrong_range",
])
def test_graphic_refs_preserve_exact_asset_placements_and_claim_ranges(graphic_case, mutation):
    result = _compose(graphic_case)
    assets, evidence = result["asset_refs"], result["evidence_refs"]
    assert assets == [
        {"material_revision_id": revision, "content_hash": content_hash, "role": "graphic_layer",
         "slot_key": f"{cid}-visual", "sort_order": index, "placement": {"canvas_id": cid, "layer_id": f"{cid}-visual"}}
        for index, (cid, revision, content_hash) in enumerate([("cover", 101, "a" * 64), ("details", 102, "b" * 64)])
    ]
    assert evidence == [{"fact_pack_item_id": 7, "snapshot_checksum": "c" * 64, "role": "claim", "sort_order": 0,
                         "locator": {"canvas_id": "cover", "layer_id": "cover-body", "start": 3, "end": 7}}]
    body = next(layer for layer in result["payload"]["canvases"][0]["layers"] if layer["id"] == "cover-body")
    assert "".join(run["text"] for run in body["runs"])[3:7] == "本地夹具"
    if mutation == "missing_asset":
        assets.pop()
    elif mutation == "duplicate_asset":
        assets.append(deepcopy(assets[0]))
    elif mutation == "wrong_revision":
        assets[0]["material_revision_id"] = 999
    elif mutation == "wrong_slot":
        assets[0]["slot_key"] = "details-visual"
    elif mutation == "wrong_canvas":
        assets[0]["placement"]["canvas_id"] = "details"
    elif mutation == "missing_evidence":
        evidence.clear()
    elif mutation == "duplicate_evidence":
        evidence.append(deepcopy(evidence[0]))
    elif mutation == "wrong_checksum":
        evidence[0]["snapshot_checksum"] = "f" * 64
    elif mutation == "wrong_range":
        evidence[0]["locator"]["end"] = 8
    if mutation == "none":
        assert validate_references(result["payload"], assets, evidence) is None
    else:
        reason = "graphic_asset_placement_mismatch" if mutation in {
            "missing_asset", "duplicate_asset", "wrong_revision", "wrong_slot", "wrong_canvas",
        } else "graphic_evidence_locator_mismatch"
        with pytest.raises(GraphicDocumentError, match=f"^{reason}$"):
            validate_references(result["payload"], assets, evidence)


def _assert_local_render_checks(db_session, master, user, persona, profile, mutation):
    from app.services.material_storage import provider

    snapshot = IdentitySnapshot(owner_user_id=user.id, persona_id=persona.id,
        effective_profile_json={"graphic_creative_profile": profile}, checksum=digest(profile))
    db_session.add(snapshot)
    db_session.flush()
    master.identity_snapshot_id = snapshot.id
    document = deepcopy(master.payload_json)
    declarations, outputs, revisions, refs = [], [], [], []
    for index, canvas in enumerate(document["canvases"]):
        content = io.BytesIO()
        Image.new("RGB", (canvas["width"], canvas["height"]), (index * 40, 80, 120)).save(content, format="PNG")
        material = materials.create_material(db_session, kind="image", title="Synthetic render contract fixture")
        revision = materials.create_revision(db_session, material, content=content.getvalue(), suffix=".png",
            declared_mime="image/png", public_use_allowed=True, width=canvas["width"], height=canvas["height"])
        revisions.append(revision)
        assert revision.content_hash == hashlib.sha256(content.getvalue()).hexdigest()
        ref = ContentMasterAssetRef(master_revision_id=master.id, material_revision_id=revision.id,
            role="render_output", slot_key=canvas["id"], sort_order=index, placement_json={"canvas_id": canvas["id"]},
            rights_snapshot_json={"public_use_allowed": True}, content_hash_snapshot=revision.content_hash)
        db_session.add(ref)
        refs.append(ref)
        declarations.append({"canvas_id": canvas["id"], "material_revision_id": revision.id})
        outputs.append({"canvas_id": canvas["id"], "material_revision_id": revision.id, "content_hash": revision.content_hash})
    document["render_asset_ref"] = declarations
    master.payload_json = canonical_payload(document)
    master.payload_hash = document_hash(document)
    master.edit_summary_json = {"render_attestation": {"origin": "manual", "confirmed": True,
        "attested_by": user.email, "render_input_hash": render_input_hash(db_session, master), "outputs": outputs}}
    db_session.flush()
    adapter = adapter_for("graphic", "graphic.master.v2")
    rendered = adapter.build_render_snapshot(db_session, master)
    assert rendered["status"] == "ready"
    assert rendered["canvas_dimensions_verified"] is True
    assert [output["content_hash"] for output in rendered["outputs"]] == [revision.content_hash for revision in revisions]
    assert all(output["mime_type"] == "image/png" for output in rendered["outputs"])
    for canvas, revision in zip(document["canvases"], revisions, strict=True):
        with Image.open(io.BytesIO(materials.read_bytes_checked(db_session, revision, require_public=True))) as image:
            assert image.size == (canvas["width"], canvas["height"])
    revision = revisions[0]
    if mutation == "render_dimensions":
        content = io.BytesIO()
        Image.new("RGB", (revision.width - 1, revision.height), "blue").save(content, format="PNG")
        provider().put("fixtures/wrong-dimensions.png", content.getvalue())
        revision.file_path = "fixtures/wrong-dimensions.png"
        revision.content_hash = hashlib.sha256(content.getvalue()).hexdigest()
        refs[0].content_hash_snapshot = revision.content_hash
        outputs[0]["content_hash"] = revision.content_hash
        master.edit_summary_json = {"render_attestation": {**master.edit_summary_json["render_attestation"],
                                                          "outputs": deepcopy(outputs)}}
        reason = "render_canvas_dimensions_mismatch"
    elif mutation == "render_hash":
        provider().put("fixtures/changed-render.png", materials.read_bytes_checked(db_session, revision) + b"changed")
        revision.file_path = "fixtures/changed-render.png"
        reason = "render_bytes_unverified"
    else:
        revision.mime_type = "image/jpeg"
        reason = "render_mime_invalid"
    db_session.flush()
    blocked = adapter.build_render_snapshot(db_session, master)
    assert blocked["status"] == "incomplete"
    assert blocked["reasons"] == [reason]


@pytest.mark.parametrize("mutation, status_code", [
    ("public_rights", 422), ("revoked", 422), ("archived", 422), ("material_archived", 422),
    ("reference_hash", 422), ("changed_bytes", 409), ("missing_bytes", 404),
    ("render_dimensions", None), ("render_hash", None), ("render_mime", None),
])
def test_live_rights_local_bytes_and_render_dimensions_hash_mime(graphic_case, db_session, tmp_path, mutation, status_code):
    assert db_session.get_bind().url.database in {None, "", ":memory:"}
    user = User(email="graphic-fixture@studio.test", name="Fixture", role="editor")
    db_session.add(user)
    db_session.flush()
    persona = ContentPersona(owner_user_id=user.id, name="Local fixture")
    project = ContentProject(owner_user_id=user.id, title="Graphic fixture")
    db_session.add_all([persona, project])
    db_session.flush()
    unit = ContentUnit(project_id=project.id, persona_id=persona.id, modality="graphic", title="Fixture")
    db_session.add(unit)
    content = io.BytesIO()
    Image.new("RGB", (16, 16), "blue").save(content, format="PNG")
    material = materials.create_material(db_session, kind="image", title="Synthetic local PNG")
    revision = materials.create_revision(db_session, material, content=content.getvalue(), suffix=".png",
        declared_mime="image/png", rights_status="cleared", public_use_allowed=True, model_use_allowed=False)
    db_session.add(ProjectMaterialReference(project_id=project.id, material_revision_id=revision.id, origin="user"))
    db_session.commit()
    for card in graphic_case["plan"]["cards"]:
        card["material_revision_id"] = revision.id
        card.pop("claims", None)
    graphic_case["assets"] = [{"material_revision_id": revision.id, "content_hash": revision.content_hash, "kind": "image"}]
    result = _compose(graphic_case)
    request = {k: deepcopy(result[k]) for k in ("payload_schema", "payload", "asset_refs", "evidence_refs")}
    request["idempotency_key"] = "initial"
    saved = content_masters.save_revision(db_session, project_id=project.id, unit_id=unit.id, user=user, payload=request)
    assert saved["payload_hash"] == document_hash(result["payload"])
    assert [ref["content_hash"] for ref in saved["assets"]] == [revision.content_hash] * 2
    assert all(ref["rights_snapshot"]["public_use_allowed"] is True for ref in saved["assets"])
    inputs = {"assets": deepcopy(result["asset_refs"]), "edit_summary": {}}
    assert content_masters._rights_check(db_session, inputs) == ("pass", {"reasons": []})
    if mutation.startswith("render_"):
        _assert_local_render_checks(db_session, db_session.get(ContentMasterRevision, saved["id"]),
                                    user, persona, graphic_case["profile"], mutation)
        return
    if mutation == "public_rights":
        revision.public_use_allowed = False
    elif mutation in {"revoked", "archived"}:
        revision.status = mutation
    elif mutation == "material_archived":
        material.status = "archived"
    elif mutation == "reference_hash":
        for ref in request["asset_refs"]:
            ref["content_hash"] = "f" * 64
        inputs["assets"] = deepcopy(request["asset_refs"])
    elif mutation == "changed_bytes":
        from app.services.material_storage import provider
        provider().put("fixtures/tampered.png", content.getvalue() + b"changed")
        revision.file_path = "fixtures/tampered.png"
    else:
        revision.file_path = "fixtures/missing.png"
    db_session.flush()
    request.update(idempotency_key="after-live-change", expected_revision=1)
    with pytest.raises(HTTPException) as error:
        content_masters.save_revision(db_session, project_id=project.id, unit_id=unit.id, user=user, payload=request)
    assert error.value.status_code == status_code
    status, report = content_masters._rights_check(db_session, inputs)
    assert status == "blocker"
    assert set(report["reasons"]) == {f"asset_unready:{revision.id}"}
    assert db_session.query(ContentMasterRevision).count() == 1
    assert (tmp_path / revision.file_path).is_file() is (mutation != "missing_bytes")
