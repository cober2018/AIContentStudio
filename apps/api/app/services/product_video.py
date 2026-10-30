"""Product video direction for the third-party model, and image-to-video per shot (automatic MiniMax or a web handoff)."""

from __future__ import annotations

import copy
import math
import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentMasterRevision, MaterialRevision, ProductSkuRevision, ProductSkuWork, ProjectMaterialReference, SystemSetting, User
from . import product_categories, product_motion

MODE_KEY = "product_i2v_mode"
JOBS_KEY = "product_i2v_jobs"
COPY_KEY = "product_publish_copy"
HAILUO = "MiniMax-Hailuo-2.3"


def _route() -> dict | None:
    """The image-to-video model chosen in 设置 → 模型与 AI → 用途路由; None means automatic generation is off.

    `mmx:<model>` is the local MiniMax CLI; anything else is a registered model bound to 生视频 over the OpenAI-compatible protocol.
    """
    from .. import runtime_config
    from .model_registration import uses

    choice = uses()["shot_video"]
    if not choice:
        return None
    if choice.startswith("mmx:"):
        return {"kind": "mmx", "model": choice[4:], "label": "MiniMax"}
    stored = runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}
    profile = (stored.get("profiles") or {}).get(choice) or {}
    binding = (profile.get("capability_bindings") or {}).get("video_generation") or {}
    vendor = (stored.get("providers") or {}).get(profile.get("provider_id")) or {}
    if binding.get("adapter_key") != "openai.compatible" or not vendor.get("enabled") or not vendor.get("api_key"):
        _fail(409, "product_i2v_model_unavailable", "用途路由里选的图生视频模型现在用不了，请检查厂商密钥和「生成能力与插件」里的生视频绑定")
    return {"kind": "openai", "model": binding.get("model_id") or profile.get("model"), "profile": choice,
            "base_url": vendor["base_url"], "api_key": vendor["api_key"], "label": vendor.get("name") or profile.get("provider_id")}
COPY_LIMITS = {"title": 15, "cover_text": 8, "interaction": 60, "description": 50}


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


FINAL_STATES = {"finishing", "final_review", "final_changes", "done"}
CLARITY = ("480p", "768p", "1080p")


def resolution(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    """小样 and 成片 each have their own generation clarity; after the 小样 is approved the 成片 one applies."""
    from . import video_chain
    from .model_registration import uses

    chosen = uses()
    phase = "final" if video_chain.state(db, user, project_id, unit_id)["state"] in FINAL_STATES else "sample"
    return {"phase": phase, "sample": chosen["shot_video_resolution"], "final": chosen["shot_video_final_resolution"],
            "current": chosen["shot_video_final_resolution" if phase == "final" else "shot_video_resolution"]}


def _setting(db: Session, key: str) -> dict:
    row = db.get(SystemSetting, key)
    return dict(row.value or {}) if row else {}


def _put(db: Session, key: str, value: dict, actor: str) -> None:
    row = db.get(SystemSetting, key) or SystemSetting(key=key)
    row.value, row.updated_by = value, actor
    db.add(row)


def default_mode(db: Session) -> str:
    # Hand-made clips are the default: automatic ones cost money and are often weaker.
    return _setting(db, MODE_KEY).get("mode", "manual")


def save_default_mode(db: Session, user: User, mode: str) -> dict:
    if mode not in {"manual", "auto"}:
        _fail(422, "product_i2v_mode_invalid", "图生视频方式只能是手动或自动")
    _put(db, MODE_KEY, {"mode": mode}, user.email)
    db.commit()
    return {"mode": mode}


def work(db: Session, unit_id: int) -> ProductSkuWork | None:
    return db.scalar(select(ProductSkuWork).where(ProductSkuWork.unit_id == unit_id))


def _latest(db: Session, unit_id: int) -> ContentMasterRevision | None:
    return db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                     .order_by(ContentMasterRevision.revision_no.desc()).limit(1))


def _settings(db: Session, link: ProductSkuWork) -> dict:
    """Launch snapshot (with the frozen category) overlaid by the work's latest saved production settings."""
    from ..models import ProductionProfileRevision

    current = db.scalar(select(ProductionProfileRevision).where(ProductionProfileRevision.unit_id == link.unit_id)
                        .order_by(ProductionProfileRevision.revision.desc()).limit(1))
    return {**(link.settings_snapshot_json or {}), **{key: value for key, value in ((current.settings_json if current else None) or {}).items()
                                                       if key != "category"}}


def _mode(db: Session, link: ProductSkuWork, unit_id: int, shot_id: str | None = None) -> str:
    shots = (_setting(db, JOBS_KEY).get(str(unit_id)) or {}).get("modes") or {}
    if shot_id and shots.get(shot_id) in {"manual", "auto"}:
        return shots[shot_id]
    chosen = _settings(db, link).get("i2v_mode", "default")
    return default_mode(db) if chosen == "default" else chosen


