from fastapi import HTTPException
from sqlalchemy import func, literal, select, union_all

from ..models import (
    ContentOpportunity,
    ContentOpportunitySignal,
    ContentProject,
    MaterialRevision,
    ProjectFactBoundaryRevision,
    ProjectMaterialReference,
    ProjectSourceBinding,
    ProjectWorkflowOutput,
)
from .system_library import RESOURCE_MODELS


def usage(db, user, kind, resource_id, limit, offset):
    resource = RESOURCE_MODELS[kind]
    if db.scalar(select(resource.id).where(resource.id == resource_id)) is None:
        raise HTTPException(404, "Resource not found")
    coverage = {
        "project_references": "supported",
        "workflow_outputs": "not_applicable",
        "opportunity_signals": "not_applicable",
        "candidate_manifests": "unsupported",
    }
    queries = []

    def project_query(binding, criterion, category):
        return (
            select(
                literal(category).label("category"),
                binding.id.label("id"),
                ContentProject.id.label("target_id"),
                ContentProject.title.label("title"),
                literal("projects").label("route"),
            )
            .join(ContentProject, ContentProject.id == binding.project_id)
            .where(ContentProject.owner_user_id == user.id, criterion)
        )

    if kind == "source":
        queries.append(
            project_query(
                ProjectSourceBinding,
                (ProjectSourceBinding.source_document_id == resource_id) & (ProjectSourceBinding.status == "active"),
                "project_references",
            )
        )
        signal = ContentOpportunitySignal
        queries.append(
            select(
                literal("opportunity_signals").label("category"),
                signal.id.label("id"),
                ContentOpportunity.id.label("target_id"),
                ContentOpportunity.title.label("title"),
                literal("opportunities").label("route"),
            )
            .join(ContentOpportunity, ContentOpportunity.id == signal.opportunity_id)
            .where(
                ContentOpportunity.owner_user_id == user.id,
                signal.signal_type == "source_document",
                signal.source_entity_id == resource_id,
                signal.status == "active",
            )
        )
        coverage["opportunity_signals"] = "supported"
    elif kind == "material":
        revisions = select(MaterialRevision.id).where(MaterialRevision.material_id == resource_id)
        queries.append(
            project_query(
                ProjectMaterialReference,
                ProjectMaterialReference.material_revision_id.in_(revisions)
                & (ProjectMaterialReference.status == "active"),
                "project_references",
            )
        )
        queries.append(
            project_query(
                ProjectWorkflowOutput,
                ProjectWorkflowOutput.entity_id.in_(revisions)
                & (ProjectWorkflowOutput.output_kind == "material_revision"),
                "workflow_outputs",
            )
        )
        coverage["workflow_outputs"] = "supported"
    elif kind == "fact_pack":
        queries.append(
            project_query(
                ProjectFactBoundaryRevision,
                ProjectFactBoundaryRevision.fact_pack_id == resource_id,
                "project_references",
            )
        )
    else:
        coverage["project_references"] = "not_applicable"
    counts = {key: 0 for key, state in coverage.items() if state == "supported"}
    items = []
    total = 0
    if queries:
        rows = union_all(*queries).subquery()
        counts.update(dict(db.execute(select(rows.c.category, func.count()).group_by(rows.c.category)).all()))
        total = sum(counts.values())
        for row in db.execute(
            select(rows).order_by(rows.c.category, rows.c.id.desc()).limit(limit).offset(offset)
        ).mappings():
            items.append(
                {
                    "category": row["category"],
                    "id": row["id"],
                    "title": row["title"],
                    "href": f"/{row['route']}/{row['target_id']}",
                }
            )
    return {
        "type": kind,
        "id": resource_id,
        "counts": counts,
        "coverage": coverage,
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
