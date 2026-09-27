"""One ownership boundary for project-bound runs and definitions."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    ContentPersona,
    ContentProject,
    ContentUnit,
    PersonaWorkflowDefault,
    ProjectWorkflowBinding,
    User,
    Workflow,
    WorkflowRun,
)


def authorize_project_run(db: Session, run: WorkflowRun, user: User, *, mutate: bool = False) -> None:
    if run.content_unit_id is None:
        return
    owner = db.execute(
        select(ContentProject.owner_user_id, ContentUnit.status)
        .join(ContentUnit, ContentUnit.project_id == ContentProject.id)
        .where(ContentUnit.id == run.content_unit_id)
    ).first()
    if owner is None or owner[0] != user.id:
        raise HTTPException(404, "运行不存在")
    if mutate and owner[1] == "archived":
        raise HTTPException(409, "已归档单元的运行历史只可查看")


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
    owners = project_owners | run_owners | persona_owners
    if workflow.scope in {"project", "persona_default"}:
        if workflow.owner_user_id is None:
            raise HTTPException(404, "工作流不存在")
        owners.add(workflow.owner_user_id)
    if owners and owners != {user.id}:
        raise HTTPException(404, "工作流不存在")
    return bool(owners)
