"""One ownership boundary for project-bound runs and definitions."""

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from ..models import (
    AccountWorkflowDefault,
    ContentAccount,
    ContentAsset,
    ContentJob,
    ContentPersona,
    ContentProject,
    ContentSeries,
    ContentUnit,
    DeliveryTarget,
    Draft,
    PersonaWorkflowDefault,
    ProjectWorkflowBinding,
    SeriesWorkflowDefault,
    User,
    Workflow,
    WorkflowRun,
)


def lock_project_context(db: Session, project_id: int, user: User) -> ContentProject:
    project = db.get(ContentProject, project_id)
    if project is None or project.owner_user_id != user.id:
        raise HTTPException(404, "项目不存在")
    # A no-op UPDATE serializes context writers on both PostgreSQL and SQLite.
    try:
        with db.no_autoflush:
            db.execute(update(ContentProject).where(ContentProject.id == project_id).values(updated_at=ContentProject.updated_at).execution_options(synchronize_session=False))
            db.refresh(project)
    except OperationalError as exc:
        db.rollback()
        sqlstate = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
        if "locked" in str(exc.orig).lower() or sqlstate in {"40001", "40P01", "55P03"}:
            raise HTTPException(409, {"code": "project_context_busy", "message": "项目上下文正在更新，请刷新后重试"}) from exc
        raise
    if project.owner_user_id != user.id:
        raise HTTPException(404, "项目不存在")
    return project


def authorize_project_asset(db: Session, asset: ContentAsset, user: User, *, mutate: bool = False) -> None:
    if asset.project_id is None:
        return
    owner = db.execute(
        select(ContentProject.owner_user_id, ContentProject.status, ContentUnit.status)
        .join(ContentUnit, ContentUnit.project_id == ContentProject.id)
        .where(ContentProject.id == asset.project_id, ContentUnit.id == asset.content_unit_id)
    ).first()
    if owner is None or owner[0] != user.id:
        raise HTTPException(404, "候选内容不存在")
    if mutate and (owner[1] == "archived" or owner[2] == "archived"):
        raise HTTPException(409, "已归档项目或单元只可查看历史")


def authorize_project_target(db: Session, target: DeliveryTarget, user: User, *, mutate: bool = False) -> None:
    asset = db.get(ContentAsset, target.content_asset_id)
    if asset is None:
        raise HTTPException(404, "交付目标不存在")
    authorize_project_asset(db, asset, user, mutate=mutate)


def authorize_project_run(db: Session, run: WorkflowRun, user: User, *, mutate: bool = False) -> None:
    if run.content_unit_id is None:
        return
    owner = db.execute(
        select(ContentProject.owner_user_id, ContentUnit.status, ContentProject.status)
        .join(ContentUnit, ContentUnit.project_id == ContentProject.id)
        .where(ContentUnit.id == run.content_unit_id)
    ).first()
    if owner is None or owner[0] != user.id:
        raise HTTPException(404, "运行不存在")
    if mutate and (owner[1] == "archived" or owner[2] == "archived"):
        raise HTTPException(409, "已归档项目或单元的运行历史只可查看")
    if mutate:
        from .content_identity import hierarchy

        unit = db.get(ContentUnit, run.content_unit_id)
        hierarchy(db, user, persona_id=unit.persona_id, account_id=unit.account_id, series_id=unit.series_id, mutable=True)


def authorize_project_job(db: Session, job: ContentJob, user: User, *, mutate: bool = False) -> None:
    if job.workflow_run_id is None:
        return
    run = db.get(WorkflowRun, job.workflow_run_id)
    if run is None:
        raise HTTPException(404, "内容任务不存在")
    authorize_project_run(db, run, user, mutate=mutate)


def authorize_project_draft(db: Session, draft: Draft, user: User, *, mutate: bool = False) -> None:
    authorize_project_job(db, draft.content_job, user, mutate=mutate)


def authorize_project_workflow(db: Session, workflow: Workflow, user: User) -> bool:
    """Return whether a definition is project/persona-scoped after checking all owners."""
    project_owners = set(db.scalars(
        select(ContentProject.owner_user_id)
        .join(ContentUnit, ContentUnit.project_id == ContentProject.id)
        .join(ProjectWorkflowBinding, ProjectWorkflowBinding.unit_id == ContentUnit.id)
        .where(ProjectWorkflowBinding.workflow_id == workflow.id)
    ).all())
    run_owners = set(db.scalars(
        select(ContentProject.owner_user_id)
        .join(ContentUnit, ContentUnit.project_id == ContentProject.id)
        .join(WorkflowRun, WorkflowRun.content_unit_id == ContentUnit.id)
        .where(WorkflowRun.workflow_id == workflow.id)
    ).all())
    persona_owners = set(db.scalars(
        select(ContentPersona.owner_user_id)
        .join(PersonaWorkflowDefault, PersonaWorkflowDefault.persona_id == ContentPersona.id)
        .where(PersonaWorkflowDefault.workflow_id == workflow.id)
    ).all())
    account_owners = set(db.scalars(
        select(ContentPersona.owner_user_id)
        .join(ContentAccount, ContentAccount.persona_id == ContentPersona.id)
        .join(AccountWorkflowDefault, AccountWorkflowDefault.account_id == ContentAccount.id)
        .where(AccountWorkflowDefault.workflow_id == workflow.id)
    ).all())
    series_owners = set(db.scalars(
        select(ContentPersona.owner_user_id)
        .join(ContentAccount, ContentAccount.persona_id == ContentPersona.id)
        .join(ContentSeries, ContentSeries.account_id == ContentAccount.id)
        .join(SeriesWorkflowDefault, SeriesWorkflowDefault.series_id == ContentSeries.id)
        .where(SeriesWorkflowDefault.workflow_id == workflow.id)
    ).all())
    owners = project_owners | run_owners | persona_owners | account_owners | series_owners
    if workflow.scope in {"project", "persona_default", "account_default", "series_default"}:
        if workflow.owner_user_id is None:
            raise HTTPException(404, "工作流不存在")
        owners.add(workflow.owner_user_id)
    if owners and owners != {user.id}:
        raise HTTPException(404, "工作流不存在")
    return bool(owners)