def direction(db: Session, unit_id: int) -> dict | None:
    """What a product work adds to the video brief; None for persona works."""
    link = work(db, unit_id)
    if link is None:
        return None
    settings = _settings(db, link)
    sku = db.get(ProductSkuRevision, link.sku_revision_id)
    product = sku.product_json or {}
    category = settings.get("category")
    profile = (category or {}).get("profile") or {}
    style = settings.get("script_style")
    styles = profile.get("styles") or list(product_categories.STYLES)
    motion = product_motion.catalog()
    mode = _mode(db, link, unit_id)
    return {
        "product": {"name": product.get("name"), "category_text": product.get("category"), "variant": product.get("variant"),
                    "selling_points": product.get("selling_points") or [], "primary_image_revision_id": sku.primary_image_revision_id},
        "category": None if category is None else {
            "name": category["name"], "revision": category["revision"], "directive": profile.get("directive"),
            "styles": [{"id": item, "name": product_categories.STYLES[item], "skill": product_categories.style_ref(item)} for item in styles],
            "default_style": profile.get("default_style"), "hooks": profile.get("hooks") or [],
            "look": profile.get("look"), "camera_plan": profile.get("camera_plan") or {}},
        "style": None if not style else {"id": style, "name": product_categories.STYLES[style], "skill": product_categories.style_ref(style),
                                          "dialogue": style in product_categories.DIALOGUE_STYLES},
        "hook": {"pinned": settings.get("hook_pinned") or None, "versions": settings.get("hook_versions", 1)},
        "reference_structure": settings.get("reference_structure") or None,
        "material_mode": settings.get("material_mode", "mixed"),
        "i2v_mode": mode,
        "motion_library": {
            "camera": [{key: item[key] for key in ("id", "name", "group", "good_for", "holds")} for item in motion["camera"]],
            "looks": [{key: item[key] for key in ("id", "name", "group")} for item in motion["looks"]],
            "intensity": list(motion["intensity"]), "max_stack": product_motion.MAX_STACK},
        "rules": _rules(settings.get("material_mode", "mixed"), mode, style) + [_people_rule(references(db, None, unit_id))],
    }


def _people_rule(refs: dict) -> str:
    if refs["person"]:
        return "人物：角色有形象照，生成画面（九宫格、首帧）自动带上，人物长相照形象照来。"
    return ("人物：角色没有形象照，生成画面里不出现人物，只拍商品和场景，拿商品只出现手部。"
            "导演稿里要人物出镜的镜头写成实拍（source_kind=shoot），或改成商品 / 场景镜头，或请用户先给角色补形象照。")


def _rules(material_mode: str, mode: str, style: str | None) -> list[str]:
    rules = [
        "脚本：用 studio.video.product-script@3；先读 product.category.directive。product.style 有值就读那个风格 skill 照着写，没有就在 product.category.styles 里挑一个并写理由；开头按 product.hook。",
        "导演稿每镜 board 可写 camera_presets（≤2 个运镜库 id，一个定住一个在动的不能叠）、look、intensity（subtle/normal/strong）、chain_from_previous；没写就用品类的 camera_plan 和 look。",
        "商品亮相和下单引导镜头只用商品原图或实拍，不让 AI 改商品；价格、评价、销量、证书只用真实资料。",
        "定稿前用 studio.product.publish-copy@1 写发布文案，用 save_publish_copy 存下，用户在页面上可改。",
    ]
    rules.append({
        "photo_only": "出片方式：一张图出整片。除亮相和下单引导外，每个镜头都用图生视频，首帧用该镜关键帧，没有关键帧用商品主图。",
        "user_footage": "出片方式：给素材剪。只用用户放进库的素材，不自动补；缺素材的镜头在回执里列出。",
        "mixed": "出片方式：混合补齐。先用用户素材，缺的依次用免费公开素材 → 图生视频 → AE 模板，每镜回执写明素材来源。",
    }[material_mode])
    rules.append("首帧：商品主图之外需要新场景时，用 generate_shot_image 生成这一镜的首帧（自动带商品主图和角色形象照作参考并检查商品一致，不过关会重画，最多 3 次；作品「共同视觉参考」里手动选的优先）；通过的图自动设为首帧。亮相和下单引导镜头只用商品原图。手动镜头把首帧和 get_shot_video_prompt 的提示词交给用户，用户在页面上传做好的视频；自动镜头生成完会直接放进这一镜。")
    rules.append("清晰度：小样阶段按小样档生成；小样通过后，成片档如果比生成时的档位高，先对每个自动生成的镜头重新 generate_shot_video（会按成片档出），再 set_shot_materials 换上新片，然后开成片剪辑；两档相同就沿用小样的片子，不重新生成。")
    rules.append("图生视频：" + ("自动。对要动起来的镜头调用 generate_shot_video，再用 get_shot_video 取结果；失败或用户不满意就把这一镜改成手动（set_shot_video_mode）。"
                               if mode == "auto" else "手动。用 get_shot_video_prompt 取这一镜的提示词和首帧，按网页交接流程让用户在 Grok / Gemini 生成后回传。"))
    if style in product_categories.DIALOGUE_STYLES:
        rules.append("剧情类风格：脚本给出 characters；角色 id 按性别以 female- 或 male- 开头（如 female-mom、male-clerk），导演稿每镜 board.character 写说话的角色 id（旁白写 narrator），一镜只一个人说话。配音会给每个角色固定一个不同的声音。")
    return rules


