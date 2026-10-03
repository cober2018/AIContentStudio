"""Project-scoped Content Master revision API."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin, require_editor
from ..models import ContentMasterRevision, User
from ..services.content_masters import (
    current_checks,
    get_readiness,
    get_revision,
    list_checks,
    list_revisions,
    preview_graphic_upgrade,
    preview_text_upgrade,
    preview_video_upgrade,
    run_checks,
    save_revision,
    upgrade_graphic_master,
    upgrade_text_master,
    upgrade_video_master,
)
from ..services.graphic_master_diff import structured_graphic_diff
from ..services.text_master_ai import suggest_text_edit
from ..services.text_master_diff import structured_diff
from ..services.video_derivations import derive_video_master
from ..services.video_master_diff import structured_video_diff
from . import CapabilityInputRoute

router = APIRouter(prefix="/api/v1", tags=["content-masters"], route_class=CapabilityInputRoute)


class MasterRevisionIn(BaseModel):
    expected_revision: int = Field(default=0, ge=0)
    expected_context_hash: str | None = Field(default=None, pattern="^[0-9a-f]{64}$")
    idempotency_key: str = Field(min_length=1, max_length=150)
    modality: str | None = None
    payload_schema: str | None = None
    payload: dict
    content_form: str | None = Field(default=None, max_length=100)
    parent_revision_id: int | None = None
    source_kind: str = Field(default="user_edit", max_length=30)
    edit_summary: dict = Field(default_factory=dict)
    asset_refs: list[dict] = Field(default_factory=list, max_length=250)
    evidence_refs: list[dict] = Field(default_factory=list, max_length=250)
    render_attestation: dict | None = None


class MasterSeedIn(BaseModel):
    expected_revision: int = Field(default=0, ge=0)
    idempotency_key: str = Field(min_length=1, max_length=150)
    project_output_id: int


class MasterUpgradeIn(BaseModel):
    expected_revision: int = Field(ge=1)
    expected_payload_hash: str = Field(pattern="^[0-9a-f]{64}$")
    expected_context_hash: str = Field(pattern="^[0-9a-f]{64}$")
    idempotency_key: str = Field(min_length=1, max_length=150)


class VideoUpgradeIn(MasterUpgradeIn):
    model_config = ConfigDict(extra="forbid")

    payload: dict
    asset_refs: list[dict] = Field(default_factory=list, max_length=250)
    evidence_refs: list[dict] = Field(default_factory=list, max_length=250)
    acknowledged_warnings: list[str] = Field(max_length=20)


class VideoDerivationIn(MasterUpgradeIn):
    model_config = ConfigDict(extra="forbid")

    operation: str = Field(pattern="^(long_to_short|aspect_ratio|shot_regeneration)$")
    parameters: dict = Field(default_factory=dict)
    result_origin: str = Field(pattern="^(user_edit|deterministic_local|provider)$")
    result_payload: dict | None = None
    asset_refs: list[dict] = Field(default_factory=list, max_length=250)
    evidence_refs: list[dict] = Field(default_factory=list, max_length=250)


class TextSuggestionIn(BaseModel):
    base_payload_hash: str = Field(pattern="^[0-9a-f]{64}$")
    working_document: dict
    operation: str = Field(pattern="^(rewrite|expand|shorten|tone|restructure)$")
    selection: dict
    instruction: str = Field(default="", max_length=2000)


class ASRSuggestionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_key: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,150}$")
    provider_version: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,50}$")
    source_revision_id: int = Field(ge=1)
    base_payload_hash: str = Field(pattern="^[0-9a-f]{64}$")


class MediaRenderPreviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    renderer_key: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,150}$")
    renderer_version: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,50}$")
    expected_payload_hash: str = Field(pattern="^[0-9a-f]{64}$")
    expected_context_hash: str = Field(pattern="^[0-9a-f]{64}$")
    canvas_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/media-render-previews")
def preview_media_render(project_id: int, unit_id: int, master_id: int, payload: MediaRenderPreviewIn,
                         db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services.media_renderers import stage_render

    return stage_render(db, user, project_id, unit_id, master_id, payload.model_dump())


class MediaRenderOutputIn(MediaRenderPreviewIn):
    output_mime: str = Field(pattern=r"^(image/(png|jpeg|webp)|video/mp4)$")


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/media-render-outputs")
def execute_media_render(project_id: int, unit_id: int, master_id: int, payload: MediaRenderOutputIn,
                         db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services.media_renderers import stage_render

    return stage_render(db, user, project_id, unit_id, master_id, payload.model_dump(), verified_execution=True)


@router.get("/asr-provider-options")
def asr_provider_options(user: User = Depends(get_current_user)):
    from ..services.content_harness import providers
    from ..services.local_mlx_asr_provider import LocalMLXASRProvider

    options = []
    for row in providers.registry.list("asr_provider"):
        provider = providers.registry.resolve("asr_provider", row.key, row.version)
        if type(provider) is LocalMLXASRProvider:
            options.append(provider.option())
        else:
            options.append({"key": row.key, "version": row.version, "verified": False, "available": True,
                            "execution_mode": "cloud", "reason": "runtime_checked_on_request",
                            "label": "MiniMax 云端转录" if row.key == "minimax.cli" else row.label or row.key})
    return options


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/asr-suggestions")
def suggest_asr(project_id: int, unit_id: int, master_id: int, payload: ASRSuggestionIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services.asr_suggestions import suggest

    return suggest(db, project_id, unit_id, master_id, user, payload.model_dump())


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions")
def get_master_revisions(project_id: int, unit_id: int, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": list_revisions(db, project_id, unit_id, user, limit=limit, offset=offset), "limit": limit, "offset": offset}


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/current")
def get_current_master(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = list_revisions(db, project_id, unit_id, user, limit=1)
    return items[0] if items else None


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}")
def get_master_revision(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_revision(db, project_id, unit_id, master_id, user)


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/text-v2-upgrade-preview")
def get_text_upgrade_preview(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return preview_text_upgrade(db, project_id, unit_id, master_id, user)


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/text-v2-upgrade", dependencies=[Depends(require_editor)])
def commit_text_upgrade(project_id: int, unit_id: int, master_id: int, body: MasterUpgradeIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return upgrade_text_master(db, project_id=project_id, unit_id=unit_id, master_id=master_id, user=user, payload=body.model_dump())


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/graphic-v2-upgrade-preview")
def get_graphic_upgrade_preview(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return preview_graphic_upgrade(db, project_id, unit_id, master_id, user)


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/graphic-v2-upgrade", dependencies=[Depends(require_editor)])
def commit_graphic_upgrade(project_id: int, unit_id: int, master_id: int, body: MasterUpgradeIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return upgrade_graphic_master(db, project_id=project_id, unit_id=unit_id, master_id=master_id, user=user, payload=body.model_dump())


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/video-v2-upgrade-preview")
def get_video_upgrade_preview(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return preview_video_upgrade(db, project_id, unit_id, master_id, user)


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/video-v2-upgrade", dependencies=[Depends(require_editor)])
def commit_video_upgrade(project_id: int, unit_id: int, master_id: int, body: VideoUpgradeIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return upgrade_video_master(db, project_id=project_id, unit_id=unit_id, master_id=master_id, user=user, payload=body.model_dump())


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/derive", dependencies=[Depends(require_editor)])
def commit_video_derivation(project_id: int, unit_id: int, master_id: int, body: VideoDerivationIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return derive_video_master(db, project_id=project_id, unit_id=unit_id, master_id=master_id, user=user, request=body.model_dump())


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions", dependencies=[Depends(require_editor)])
def create_master_revision(project_id: int, unit_id: int, body: MasterRevisionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload=body.model_dump())


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/text-suggestions", dependencies=[Depends(require_editor)])
async def text_suggestion(project_id: int, unit_id: int, master_id: int, body: TextSuggestionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return await suggest_text_edit(db, project_id=project_id, unit_id=unit_id, master_id=master_id, user=user, payload=body.model_dump())


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/checks")
def get_master_checks(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": list_checks(db, project_id, unit_id, master_id, user)}


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/diff")
def diff_master_revision(project_id: int, unit_id: int, master_id: int, compare_to_id: int = Query(..., ge=1), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    target = db.get(ContentMasterRevision, master_id)
    if target is not None and target.payload_schema.startswith("graphic.master."):
        return structured_graphic_diff(db, project_id=project_id, unit_id=unit_id, from_master_id=compare_to_id, to_master_id=master_id, user=user)
    if target is not None and target.payload_schema == "video.master.v2":
        return structured_video_diff(db, project_id=project_id, unit_id=unit_id, from_master_id=compare_to_id, to_master_id=master_id, user=user)
    return structured_diff(db, project_id=project_id, unit_id=unit_id, from_master_id=compare_to_id, to_master_id=master_id, user=user)


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/readiness")
def get_master_readiness(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_readiness(db, project_id, unit_id, master_id, user)


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/checks", dependencies=[Depends(require_editor)])
def execute_master_checks(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": run_checks(db, project_id, unit_id, master_id, user)}


@router.get("/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/checks/current")
def get_current_master_checks(project_id: int, unit_id: int, master_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": current_checks(db, project_id, unit_id, master_id, user)}


@router.post("/content-projects/{project_id}/units/{unit_id}/master-revisions/from-output")
def seed_master_from_output(project_id: int, unit_id: int, body: MasterSeedIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    from ..services.content_masters import seed_from_output

    return seed_from_output(db, project_id=project_id, unit_id=unit_id, user=user, output_id=body.project_output_id, idempotency_key=body.idempotency_key, expected_revision=body.expected_revision)
