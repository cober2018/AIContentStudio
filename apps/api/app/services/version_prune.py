"""Once a video work's 成片 is approved, older 小样 / 成片 versions are deleted for good; one project log line stays."""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..models import (
    CapabilityArtifactRevision, CapabilityUse, ChannelVariantAssetRef, ContentAsset, ContentMasterAssetRef,
    ContentMasterRevision, CreativeExecution, CreativeExecutionOutput, CreativeExecutionPackage, DeliveryTarget,
    ExportRecord, Material, MaterialCollectionItem, MaterialRevision, ProductSkuRevision, ProjectMaterialReference,
    ProviderGenerationTask, PublishedContentRecord, Review,
)

log = logging.getLogger(__name__)


def _revision_ids(value, found: set[int]) -> set[int]:
    # Cover and cut ids sit under keys like vertical_material_revision_id inside master payloads and candidate manifests.
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, int) and "revision_id" in key:
                found.add(item)
            else:
                _revision_ids(item, found)
    elif isinstance(value, list):
        for item in value:
            _revision_ids(item, found)
    return found


def _approved(record: dict, stage: str) -> int | None:
    return next((item["target_id"] for item in reversed(record.get("decisions") or [])
                 if item["stage"] == stage and item["decision"] == "approve" and item.get("outputs_accepted") is not False), None)


def plan(db: Session, project_id: int, unit_id: int) -> dict | None:
    """What would go; None while the 成片 is not approved."""
    from . import project_folders, video_chain

    record = video_chain._unit_record(db, unit_id)
    final = _approved(record, "final")
    if final is None:
        return None
    candidates = db.scalars(select(ContentAsset).where(ContentAsset.content_unit_id == unit_id).order_by(ContentAsset.id.desc())).all()
    delivered = set(db.scalars(select(DeliveryTarget.content_asset_id).where(DeliveryTarget.content_asset_id.in_([row.id for row in candidates])))) | \
        set(db.scalars(select(PublishedContentRecord.content_asset_id).where(PublishedContentRecord.content_asset_id.in_([row.id for row in candidates]))))
    kept_candidates = [row for index, row in enumerate(candidates) if index == 0 or row.id in delivered]
    keep = {final, _approved(record, "sample")} | {(row.candidate_manifest_json or {}).get("execution_id") for row in kept_candidates}
    tasks = [task for task in record.get("tasks") or [] if task["execution_id"] not in keep]
    executions = [row for task in tasks for row in [db.get(CreativeExecution, task["execution_id"])]
                  if row is not None and row.content_unit_id == unit_id]
    gone_ids = {row.id for row in executions}
    outputs = db.scalars(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id.in_(gone_ids))).all() if gone_ids else []
    kept_outputs = db.scalars(select(CreativeExecutionOutput).join(CreativeExecution).where(
        CreativeExecution.content_unit_id == unit_id, CreativeExecutionOutput.execution_id.notin_(gone_ids))).all()

    master = db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                       .order_by(ContentMasterRevision.id.desc()).limit(1))
    used = _revision_ids(master.payload_json if master else {}, set())
    for row in kept_candidates:
        _revision_ids(row.candidate_manifest_json or {}, used)
    used |= {row.material_revision_id for row in kept_outputs if row.material_revision_id}
    revisions = []
    for revision_id in {row.material_revision_id for row in outputs if row.material_revision_id} - used:
        revision = db.get(MaterialRevision, revision_id)
        if revision is None or _referenced_elsewhere(db, revision_id):
            continue
        revisions.append(revision)

    root = project_folders.ensure_project_dir(db, project_id).resolve()
    kept_paths = {Path(row.staging_key).resolve() for row in kept_outputs if row.staging_key.startswith("/")}
    files = {Path(row.staging_key).resolve() for row in outputs if row.staging_key.startswith("/")}
    for revision in revisions:
        path = project_folders.current_path(db, revision)
        if path is not None:
            files.add(path.resolve())
    files = {path for path in files - kept_paths if path.is_relative_to(root) and path.is_file()}
    work = project_folders._work_folder(db, project_id, unit_id)
    folders = [work / f"任务{row.id}" for row in executions if (work / f"任务{row.id}").is_dir()]
    old_candidates = [row for row in candidates if row not in kept_candidates]
    size = sum(path.stat().st_size for path in files) + sum(item.stat().st_size for folder in folders for item in folder.rglob("*") if item.is_file())
    return {"record": record, "executions": executions, "outputs": outputs, "revisions": revisions, "files": sorted(files),
            "folders": folders, "candidates": old_candidates, "bytes": size, "final_execution_id": final}