def _shot(document: dict, shot_id: str) -> tuple[dict, dict | None]:
    shots = sorted(document["shots"], key=lambda item: item["order"])
    for index, shot in enumerate(shots):
        if shot["id"] == shot_id:
            return shot, shots[index + 1] if index + 1 < len(shots) else None
    _fail(404, "product_shot_unknown", f"没有镜头 {shot_id}")


def _people(board: dict) -> bool:
    # A speaking presenter, a named role or a person in the picture all mean a real face may appear;
    # hands alone do not, since hands holding the product are allowed without a portrait.
    return board.get("speaker") in {"presenter", "dialogue"} or bool(board.get("character") or board.get("attitude")) or any(
        word in (board.get("visual") or "") for word in ("人", "女生", "男生", "模特", "主播", "博主", "妈妈", "爸爸", "孩子", "宝宝", "小朋友", "女孩", "男孩"))


NO_PORTRAIT = "这个角色没有形象照，这一镜不会出现人物"
WITH_PORTRAIT = "人物长相照参考照片（角色形象照）来，同一个人，不换脸。"
WITHOUT_PERSON = "画面里不出现人物（不露脸、不出现身体），只出现商品与场景；需要拿取商品时只出现手部。"
WITHOUT_PERSON_EN = "No person in the frame (no face, no body), only the product and the setting; when the product is handled, show only hands."


def references(db: Session, user: User | None, unit_id: int) -> dict:
    """Pictures a generated shot is drawn against: the work's own shared references first, else the SKU primary image and the persona portrait."""
    from ..models import ContentUnit
    from .content_identity import current_revision, usable_portrait

    link = work(db, unit_id)
    chosen = {"product": [], "person": [], "scene": []}
    for ref in (_settings(db, link).get("shared_references") or []) if link else []:
        if ref.get("role") in chosen and ref.get("material_revision_id") not in chosen[ref["role"]]:
            chosen[ref["role"]].append(ref["material_revision_id"])
    origin = {role: "manual" for role, ids in chosen.items() if ids}
    if not chosen["product"] and link is not None:
        primary = db.get(ProductSkuRevision, link.sku_revision_id).primary_image_revision_id
        # A main image added to the product after this work started still serves it: the picture, not the facts, is what changes.
        primary = primary or db.scalar(select(ProductSkuRevision.primary_image_revision_id).where(
            ProductSkuRevision.sku_id == link.sku_id, ProductSkuRevision.primary_image_revision_id.is_not(None))
            .order_by(ProductSkuRevision.revision.desc()).limit(1))
        if primary:
            chosen["product"], origin["product"] = [primary], "sku_primary_image"
    unit = db.get(ContentUnit, unit_id)
    if not chosen["person"] and unit is not None and unit.persona_id is not None:
        revision = current_revision(db, "persona", unit.persona_id)
        portraits = [item for item in ((revision.profile_json or {}).get("portrait_material_revision_ids") or []) if usable_portrait(db, item)] if revision else []
        if portraits:
            chosen["person"], origin["person"] = portraits[:3], "persona_portrait"
    return {**chosen, "origin": origin}


def person_notices(document: dict, refs: dict) -> dict:
    """People shots that will come out without a person because nobody gave a face to draw."""
    if refs["person"]:
        return {}
    return {shot["id"]: NO_PORTRAIT for shot in document.get("shots", []) if _people(shot.get("board") or {})}


def person_rule(refs: dict) -> str:
    return WITH_PORTRAIT if refs["person"] else WITHOUT_PERSON


def _keyframe(db: Session, link: ProductSkuWork, shot: dict | None) -> int | None:
    """A shot's own first frame: the one picked for it here (e.g. a generated still), else the 导演稿 keyframe."""
    if shot is None:
        return None
    picked = ((_setting(db, JOBS_KEY).get(str(link.unit_id)) or {}).get("frames") or {}).get(shot["id"])
    return picked or (shot.get("production") or {}).get("reference_material_revision_id")


def _frames(db: Session, link: ProductSkuWork, document: dict, shot: dict, following: dict | None, product: list[int]) -> tuple[int | None, int | None]:
    first = _keyframe(db, link, shot) or (product[0] if product else None)
    # Chaining pins this clip's last frame to the next shot's keyframe, so the cut between them does not jump.
    last = _keyframe(db, link, following) if following and (following.get("board") or {}).get("chain_from_previous") else None
    return first, last


