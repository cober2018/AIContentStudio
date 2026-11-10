"""Auto-start of rough-cut edits: dispatcher endpoints (MCP token) and page/settings endpoints."""

import time

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin, require_editor
from ..models import User
from ..services import edit_agent

router = APIRouter(tags=["edit-agent"])


def _dispatcher(db: Session, authorization: str | None) -> User:
    from ..services.creative_mcp import MCPError, authenticate, resolve_owner

    try:
        return resolve_owner(db, authenticate(authorization))
    except MCPError:
        raise HTTPException(401, {"code": "edit_agent_unauthorized"}) from None


class ReportIn(BaseModel):
    state: str = Field(pattern="^(launched|finished|failed)$")
    reason: str = Field(default="", max_length=500)
    log: str = Field(default="", max_length=500)


class SettingsIn(BaseModel):
    enabled: bool
    assistant: str = Field(pattern="^(claude|codex)$")


@router.get("/api/v1/edit-agent/next")
def next_task(db: Session = Depends(get_db), authorization: str | None = Header(default=None)):
    return {"task": edit_agent.next_task(db, _dispatcher(db, authorization))}


@router.post("/api/v1/edit-agent/tasks/{execution_id}/report")
def report(execution_id: int, payload: ReportIn, db: Session = Depends(get_db), authorization: str | None = Header(default=None)):
    return edit_agent.report(db, _dispatcher(db, authorization), execution_id, payload.state, payload.reason, payload.log)


@router.get("/api/v1/settings/edit-agent")
def read_settings(user: User = Depends(get_current_user)):
    return edit_agent.view_settings()


