"""Shot-bound website work and professional edit packages reuse the execution domain."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CreativeExecution, CreativeExecutionOutput, User
from .creative_contracts import canonical_hash

TRANSFER_POLICY = {"schema": "creative.media-transfer.v1", "max_file_bytes": 512 * 1024 * 1024,
                   "max_total_bytes": 4 * 1024 * 1024 * 1024, "max_concurrent_transfers": 1}
WEBSITES = {"grok": "https://grok.com/", "gemini": "https://gemini.google.com/"}


def _fail(code: str, status: int = 422):
    raise HTTPException(status, {"code": code})


def read_reference_image(db: Session, project_id: int, unit_id: int, revision_id: int,
                         content_hash: str, user: User, *, package_id: int | None = None) -> tuple[bytes, str]:
    from . import creative_packages as packages
    from .content_masters import owned_unit
    from .materials import read_bytes_checked

    owned_unit(db, project_id, unit_id, user)
    ref = {"material_revision_id": revision_id, "content_hash": content_hash}
    if package_id is not None:
        package = packages.owned_package(db, project_id, unit_id, package_id, user, current=True)
        handoff = package.package_json.get("web_video") or {}
        if (handoff.get("reference_material_revision_id") != revision_id
                or not any(asset.get("material_revision_id") == revision_id and asset.get("content_hash") == content_hash
                           for asset in package.package_json["assets"])):
            _fail("web_video_reference_image_mismatch", 409)
    material = packages._check_asset(db, project_id, ref)
    if material.material.kind != "image" or not str(material.mime_type or "").startswith("image/"):
        _fail("web_video_reference_image_required")
    return read_bytes_checked(db, material), material.mime_type


def source_asset_refs(projection: dict, handoff: dict | None) -> list[dict]:
    if handoff is None:
        return projection["assets"]
    # These are analysis references, separate from the one image sent to the website.
    for dependency in handoff.get("continuity_references", []):
        if not any(ref.get("role") == "shot_reference"
                   and ref.get("slot_key") == dependency["shot_id"]
                   and ref.get("material_revision_id") == dependency["material_revision_id"]
                   and ref.get("content_hash") == dependency["content_hash"]
                   for ref in projection["assets"]):
            _fail("web_video_continuity_reference_stale", 409)
    revision = handoff.get("reference_material_revision_id")
    return [ref for ref in projection["assets"] if ref["role"] == "shot_reference"
            and ref.get("slot_key") == handoff["shot_id"] and ref["material_revision_id"] == revision]


def build_web_handoff(source: dict, shot_id: str, *, new_execution: bool = False) -> dict:
    if source.get("payload_schema") != "video.master.v2":
        _fail("web_video_requires_video_master")
    document = source["content"]
    shot = next((s for s in document["shots"] if s["id"] == shot_id), None)
    production = (shot or {}).get("production", {})
    if production.get("source_mode") != "web_video" or production.get("web_provider") not in WEBSITES:
        _fail("web_video_saved_shot_configuration_required")
    if new_execution and (production.get("schema") != "video.shot-production.v2"
            or not production.get("reference_material_revision_id") or not production.get("prompt", "").strip()
            or (production.get("prompt_reference") or {}).get("revision_id") != production.get("reference_material_revision_id")):
        _fail("web_video_confirmed_image_prompt_required")
    if shot["duration_ms"] > production["requested_generation_duration_ms"]:
        _fail("web_video_generation_shorter_than_use")
    handoff = {"schema": "web.video-shot.v1", "shot_id": shot_id,
            "source_master_revision_id": source["id"], "source_payload_hash": source["payload_hash"],
            "provider": production["web_provider"], "website": WEBSITES[production["web_provider"]],
            "mode": "image_to_video" if production.get("reference_material_revision_id") else "text_to_video",
            "prompt": production["prompt"], "prompt_hash": canonical_hash(production["prompt"]),
            "reference_material_revision_id": production.get("reference_material_revision_id"),
            "aspect_ratio": document["aspect_ratio"], "use_duration_ms": shot["duration_ms"],
            "requested_generation_duration_ms": production["requested_generation_duration_ms"],
            "audio_intent": production["audio_intent"], "max_generation_submissions": 1,
            "runtime_verified": False}
    if production.get("continuity_reference"):
        from .video_documents import VideoDocumentError, validate_continuity_dependencies

        try:
            validate_continuity_dependencies(document["shots"])
        except VideoDocumentError as exc:
            _fail(str(exc))
        by_id = {item["id"]: item for item in document["shots"]}
        dependencies = []
        current = shot
        while reference := (current.get("production") or {}).get("continuity_reference"):
            previous = by_id[reference["shot_id"]]
            if new_execution and (previous.get("production") or {}).get("reference_material_revision_id") != reference["material_revision_id"]:
                _fail("web_video_continuity_reference_stale", 409)
            dependencies.append({"from_shot_id": current["id"], **reference})
            current = previous
        handoff["continuity_references"] = dependencies
        handoff["continuity_model_input"] = False
    if production.get("schema") == "video.shot-production.v2":
        handoff["prompt_reference"] = production.get("prompt_reference")
    return handoff


def validate_new_web_package(package: dict) -> None:
    """New work requires image-bound confirmation; historical package reads stay valid."""
    handoff = package["web_video"]
    source = package["source"]
    rebuilt = build_web_handoff(source, handoff["shot_id"], new_execution=True)
    if any(handoff.get(key) != value for key, value in rebuilt.items()):
        _fail("web_video_package_integrity", 409)
    reference = handoff.get("prompt_reference") or {}
    assets = package["assets"]
    if (handoff.get("mode") != "image_to_video" or len(assets) != 1
            or assets[0].get("material_revision_id") != reference.get("revision_id")
            or assets[0].get("content_hash") != reference.get("content_hash")
            or not str(assets[0].get("mime_type", "")).startswith("image/")):
        _fail("web_video_prompt_reference_stale")


def role(role_id: str, kind: str, mime: str, *, maximum: int | None = None) -> dict:
    return {"role_id": role_id, "kind": kind, "required": True, "allowed_mime": [mime],
            "min_count": 1, "max_count": 1,
            "max_bytes": maximum or (TRANSFER_POLICY["max_file_bytes"] if kind in {"video", "other"} else 30 * 1024 * 1024)}


def edit_contract(document: dict) -> dict:
    post = document.get("postproduction")
    if not post:
        _fail("video_saved_postproduction_required")
    missing = [f"镜头 {shot['order'] + 1}" for shot in sorted(document["shots"], key=lambda item: item["order"]) if not shot.get("source_material_revision_id")]
    if not document["shots"] or missing:
        # Naming the shots lets the user fill exactly those slots; everything else keeps working meanwhile.
        raise HTTPException(422, {"code": "video_edit_shot_sources_missing", "missing_shots": missing})
    phase = post["phase"]
    roles = [role("rough_cut" if phase == "rough_cut" else "final", "video", "video/mp4"),
             role("resolve_project", "other", "application/x-resolve-project"),
             role("edit_manifest", "other", "application/json", maximum=2 * 1024 * 1024)]
    if document["voice"]["mode"] != "none" or document["subtitles"]["cues"]:
        roles.append(role("subtitles", "other", "application/x-subrip", maximum=2 * 1024 * 1024))
    if post["ae_shot_ids"]:
        roles.append(role("ae_project", "other", "application/x-after-effects-project"))
        for comp in post["ae_compositions"]:
            intermediate = role(comp["role_id"], "video", "video/quicktime" if comp["alpha_required"] else "video/mp4")
            if not comp["alpha_required"]:
                intermediate["allowed_mime"] = ["video/mp4", "video/quicktime"]
            roles.append(intermediate)
    # Optional: a separate publish cover, exported to 导出/封面.
    roles.append({**role("cover", "image", "image/jpeg"), "required": False, "min_count": 0, "allowed_mime": ["image/jpeg", "image/png"]})
    return {"roles": roles, "media_transfer_policy": dict(TRANSFER_POLICY)}


def validate_parent(db: Session, project_id: int, unit_id: int, document: dict, owner_id: int) -> None:
    post = document.get("postproduction") or {}
    if "parent_output_id" not in post:
        return
    output = db.get(CreativeExecutionOutput, post["parent_output_id"])
    execution = db.get(CreativeExecution, output.execution_id) if output else None
    if (not output or not execution or (execution.project_id, execution.content_unit_id, execution.owner_user_id) != (project_id, unit_id, owner_id)
            or output.state != "accepted" or output.kind != "video"
            or output.content_hash != post["parent_output_hash"]
            or output.material_revision_id != post["parent_material_revision_id"]):
        _fail("video_feedback_parent_mismatch", 409)


def _prepare(db: Session, project_id: int, unit_id: int, payload: dict, user: User, *, edit: bool) -> dict:
    from . import creative_executions as executions
    from . import creative_packages as packages
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user, mutate=True)
    master_id = payload["source_master_revision_id"]
    source, _projection, _master = packages._source(db, project_id, unit_id, user, master_id=master_id, variant_id=None, current=True)
    if source.payload_schema != "video.master.v2":
        _fail("web_video_requires_video_master")
    mode = "codex" if edit else payload.get("execution_mode", "manual")
    if mode not in {"codex", "manual"}:
        _fail("web_video_executor_invalid")
    executor = {"executor_kind": "agent" if mode == "codex" else "human",
                "executor_key": "codex-video-production" if mode == "codex" else "manual-web-video", "executor_version": "1"}
    key = payload["idempotency_key"]
    previous = db.scalar(select(CreativeExecution).where(CreativeExecution.owner_user_id == user.id, CreativeExecution.idempotency_key == key))
    if previous:
        execution = executions.get_execution(db, project_id, unit_id, previous.id, user)
        package = packages.owned_package(db, project_id, unit_id, previous.package_id, user, current=True)
        if (package.source_master_revision_id != master_id or previous.executor_key != executor["executor_key"]
                or (package.package_schema == "director.video.v1") != edit
                or (not edit and package.package_json.get("web_video", {}).get("shot_id") != payload["shot_id"])):
            _fail("creative_execution_idempotency_conflict", 409)
    else:
        if not edit and mode != "manual":
            _fail("web_video_manual_generation_required")
        if edit:
            if source.payload_json.get("capture_plan"):
                from .content_masters import capture_status
                state = capture_status(db, source)
                if not state or not state["ready_to_shoot"] or any(value != "current" for value in state.get("adoptions", {}).values()):
                    _fail("capture_edit_requires_current_review", 409)
            validate_parent(db, project_id, unit_id, source.payload_json, user.id)
            contract = edit_contract(source.payload_json)
        else:
            contract = {"roles": [role("clip", "video", "video/mp4")], "media_transfer_policy": dict(TRANSFER_POLICY)}
        body = {"source_master_revision_id": master_id,
                "package_schema": "director.video.v1" if edit else "creative.execution.v1",
                "objective": "达芬奇主剪、AE按需制作" if edit else f"网页生成分镜 {payload['shot_id']}",
                "output_contract": contract,
                "acceptance_criteria": ["真实文件经检查和明确接受；不自动更改主稿或发布", "保留精确来源和全部素材/工程依赖"]}
        if not edit:
            body["web_video_shot_id"] = payload["shot_id"]
        package_result = packages.create_package(db, project_id=project_id, unit_id=unit_id, user=user, payload=body)
        execution = executions.prepare_execution(db, project_id, unit_id,
            {**executor, "package_id": package_result["id"], "idempotency_key": key,
             "metadata": {"summary": "等待Codex领取" if mode == "codex" else "人工网页制作，回传前核对生成结果"}}, user)
        package = packages.owned_package(db, project_id, unit_id, package_result["id"], user, current=True)
    package_view = packages.package_projection(db, package, user)
    return {"execution": execution, "package": package_view,
            "instructions": (f"使用 video-production-handoff Skill，通过MCP领取 project={project_id} unit={unit_id} execution={execution['id']} package_hash={package.package_hash}；达芬奇主剪、AE按需制作；素材用原始路径（只读），小样 / 成片导出到项目的 导出/小样 或 导出/成片，其他文件放 工作/<作品>/任务{execution['id']}/，交付时给绝对路径；平台只用MCP或命令行REST。"
                             if edit else manual_instructions(package.package_json, execution["id"])),
            "website": (package.package_json.get("web_video") or {}).get("website")}


def manual_instructions(package: dict, execution_id: int) -> str:
    handoff = package["web_video"]
    document = package["source"]["content"]
    shot = next(item for item in document["shots"] if item["id"] == handoff["shot_id"])
    block = next((item for item in document["script"]["blocks"] if item["id"] == shot.get("script_block_id")), None)
    reference = handoff.get("reference_material_revision_id")
    reference_asset = next((item for item in package["assets"] if item["material_revision_id"] == reference), None)
    return "\n".join([
        f"人工网页视频任务 #{execution_id} / 镜头 {handoff['shot_id']}",
        f"网站：{handoff['website']}；模式：{handoff['mode']}",
        f"冻结主稿：#{handoff['source_master_revision_id']} / {handoff['source_payload_hash']}",
        f"分镜文案：{block['text'] if block else shot.get('purpose') or shot.get('label') or '未关联文案'}",
        f"视频动作 / 运镜提示词：{handoff['prompt']}",
        f"画幅：{handoff['aspect_ratio'][0]}:{handoff['aspect_ratio'][1]}；期望生成：{handoff['requested_generation_duration_ms'] / 1000:g}秒；剪辑使用：{handoff['use_duration_ms'] / 1000:g}秒",
        "声音：" + ("保留原片声音并审阅" if handoff["audio_intent"] == "keep" else "剪辑时静音，使用统一旁白"),
        f"参考图：MaterialRevision #{reference} / {reference_asset['content_hash']}" if reference_asset else "参考图：无，文生视频",
        ("请先下载并上传上述精确图片，再人工粘贴视频动作提示词、核对网页参数并生成，下载原始MP4后回传此任务。" if reference_asset else "历史文生视频任务：人工粘贴冻结提示词、核对参数；不要以此创建新的无图任务。") + "网页实际不支持的参数请如实记录，不冒称已验证。",
        "同一任务最多提交一次；失败或结果不明先核对原任务，不自动重新生成。回传后预览并明确接受，再选用并保存主稿。",
    ])


def prepare_web(db: Session, project_id: int, unit_id: int, payload: dict, user: User) -> dict:
    return _prepare(db, project_id, unit_id, payload, user, edit=False)


def prepare_edit(db: Session, project_id: int, unit_id: int, payload: dict, user: User) -> dict:
    return _prepare(db, project_id, unit_id, payload, user, edit=True)


def list_tasks(db: Session, project_id: int, unit_id: int, user: User, limit: int = 20, offset: int = 0) -> dict:
    from ..models import CreativeExecutionPackage
    from . import creative_executions as executions
    from . import creative_packages as packages
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    if type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or not 0 <= offset <= 10000:
        _fail("web_video_pagination_invalid")
    rows = db.scalars(select(CreativeExecution).join(CreativeExecutionPackage, CreativeExecutionPackage.id == CreativeExecution.package_id)
        .where(CreativeExecution.owner_user_id == user.id, CreativeExecution.project_id == project_id,
               CreativeExecution.content_unit_id == unit_id,
               CreativeExecutionPackage.package_json["web_video"]["schema"].as_string() == "web.video-shot.v1")
        .order_by(CreativeExecution.id.desc()).offset(offset).limit(limit)).all()
    items = []
    for row in rows:
        package = packages.owned_package(db, project_id, unit_id, row.package_id, user)
        projected = packages.package_projection(db, package, user)
        items.append({"execution": executions.get_execution(db, project_id, unit_id, row.id, user),
                      "web_video": package.package_json["web_video"], "instructions": manual_instructions(package.package_json, row.id), "package_id": row.package_id,
                      "is_current": projected["is_current"]})
    return {"items": items, "limit": limit, "offset": offset}


def validate_edit_manifest(package: dict, body: dict) -> None:
    import re

    from .creative_contracts import bounded_json

    post = (package.get("director") or {}).get("postproduction")
    if post is None:
        return
    if not isinstance(body, dict):
        _fail("video_edit_manifest_invalid")
    bounded_json(body, max_bytes=2 * 1024 * 1024)
    source = package["source"]
    document = source["content"]
    if (body.get("schema") != "video.edit-manifest.v1" or body.get("source_master_revision_id") != source["id"]
            or body.get("source_payload_hash") != source["payload_hash"] or body.get("phase") != post["phase"]
            or body.get("fps") != post["fps"] or body.get("resolution") != post["resolution"]):
        _fail("video_edit_manifest_source_mismatch")
    assets = body.get("assets")
    expected = {item["material_revision_id"]: item["content_hash"] for item in package["assets"]}
    if not isinstance(assets, list) or len(assets) != len(expected):
        _fail("video_edit_manifest_assets_mismatch")
    seen = set()
    for asset in assets:
        if not isinstance(asset, dict):
            _fail("video_edit_manifest_assets_mismatch")
        revision = asset.get("material_revision_id")
        # The original file on the drive materialize_inputs named; the revision and hash are what bind it.
        path = asset.get("path")
        if (type(revision) is not int or revision in seen or revision not in expected
                or asset.get("content_hash") != expected[revision] or not isinstance(path, str)
                or not path.startswith("/") or len(path) > 1000):
            _fail("video_edit_manifest_assets_mismatch")
        seen.add(revision)
    timeline = body.get("timeline")
    shots = {shot["id"]: shot for shot in document["shots"]}
    if not isinstance(timeline, list) or not 1 <= len(timeline) <= 1000:
        _fail("video_edit_manifest_timeline_invalid")
    spans = {item["shot_id"]: (item["start_ms"], item["end_ms"]) for track in document["timeline"]["tracks"]
             for item in track["items"] if "shot_id" in item}
    placements = [item for track in document["timeline"]["tracks"] if track["kind"] == "video"
                  for item in track["items"] if "material_revision_id" in item]
    present = set()
    for item in timeline:
        if not isinstance(item, dict) or item.get("shot_id") not in shots:
            _fail("video_edit_manifest_timeline_invalid")
        shot = shots[item["shot_id"]]
        start, end = item.get("start_ms"), item.get("end_ms")
        trim_start, trim_end = item.get("trim_start_ms"), item.get("trim_end_ms")
        revision = item.get("material_revision_id")
        # A shot may be cut from several clips, each one placed inside the shot on the Master timeline.
        span = spans.get(shot["id"])
        placed = span is not None and type(trim_start) is int and type(trim_end) is int and any(
            p["material_revision_id"] == revision and span[0] <= p["start_ms"] < span[1]
            and p.get("trim_start_ms", trim_start) <= trim_start and trim_end <= p.get("trim_end_ms", trim_end)
            for p in placements)
        if (revision != shot.get("source_material_revision_id") and not placed
                or any(type(n) is not int for n in (start, end, trim_start, trim_end))
                or not 0 <= start < end <= document["timeline"]["duration_ms"]
                or not 0 <= trim_start < trim_end or trim_end - trim_start < end - start
                or item.get("audio_intent") != (shot.get("production") or {}).get("audio_intent", "mute")):
            _fail("video_edit_manifest_timeline_invalid")
        if document.get("capture_plan"):
            from .content_masters import _real_capture_shot
            from .video_documents import capture_content_hash
            if _real_capture_shot(document, shot) and not any(
                take["state"] == "usable" and take["material_revision_id"] == item["material_revision_id"]
                and take["task_content_hash"] == capture_content_hash(document, "task")
                and take.get("trim_start_ms", -1) <= trim_start < trim_end <= take.get("trim_end_ms", -1)
                for take in shot.get("capture_takes", [])
            ):
                _fail("capture_edit_manifest_outside_reviewed_range")
        composition = next((comp for comp in post["ae_compositions"] if comp["shot_id"] == shot["id"]), None)
        if composition and item.get("composition_role") != composition["role_id"]:
            _fail("video_edit_manifest_ae_missing")
        present.add(shot["id"])
    if present != shots.keys():
        _fail("video_edit_manifest_shot_missing")
    hashes = body.get("output_hashes")
    roles = [role for role in package["output_contract"]["roles"] if role["role_id"] != "edit_manifest"]
    required = {role["role_id"] for role in roles if role["required"]}
    # Optional roles (the cover) may be listed when handed in; required ones must always be.
    if (not isinstance(hashes, dict) or not required <= set(hashes) <= {role["role_id"] for role in roles}
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes.values())):
        _fail("video_edit_manifest_output_hashes_invalid")
    readbacks = body.get("project_reopen")
    for tool in ("resolve", "ae") if post["ae_shot_ids"] else ("resolve",):
        check = readbacks.get(tool) if isinstance(readbacks, dict) else None
        if (not isinstance(check, dict) or check.get("verified") is not True or type(check.get("missing_media")) is not int
                or check["missing_media"] != 0 or not isinstance(check.get("tool_version"), str) or not check["tool_version"]
                or not isinstance(check.get("observation_hash"), str) or not re.fullmatch(r"[0-9a-f]{64}", check["observation_hash"])):
            _fail("video_edit_manifest_project_readback_required")


def validate_edit_output_hashes(package: dict, outputs: list, manifest: dict) -> None:
    validate_edit_manifest(package, manifest)
    if (package.get("director") or {}).get("postproduction") is None:
        return
    def value(row, name):
        return row.get(name) if isinstance(row, dict) else getattr(row, name)
    latest = {}
    for output in outputs:
        role_id = value(output, "role_id")
        if value(output, "state") in {"staged", "accepted"} and (role_id not in latest or value(output, "attempt_no") > value(latest[role_id], "attempt_no")):
            latest[role_id] = output
    for role_id, expected_hash in manifest["output_hashes"].items():
        if role_id not in latest or value(latest[role_id], "content_hash") != expected_hash:
            _fail("video_edit_manifest_output_mismatch")