def set_shot_first_frame(db: Session, user: User, project_id: int, unit_id: int, shot_id: str, revision_id: int | None) -> dict:
    """Pick the picture one shot's image-to-video starts from; None goes back to the 导演稿 keyframe or the product photo."""
    _context(db, user, project_id, unit_id, shot_id)
    _after_approval(db, user, project_id, unit_id)
    if revision_id is not None:
        revision = db.get(MaterialRevision, revision_id)
        attached = db.scalar(select(ProjectMaterialReference.id).where(ProjectMaterialReference.project_id == project_id,
                                                                       ProjectMaterialReference.material_revision_id == revision_id))
        if revision is None or revision.material.kind != "image" or attached is None:
            _fail(422, "product_first_frame_invalid", "首帧必须是这个项目里的一张图片")
    jobs = _setting(db, JOBS_KEY)
    frames = jobs.setdefault(str(unit_id), {}).setdefault("frames", {})
    if revision_id is None:
        frames.pop(shot_id, None)
    else:
        frames[shot_id] = revision_id
    _put(db, JOBS_KEY, jobs, user.email)
    db.commit()
    return {"shot_id": shot_id, "first_frame_revision_id": revision_id}


def _context(db: Session, user: User, project_id: int, unit_id: int, shot_id: str):
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    link = work(db, unit_id)
    if link is None:
        _fail(409, "product_work_required", "只有商品作品能用图生视频补镜头")
    master = _latest(db, unit_id)
    if master is None or master.payload_schema != "video.master.v2":
        _fail(409, "product_master_required", "先存导演稿")
    shot, following = _shot(master.payload_json, shot_id)
    return link, master, shot, following


def shot_prompt(db: Session, user: User, project_id: int, unit_id: int, shot_id: str) -> dict:
    """The same prompt and frames for either route, so switching a shot to manual keeps its direction."""
    link, master, shot, following = _context(db, user, project_id, unit_id, shot_id)
    board = copy.deepcopy(shot.get("board") or {})
    profile = ((link.settings_snapshot_json or {}).get("category") or {}).get("profile") or {}
    board.setdefault("look", profile.get("look"))
    refs = references(db, user, unit_id)
    first, last = _frames(db, link, master.payload_json, shot, following, refs["product"])
    people = _people(board) and bool(refs["person"])
    if not refs["person"]:
        # Without a portrait nobody is drawn, so a person's attitude has nothing to act on.
        board.pop("attitude", None)
    notice = person_notices({"shots": [shot]}, refs).get(shot_id)
    return {"shot_id": shot_id, "mode": _mode(db, link, unit_id, shot_id),
            "prompt": product_motion.motion_prompt(board, people=people, english=False) + ("" if refs["person"] else "。" + WITHOUT_PERSON),
            "prompt_en": product_motion.motion_prompt(board, people=people, english=True) + ("" if refs["person"] else ". " + WITHOUT_PERSON_EN),
            # Four-part wording for a new first-frame still of this shot (generate_shot_image or a web image tool).
            "still_prompt": product_motion.still_prompt(board, people=people) + "\n" + person_rule(refs),
            "references": refs, **({"notice": notice} if notice else {}),
            "first_frame_revision_id": first, "last_frame_revision_id": last,
            "aspect_ratio": "{}:{}".format(*master.payload_json["aspect_ratio"]),
            "seconds": min(15, max(4, math.ceil(shot["duration_ms"] / 1000))),
            "manual_note": "网页不支持尾帧时只传首帧；生成后下载原始 MP4 回传。" if last else "生成后下载原始 MP4 回传。"}


def _after_approval(db: Session, user: User, project_id: int, unit_id: int) -> None:
    # Which shots need a generated picture is only known once the user's materials are mapped, i.e. after approval.
    from . import video_chain

    if video_chain.state(db, user, project_id, unit_id)["state"] in {"not_started", "draft_review", "draft_changes"}:
        _fail(409, "video_chain_draft_not_approved", "先采用导演稿，对应完素材再生成：已有素材的镜头不用生成")


def set_shot_mode(db: Session, user: User, project_id: int, unit_id: int, shot_id: str, mode: str) -> dict:
    _context(db, user, project_id, unit_id, shot_id)
    _after_approval(db, user, project_id, unit_id)
    if mode not in {"manual", "auto"}:
        _fail(422, "product_i2v_mode_invalid", "图生视频方式只能是手动或自动")
    jobs = _setting(db, JOBS_KEY)
    record = jobs.setdefault(str(unit_id), {})
    record.setdefault("modes", {})[shot_id] = mode
    _put(db, JOBS_KEY, jobs, user.email)
    db.commit()
    return {"shot_id": shot_id, "mode": mode}


def _provider():
    from .content_harness.registry import RegistryError, registry

    try:
        return registry.resolve("video_provider", "minimax.cli", "1")
    except RegistryError:
        _fail(503, "product_i2v_unavailable", "MiniMax 视频没启用，请在设置里配置，或把这一镜改成手动")


