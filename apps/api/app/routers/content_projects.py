"""Persistent content projects, personas, and units."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor, require_editor_or_reviewer
from ..models import (
    AccountWorkflowDefault, ContentPersona, ContentProject, ContentUnit, CreativeBriefRevision, DataSnapshot, PersonaWorkflowDefault, SeriesWorkflowDefault,
    ProjectWorkflowBinding, ProjectWorkflowOutput, User, Workflow, WorkflowRun,
)
from ..services.project_authorization import authorize_project_run, authorize_project_workflow
from ..services.project_events import record_project_event
from ..services.project_brief import checksum_brief, current_brief, serialize_brief
from ..services.project_assets import shared_assets
from ..services.project_workflows import execution_options, new_workflow_version, resolve_placeholders, validate_definition, validate_portable, validate_reusable_profiles
from ..services import workflow_engine
from ..services import content_identity
from ..services.data_source_plugins import assert_executable, descriptors as data_source_descriptors
from .workflows import NodeCompleteIn, _serialize_run, list_node_attempts

router = APIRouter(prefix="/api/v1", tags=["content-projects"])


class PersonaIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ProjectIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    objective: str = ""


class ProjectPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    objective: str | None = None
    status: str | None = None


class UnitIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    persona_id: int
    account_id: int | None = None
    series_id: int | None = None
    modality: str
    channel_id: str | None = None
    pinned_workflow_id: int | None = None


class UnitPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    status: str | None = None
    channel_id: str | None = None
    persona_id: int | None = None
    account_id: int | None = None
    series_id: int | None = None
    rebind_identity: bool = False
    modality: str | None = None
    pinned_workflow_id: int | None = None
    rebind_default: bool = False


class WorkflowSaveIn(BaseModel):
    expected_revision: int = Field(ge=0)
    definition: dict
    source_project_id: int | None = None
    source_unit_id: int | None = None


class ProjectRunIn(BaseModel):
    params: dict = Field(default_factory=dict)


class BriefRevisionIn(BaseModel):
    expected_revision: int = Field(ge=0)
    objective: str = Field(min_length=1)
    primary_audience: str | None = None
    core_message: str | None = None
    angle: str | None = None
    required_evidence: list = Field(default_factory=list)
    content_constraints: list = Field(default_factory=list)
    identity_scope: list = Field(default_factory=list)
    modality_scope: list = Field(default_factory=list)
    channel_scope: list = Field(default_factory=list)
    cta: str | None = None
    references: list = Field(default_factory=list)


def owned_project(db: Session, project_id: int, user: User) -> ContentProject:
    project = db.get(ContentProject, project_id)
    if project is None or project.owner_user_id != user.id:
        raise HTTPException(404, "项目不存在")
    return project


def mutable_project(db: Session, project_id: int, user: User) -> ContentProject:
    project = owned_project(db, project_id, user)
    if project.status == "archived":
        raise HTTPException(409, "已归档项目仅可查看历史")
    return project


def owned_unit(db: Session, project_id: int, unit_id: int, user: User) -> ContentUnit:
    owned_project(db, project_id, user)
    unit = db.get(ContentUnit, unit_id)
    if unit is None or unit.project_id != project_id:
        raise HTTPException(404, "内容单元不存在")
    return unit


def _persona_json(db: Session, persona: ContentPersona) -> dict:
    revision = content_identity.current_revision(db, "persona", persona.id)
    return {"id": persona.id, "name": persona.name, "brand_id": persona.brand_id, "status": persona.status, "current_revision": revision.revision_no if revision else 0}


def _unit_json(unit: ContentUnit) -> dict:
    return {
        "id": unit.id,
        "project_id": unit.project_id,
        "persona_id": unit.persona_id,
        "account_id": unit.account_id,
        "series_id": unit.series_id,
        "identity_snapshot_id": unit.identity_snapshot_id,
        "identity_state": "frozen" if unit.identity_snapshot_id else "legacy_identity",
        "modality": unit.modality,
        "channel_id": unit.channel_id,
        "title": unit.title,
        "status": unit.status,
        "pinned_workflow_id": unit.pinned_workflow_id,
    }


def _effective_default(db: Session, *, persona_id: int, account_id: int | None, series_id: int | None, modality: str) -> tuple[str, PersonaWorkflowDefault | AccountWorkflowDefault | SeriesWorkflowDefault | None]:
    for source, model, column, entity_id in (
        ("series", SeriesWorkflowDefault, SeriesWorkflowDefault.series_id, series_id),
        ("account", AccountWorkflowDefault, AccountWorkflowDefault.account_id, account_id),
        ("persona", PersonaWorkflowDefault, PersonaWorkflowDefault.persona_id, persona_id),
    ):
        if entity_id is not None:
            binding = db.scalar(select(model).where(column == entity_id, model.modality == modality))
            if binding is not None:
                return source, binding
    return "unbound", None


def _default_version_matches(workflow: Workflow, *, persona_id: int, account_id: int | None, series_id: int | None, modality: str) -> bool:
    return workflow.status == "published" and (
        (workflow.scope == "persona_default" and workflow.workflow_key == f"persona.{persona_id}.{modality}")
        or (account_id is not None and workflow.scope == "account_default" and workflow.workflow_key == f"account.{account_id}.{modality}")
        or (series_id is not None and workflow.scope == "series_default" and workflow.workflow_key == f"series.{series_id}.{modality}")
    )


def _project_json(project: ContentProject, db: Session) -> dict:
    units = db.scalars(select(ContentUnit).where(ContentUnit.project_id == project.id).order_by(ContentUnit.id)).all()
    brief = current_brief(db, project.id)
    return {
        "id": project.id,
        "title": project.title,
        "objective": brief.objective if brief else project.objective,
        "status": project.status,
        "units": [_unit_json(unit) for unit in units],
    }


@router.get("/content-personas")
def list_personas(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [_persona_json(db, row) for row in db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == user.id).order_by(ContentPersona.id))]


@router.get("/data-source-plugins")
def list_data_source_plugins(user: User = Depends(get_current_user)):
    return data_source_descriptors()


@router.get("/workflow-execution-options")
def list_workflow_execution_options(user: User = Depends(get_current_user)):
    return execution_options()


@router.post("/content-personas", status_code=201)
def create_persona(payload: PersonaIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    persona = ContentPersona(owner_user_id=user.id, name=payload.name)
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return _persona_json(db, persona)


@router.get("/content-projects")
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(ContentProject).where(ContentProject.owner_user_id == user.id).order_by(ContentProject.id.desc())).all()
    return [_project_json(row, db) for row in rows]


@router.post("/content-projects", status_code=201)
def create_project(payload: ProjectIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    project = ContentProject(owner_user_id=user.id, title=payload.title, objective=payload.objective)
    db.add(project)
    db.flush()
    record_project_event(db, project_id=project.id, event_type="project.created", actor=user.email, entity_type="content_project", entity_id=project.id)
    db.commit()
    db.refresh(project)
    return _project_json(project, db)


@router.get("/content-projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _project_json(owned_project(db, project_id, user), db)


@router.patch("/content-projects/{project_id}")
def patch_project(payload: ProjectPatch, project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    project = mutable_project(db, project_id, user)
    if "objective" in payload.model_fields_set:
        raise HTTPException(422, "项目目标请保存为 Brief 新版本")
    if payload.status == "archived":
        raise HTTPException(422, "请使用归档接口归档项目")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    record_project_event(db, project_id=project_id, event_type="project.updated", actor=user.email, entity_type="content_project", entity_id=project_id)
    db.commit()
    return _project_json(project, db)


@router.delete("/content-projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    project = owned_project(db, project_id, user)
    if project.status == "archived":
        return
    project.status = "archived"
    record_project_event(db, project_id=project_id, event_type="project.archived", actor=user.email, entity_type="content_project", entity_id=project_id)
    db.commit()


@router.get("/content-projects/{project_id}/brief")
def get_project_brief(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    row = current_brief(db, project_id)
    return serialize_brief(row) if row else None


@router.get("/content-projects/{project_id}/brief/revisions")
def list_project_briefs(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    rows = db.scalars(select(CreativeBriefRevision).where(CreativeBriefRevision.project_id == project_id).order_by(CreativeBriefRevision.revision_no.desc()).limit(100)).all()
    return [serialize_brief(row) for row in rows]


@router.get("/content-projects/{project_id}/brief/revisions/{revision_id}")
def get_project_brief_revision(project_id: int, revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    row = db.get(CreativeBriefRevision, revision_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(404, "Brief 版本不存在")
    return serialize_brief(row)


@router.post("/content-projects/{project_id}/brief/revisions", status_code=201)
def save_project_brief(payload: BriefRevisionIn, project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    for entry in payload.identity_scope:
        if not isinstance(entry, dict) or not any(key in entry for key in ("brand_id", "persona_id", "account_id", "series_id")):
            continue
        if not set(entry) <= {"brand_id", "persona_id", "account_id", "series_id"}:
            raise HTTPException(422, "身份引用包含不支持的字段")
        if entry.get("persona_id") is None:
            if set(entry) != {"brand_id"} or not isinstance(entry["brand_id"], int):
                raise HTTPException(422, "账号和栏目引用必须包含角色")
            content_identity.owned_entity(db, user, "brand", entry["brand_id"])
            continue
        if any(value is not None and not isinstance(value, int) for value in entry.values()):
            raise HTTPException(422, "身份引用 ID 必须为整数")
        selected = content_identity.hierarchy(db, user, persona_id=entry["persona_id"], account_id=entry.get("account_id"), series_id=entry.get("series_id"))
        if "brand_id" in entry and entry["brand_id"] != (selected.brand.id if selected.brand else None):
            raise HTTPException(422, "品牌与角色不属于同一身份层级")
    previous = current_brief(db, project_id)
    current_revision = previous.revision_no if previous else 0
    if payload.expected_revision != current_revision:
        raise HTTPException(409, "Brief 已更新，请刷新后重试")
    data = payload.model_dump(exclude={"expected_revision"})
    row = CreativeBriefRevision(
        project_id=project_id,
        revision_no=current_revision + 1,
        parent_revision_id=previous.id if previous else None,
        objective=payload.objective,
        primary_audience=payload.primary_audience,
        core_message=payload.core_message,
        angle=payload.angle,
        required_evidence_json=payload.required_evidence,
        content_constraints_json=payload.content_constraints,
        identity_scope_json=payload.identity_scope,
        modality_scope_json=payload.modality_scope,
        channel_scope_json=payload.channel_scope,
        cta=payload.cta,
        references_json=payload.references,
        checksum=checksum_brief(data),
        created_by=user.email,
    )
    db.add(row)
    try:
        db.flush()
        record_project_event(db, project_id=project_id, event_type="brief.revision_created", actor=user.email, entity_type="creative_brief_revision", entity_id=row.id, payload={"revision_no": row.revision_no, "checksum": row.checksum})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Brief 已更新，请刷新后重试") from exc
    return serialize_brief(row)


@router.post("/content-projects/{project_id}/units", status_code=201)
def create_unit(payload: UnitIn, project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    persona = db.get(ContentPersona, payload.persona_id)
    if persona is None or persona.owner_user_id != user.id:
        raise HTTPException(404, "内容角色不存在")
    if payload.modality not in {"text", "graphic", "video"}:
        raise HTTPException(422, "不支持的内容形态")
    snapshot = content_identity.create_snapshot(db, user, persona_id=persona.id, account_id=payload.account_id, series_id=payload.series_id)
    selected_workflow = payload.pinned_workflow_id
    if selected_workflow is not None:
        workflow = db.get(Workflow, selected_workflow)
        if workflow is None:
            raise HTTPException(404, "工作流版本不存在")
        authorize_project_workflow(db, workflow, user)
        if not _default_version_matches(workflow, persona_id=persona.id, account_id=payload.account_id, series_id=payload.series_id, modality=payload.modality):
            raise HTTPException(409, "工作流版本与身份或内容形态不匹配")
    if selected_workflow is None:
        _, binding = _effective_default(db, persona_id=persona.id, account_id=payload.account_id, series_id=payload.series_id, modality=payload.modality)
        selected_workflow = binding.workflow_id if binding else None
    unit = ContentUnit(project_id=project_id, persona_id=persona.id, account_id=payload.account_id, series_id=payload.series_id, identity_snapshot_id=snapshot.id, modality=payload.modality, channel_id=payload.channel_id, title=payload.title, pinned_workflow_id=selected_workflow)
    db.add(unit)
    db.flush()
    record_project_event(db, project_id=project_id, event_type="unit.created", actor=user.email, entity_type="content_unit", entity_id=unit.id, payload={"identity_snapshot_id": snapshot.id})
    db.commit()
    db.refresh(unit)
    return _unit_json(unit)


@router.get("/content-projects/{project_id}/units")
def list_units(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    rows = db.scalars(select(ContentUnit).where(ContentUnit.project_id == project_id).order_by(ContentUnit.id)).all()
    return [_unit_json(row) for row in rows]


@router.get("/content-projects/{project_id}/units/{unit_id}")
def get_unit(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _unit_json(owned_unit(db, project_id, unit_id, user))


@router.patch("/content-projects/{project_id}/units/{unit_id}")
def patch_unit(payload: UnitPatch, project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    unit = owned_unit(db, project_id, unit_id, user)
    if unit.status == "archived":
        raise HTTPException(409, "已归档单元不可编辑")
    if payload.status == "archived":
        raise HTTPException(422, "请使用删除接口归档内容单元")
    fields = payload.model_fields_set
    persona_id = payload.persona_id if "persona_id" in fields else unit.persona_id
    account_id = payload.account_id if "account_id" in fields else unit.account_id
    series_id = payload.series_id if "series_id" in fields else unit.series_id
    modality = payload.modality if "modality" in fields else unit.modality
    if persona_id is None or modality not in {"text", "graphic", "video"}:
        raise HTTPException(422, "身份或内容形态无效")
    persona = db.get(ContentPersona, persona_id)
    if persona is None or persona.owner_user_id != user.id:
        raise HTTPException(404, "内容角色不存在")
    if persona_id != unit.persona_id and "account_id" not in fields and unit.account_id is not None:
        raise HTTPException(422, "更换角色时请显式选择或清空账号")
    if account_id != unit.account_id and "series_id" not in fields and unit.series_id is not None:
        raise HTTPException(422, "更换账号时请显式选择或清空栏目")
    content_identity.hierarchy(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id, mutable=True)
    if payload.rebind_default and "pinned_workflow_id" in fields:
        raise HTTPException(422, "重新绑定默认与指定工作流版本不能同时提交")
    hierarchy_changed = (persona_id, account_id, series_id) != (unit.persona_id, unit.account_id, unit.series_id)
    modality_changed = modality != unit.modality
    workflow_changed = "pinned_workflow_id" in fields and payload.pinned_workflow_id != unit.pinned_workflow_id
    selection_changed = hierarchy_changed or modality_changed or payload.rebind_identity or payload.rebind_default or workflow_changed
    preserve_override = payload.rebind_identity and not (hierarchy_changed or modality_changed or payload.rebind_default or workflow_changed)
    selected_workflow = unit.pinned_workflow_id
    if selection_changed and not preserve_override:
        if "pinned_workflow_id" in fields:
            selected_workflow = payload.pinned_workflow_id
        else:
            _, default = _effective_default(db, persona_id=persona_id, account_id=account_id, series_id=series_id, modality=modality)
            selected_workflow = default.workflow_id if default else None
        if selected_workflow is not None:
            workflow = db.get(Workflow, selected_workflow)
            if workflow is None:
                raise HTTPException(404, "工作流版本不存在")
            authorize_project_workflow(db, workflow, user)
            if not _default_version_matches(workflow, persona_id=persona_id, account_id=account_id, series_id=series_id, modality=modality):
                raise HTTPException(409, "工作流版本与身份或内容形态不匹配")
    values = {"title": payload.title if "title" in fields else unit.title, "channel_id": payload.channel_id if "channel_id" in fields else unit.channel_id}
    previous_snapshot_id = unit.identity_snapshot_id
    snapshot = content_identity.create_snapshot(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id) if selection_changed else None
    if selection_changed and _has_execution_history(db, unit.id):
        replacement = ContentUnit(project_id=project_id, persona_id=persona_id, account_id=account_id, series_id=series_id, identity_snapshot_id=snapshot.id if snapshot else unit.identity_snapshot_id, modality=modality, pinned_workflow_id=selected_workflow, **values)
        db.add(replacement)
        unit.status = "archived"
        db.flush()
        if preserve_override:
            binding = db.scalar(select(ProjectWorkflowBinding).where(ProjectWorkflowBinding.unit_id == unit.id))
            if binding:
                db.add(ProjectWorkflowBinding(unit_id=replacement.id, workflow_id=binding.workflow_id, revision=binding.revision))
        record_project_event(db, project_id=project_id, event_type="unit.replaced", actor=user.email, entity_type="content_unit", entity_id=replacement.id, payload={"replaced_unit_id": unit.id, "old_identity_snapshot_id": previous_snapshot_id, "new_identity_snapshot_id": replacement.identity_snapshot_id})
        db.commit()
        db.refresh(replacement)
        return _unit_json(replacement)
    if selection_changed:
        binding = db.scalar(select(ProjectWorkflowBinding).where(ProjectWorkflowBinding.unit_id == unit.id))
        if binding and not preserve_override:
            db.delete(binding)
        unit.persona_id = persona_id
        unit.account_id = account_id
        unit.series_id = series_id
        if snapshot:
            unit.identity_snapshot_id = snapshot.id
        unit.modality = modality
        unit.pinned_workflow_id = selected_workflow
    for field, value in values.items():
        setattr(unit, field, value)
    if "status" in fields and payload.status is not None:
        unit.status = payload.status
    record_project_event(db, project_id=project_id, event_type="unit.updated", actor=user.email, entity_type="content_unit", entity_id=unit.id, payload={"old_identity_snapshot_id": previous_snapshot_id, "new_identity_snapshot_id": unit.identity_snapshot_id} if selection_changed else None)
    db.commit()
    return _unit_json(unit)


@router.delete("/content-projects/{project_id}/units/{unit_id}", status_code=204)
def delete_unit(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    unit = owned_unit(db, project_id, unit_id, user)
    event_type = "unit.archived" if _has_execution_history(db, unit.id) else "unit.deleted"
    if _has_execution_history(db, unit.id):
        unit.status = "archived"
    else:
        binding = db.scalar(select(ProjectWorkflowBinding).where(ProjectWorkflowBinding.unit_id == unit.id))
        if binding:
            db.delete(binding)
        db.delete(unit)
    record_project_event(db, project_id=project_id, event_type=event_type, actor=user.email, entity_type="content_unit", entity_id=unit_id)
    db.commit()


def _has_execution_history(db: Session, unit_id: int) -> bool:
    return any(db.scalar(select(model.id).where(column == unit_id).limit(1)) is not None for model, column in (
        (WorkflowRun, WorkflowRun.content_unit_id),
        (DataSnapshot, DataSnapshot.unit_id),
        (ProjectWorkflowOutput, ProjectWorkflowOutput.unit_id),
    ))


def _binding_json(db: Session, binding: ProjectWorkflowBinding | PersonaWorkflowDefault | None) -> dict:
    workflow = db.get(Workflow, binding.workflow_id) if binding else None
    return {
        "revision": binding.revision if binding else 0,
        "workflow_id": workflow.id if workflow else None,
        "workflow_version": workflow.version if workflow else None,
        "definition_checksum": workflow.checksum if workflow else None,
        "definition": workflow.definition_json if workflow else {"nodes": [], "edges": [], "visual_order": []},
    }


@router.get("/content-projects/{project_id}/units/{unit_id}/workflow-override")
def get_workflow_override(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_unit(db, project_id, unit_id, user)
    binding = db.scalar(select(ProjectWorkflowBinding).where(ProjectWorkflowBinding.unit_id == unit_id))
    return _binding_json(db, binding)


@router.get("/content-projects/{project_id}/units/{unit_id}/effective-workflow")
def get_effective_workflow(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    unit = owned_unit(db, project_id, unit_id, user)
    workflow = db.get(Workflow, unit.pinned_workflow_id) if unit.pinned_workflow_id else None
    if workflow is None:
        return {**_binding_json(db, None), "source": "unbound"}
    authorize_project_workflow(db, workflow, user)
    binding = db.scalar(select(ProjectWorkflowBinding).where(ProjectWorkflowBinding.unit_id == unit.id))
    return {
        "revision": binding.revision if binding and binding.workflow_id == workflow.id else 0,
        "workflow_id": workflow.id,
        "workflow_version": workflow.version,
        "definition_checksum": workflow.checksum,
        "definition": workflow.definition_json,
        "source": "project_override" if binding and binding.workflow_id == workflow.id else workflow.scope,
    }


@router.post("/content-projects/{project_id}/units/{unit_id}/workflow-override", status_code=201)
def save_workflow_override(payload: WorkflowSaveIn, project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    unit = owned_unit(db, project_id, unit_id, user)
    if unit.status == "archived":
        raise HTTPException(409, "已归档单元不可修改工作流")
    content_identity.hierarchy(db, user, persona_id=unit.persona_id, account_id=unit.account_id, series_id=unit.series_id, mutable=True)
    binding = db.scalar(select(ProjectWorkflowBinding).where(ProjectWorkflowBinding.unit_id == unit_id))
    current_revision = binding.revision if binding else 0
    if payload.expected_revision != current_revision:
        raise HTTPException(409, "项目工作流已被更新，请刷新后再保存")
    try:
        definition = validate_definition(payload.definition)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        workflow = new_workflow_version(db, key=f"project.unit.{unit.id}", name=f"{unit.title} 工作流", definition=definition, owner_user_id=user.id, scope="project", created_by=user.email)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "项目工作流版本冲突，请刷新后再保存") from exc
    if binding:
        result = db.execute(update(ProjectWorkflowBinding).where(ProjectWorkflowBinding.id == binding.id, ProjectWorkflowBinding.revision == payload.expected_revision).values(workflow_id=workflow.id, revision=payload.expected_revision + 1))
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "项目工作流已被更新，请刷新后再保存")
        db.expire(binding)
    else:
        binding = ProjectWorkflowBinding(unit_id=unit.id, workflow_id=workflow.id, revision=1)
        db.add(binding)
    unit.pinned_workflow_id = workflow.id
    record_project_event(db, project_id=project_id, event_type="workflow.override_saved", actor=user.email, entity_type="workflow", entity_id=workflow.id, payload={"unit_id": unit_id, "revision": current_revision + 1, "checksum": workflow.checksum})
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "项目工作流已被更新，请刷新后再保存") from exc
    return _binding_json(db, binding)


def _owned_persona(db: Session, persona_id: int, user: User) -> ContentPersona:
    persona = db.get(ContentPersona, persona_id)
    if persona is None or persona.owner_user_id != user.id:
        raise HTTPException(404, "内容角色不存在")
    return persona


@router.get("/content-personas/{persona_id}/default-workflows/{modality}")
def get_persona_default(persona_id: int, modality: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _owned_persona(db, persona_id, user)
    binding = db.scalar(select(PersonaWorkflowDefault).where(PersonaWorkflowDefault.persona_id == persona_id, PersonaWorkflowDefault.modality == modality))
    return _binding_json(db, binding)


@router.post("/content-personas/{persona_id}/default-workflows/{modality}", status_code=201)
def save_persona_default(payload: WorkflowSaveIn, persona_id: int, modality: str, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    persona = content_identity.owned_entity(db, user, "persona", persona_id, mutable=True)
    if modality not in {"text", "graphic", "video"}:
        raise HTTPException(422, "不支持的内容形态")
    if payload.source_project_id is not None or payload.source_unit_id is not None:
        if payload.source_project_id is None or payload.source_unit_id is None:
            raise HTTPException(422, "来源项目和单元必须同时提供")
        source_unit = owned_unit(db, payload.source_project_id, payload.source_unit_id, user)
        mutable_project(db, payload.source_project_id, user)
        if source_unit.persona_id != persona_id or source_unit.modality != modality:
            raise HTTPException(422, "来源单元的身份或形态与默认模板不一致")
    binding = db.scalar(select(PersonaWorkflowDefault).where(PersonaWorkflowDefault.persona_id == persona_id, PersonaWorkflowDefault.modality == modality))
    current_revision = binding.revision if binding else 0
    if payload.expected_revision != current_revision:
        raise HTTPException(409, "角色默认工作流已被更新，请刷新后再保存")
    try:
        definition = validate_portable(validate_definition(payload.definition), source_project_id=payload.source_project_id, source_unit_id=payload.source_unit_id)
        validate_reusable_profiles(db, definition)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        workflow = new_workflow_version(db, key=f"persona.{persona.id}.{modality}", name=f"{persona.name} × {modality}", definition=definition, owner_user_id=user.id, scope="persona_default", created_by=user.email)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "角色默认工作流版本冲突，请刷新后再保存") from exc
    if binding:
        result = db.execute(update(PersonaWorkflowDefault).where(PersonaWorkflowDefault.id == binding.id, PersonaWorkflowDefault.revision == payload.expected_revision).values(workflow_id=workflow.id, revision=payload.expected_revision + 1))
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "角色默认工作流已被更新，请刷新后再保存")
        db.expire(binding)
    else:
        binding = PersonaWorkflowDefault(persona_id=persona.id, modality=modality, workflow_id=workflow.id, revision=1)
        db.add(binding)
    if payload.source_project_id is not None:
        record_project_event(db, project_id=payload.source_project_id, event_type="workflow.role_default_saved", actor=user.email, entity_type="workflow", entity_id=workflow.id, payload={"unit_id": payload.source_unit_id, "revision": current_revision + 1, "checksum": workflow.checksum})
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "角色默认工作流已被更新，请刷新后再保存") from exc
    return _binding_json(db, binding)


@router.get("/content-identities/effective-workflow")
def get_hierarchical_default(persona_id: int, modality: str, account_id: int | None = None, series_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    content_identity.hierarchy(db, user, persona_id=persona_id, account_id=account_id, series_id=series_id)
    if modality not in {"text", "graphic", "video"}:
        raise HTTPException(422, "不支持的内容形态")
    source, binding = _effective_default(db, persona_id=persona_id, account_id=account_id, series_id=series_id, modality=modality)
    return {**_binding_json(db, binding), "source": source}


def _scoped_default_owner(db: Session, user: User, kind: str, entity_id: int, *, mutable: bool):
    return content_identity.owned_entity(db, user, kind, entity_id, mutable=mutable)


def _scoped_default_binding(db: Session, kind: str, entity_id: int, modality: str):
    model = AccountWorkflowDefault if kind == "account" else SeriesWorkflowDefault
    owner_column = model.account_id if kind == "account" else model.series_id
    return db.scalar(select(model).where(owner_column == entity_id, model.modality == modality))


def _save_scoped_default(db: Session, user: User, *, kind: str, entity_id: int, modality: str, payload: WorkflowSaveIn) -> dict:
    entity = _scoped_default_owner(db, user, kind, entity_id, mutable=True)
    if modality not in {"text", "graphic", "video"}:
        raise HTTPException(422, "不支持的内容形态")
    if payload.source_project_id is not None or payload.source_unit_id is not None:
        if payload.source_project_id is None or payload.source_unit_id is None:
            raise HTTPException(422, "来源项目和单元必须同时提供")
        mutable_project(db, payload.source_project_id, user)
        source_unit = owned_unit(db, payload.source_project_id, payload.source_unit_id, user)
        if source_unit.modality != modality or (kind == "account" and source_unit.account_id != entity_id) or (kind == "series" and source_unit.series_id != entity_id):
            raise HTTPException(422, "来源单元身份或形态与默认模板不一致")
    binding = _scoped_default_binding(db, kind, entity_id, modality)
    current_revision = binding.revision if binding else 0
    if payload.expected_revision != current_revision:
        raise HTTPException(409, "默认工作流已被更新，请刷新后再保存")
    try:
        definition = validate_portable(validate_definition(payload.definition), source_project_id=payload.source_project_id, source_unit_id=payload.source_unit_id)
        validate_reusable_profiles(db, definition)
        workflow = new_workflow_version(db, key=f"{kind}.{entity_id}.{modality}", name=f"{entity.name} × {modality}", definition=definition, owner_user_id=user.id, scope=f"{kind}_default", created_by=user.email)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "默认工作流版本冲突，请刷新后再保存") from exc
    if binding:
        result = db.execute(update(type(binding)).where(type(binding).id == binding.id, type(binding).revision == payload.expected_revision).values(workflow_id=workflow.id, revision=current_revision + 1))
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "默认工作流已被更新，请刷新后再保存")
        db.expire(binding)
    else:
        model = AccountWorkflowDefault if kind == "account" else SeriesWorkflowDefault
        binding = model(**{f"{kind}_id": entity_id}, modality=modality, workflow_id=workflow.id, revision=1)
        db.add(binding)
    if payload.source_project_id is not None:
        record_project_event(db, project_id=payload.source_project_id, event_type="workflow.identity_default_saved", actor=user.email, entity_type="workflow", entity_id=workflow.id, payload={"unit_id": payload.source_unit_id, "scope": kind, "revision": current_revision + 1, "checksum": workflow.checksum})
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "默认工作流已被更新，请刷新后再保存") from exc
    return _binding_json(db, binding)


@router.get("/content-accounts/{account_id}/default-workflows/{modality}")
def get_account_default(account_id: int, modality: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _scoped_default_owner(db, user, "account", account_id, mutable=False)
    return _binding_json(db, _scoped_default_binding(db, "account", account_id, modality))


@router.post("/content-accounts/{account_id}/default-workflows/{modality}", status_code=201)
def save_account_default(payload: WorkflowSaveIn, account_id: int, modality: str, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _save_scoped_default(db, user, kind="account", entity_id=account_id, modality=modality, payload=payload)


@router.get("/content-series/{series_id}/default-workflows/{modality}")
def get_series_default(series_id: int, modality: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _scoped_default_owner(db, user, "series", series_id, mutable=False)
    return _binding_json(db, _scoped_default_binding(db, "series", series_id, modality))


@router.post("/content-series/{series_id}/default-workflows/{modality}", status_code=201)
def save_series_default(payload: WorkflowSaveIn, series_id: int, modality: str, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    return _save_scoped_default(db, user, kind="series", entity_id=series_id, modality=modality, payload=payload)


def _owned_run(db: Session, project_id: int, unit_id: int, run_id: int, user: User) -> WorkflowRun:
    owned_unit(db, project_id, unit_id, user)
    run = db.get(WorkflowRun, run_id)
    if run is None or run.content_unit_id != unit_id:
        raise HTTPException(404, "运行不存在")
    return run


@router.get("/content-projects/{project_id}/units/{unit_id}/runs")
def list_project_runs(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_unit(db, project_id, unit_id, user)
    rows = db.scalars(select(WorkflowRun).where(WorkflowRun.content_unit_id == unit_id).order_by(WorkflowRun.id.desc()).limit(100)).all()
    return [{"id": row.id, "status": row.status, "workflow_id": row.workflow_id, "definition_checksum": row.definition_checksum} for row in rows]


@router.post("/content-projects/{project_id}/units/{unit_id}/runs", status_code=201)
def start_project_run(payload: ProjectRunIn, project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    mutable_project(db, project_id, user)
    unit = owned_unit(db, project_id, unit_id, user)
    if unit.status == "archived":
        raise HTTPException(409, "已归档单元不可启动新运行")
    workflow = db.get(Workflow, unit.pinned_workflow_id) if unit.pinned_workflow_id else None
    if workflow is None or not workflow.enabled or workflow.status != "published":
        raise HTTPException(409, "内容单元尚未绑定可运行的工作流版本")
    authorize_project_workflow(db, workflow, user)
    try:
        validate_definition(workflow.definition_json)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    for node in workflow.definition_json.get("nodes", []):
        if node.get("kind") == "Data":
            try:
                config = resolve_placeholders(node.get("config") or {}, project_id=project_id, unit_id=unit_id, run_params=payload.params)
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from exc
            try:
                assert_executable(db, config.get("data_source_plugin_key", ""), str(config.get("source_ref", "")))
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from exc
    try:
        run = workflow_engine.start_run(db, workflow, payload.params, user, content_unit_id=unit.id)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _serialize_run(db, run)


@router.get("/content-projects/{project_id}/units/{unit_id}/runs/{run_id}")
def get_project_run(project_id: int, unit_id: int, run_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _serialize_run(db, _owned_run(db, project_id, unit_id, run_id, user))


@router.get("/content-projects/{project_id}/units/{unit_id}/runs/{run_id}/nodes/{node_id}/attempts")
def get_project_attempts(project_id: int, unit_id: int, run_id: int, node_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _owned_run(db, project_id, unit_id, run_id, user)
    return list_node_attempts(run_id, node_id, db, user)


@router.post("/content-projects/{project_id}/units/{unit_id}/runs/{run_id}/nodes/{node_id}/rerun")
def rerun_project_node(project_id: int, unit_id: int, run_id: int, node_id: str, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    run = _owned_run(db, project_id, unit_id, run_id, user)
    authorize_project_run(db, run, user, mutate=True)
    try:
        return _serialize_run(db, workflow_engine.rerun_node(db, run, node_id, user))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/content-projects/{project_id}/units/{unit_id}/runs/{run_id}/nodes/{node_id}/rerun-from-here")
def rerun_project_from_here(project_id: int, unit_id: int, run_id: int, node_id: str, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    run = _owned_run(db, project_id, unit_id, run_id, user)
    authorize_project_run(db, run, user, mutate=True)
    try:
        return _serialize_run(db, workflow_engine.rerun_from_here(db, run, node_id, user))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/content-projects/{project_id}/units/{unit_id}/runs/{run_id}/nodes/{node_id}/complete")
def complete_project_node(payload: NodeCompleteIn, project_id: int, unit_id: int, run_id: int, node_id: str, db: Session = Depends(get_db), user: User = Depends(require_editor_or_reviewer)):
    run = _owned_run(db, project_id, unit_id, run_id, user)
    authorize_project_run(db, run, user, mutate=True)
    try:
        return _serialize_run(db, workflow_engine.complete_node(db, run, node_id, payload.payload, user))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


def _snapshot_json(row: DataSnapshot) -> dict:
    return {
        "id": row.id,
        "unit_id": row.unit_id,
        "run_id": row.run_id,
        "node_id": row.node_id,
        "plugin_key": row.plugin_key,
        "source_ref": row.source_ref,
        "source_version": row.source_version,
        "checksum": row.checksum,
        "normalized_output": row.normalized_output,
        "lineage": row.lineage_json,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/content-projects/{project_id}/units/{unit_id}/snapshots")
def list_unit_snapshots(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_unit(db, project_id, unit_id, user)
    rows = db.scalars(select(DataSnapshot).where(DataSnapshot.unit_id == unit_id).order_by(DataSnapshot.id.desc()).limit(100)).all()
    return [_snapshot_json(row) for row in rows]


@router.get("/content-projects/{project_id}/units/{unit_id}/snapshots/{snapshot_id}")
def get_unit_snapshot(project_id: int, unit_id: int, snapshot_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_unit(db, project_id, unit_id, user)
    row = db.get(DataSnapshot, snapshot_id)
    if row is None or row.unit_id != unit_id:
        raise HTTPException(404, "数据快照不存在")
    return _snapshot_json(row)


@router.get("/content-projects/{project_id}/shared-assets")
def list_project_shared_assets(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_project(db, project_id, user)
    return shared_assets(db, project_id)


@router.get("/content-projects/{project_id}/units/{unit_id}/outputs")
def list_unit_outputs(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_unit(db, project_id, unit_id, user)
    rows = db.scalars(select(ProjectWorkflowOutput).where(ProjectWorkflowOutput.project_id == project_id, ProjectWorkflowOutput.unit_id == unit_id).order_by(ProjectWorkflowOutput.id.desc()).limit(100)).all()
    return [{
        "id": row.id,
        "output_kind": row.output_kind,
        "entity_id": row.entity_id,
        "run_id": row.run_id,
        "node_id": row.node_id,
        "attempt_id": row.attempt_id,
        "provenance": row.provenance_json,
    } for row in rows]