@router.put("/api/v1/settings/edit-agent")
def write_settings(payload: SettingsIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return edit_agent.save_settings(db, payload.enabled, payload.assistant, user)


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/edit-agent")
def unit_status(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return edit_agent.status(db, user, project_id, unit_id)


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/edit-agent/retry")
def unit_retry(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return edit_agent.retry(db, user, project_id, unit_id)


class VoiceSettingsIn(BaseModel):
    model_id: str | None = None
    voice_id: str | None = None
    emotion: str | None = None
    rate: float | None = None
    volume: float | None = None
    pitch: int | None = None
    format: str | None = None
    sample_rate: int | None = None
    bitrate: int | None = None
    channels: int | None = None
    latex_read: bool | None = None
    text_normalization: bool | None = None
    language_boost: str | None = None
    voice_modify: dict[str, int] | None = None


@router.get("/api/v1/settings/voice")
def read_voice_settings(user: User = Depends(get_current_user)):
    from ..services import voiceover

    return {**voiceover.presets(), "emotions": {k: v for k, v in voiceover.EMOTIONS.items() if v} | {"auto": "自动"}}


class VoicePresetIn(VoiceSettingsIn):
    name: str = Field(min_length=1, max_length=40)


@router.post("/api/v1/settings/voice/presets")
def create_voice_preset(payload: VoicePresetIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services import voiceover

    return voiceover.save_preset(db, user, None, payload.name, payload.model_dump(exclude_unset=True, exclude={"name"}))


@router.put("/api/v1/settings/voice/presets/{preset_id}")
def update_voice_preset(preset_id: str, payload: VoicePresetIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services import voiceover

    return voiceover.save_preset(db, user, preset_id, payload.name, payload.model_dump(exclude_unset=True, exclude={"name"}))


@router.delete("/api/v1/settings/voice/presets/{preset_id}")
def delete_voice_preset(preset_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services import voiceover

    return voiceover.delete_preset(db, user, preset_id)


@router.put("/api/v1/settings/voice/default/{preset_id}")
def default_voice_preset(preset_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services import voiceover

    return voiceover.set_default(db, user, preset_id)


class PersonaVoiceIn(BaseModel):
    preset_id: str | None = Field(default=None, max_length=40)


@router.put("/api/v1/personas/{persona_id}/voice-preset")
def persona_voice_preset(persona_id: int, payload: PersonaVoiceIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..models import ContentPersona
    from ..services import voiceover

    persona = db.get(ContentPersona, persona_id)
    if persona is None or persona.owner_user_id != user.id:
        raise HTTPException(404, {"code": "persona_not_found", "message": "没有这个角色"})
    return voiceover.set_persona_preset(db, user, persona_id, payload.preset_id)


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/voiceover")
def make_voiceover(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import voiceover

    return voiceover.generate(db, user, project_id, unit_id)


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/voiceover")
def read_voiceover(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import voiceover

    return voiceover.status(db, user, project_id, unit_id)


class SpeechSpeedIn(BaseModel):
    speed_percent: int = Field(ge=80, le=150)


@router.put("/api/v1/content-projects/{project_id}/units/{unit_id}/voiceover/speed")
def set_speech_speed(project_id: int, unit_id: int, payload: SpeechSpeedIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import voiceover

    return voiceover.set_speed(db, user, project_id, unit_id, payload.speed_percent)


class VideoNoteIn(BaseModel):
    time_ms: int | None = Field(default=None, ge=0, le=24 * 3600 * 1000)
    note: str = Field(min_length=1, max_length=2000)


class VideoDecisionIn(BaseModel):
    stage: str = Field(pattern=r"^(draft|materials|sample|final|covers)$")
    decision: str = Field(pattern=r"^(approve|changes)$")
    notes: list[VideoNoteIn] = Field(default_factory=list, max_length=50)


class VideoMaterialsModeIn(BaseModel):
    mode: str = Field(pattern=r"^(manual|auto)$")


class CoverRedoIn(BaseModel):
    note: str = Field(default="", max_length=2000)


class PlatformSkillsIn(BaseModel):
    writing_skills: bool


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/platform-skills")
def platform_skills_state(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import craft_skills
    from ..services.content_masters import owned_unit

    _project, unit = owned_unit(db, project_id, unit_id, user)
    return craft_skills.platform_skills(db, unit)


@router.put("/api/v1/content-projects/{project_id}/units/{unit_id}/platform-skills")
def platform_skills_save(project_id: int, unit_id: int, payload: PlatformSkillsIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import craft_skills

    return craft_skills.set_writing_skills(db, user, project_id, unit_id, payload.writing_skills)


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain")
def video_chain_state(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import video_chain

    result = video_chain.decisions(db, user, project_id, unit_id)
    master = video_chain._latest(db, unit_id)
    # The page shows the storyboard the user is asked to judge.
    result["master"] = {"id": master.id, "revision_no": master.revision_no, "payload": master.payload_json} if master and master.payload_schema == "video.master.v2" else None
    if result.get("execution_id"):
        from sqlalchemy import select

        from ..models import CreativeExecutionOutput

        # The page plays the 小样 / 成片 itself through the existing signed preview stream.
        result["cut_output_id"] = db.scalar(select(CreativeExecutionOutput.id).where(
            CreativeExecutionOutput.execution_id == result["execution_id"], CreativeExecutionOutput.role_id.in_(("rough_cut", "final")))
            .order_by(CreativeExecutionOutput.attempt_no.desc()).limit(1))
        cover = lambda execution_id, role_id="cover": db.scalar(select(CreativeExecutionOutput.id).where(  # noqa: E731
            CreativeExecutionOutput.execution_id == execution_id, CreativeExecutionOutput.role_id == role_id,
            CreativeExecutionOutput.state.in_(("staged", "accepted"))).order_by(CreativeExecutionOutput.attempt_no.desc()).limit(1))
        result["cover_output_id"] = cover(result["execution_id"])
        from ..models import CreativeExecution, CreativeExecutionPackage

        # The 成片 page says which persona clips this task added.
        execution = db.get(CreativeExecution, result["execution_id"])
        package = db.get(CreativeExecutionPackage, execution.package_id) if execution else None
        result["persona_clips"] = ((package.package_json if package else {}).get("director") or {}).get("persona_clips") or []
        from ..services.web_video_handoff import cover_roles, separate_covers

        # Landscape tasks also deliver a 3:4 cover, and newer ones a 4:3 cut of the 16:9 one.
        separate = bool(package and separate_covers(package.package_json))
        roles = cover_roles(package.package_json) if package else ()
        result["separate_covers"] = separate
        if separate:
            result["cover_vertical_output_id"] = cover(result["execution_id"], "cover_vertical")
            if "cover_43" in roles:
                result["cover_43_output_id"] = cover(result["execution_id"], "cover_43")
        # The 小样 page stays watchable after the chain has moved on to the 成片.
        sample = next((task for task in reversed(result["tasks"]) if task.get("phase") == "rough_cut"), None)
        if sample and sample["execution_id"] != result["execution_id"]:
            result["sample"] = {"execution_id": sample["execution_id"], "cut_output_id": db.scalar(select(CreativeExecutionOutput.id).where(
                CreativeExecutionOutput.execution_id == sample["execution_id"], CreativeExecutionOutput.role_id == "rough_cut")
                .order_by(CreativeExecutionOutput.attempt_no.desc()).limit(1)), "cover_output_id": cover(sample["execution_id"])}
            result["sample"]["shot_checks"] = _with_template_check(db, _shot_checks(db, result["sample"]["cut_output_id"]), result["sample"]["cover_output_id"])
        if separate and result["cut_output_id"]:
            checks = _with_cover_check(db, _shot_checks(db, result["cut_output_id"]), result["cut_output_id"], result["cover_output_id"])
            outputs = {role: result.get(f"{role}_output_id") for role in roles}
            checks = _with_cover_sizes(db, checks, outputs)
            for output_id in reversed(list(outputs.values())):
                checks = _with_template_check(db, checks, output_id)
            result["shot_checks"] = checks
        elif separate:
            result["shot_checks"] = _shot_checks(db, result["cut_output_id"])
        else:
            result["shot_checks"] = _with_template_check(db, _with_cover_check(db, _shot_checks(db, result["cut_output_id"]), result["cut_output_id"], result["cover_output_id"]),
                                                         result["cover_output_id"])
    return result


def _with_cover_sizes(db: Session, checks: dict | None, outputs: dict[str, int | None]) -> dict | None:
    """Warns when one of a landscape task's covers is missing or not its required size."""
    from ..models import CreativeExecutionOutput
    from ..services import delivery_checks
    from ..services.web_video_handoff import LANDSCAPE_COVER_SIZES

    warnings = []
    for role_id, output_id in outputs.items():
        width, height = LANDSCAPE_COVER_SIZES[role_id]
        if not output_id:
            warnings.append({"code": "cover_missing", "role": role_id})
            continue
        size = str((db.get(CreativeExecutionOutput, output_id).metadata_json or {}).get("cover_size") or "")
        if size and size != f"{width}x{height}":
            actual_w, actual_h = (int(part) for part in size.split("x"))
            warnings.append({"code": "cover_size_invalid", "role": role_id, "width": actual_w, "height": actual_h,
                             "expected_width": width, "expected_height": height})
    if not warnings:
        return checks
    base = checks or {"status": "measured", "basis": "fixed", "warnings": [], "thresholds": delivery_checks.thresholds(db)}
    return {**base, "warnings": [*warnings, *base.get("warnings", [])]}


def _with_template_check(db: Session, checks: dict | None, cover_id: int | None) -> dict | None:
    """Warns when the shown cover was not made with the persona's 封面 template."""
    from ..models import CreativeExecutionOutput
    from ..services import delivery_checks

    output = db.get(CreativeExecutionOutput, cover_id) if cover_id else None
    code = (output.metadata_json or {}).get("cover_template_check") if output else None
    if code not in {"cover_template_missing", "cover_template_mismatch"}:
        return checks
    base = checks or {"status": "measured", "basis": "fixed", "warnings": [], "thresholds": delivery_checks.thresholds(db)}
    return {**base, "warnings": [{"code": code, "role": output.role_id}, *base.get("warnings", [])]}


def _with_cover_check(db: Session, checks: dict | None, cut_id: int | None, cover_id: int | None) -> dict | None:
    """The cover comparison lives on whichever of the pair was delivered second; it counts only for the pair shown now."""
    import json

    from ..models import CreativeExecutionOutput
    from ..services import delivery_checks

    if not cut_id or not cover_id:
        return checks
    for output_id, against in ((cover_id, cut_id), (cut_id, cover_id)):
        try:
            check = json.loads((db.get(CreativeExecutionOutput, output_id).metadata_json or {})["cover_check"])
            if check["against"] != against:
                continue
            warning = delivery_checks.cover_warning({key: check[key] for key in ("at_ms", "mean", "rgb", "threshold")})
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
        if warning is None:
            return checks
        base = checks or {"status": "measured", "basis": "fixed", "warnings": [], "thresholds": delivery_checks.thresholds(db)}
        return {**base, "warnings": [warning, *base.get("warnings", [])]}
    return checks


def _shot_checks(db: Session, output_id: int | None) -> dict | None:
    import json

    from ..models import CreativeExecutionOutput

    output = db.get(CreativeExecutionOutput, output_id) if output_id else None
    try:
        return json.loads((output.metadata_json or {})["shot_checks"]) if output else None
    except (KeyError, TypeError, ValueError):
        return None


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/covers")
def video_chain_covers(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import video_chain
    from ..services.content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    return video_chain.work_covers(db, unit_id)


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/publish-copy")
def get_publish_copy(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import publish_copy

    return publish_copy.get(db, user, project_id, unit_id)


@router.put("/api/v1/content-projects/{project_id}/units/{unit_id}/publish-copy")
def put_publish_copy(project_id: int, unit_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import publish_copy

    return publish_copy.save(db, user, project_id, unit_id, payload)


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/decision")
def video_chain_decide(project_id: int, unit_id: int, payload: VideoDecisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import video_chain

    notes = [item.model_dump() for item in payload.notes]
    if payload.stage == "covers":
        return video_chain.decide_covers(db, user, project_id, unit_id, payload.decision, notes)
    # Another writer can hold the SQLite write lock for a few seconds; one lock timeout must not fail the user's click.
    deadline = time.monotonic() + DECISION_BUSY_SECONDS
    while True:
        try:
            return video_chain.decide(db, user, project_id, unit_id, payload.stage, payload.decision, notes)
        except (HTTPException, OperationalError) as exc:
            if not _db_busy(exc):
                raise
            db.rollback()
            if time.monotonic() >= deadline:
                break
            time.sleep(1.5)
    try:
        video_chain._clear_approving(db, unit_id)
    except OperationalError:
        db.rollback()
    raise HTTPException(409, {"code": "video_chain_db_busy", "message": "数据库正忙，这次没通过，请再点一次"})


# Each attempt can itself wait out the 8 s busy_timeout, so 22 s of retries ends near 30 s in total.
DECISION_BUSY_SECONDS = 22


def _db_busy(exc: Exception) -> bool:
    if isinstance(exc, OperationalError):
        return "locked" in str(exc.orig).lower()
    return isinstance(exc.detail, dict) and exc.detail.get("code") == "project_context_busy"


@router.put("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/materials-mode")
def video_chain_materials_mode(project_id: int, unit_id: int, payload: VideoMaterialsModeIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import video_chain

    return video_chain.set_materials_mode(db, user, project_id, unit_id, payload.mode)


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/cover-redo")
def video_chain_cover_redo(project_id: int, unit_id: int, payload: CoverRedoIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import video_chain

    return video_chain.redo_cover(db, user, project_id, unit_id, payload.note)


class VideoMaterialsIn(BaseModel):
    picks: dict[str, int] = Field(default_factory=dict, max_length=200)
    music: int | None = None
    no_music: bool = False


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/materials")
def video_chain_materials(project_id: int, unit_id: int, payload: VideoMaterialsIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import video_chain

    # Same write the video model makes over MCP, so a shot or the music the user drops in counts the same way.
    return video_chain.set_materials(db, user, project_id, unit_id, payload.picks, payload.music, no_music=payload.no_music)


class ReferenceVideoIn(BaseModel):
    material_revision_id: int = Field(gt=0)


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/reference")
def reference_video_state(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import reference_video

    return reference_video.result(db, user, project_id, unit_id)


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/reference")
def reference_video_from_library(project_id: int, unit_id: int, payload: ReferenceVideoIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import reference_video

    return reference_video.start(db, user, project_id, unit_id, material_revision_id=payload.material_revision_id)


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/reference/upload")
async def reference_video_upload(project_id: int, unit_id: int, file: UploadFile, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import reference_video

    content = await file.read(reference_video.MAX_UPLOAD + 1)
    return reference_video.start(db, user, project_id, unit_id, upload=(content, file.filename or "reference.mp4"))


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/reference/grids/{name}")
def reference_video_grid(project_id: int, unit_id: int, name: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from fastapi.responses import FileResponse

    from ..services import reference_video

    record = reference_video.result(db, user, project_id, unit_id)
    grids = ((record.get("summary") or {}).get("files") or {}).get("grids") or []
    path = next((item for item in grids if item.rsplit("/", 1)[-1] == name), None)
    if path is None:
        raise HTTPException(404, {"code": "reference_video_grid_missing", "message": "找不到这张拼图"})
    return FileResponse(path, media_type="image/jpeg")


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/reference/shot-list/export")
def reference_video_export(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import reference_video

    return reference_video.export_shot_list(db, user, project_id, unit_id)


class ArticleWriterIn(BaseModel):
    writer: str = Field(pattern=r"^(platform|external)$")


class ArticleNoteIn(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


class ArticleDecisionIn(BaseModel):
    decision: str = Field(pattern=r"^(approve|accept|changes)$")
    notes: list[ArticleNoteIn] = Field(default_factory=list, max_length=50)


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/article-chain")
def article_chain_state(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import article_chain

    return article_chain.state(db, user, project_id, unit_id)


@router.put("/api/v1/content-projects/{project_id}/units/{unit_id}/article-chain/writer")
def article_chain_writer(project_id: int, unit_id: int, payload: ArticleWriterIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import article_chain

    return article_chain.set_writer(db, user, project_id, unit_id, payload.writer)


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/article-chain/decision")
def article_chain_decide(project_id: int, unit_id: int, payload: ArticleDecisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import article_chain

    return article_chain.decide(db, user, project_id, unit_id, payload.decision, [item.model_dump() for item in payload.notes])


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/article-chain/send-to-review")
def article_chain_send_to_review(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import article_chain

    return article_chain.send_to_review(db, user, project_id, unit_id)


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/article-chain/versions")
def article_chain_versions(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import article_chain

    return article_chain.versions(db, user, project_id, unit_id)


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/article-chain/versions/{master_id}/restore")
def article_chain_restore(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import article_chain

    return article_chain.restore(db, user, project_id, unit_id, master_id)


@router.delete("/api/v1/content-projects/{project_id}/units/{unit_id}/article-chain/versions/{master_id}")
def article_chain_delete(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import article_chain

    return article_chain.delete_version(db, user, project_id, unit_id, master_id)


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/cuts/{output_id}/location")
def video_chain_location(project_id: int, unit_id: int, output_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import video_chain

    return {"path": str(video_chain.cut_location(db, user, project_id, unit_id, output_id))}


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/cuts/{output_id}/reveal")
def video_chain_reveal(project_id: int, unit_id: int, output_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import video_chain
    from .materials import _reveal

    path = video_chain.cut_location(db, user, project_id, unit_id, output_id)
    _reveal(path)
    return {"path": str(path)}



@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/outputs-folder/reveal")
def outputs_folder_reveal(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """审阅与交付「打开成果文件夹」: the approved 成片 selected in Finder, else the project's 导出 folder."""
    import subprocess
    import sys

    from sqlalchemy import select

    from ..models import CreativeExecutionOutput
    from ..services import project_folders, version_prune, video_chain
    from ..services.content_masters import owned_unit
    from .materials import _reveal

    owned_unit(db, project_id, unit_id, user)
    final = version_prune._approved(video_chain._unit_record(db, unit_id), "final")
    output = db.scalar(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id == final,
        CreativeExecutionOutput.role_id == "final", CreativeExecutionOutput.state == "accepted")
        .order_by(CreativeExecutionOutput.attempt_no.desc()).limit(1)) if final else None
    if output is not None:
        try:
            path = video_chain.cut_location(db, user, project_id, unit_id, output.id)
            _reveal(path)
            return {"path": str(path)}
        except HTTPException as exc:
            if (exc.detail or {}).get("code") == "reveal_unsupported":
                raise
    folder = project_folders.ensure_project_dir(db, project_id) / "导出"
    folder.mkdir(parents=True, exist_ok=True)
    if sys.platform != "darwin":
        raise HTTPException(409, {"code": "reveal_unsupported", "message": "只能在 Mac 本机上打开访达"})
    subprocess.run(["open", str(folder)], check=False, timeout=10)
    return {"path": str(folder)}