def start_shot_video(db: Session, user: User, project_id: int, unit_id: int, shot_id: str) -> dict:
    from .materials import read_bytes_checked

    _after_approval(db, user, project_id, unit_id)
    plan = shot_prompt(db, user, project_id, unit_id, shot_id)
    if plan["mode"] != "auto":
        _fail(409, "product_i2v_manual", "这一镜是手动生成；要自动请先切换")
    route = _route()
    if route is None:
        _fail(409, "product_i2v_model_unset", "设置 → 模型与 AI → 用途路由里还没选图生视频模型")
    model = route["model"]
    # Local Hailuo takes the first frame alone; H3 and the Videos API also take the chained last frame.
    last = plan["last_frame_revision_id"] if not (route["kind"] == "mmx" and model == HAILUO) else None
    frames = [revision_id for revision_id in (plan["first_frame_revision_id"], last) if revision_id]
    if not frames:
        _fail(409, "product_i2v_first_frame_required", "这一镜没有关键帧，商品也没有主图，先补一张首帧")
    images = []
    for revision_id in frames:
        revision = db.get(MaterialRevision, revision_id)
        if revision is None or revision.material.kind != "image":
            _fail(409, "product_i2v_frame_invalid", f"首尾帧 {revision_id} 不是图片")
        images.append(read_bytes_checked(db, revision))
    clarity = resolution(db, user, project_id, unit_id)["current"]
    if route["kind"] == "openai":
        from . import openai_video

        sent = openai_video.submit(route["base_url"], route["api_key"], model, plan["prompt_en"], seconds=plan["seconds"],
                                   aspect_ratio=plan["aspect_ratio"], first_frame=images[0],
                                   last_frame=images[1] if len(images) > 1 else None, resolution=clarity)
        job, reason = sent.get("job_id"), sent.get("error")
        if not job:
            _fail(502, "product_i2v_failed", f"{route['label']} 没接下这个任务：{reason}；可以稍后再试，或把这一镜改成手动")
    else:
        parameters = {"seconds": 6} if model == HAILUO else {"seconds": plan["seconds"], "aspect_ratio": plan["aspect_ratio"]}
        output = _provider().submit_task({"prompt": plan["prompt_en"], "model_id": model, "timeout_seconds": 25, "parameters": parameters,
                                          "source_bytes": images, "source_revision_ids": frames})
        job = (output.metadata or {}).get("job_id")
        if output.status != "running" or not job:
            # An unclear submission is not retried: the supplier may already be charging for it.
            reason = (output.metadata or {}).get("reason")
            _fail(502, f"product_i2v_{output.status}", f"MiniMax 没接下这个任务{'：' + reason if reason else ''}；可以稍后再试，或把这一镜改成手动")
    jobs = _setting(db, JOBS_KEY)
    jobs.setdefault(str(unit_id), {}).setdefault("jobs", {})[shot_id] = {"job_id": job, "project_id": project_id, "prompt": plan["prompt_en"], "model": model,
                                                                         "route": {key: route[key] for key in ("kind", "profile", "label") if key in route}, "resolution": clarity,
                                                                         "frames": frames, "state": "running"}
    _put(db, JOBS_KEY, jobs, user.email)
    db.commit()
    return {"shot_id": shot_id, "state": "running", "frames": frames, "seconds": plan["seconds"], "resolution": clarity}