def _referenced_elsewhere(db: Session, revision_id: int) -> bool:
    checks = [
        select(ContentMasterAssetRef.id).where(ContentMasterAssetRef.material_revision_id == revision_id),
        select(ChannelVariantAssetRef.id).where(ChannelVariantAssetRef.material_revision_id == revision_id),
        select(MaterialRevision.id).where(MaterialRevision.parent_revision_id == revision_id),
        select(ProviderGenerationTask.id).where(ProviderGenerationTask.accepted_material_revision_id == revision_id),
        select(ProductSkuRevision.id).where(ProductSkuRevision.primary_image_revision_id == revision_id),
    ]
    return any(db.scalar(query.limit(1)) is not None for query in checks)


def summary(found: dict) -> dict:
    return {"execution_ids": [row.id for row in found["executions"]], "candidate_ids": [row.id for row in found["candidates"]],
            "material_revision_ids": [row.id for row in found["revisions"]], "file_count": len(found["files"]),
            "folder_count": len(found["folders"]), "bytes": found["bytes"], "kept_execution_id": found["final_execution_id"],
            "files": [str(path) for path in found["files"]], "folders": [str(path) for path in found["folders"]]}


def prune(db: Session, project_id: int, unit_id: int, actor: str | None) -> dict | None:
    from . import video_chain
    from .project_events import record_project_event

    found = plan(db, project_id, unit_id)
    if found is None or not (found["executions"] or found["candidates"] or found["files"] or found["folders"]):
        return None
    info = summary(found)
    gone = set(info["execution_ids"])
    if gone:
        # Learned skills and usage stats outlive the task that produced them.
        db.execute(update(CapabilityUse).where(CapabilityUse.execution_id.in_(gone)).values(execution_id=None))
        db.execute(update(CapabilityArtifactRevision).where(CapabilityArtifactRevision.source_execution_id.in_(gone)).values(source_execution_id=None))
        db.execute(update(CreativeExecution).where(CreativeExecution.retry_of_id.in_(gone)).values(retry_of_id=None))
    for row in found["outputs"]:
        db.delete(row)
    db.flush()
    for revision in found["revisions"]:
        db.execute(ProjectMaterialReference.__table__.delete().where(ProjectMaterialReference.material_revision_id == revision.id))
        material_id = revision.material_id
        db.delete(revision)
        db.flush()
        if db.scalar(select(MaterialRevision.id).where(MaterialRevision.material_id == material_id).limit(1)) is None:
            db.execute(MaterialCollectionItem.__table__.delete().where(MaterialCollectionItem.material_id == material_id))
            material = db.get(Material, material_id)
            if material is not None:
                db.delete(material)
    packages = {row.package_id for row in found["executions"]}
    for row in found["executions"]:
        db.delete(row)
    db.flush()
    for package_id in packages:
        if db.scalar(select(CreativeExecution.id).where(CreativeExecution.package_id == package_id).limit(1)) is None:
            package = db.get(CreativeExecutionPackage, package_id)
            if package is not None:
                db.delete(package)
    for row in found["candidates"]:
        db.execute(Review.__table__.delete().where(Review.content_asset_id == row.id))
        db.execute(ExportRecord.__table__.delete().where(ExportRecord.asset_id == row.id))
        db.delete(row)
    record = found["record"]
    record["tasks"] = [task for task in record.get("tasks") or [] if task["execution_id"] not in gone]
    video_chain._put(db, unit_id, record)
    record_project_event(db, project_id=project_id, event_type="versions.pruned", actor=actor, entity_type="content_unit",
                         entity_id=unit_id, payload={key: value for key, value in info.items() if key not in {"files", "folders"}})
    db.commit()
    # Files go only after the records are gone, so a failed commit never leaves records pointing at deleted files.
    for path in found["files"]:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            log.warning("old version file not deleted: %s", path, exc_info=True)
    for folder in found["folders"]:
        shutil.rmtree(folder, ignore_errors=True)
    return info
