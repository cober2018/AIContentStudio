"""Project-first Candidate and Review APIs."""

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor, require_editor_or_reviewer
from ..models import ChannelVariantRevision, ContentAsset, ContentProject, MaterialRevision, User
from ..services import delivery as delivery_service
from ..services import project_review as review_service
from ..services import project_review_projection as projection
from ..services.project_authorization import authorize_project_asset
from ..services.project_projection_context import ProjectProjectionContext
from .content_projects import owned_project, owned_unit
from .delivery import GenericTargetIn, _target_json

router = APIRouter(prefix="/api/v1", tags=["project-review"])


@router.get("/review-center/projects")
def review_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    projects = db.scalars(select(ContentProject).where(ContentProject.owner_user_id == user.id).order_by(ContentProject.id.desc())).all()
    # 一个批量 context 预取全部单元的候选/评审/投递数据，替代逐单元 N+1
    context = ProjectProjectionContext(db, [project.id for project in projects])
    return [projection.project_projection(db, project, context=context) for project in projects]


@router.get("/review-center/projects/{project_id}")
def review_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return projection.project_projection(db, owned_project(db, project_id, user))


@router.get("/review-center/projects/{project_id}/units/{unit_id}")
def review_unit(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return projection.unit_projection(db, owned_unit(db, project_id, unit_id, user))


@router.get("/review-center/projects/{project_id}/units/{unit_id}/candidates")
def review_candidates(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_unit(db, project_id, unit_id, user)
    return [_candidate_json(asset) for asset in projection.candidate_rows(db, unit_id)]


@router.get("/review-center/projects/{project_id}/units/{unit_id}/candidates/{candidate_id}")
def review_candidate(project_id: int, unit_id: int, candidate_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = review_service._candidate(db, project_id, unit_id, candidate_id, user, mutate=False)
    return _candidate_json(asset, include_manifest=True)


@router.get("/review-center/projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/diff")
def review_candidate_diff(project_id: int, unit_id: int, candidate_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    current = review_service._candidate(db, project_id, unit_id, candidate_id, user, mutate=False)
    manifest = current.candidate_manifest_json or {}
    if manifest.get("schema_version") == 5:
        projection.candidate_preview(current)
        previous = db.scalar(select(ContentAsset).join(
            ChannelVariantRevision, ContentAsset.channel_variant_revision_id == ChannelVariantRevision.id,
        ).where(ContentAsset.content_unit_id == unit_id, ContentAsset.id < candidate_id,
                ChannelVariantRevision.variant_key == manifest["variant"]["variant_key"])
            .order_by(ContentAsset.id.desc()).limit(1))
    else:
        previous = db.scalar(select(ContentAsset).where(ContentAsset.content_unit_id == unit_id, ContentAsset.id < candidate_id).order_by(ContentAsset.id.desc()).limit(1))
    return projection.candidate_diff(previous, current)


@router.get("/review-center/projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/renders/{revision_id}")
def review_candidate_render(project_id: int, unit_id: int, candidate_id: int, revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..services.candidates import candidate_hash
    from ..services.materials import read_bytes_checked, sniff_mime

    asset = review_service._candidate(db, project_id, unit_id, candidate_id, user, mutate=False)
    manifest = asset.candidate_manifest_json or {}
    if manifest.get("schema_version") == 5:
        manifest = projection._verify_frozen_variant(asset)
        ref = next((item for item in manifest["assets"] if item["material_revision_id"] == revision_id), None)
        if ref is None:
            raise HTTPException(404, "候选未引用此素材版本")
        revision = db.get(MaterialRevision, revision_id)
        if (revision is None or revision.content_hash != ref["content_hash_snapshot"]
                or revision.material is None or revision.material.status != "active"
                or revision.status in {"revoked", "archived"}):
            raise HTTPException(409, "冻结素材版本不可用")
        content = read_bytes_checked(db, revision, require_public=True)
        if revision.mime_type not in {"image/png", "image/jpeg", "image/webp", "image/gif", "video/mp4"} or sniff_mime(content, None) != revision.mime_type:
            raise HTTPException(409, "冻结素材媒体类型未验证")
        return Response(content, media_type=revision.mime_type, headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
    if manifest.get("schema_version") != 4:
        raise HTTPException(404, "此候选没有Master渲染")
    output = next((row for row in (manifest.get("render") or {}).get("outputs", []) if row.get("material_revision_id") == revision_id), None)
    if output is None:
        raise HTTPException(404, "候选未引用此渲染版本")
    if candidate_hash(manifest) != asset.candidate_hash:
        raise HTTPException(409, "候选完整性检查失败")
    revision = db.get(MaterialRevision, revision_id)
    if revision is None or revision.content_hash != output.get("content_hash") or revision.mime_type != output.get("mime_type"):
        raise HTTPException(409, "冻结渲染版本不一致")
    content = read_bytes_checked(db, revision, require_public=True)
    if revision.mime_type not in {"image/png", "image/jpeg", "image/webp", "image/gif", "video/mp4"} or sniff_mime(content, None) != revision.mime_type:
        raise HTTPException(409, "渲染媒体类型未验证")
    return Response(content, media_type=revision.mime_type, headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


class FreezeIn(BaseModel):
    content_master_revision_id: int | None = None
    channel_variant_revision_id: int | None = None
    expected_payload_hash: str | None = Field(default=None, pattern="^[0-9a-f]{64}$")


class CandidateDecisionIn(BaseModel):
    candidate_hash: str = Field(min_length=64, max_length=64)
    comment: str | None = None
    warning_dispositions: dict[str, str] | None = None


def _candidate_json(asset: ContentAsset, *, include_manifest: bool = False) -> dict:
    data = {
        "id": asset.id, "project_id": asset.project_id, "unit_id": asset.content_unit_id,
        "identity_snapshot_id": asset.identity_snapshot_id, "workflow_run_id": asset.workflow_run_id,
        "title": asset.title, "channel": asset.channel,
        "content_form": asset.content_form, "status": asset.status,
        "artifact_kind": asset.artifact_kind, "content_master_revision_id": asset.content_master_revision_id,
        "channel_variant_revision_id": asset.channel_variant_revision_id,
        "manifest_schema_version": (asset.candidate_manifest_json or {}).get("schema_version"),
        "candidate_hash": asset.candidate_hash, "approved_candidate_hash": asset.approved_candidate_hash,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
    }
    if include_manifest:
        data["manifest"] = asset.candidate_manifest_json
        data["preview"] = projection.candidate_preview(asset)
    return data


@router.post("/content-projects/{project_id}/units/{unit_id}/candidates/freeze", status_code=201)
def freeze(project_id: int, unit_id: int, payload: FreezeIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    sources = (payload.content_master_revision_id, payload.channel_variant_revision_id)
    if sum(source is not None for source in sources) != 1:
        raise HTTPException(422, "必须且只能选择Content Master或ChannelVariant作为候选来源")
    if (payload.content_master_revision_id is not None or payload.channel_variant_revision_id is not None) and payload.expected_payload_hash is None:
        raise HTTPException(422, "Master或Variant冻结必须提交expected_payload_hash")
    if payload.content_master_revision_id is not None:
        candidate = review_service.freeze_master_candidate(db, project_id, unit_id, payload.content_master_revision_id, user, expected_payload_hash=payload.expected_payload_hash)
    else:
        candidate = review_service.freeze_variant_candidate(db, project_id, unit_id, payload.channel_variant_revision_id, user, expected_payload_hash=payload.expected_payload_hash)
    return _candidate_json(candidate, include_manifest=True)


@router.get("/content-projects/{project_id}/units/{unit_id}/candidates")
def list_candidates(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_unit(db, project_id, unit_id, user)
    rows = db.scalars(select(ContentAsset).where(ContentAsset.project_id == project_id, ContentAsset.content_unit_id == unit_id).order_by(ContentAsset.id.desc())).all()
    return [_candidate_json(asset) for asset in rows]


@router.get("/content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}")
def get_candidate(project_id: int, unit_id: int, candidate_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = review_service._candidate(db, project_id, unit_id, candidate_id, user, mutate=False)
    authorize_project_asset(db, asset, user)
    return _candidate_json(asset, include_manifest=True)


@router.post("/content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/approve")
def approve(project_id: int, unit_id: int, candidate_id: int, payload: CandidateDecisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor_or_reviewer)):
    return _candidate_json(review_service.decide_candidate(db, project_id, unit_id, candidate_id, payload.candidate_hash, "approved", payload.comment, user, warning_dispositions=payload.warning_dispositions), include_manifest=True)


@router.post("/content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/request-changes")
def request_changes(project_id: int, unit_id: int, candidate_id: int, payload: CandidateDecisionIn, db: Session = Depends(get_db), user: User = Depends(require_editor_or_reviewer)):
    return _candidate_json(review_service.decide_candidate(db, project_id, unit_id, candidate_id, payload.candidate_hash, "changes_requested", payload.comment, user), include_manifest=True)


@router.post("/content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/delivery-authorizations", status_code=201)
def authorize_delivery(project_id: int, unit_id: int, candidate_id: int, payload: GenericTargetIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    asset = review_service._candidate(db, project_id, unit_id, candidate_id, user, mutate=True)
    return _target_json(delivery_service.authorize_target(db, asset, payload, user))