def get_shot_video(db: Session, user: User, project_id: int, unit_id: int, shot_id: str) -> dict:
    from .content_masters import owned_unit
    from .materials import create_material, create_revision
    from .project_folders import store_new
    from .voiceover import _duration_ms

    owned_unit(db, project_id, unit_id, user)
    jobs = _setting(db, JOBS_KEY)
    job = ((jobs.get(str(unit_id)) or {}).get("jobs") or {}).get(shot_id)
    if job is None:
        _fail(404, "product_i2v_job_missing", "这一镜还没有自动生成任务")
    if job["state"] != "running":
        return {"shot_id": shot_id, **{key: job.get(key) for key in ("state", "material_revision_id", "reason")}}
    model, route = job.get("model", "MiniMax-H3"), job.get("route") or {"kind": "mmx", "label": "MiniMax"}
    if route["kind"] == "openai":
        from .. import runtime_config
        from . import openai_video

        stored = runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}
        vendor = (stored.get("providers") or {}).get(((stored.get("profiles") or {}).get(route.get("profile")) or {}).get("provider_id")) or {}
        result = openai_video.query(vendor.get("base_url", ""), vendor.get("api_key", ""), job["job_id"])
        state, content, failure = result["state"], result.get("content"), result.get("reason")
    else:
        output = _provider().query_task({"job_id": job["job_id"], "model_id": model, "timeout_seconds": 25,
                                         "protocol_version": "minimax.video.v1" if model == HAILUO else "minimax.video.v2"})
        unclear = output.status == "unknown" and not (output.metadata or {}).get("reason")
        state = "running" if output.status == "running" or unclear else "succeeded" if output.status == "succeeded" and output.content else "failed"
        content, failure = output.content, (output.metadata or {}).get("reason") or output.status
    if state == "running":
        return {"shot_id": shot_id, "state": "running"}
    if state == "succeeded":
        output_content = content
        material = create_material(db, kind="video", title=f"AI 视频 · {shot_id}"[:200], tags=["AI 视频", "图生视频"], created_by=user.email)
        revision = create_revision(
            db, material, content=output_content, suffix=".mp4", declared_mime="video/mp4", source_kind="ai_generated",
            provider_key="minimax.cli" if route["kind"] == "mmx" else "openai.compatible", provider_version=model,
            prompt_text=job["prompt"][:4000], rights_status="cleared",
            public_use_allowed=True, model_use_allowed=True, attribution_text=f"{route.get('label') or 'AI'} 图生视频",
            duration_ms=_duration_ms(output_content, ".mp4"),
            metadata={"shot_id": shot_id, "first_frames": job["frames"], "provider_job_id": job["job_id"], "material_source": "i2v_auto"},
            created_by=user.email)
        db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id, origin="system_reference", status="active",
                                        attached_by=user.email, note=f"图生视频 · {shot_id}"))
        store_new(db, revision, project_id, "视频/Broll")
        job.update(state="done", material_revision_id=revision.id)
        _put(db, JOBS_KEY, jobs, user.email)
        db.commit()
        # The automatic route ends with the clip on its shot; before the 导演稿 is approved it stays a candidate.
        try:
            place_shot_video(db, user, project_id, unit_id, shot_id, revision.id)
            job["placed"] = True
        except HTTPException:
            db.rollback()
            jobs = _setting(db, JOBS_KEY)
            job = jobs[str(unit_id)]["jobs"][shot_id]
    else:
        job.update(state="failed", reason=failure)
    _put(db, JOBS_KEY, jobs, user.email)
    db.commit()
    return {"shot_id": shot_id, **{key: job.get(key) for key in ("state", "material_revision_id", "reason")},
            **({"next": "这一镜可以改成手动：set_shot_video_mode(mode=manual)，再取 get_shot_video_prompt"} if job["state"] == "failed" else {})}


def save_publish_copy(db: Session, user: User, project_id: int, unit_id: int, value: dict) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    if work(db, unit_id) is None:
        _fail(409, "product_work_required", "发布文案只给商品作品")
    if type(value) is not dict or set(value) - {"channel", "title", "hashtags", "cover_text", "interaction", "description"}:
        _fail(422, "publish_copy_invalid", "发布文案格式不对")
    for key, limit in COPY_LIMITS.items():
        if type(value.get(key, "")) is not str or len(value.get(key, "")) > limit:
            _fail(422, "publish_copy_too_long", f"{key} 不能超过 {limit} 个字")
    tags = value.get("hashtags", [])
    if type(tags) is not list or len(tags) > 5 or any(type(tag) is not str or not 0 < len(tag) <= 30 for tag in tags):
        _fail(422, "publish_copy_hashtags_invalid", "话题最多 5 个，每个不超过 30 个字")
    stored = _setting(db, COPY_KEY)
    stored[str(unit_id)] = {key: value.get(key, [] if key == "hashtags" else "") for key in ("channel", "title", "hashtags", "cover_text", "interaction", "description")}
    _put(db, COPY_KEY, stored, user.email)
    db.commit()
    return stored[str(unit_id)]


def publish_copy(db: Session, user: User, project_id: int, unit_id: int) -> dict | None:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    return _setting(db, COPY_KEY).get(str(unit_id))


def _source_label(revision: MaterialRevision) -> tuple[str, bool]:
    """Where a shot's footage came from, and whether it is an image-to-video clip (only those get the generate buttons)."""
    source = (revision.metadata_json or {}).get("material_source")
    if source in {"i2v_auto", "i2v_manual"}:
        return ("自动图生视频" if source == "i2v_auto" else "手动图生视频"), True
    if revision.source_kind == "chart":
        return "AE 模板", False
    if revision.source_kind == "ai_generated":
        return "AI 生成", False
    return {"upload": "我的素材", "stock": "免费素材"}.get(revision.source_kind, "素材库"), False


def _first_frames(db: Session, record: dict) -> dict:
    frames = {}
    for shot_id, revision_id in (record.get("frames") or {}).items():
        revision = db.get(MaterialRevision, revision_id)
        if revision is not None:
            check = (revision.metadata_json or {}).get("consistency")
            frames[shot_id] = {"material_revision_id": revision.id, "material_id": revision.material_id,
                               "consistency": _verdict(check),
                               "tries": len((check or {}).get("tries") or [])}
    return frames


def _verdict(check: dict | None) -> str | None:
    return None if check is None else ("通过" if check.get("pass") else "不通过")


