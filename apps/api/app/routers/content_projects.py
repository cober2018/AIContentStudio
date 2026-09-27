"""Persistent content projects, personas, and units."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor, require_editor_or_reviewer
from ..models import (
    ContentPersona, ContentProject, ContentUnit, DataSnapshot, MaterialRevision, PersonaWorkflowDefault,
    ProjectWorkflowBinding, ProjectWorkflowOutput, User, Workflow, WorkflowRun,
)
from ..services.project_authorization import authorize_project_run, authorize_project_workflow
from ..services.project_workflows import execution_options, new_workflow_version, resolve_placeholders, validate_definition, validate_portable, validate_reusable_profiles
from ..services import workflow_engine
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
    modality: str
    channel_id: str | None = None
    pinned_workflow_id: int | None = None


class UnitPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    status: str | None = None
    channel_id: str | None = None
    persona_id: int | None = None
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


def owned_project(db: Session, project_id: int, user: User) -> ContentProject:
    project = db.get(ContentProject, project_id)
    if project is None or project.owner_user_id != user.id:
        raise HTTPException(404, "项目不存在")
    return project


def owned_unit(db: Session, project_id: int, unit_id: int, user: User) -> ContentUnit:
    owned_project(db, project_id, user)
    unit = db.get(ContentUnit, unit_id)
    if unit is None or unit.project_id != project_id:
        raise HTTPException(404, "内容单元不存在")
    return unit


def _persona_json(persona: ContentPersona) -> dict:
    return {"id": persona.id, "name": persona.name}


def _unit_json(unit: ContentUnit) -> dict:
    return {
        "id": unit.id,
        "project_id": unit.project_id,
        "persona_id": unit.persona_id,
        "modality": unit.modality,
        "channel_id": unit.channel_id,
        "title": unit.title,
        "status": unit.status,
        "pinned_workflow_id": unit.pinned_workflow_id,
    }


def _project_json(project: ContentProject, db: Session) -> dict:
    units = db.scalars(select(ContentUnit).where(ContentUnit.project_id == project.id).order_by(ContentUnit.id)).all()
    return {
        "id": project.id,
        "title": project.title,
        "objective": project.objective,
        "status": project.status,
        "units": [_unit_json(unit) for unit in units],
    }


@router.get("/content-personas")
def list_personas(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [_persona_json(row) for row in db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == user.id).order_by(ContentPersona.id))]


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
    return _persona_json(persona)


@router.get("/content-projects")
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(ContentProject).where(ContentProject.owner_user_id == user.id).order_by(ContentProject.id.desc())).all()
    return [_project_json(row, db) for row in rows]


@router.post("/content-projects", status_code=201)
def create_project(payload: ProjectIn, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    project = ContentProject(owner_user_id=user.id, title=payload.title, objective=payload.objective)
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_json(project, db)


@router.get("/content-projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _project_json(owned_project(db, project_id, user), db)


@router.patch("/content-projects/{project_id}")
def patch_project(payload: ProjectPatch, project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    project = owned_project(db, project_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    return _project_json(project, db)


@router.delete("/content-projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    project = owned_project(db, project_id, user)
    if db.scalar(select(ContentUnit.id).where(ContentUnit.project_id == project_id).limit(1)) is not None:
        raise HTTPException(409, "请先处理项目中的内容单元")
    db.delete(project)
    db.commit()


@router.post("/content-projects/{project_id}/units", status_code=201)
def create_unit(payload: UnitIn, project_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    owned_project(db, project_id, user)
    persona = db.get(ContentPersona, payload.persona_id)
    if persona is None or persona.owner_user_id != user.id:
        raise HTTPException(404, "内容角色不存在")
    if payload.modality not in {"text", "graphic", "video"}:
        raise HTTPException(422, "不支持的内容形态")
    selected_workflow = payload.pinned_workflow_id
    if selected_workflow is not None:
        workflow = db.get(Workflow, selected_workflow)
        if workflow is None:
            raise HTTPException(404, "工作流版本不存在")
        authorize_project_workflow(db, workflow, user)
        if workflow.scope != "persona_default" or workflow.workflow_key != f"persona.{persona.id}.{payload.modality}" or workflow.status != "published":
            raise HTTPException(409, "只能选用当前身份与内容形态的角色默认版本")
    if selected_workflow is None:
        binding = db.scalar(select(PersonaWorkflowDefault).where(PersonaWorkflowDefault.persona_id == persona.id, PersonaWorkflowDefault.modality == payload.modality))
        selected_workflow = binding.workflow_id if binding else None
    unit = ContentUnit(project_id=project_id, persona_id=persona.id, modality=payload.modality, channel_id=payload.channel_id, title=payload.title, pinned_workflow_id=selected_workflow)
    db.add(unit)
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
    unit = owned_unit(db, project_id, unit_id, user)
    if unit.status == "archived":
        raise HTTPException(409, "已归档单元不可编辑")
    fields = payload.model_fields_set
    persona_id = payload.persona_id if "persona_id" in fields else unit.persona_id
    modality = payload.modality if "modality" in fields else unit.modality
    if persona_id is None or modality not in {"text", "graphic", "video"}:
        raise HTTPException(422, "身份或内容形态无效")
    persona = db.get(ContentPersona, persona_id)
    if persona is None or persona.owner_user_id != user.id:
        raise HTTPException(404, "内容角色不存在")
    if payload.rebind_default and "pinned_workflow_id" in fields:
        raise HTTPException(422, "重新绑定默认与指定工作流版本不能同时提交")
    selection_changed = persona_id != unit.persona_id or modality != unit.modality or payload.rebind_default or "pinned_workflow_id" in fields and payload.pinned_workflow_id != unit.pinned_workflow_id
    selected_workflow = unit.pinned_workflow_id
    if selection_changed:
        if "pinned_workflow_id" in fields:
            selected_workflow = payload.pinned_workflow_id
        else:
            default = db.scalar(select(PersonaWorkflowDefault).where(PersonaWorkflowDefault.persona_id == persona_id, PersonaWorkflowDefault.modality == modality))
            selected_workflow = default.workflow_id if default else None
        if selected_workflow is not None:
            workflow = db.get(Workflow, selected_workflow)
            if workflow is None:
                raise HTTPException(404, "工作流版本不存在")
            authorize_project_workflow(db, workflow, user)
            if workflow.scope != "persona_default" or workflow.workflow_key != f"persona.{persona_id}.{modality}" or workflow.status != "published":
                raise HTTPException(409, "工作流版本与身份或内容形态不匹配")
    values = {"title": payload.title if "title" in fields else unit.title, "channel_id": payload.channel_id if "channel_id" in fields else unit.channel_id}
    if selection_changed and _has_execution_history(db, unit.id):
        replacement = ContentUnit(project_id=project_id, persona_id=persona_id, modality=modality, pinned_workflow_id=selected_workflow, **values)
        db.add(replacement)
        unit.status = "archived"
        db.commit()
        db.refresh(replacement)
        return _unit_json(replacement)
    if selection_changed:
        binding = db.scalar(select(ProjectWorkflowBinding).where(ProjectWorkflowBinding.unit_id == unit.id))
        if binding:
            db.delete(binding)
        unit.persona_id = persona_id
        unit.modality = modality
        unit.pinned_workflow_id = selected_workflow
    for field, value in values.items():
        setattr(unit, field, value)
    if "status" in fields and payload.status is not None:
        unit.status = payload.status
    db.commit()
    return _unit_json(unit)


@router.delete("/content-projects/{project_id}/units/{unit_id}", status_code=204)
def delete_unit(project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    unit = owned_unit(db, project_id, unit_id, user)
    if _has_execution_history(db, unit.id):
        unit.status = "archived"
    else:
        binding = db.scalar(select(ProjectWorkflowBinding).where(ProjectWorkflowBinding.unit_id == unit.id))
        if binding:
            db.delete(binding)
        db.delete(unit)
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
        "source": "project_override" if binding and binding.workflow_id == workflow.id else "persona_default",
    }


@router.post("/content-projects/{project_id}/units/{unit_id}/workflow-override", status_code=201)
def save_workflow_override(payload: WorkflowSaveIn, project_id: int, unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_editor)):
    unit = owned_unit(db, project_id, unit_id, user)
    if unit.status == "archived":
        raise HTTPException(409, "已归档单元不可修改工作流")
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
    persona = _owned_persona(db, persona_id, user)
    if modality not in {"text", "graphic", "video"}:
        raise HTTPException(422, "不支持的内容形态")
    if payload.source_project_id is not None or payload.source_unit_id is not None:
        if payload.source_project_id is None or payload.source_unit_id is None:
            raise HTTPException(422, "来源项目和单元必须同时提供")
        source_unit = owned_unit(db, payload.source_project_id, payload.source_unit_id, user)
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
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "角色默认工作流已被更新，请刷新后再保存") from exc
    return _binding_json(db, binding)


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
    rows = db.scalars(select(ProjectWorkflowOutput).where(ProjectWorkflowOutput.project_id == project_id, ProjectWorkflowOutput.output_kind == "material_revision").order_by(ProjectWorkflowOutput.id.desc())).all()
    assets = []
    for row in rows:
        revision = db.get(MaterialRevision, row.entity_id)
        if revision is None:
            continue
        assets.append({
            "id": row.id,
            "material_revision_id": revision.id,
            "material_id": revision.material_id,
            "kind": revision.material.kind if revision.material else None,
            "content_hash": revision.content_hash,
            "mime_type": revision.mime_type,
            "rights_status": revision.rights_status,
            "public_use_allowed": revision.public_use_allowed,
            "project_id": row.project_id,
            "unit_id": row.unit_id,
            "run_id": row.run_id,
            "node_id": row.node_id,
            "attempt_id": row.attempt_id,
            "provenance": row.provenance_json,
        })
    return assets


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
