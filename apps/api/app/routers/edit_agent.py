"""Auto-start of rough-cut edits: dispatcher endpoints (MCP token) and page/settings endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
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


@router.get("/api/v1/settings/voice")
def read_voice_settings(user: User = Depends(get_current_user)):
    from ..services import voiceover

    return {"settings": voiceover.settings(), "emotions": {k: v for k, v in voiceover.EMOTIONS.items() if v} | {"auto": "自动"}}


@router.put("/api/v1/settings/voice")
def write_voice_settings(payload: VoiceSettingsIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services import voiceover

    return voiceover.save_settings(db, payload.model_dump(exclude_none=True), user)


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/voiceover")
def make_voiceover(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import voiceover

    return voiceover.generate(db, user, project_id, unit_id)


@router.get("/api/v1/content-projects/{project_id}/units/{unit_id}/voiceover")
def read_voiceover(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services import voiceover

    return voiceover.status(db, user, project_id, unit_id)


class VideoNoteIn(BaseModel):
    time_ms: int | None = Field(default=None, ge=0, le=24 * 3600 * 1000)
    note: str = Field(min_length=1, max_length=2000)


class VideoDecisionIn(BaseModel):
    stage: str = Field(pattern=r"^(draft|sample|final)$")
    decision: str = Field(pattern=r"^(approve|changes)$")
    notes: list[VideoNoteIn] = Field(default_factory=list, max_length=50)


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
    return result


@router.post("/api/v1/content-projects/{project_id}/units/{unit_id}/video-chain/decision")
def video_chain_decide(project_id: int, unit_id: int, payload: VideoDecisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services import video_chain

    return video_chain.decide(db, user, project_id, unit_id, payload.stage, payload.decision, [item.model_dump() for item in payload.notes])


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