def _grid_candidates(db: Session, record: dict) -> dict:
    """Storyboard-grid first-frame candidates per shot, newest first; none is in use until the user picks it."""
    view = {}
    for shot_id, entry in (record.get("grid") or {}).items():
        rows = [db.get(MaterialRevision, revision_id) for revision_id in reversed(entry.get("candidates") or [])]
        view[shot_id] = [{"material_revision_id": row.id, "material_id": row.material_id,
                          "consistency": _verdict((row.metadata_json or {}).get("consistency"))} for row in rows if row is not None]
    return view


def _used(db: Session, unit_id: int) -> dict:
    master = _latest(db, unit_id)
    used = {}
    for shot in (master.payload_json or {}).get("shots", []) if master else []:
        revision = db.get(MaterialRevision, shot["source_material_revision_id"]) if shot.get("source_material_revision_id") else None
        if revision is not None:
            label, generated = _source_label(revision)
            used[shot["id"]] = {"material_revision_id": revision.id, "source": label, "i2v": generated, "title": revision.material.title}
    return used


def shot_videos(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    """Per-shot image-to-video state for the production page."""
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    link = work(db, unit_id)
    if link is None:
        return {"product": False}
    record = _setting(db, JOBS_KEY).get(str(unit_id)) or {}
    refs, master = references(db, user, unit_id), _latest(db, unit_id)
    return {"product": True, "default_mode": _mode(db, link, unit_id), "modes": record.get("modes") or {},
            "resolution": resolution(db, user, project_id, unit_id), "used": _used(db, unit_id), "frames": _first_frames(db, record),
            "grid": _grid_candidates(db, record), "grid_run": record.get("grid_run"), "references": refs,
            "person_notices": person_notices(master.payload_json if master else {}, refs),
            "jobs": {shot: {key: job.get(key) for key in ("state", "material_revision_id", "reason", "resolution")} for shot, job in (record.get("jobs") or {}).items()}}


def set_shot_motion(db: Session, user: User, project_id: int, unit_id: int, shot_id: str, motion: dict) -> dict:
    """The user's own camera / look choice for one shot becomes a new 导演稿 version; the old one is kept."""
    from . import video_chain
    from .video_documents import VideoDocumentError, canonical_payload

    _link, master, _shot_row, _following = _context(db, user, project_id, unit_id, shot_id)
    if video_chain.locked(db, unit_id):
        _fail(409, "product_motion_locked", "成片已定稿，不能再改镜头")
    document = copy.deepcopy(master.payload_json)
    document.pop("postproduction", None)
    shot = next(item for item in document["shots"] if item["id"] == shot_id)
    board = shot.get("board")
    if board is None:
        _fail(409, "product_shot_board_missing", "这一镜没有分镜表，先让模型出导演稿")
    board.update({key: value for key, value in motion.items() if value is not None})
    if motion.get("look") is None:
        board.pop("look", None)
    try:
        canonical_payload(document)
    except VideoDocumentError as exc:
        _fail(422, "product_motion_invalid", str(exc).split("：", 1)[-1])
    master_id = video_chain._save(db, user, project_id, unit_id, document, {"video_chain": "draft", "note": f"用户改了 {shot_id} 的运镜 / 光线 / 强度"})
    db.commit()
    return {"master_id": master_id, "shot_id": shot_id, "board": board}


# Reveal and call-to-action shots show the real product photo; a generated still must not stand in for it.
_ORIGINAL_ONLY = ("product_reveal", "cta", "商品亮相", "整机亮相", "下单引导", "行动引导")
MAX_STILL_TRIES = 3


def _original_only(shot: dict) -> bool:
    # The shot type leads the purpose followed by a colon ("cta：…"); "product_reveal 前的拆箱" only mentions it.
    found = re.match(r"\s*([a-z_]+|[一-鿿]+)\s*[：:]", (shot.get("purpose") or "").lower())
    return bool(found and found.group(1) in _ORIGINAL_ONLY) or (shot.get("label") or "") in _ORIGINAL_ONLY


def _image_bytes(db: Session, revision_id: int) -> bytes:
    from .materials import read_bytes_checked

    revision = db.get(MaterialRevision, revision_id)
    if revision is None or revision.material.kind != "image":
        _fail(422, "shot_image_reference_invalid", f"参考图 {revision_id} 不是图片")
    return read_bytes_checked(db, revision)


def generate_shot_image(db: Session, user: User, project_id: int, unit_id: int, shot_id: str, prompt: str,
                        extra_reference_id: int | None = None, as_first_frame: bool = True) -> dict:
    """Still for one shot with the product photo as reference; it is used only after it passes the subject check."""
    from . import shot_image

    _after_approval(db, user, project_id, unit_id)
    from .materials import create_material, create_revision
    from .model_registration import uses
    from .project_folders import store_new

    link, master, shot, _following = _context(db, user, project_id, unit_id, shot_id)
    if as_first_frame and _original_only(shot):
        _fail(409, "shot_image_original_only", "商品亮相和下单引导镜头只用商品原图，不用生成图作首帧")
    refs = references(db, user, unit_id)
    if not refs["product"]:
        _fail(409, "shot_image_product_photo_missing", "商品还没有主图，没法对照保持主体一致")
    product_id = refs["product"][0]
    choice = uses()["shot_image"]
    if not choice:
        _fail(409, "shot_image_model_unset", "「用途路由 → 镜头生图」还没选模型")
    target = shot_image.route(choice)
    product = shot_image.to_png(_image_bytes(db, product_id))
    aspect = "{}:{}".format(*master.payload_json["aspect_ratio"])
    used_ids = [product_id, *refs["person"], *refs["scene"], *([extra_reference_id] if extra_reference_id else [])]
    references_png = [shot_image.fit(product, aspect)] + [shot_image.fit(shot_image.to_png(_image_bytes(db, item)), aspect) for item in used_ids[1:]]
    base = prompt.strip() + "\n" + person_rule(refs)
    tries, request = [], base
    for attempt in range(1, MAX_STILL_TRIES + 1):
        still = shot_image.generate(target, request, references_png, aspect)
        verdict = shot_image.check(product, still)
        tries.append({"attempt": attempt, **verdict})
        if verdict["pass"]:
            break
        # The next try is told exactly what drifted, so it fixes the product instead of redrawing at random.
        request = base + "\n上一张的问题（这次必须改正）：" + "；".join(verdict["problems"] or ["商品和参考照片不一致"])
    passed = tries[-1]["pass"]
    material = create_material(db, kind="image", title=f"AI 示意 · {shot_id} 首帧"[:200], tags=["AI 示意", "镜头生图"], created_by=user.email)
    revision = create_revision(
        db, material, content=still, suffix=".png", declared_mime="image/png", source_kind="ai_generated",
        provider_key="openai.compatible", provider_version=target["model"], prompt_text=request[:4000], rights_status="cleared",
        public_use_allowed=True, model_use_allowed=True, attribution_text=f"{target['label']} 生图（AI 示意）",
        metadata={"shot_id": shot_id, "reference_revision_ids": used_ids,
                  "consistency": {"pass": passed, "tries": tries}, "material_source": "shot_still"}, created_by=user.email)
    db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id, origin="system_reference", status="active",
                                    attached_by=user.email, note=f"镜头生图 · {shot_id}"))
    store_new(db, revision, project_id, "图片/图片素材")
    db.commit()
    result = {"shot_id": shot_id, "material_revision_id": revision.id, "consistency": shot_image.summary(tries[-1]), "tries": len(tries),
              **({"notice": NO_PORTRAIT} if not refs["person"] and _people(shot.get("board") or {}) else {})}
    if not passed:
        return {**result, "used": False, "next": f"试了 {len(tries)} 次商品都和原图不一致，这张不用；可以改提示词再试，或用商品原图作首帧"}
    if as_first_frame:
        set_shot_first_frame(db, user, project_id, unit_id, shot_id, revision.id)
    return {**result, "used": as_first_frame}


def place_shot_video(db: Session, user: User, project_id: int, unit_id: int, shot_id: str, revision_id: int) -> dict:
    """Put a finished clip on its shot in the approved 导演稿 (a new version; picture content stays as approved)."""
    from . import video_chain

    return video_chain.set_materials(db, user, project_id, unit_id, {shot_id: revision_id})


def upload_shot_video(db: Session, user: User, project_id: int, unit_id: int, shot_id: str, content: bytes, filename: str) -> dict:
    """Manual route: the user made the clip on a website from the given still and prompt; it goes straight onto that shot."""
    from .materials import create_material, create_revision
    from .project_folders import store_new
    from .voiceover import _duration_ms

    _context(db, user, project_id, unit_id, shot_id)
    if content[4:8] != b"ftyp":
        _fail(422, "shot_video_upload_invalid", "请上传 MP4 / MOV 视频文件")
    suffix = ".mov" if filename.lower().endswith(".mov") else ".mp4"
    material = create_material(db, kind="video", title=f"手动图生视频 · {shot_id}"[:200], tags=["图生视频", "手动"], created_by=user.email)
    revision = create_revision(
        db, material, content=content, suffix=suffix, declared_mime="video/quicktime" if suffix == ".mov" else "video/mp4", source_kind="upload",
        rights_status="cleared", public_use_allowed=True, model_use_allowed=True, attribution_text="手动图生视频",
        duration_ms=_duration_ms(content, suffix), metadata={"shot_id": shot_id, "material_source": "i2v_manual"}, created_by=user.email)
    db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id, origin="user_upload", status="active",
                                    attached_by=user.email, note=f"手动图生视频 · {shot_id}"))
    store_new(db, revision, project_id, "视频/Broll")
    db.commit()
    placed = place_shot_video(db, user, project_id, unit_id, shot_id, revision.id)
    return {"shot_id": shot_id, "material_revision_id": revision.id, "master_id": placed["master_id"]}
