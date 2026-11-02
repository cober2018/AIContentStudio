"""数据保留策略：分级清理无界增长表，库体积可控（防"杂乱数据拖垮系统"）。

- llm_run：调用记录永久保留（审计），但 raw_output / parsed 超过 N 天的清空大字段
- audit_log：超过 90 天删除；未处理的项目素材孤儿字节候选例外
- workflow_run / workflow_step：终态超过 30 天删除（steps 先删）
- export_record：超过 90 天删除
- 存储清理（run_storage_cleanup，每日一次）：采集文章全文、未采用的生成结果文件、
  未采用且未挂项目的候选素材；SQLite 每周 VACUUM。天数存 system_settings.storage_cleanup
清理只按主键范围批量删，SQLite WAL 下安全；每类限量分批，避免长事务。
"""

import logging
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import JSON, LargeBinary, Text, cast, delete, func, inspect, or_, select, union, update
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import flag_modified

from ..models import (
    AuditLog,
    ContentAsset,
    ContentMasterRevision,
    DataSnapshot,
    ExportRecord,
    LLMRun,
    MaterialRevision,
    ProjectWorkflowOutput,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepAttempt,
)

logger = logging.getLogger(__name__)

DEFAULTS = {
    "llm_run_payload_days": 30,   # 超期清空大字段（行保留）
    "audit_log_days": 90,
    "material_orphan_grace_days": 1,
    "workflow_run_days": 30,
    "export_record_days": 90,
    "batch": 500,
}


def _cutoff(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)


def _process_material_orphan_candidates(db, *, cutoff: datetime, batch: int) -> dict:
    from .material_byte_lock import locked_hash
    from .material_storage import provider

    rows = db.scalars(select(AuditLog).where(AuditLog.event == "material.upload_orphan_candidate", AuditLog.created_at < cutoff).order_by(AuditLog.id).limit(batch)).all()
    removed = referenced = invalid = 0
    storage = provider()
    for row in rows:
        detail = row.detail_json or {}
        raw_path = detail.get("file_path")
        content_hash = detail.get("content_hash")
        relative = Path(raw_path) if isinstance(raw_path, str) else Path()
        safe = (
            isinstance(content_hash, str) and len(content_hash) == 64
            and relative.parts[:2] == ("material", content_hash[:2])
            and relative.name.startswith(content_hash + ".")
            and relative.as_posix().startswith("material/")
        )
        if not safe:
            invalid += 1
            row.event = "material.upload_orphan_resolved"
            row.detail_json = {**detail, "cleanup_status": "invalid_path_not_deleted"}
            db.commit()
            continue
        with locked_hash(content_hash):
            path_value = str(relative)
            in_use = any((
                db.scalar(select(MaterialRevision.id).where(MaterialRevision.file_path == path_value).limit(1)),
            ))
            if in_use:
                referenced += 1
                row.detail_json = {**detail, "cleanup_status": "retained_referenced"}
            else:
                try:
                    storage.delete_if_unreferenced(relative.as_posix(), expected_hash=content_hash)
                except Exception:  # noqa: BLE001 Cleanup leaves unresolved evidence on any storage failure.
                    logger.warning("material_orphan_cleanup_failed audit_id=%s", row.id)
                    continue
                removed += 1
                row.detail_json = {**detail, "cleanup_status": "removed_or_missing"}
        row.event = "material.upload_orphan_resolved"
        db.commit()
    return {"material_orphan_bytes_removed": removed, "material_orphan_referenced": referenced, "material_orphan_invalid": invalid}


def run_retention(db, cfg: dict | None = None) -> dict:
    """执行一轮清理；cfg 覆盖 DEFAULTS（配置化留给后续，当前用默认档位）。"""
    c = {**DEFAULTS, **(cfg or {})}
    stats = {}

    # Resolve orphan bytes before taking any database write locks.
    stats.update(_process_material_orphan_candidates(db, cutoff=_cutoff(c["material_orphan_grace_days"]), batch=c["batch"]))

    # 1) llm_run 大字段瘦身（行保留：审计线索 id/purpose/status/model 不动）
    cutoff = _cutoff(c["llm_run_payload_days"])
    rows = db.scalars(
        select(LLMRun.id).where(LLMRun.created_at < cutoff, LLMRun.raw_output.is_not(None)).limit(c["batch"])
    ).all()
    for rid in rows:
        run = db.get(LLMRun, rid)
        run.raw_output = None
        # Validated AI receipts remain live provenance for immutable Masters and Variants.
        if run.purpose not in {"text_master_edit", "channel_variant_adapt"}:
            run.parsed_output_json = None
    stats["llm_run_payloads_cleared"] = len(rows)

    # 2) audit_log: unresolved byte candidates survive normal log expiry.
    res = db.execute(delete(AuditLog).where(AuditLog.created_at < _cutoff(c["audit_log_days"]), AuditLog.event != "material.upload_orphan_candidate"))
    stats["audit_log_deleted"] = res.rowcount

    # Immutable project/output/attempt lineage must survive the legacy sweep.
    old_runs = db.scalars(
        select(WorkflowRun.id)
        .where(WorkflowRun.finished_at.is_not(None), WorkflowRun.finished_at < _cutoff(c["workflow_run_days"]))
        .where(WorkflowRun.content_unit_id.is_(None))
        .where(~select(WorkflowStepAttempt.id).where(WorkflowStepAttempt.run_id == WorkflowRun.id).exists())
        .where(~select(ContentAsset.id).where(ContentAsset.workflow_run_id == WorkflowRun.id).exists())
        .where(~select(ContentMasterRevision.id).where(ContentMasterRevision.origin_workflow_run_id == WorkflowRun.id).exists())
        .where(~select(DataSnapshot.id).where(DataSnapshot.run_id == WorkflowRun.id).exists())
        .where(~select(ProjectWorkflowOutput.id).where(ProjectWorkflowOutput.run_id == WorkflowRun.id).exists())
        .limit(c["batch"])
    ).all()
    if old_runs:
        db.execute(delete(WorkflowStep).where(WorkflowStep.run_id.in_(old_runs)))
        db.execute(delete(WorkflowRun).where(WorkflowRun.id.in_(old_runs)))
    stats["workflow_runs_deleted"] = len(old_runs)

    # 4) export_record
    res = db.execute(delete(ExportRecord).where(ExportRecord.created_at < _cutoff(c["export_record_days"])))
    stats["export_records_deleted"] = res.rowcount

    db.commit()
    logger.info("retention_sweep %s", stats)
    return stats


# ---------- 存储清理（设置页「存储与清理」） ----------

STORAGE_KEY = "storage_cleanup"
STORAGE_LAST_KEY = "storage_cleanup.last"
STORAGE_DEFAULTS = {
    "source_document_text_days": 30,
    "generation_result_days": 7,
    "candidate_material_days": 30,
}
_DAY_LIMIT = (1, 3650)
_GENERATION_DIR = re.compile(r"[0-9a-f]{32}")
_LIVE_GENERATION_STATES = {"prepared", "submitting", "running", "unknown", "accepted"}
# Material ids live in many JSON documents (shot slots, packages, persona portraits); any mention keeps the candidate.
_JSON_MATERIAL_REF = re.compile(r'"[a-z_]*?(revision|material)_ids?"\s*:\s*(\[[^\]]*\]|\d+)')
_JSON_SCAN_SKIP = {"audit_log", "llm_run", "material_revision"}


def _setting(db, key: str) -> dict:
    from ..models import SystemSetting

    row = db.get(SystemSetting, key)
    return dict(row.value or {}) if row else {}


def _put_setting(db, key: str, value: dict, actor: str | None) -> None:
    from ..models import SystemSetting

    row = db.get(SystemSetting, key)
    if row is None:
        row = SystemSetting(key=key, value={})
        db.add(row)
    row.value = value
    row.updated_by = actor
    flag_modified(row, "value")
    db.commit()


def storage_days(db) -> dict:
    saved = _setting(db, STORAGE_KEY).get("days") or {}
    return {key: saved[key] if isinstance(saved.get(key), int) else default for key, default in STORAGE_DEFAULTS.items()}


def set_storage_days(db, days: dict, actor: str | None) -> dict:
    from fastapi import HTTPException

    current = storage_days(db)
    for key, value in days.items():
        if key not in STORAGE_DEFAULTS or type(value) is not int or not _DAY_LIMIT[0] <= value <= _DAY_LIMIT[1]:
            raise HTTPException(422, {"code": "storage_cleanup_days_invalid", "field": key})
        current[key] = value
    _put_setting(db, STORAGE_KEY, {**_setting(db, STORAGE_KEY), "days": current}, actor)
    return current


def _clear_source_texts(db, *, cutoff: datetime, batch: int) -> dict:
    from ..models import (
        ContentOpportunitySignal,
        Fact,
        FactPackItem,
        KnowledgeCollectionItem,
        ProjectSourceBinding,
        SourceDocument,
    )

    used = union(
        select(ProjectSourceBinding.source_document_id),
        select(KnowledgeCollectionItem.source_document_id).where(KnowledgeCollectionItem.source_document_id.is_not(None)),
        select(ContentOpportunitySignal.source_entity_id).where(ContentOpportunitySignal.signal_type == "source_document"),
        select(Fact.source_document_id).where(or_(
            Fact.status == "confirmed", Fact.id.in_(select(FactPackItem.fact_id).where(FactPackItem.fact_id.is_not(None))))),
    )
    # Only collected articles: user-provided texts (product notes, Obsidian notes) are inputs, not crawl output.
    docs = db.scalars(
        select(SourceDocument).where(SourceDocument.source_type == "connector", SourceDocument.created_at < cutoff,
                                     SourceDocument.raw_text.is_not(None), SourceDocument.id.not_in(used))
        .order_by(SourceDocument.id).limit(batch)
    ).all()
    freed = 0
    stamp = datetime.now(UTC).isoformat()
    for doc in docs:
        freed += len((doc.raw_text or "").encode())
        doc.raw_text = None
        doc.parsed_json = None
        doc.metadata_json = {**(doc.metadata_json or {}), "text_cleared_at": stamp}
    db.commit()
    return {"source_texts_cleared": len(docs), "source_text_bytes_freed": freed}


def _clean_generation_results(db, *, cutoff: datetime, batch: int) -> dict:
    from ..models import MaterialRevision, ProviderGenerationTask, utcnow
    from .material_storage import LocalMaterialStorage, provider

    storage = provider()
    stats = {"generation_files_deleted": 0, "generation_bytes_freed": 0, "generation_tasks_expired": 0}
    if not isinstance(storage, LocalMaterialStorage):
        return stats
    root = storage.root / "generation"
    if not root.is_dir() or root.is_symlink():
        return stats
    cutoff_ts = cutoff.timestamp()
    handled = 0
    for folder in sorted(root.iterdir()):
        if handled >= batch:
            break
        if folder.is_symlink() or not folder.is_dir() or not _GENERATION_DIR.fullmatch(folder.name):
            continue
        files = [item for item in folder.iterdir() if item.is_file() and not item.is_symlink()]
        if any(item.stat().st_mtime >= cutoff_ts for item in files):
            continue
        task = db.get(ProviderGenerationTask, folder.name)
        recent = select(ProviderGenerationTask.id).where(ProviderGenerationTask.id == folder.name, ProviderGenerationTask.created_at >= cutoff)
        if task is not None and (task.state in _LIVE_GENERATION_STATES or db.scalar(recent) is not None):
            continue
        hashes = [item.stem for item in files]
        keys = [f"generation/{folder.name}/{item.name}" for item in files]
        if hashes and db.scalar(select(MaterialRevision.id).where(or_(
                MaterialRevision.content_hash.in_(hashes), MaterialRevision.file_path.in_(keys))).limit(1)) is not None:
            continue
        if task is not None and task.state == "result_ready":
            # The result is gone after this, so the task must stop offering acceptance.
            changed = db.execute(update(ProviderGenerationTask).where(
                ProviderGenerationTask.id == task.id, ProviderGenerationTask.state == "result_ready",
                ProviderGenerationTask.revision == task.revision,
            ).values(state="cancelled", reason_code="result_expired", revision=task.revision + 1, updated_at=utcnow())
                .execution_options(synchronize_session=False))
            db.commit()
            if changed.rowcount != 1:
                continue
            stats["generation_tasks_expired"] += 1
        handled += 1
        for item in files:
            try:
                size = item.stat().st_size
                item.unlink()
            except OSError:
                logger.warning("generation_cleanup_failed path=%s", item.name)
                continue
            stats["generation_files_deleted"] += 1
            stats["generation_bytes_freed"] += size
        try:
            folder.rmdir()
        except OSError:
            pass
    return stats


def _json_material_refs(db) -> tuple[set[int], set[int]]:
    from ..db import Base

    revisions: set[int] = set()
    materials: set[int] = set()
    # Models can be ahead of the database between a code update and its migration.
    present = set(inspect(db.get_bind()).get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name in _JSON_SCAN_SKIP or table.name not in present:
            continue
        for column in table.columns:
            if not isinstance(column.type, JSON):
                continue
            for text in db.scalars(select(cast(column, Text)).where(column.is_not(None))):
                for match in _JSON_MATERIAL_REF.finditer(text or ""):
                    target = revisions if match.group(1) == "revision" else materials
                    target.update(int(value) for value in re.findall(r"\d+", match.group(2)))
    return revisions, materials


def _clean_candidate_materials(db, *, cutoff: datetime, batch: int) -> dict:
    from ..models import (
        ContentMasterAssetRef,
        Material,
        MaterialCollectionItem,
        MaterialRevision,
        ProductSkuRevision,
        ProjectMaterialReference,
        ProjectWorkflowOutput,
        ProviderGenerationTask,
    )
    from .material_byte_lock import locked_hash
    from .material_storage import provider
    from .materials import approved_revision_ids

    stats = {"candidate_materials_deleted": 0, "candidate_bytes_freed": 0}
    revision = MaterialRevision
    sibling = aliased(MaterialRevision)
    other = select(sibling.id).where(sibling.material_id == revision.material_id, sibling.status != "candidate")
    child = select(MaterialRevision.parent_revision_id).where(MaterialRevision.parent_revision_id.is_not(None))
    rows = db.scalars(
        select(revision).join(Material, Material.id == revision.material_id)
        .where(revision.status == "candidate", revision.created_at < cutoff, revision.file_path.like("material/%"),
               Material.status == "active", ~other.exists(), revision.id.not_in(child),
               ~select(ProjectMaterialReference.id).where(ProjectMaterialReference.material_revision_id == revision.id).exists(),
               ~select(ContentMasterAssetRef.id).where(ContentMasterAssetRef.material_revision_id == revision.id).exists(),
               ~select(ProductSkuRevision.id).where(ProductSkuRevision.primary_image_revision_id == revision.id).exists(),
               ~select(ProviderGenerationTask.id).where(ProviderGenerationTask.accepted_material_revision_id == revision.id).exists(),
               ~select(ProjectWorkflowOutput.id).where(ProjectWorkflowOutput.output_kind == "material_revision",
                                                       ProjectWorkflowOutput.entity_id == revision.id).exists(),
               ~select(MaterialCollectionItem.id).where(MaterialCollectionItem.material_id == revision.material_id).exists())
        .order_by(revision.id).limit(batch)
    ).all()
    # Filed into a project or common folder means someone chose it, even without a reference row.
    rows = [row for row in rows if "placement" not in (row.metadata_json or {}) and Path(row.file_path).stem == row.content_hash]
    if not rows:
        return stats
    json_revisions, json_materials = _json_material_refs(db)
    approved = approved_revision_ids(db)
    storage = provider()
    stamp = datetime.now(UTC).isoformat()
    for row in rows:
        if row.id in json_revisions or row.id in approved or row.material_id in json_materials:
            continue
        key = row.file_path
        with locked_hash(row.content_hash):
            try:
                # Missing bytes usually mean an unplugged drive; leave the row for when it is back.
                if not storage.exists(key):
                    continue
                size = storage.size(key)
            except (OSError, ValueError):
                continue
            row.status = "archived"
            row.metadata_json = {**(row.metadata_json or {}), "archived_reason": "storage_cleanup_unused_candidate", "archived_at": stamp}
            shared = db.scalar(select(MaterialRevision.id).where(MaterialRevision.file_path == key, MaterialRevision.id != row.id,
                                                                 MaterialRevision.status != "archived").limit(1))
            if db.scalar(select(func.count(MaterialRevision.id)).where(MaterialRevision.material_id == row.material_id,
                                                                       MaterialRevision.status != "archived",
                                                                       MaterialRevision.id != row.id)) == 0:
                row.material.status = "archived"
            db.commit()
            stats["candidate_materials_deleted"] += 1
            if shared is None:
                try:
                    storage.delete_if_unreferenced(key, expected_hash=row.content_hash)
                    stats["candidate_bytes_freed"] += size
                except Exception:  # noqa: BLE001 The row is already archived; leftover bytes are harmless.
                    logger.warning("candidate_cleanup_bytes_failed revision_id=%s", row.id)
    return stats


def _sqlite_file(db) -> Path | None:
    url = db.get_bind().url
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return None
    return Path(url.database).resolve()


def _db_bytes(db) -> int | None:
    path = _sqlite_file(db)
    if path is None or not path.exists():
        return None
    return sum(item.stat().st_size for item in (path, Path(f"{path}-wal")) if item.exists())


def _vacuum(db) -> dict:
    if db.get_bind().url.get_backend_name() != "sqlite":
        return {"status": "skipped"}
    before = _db_bytes(db)
    db.commit()
    try:
        with db.get_bind().connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql("VACUUM")
            conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception as exc:  # noqa: BLE001 A busy database just waits for next week.
        logger.warning("sqlite_vacuum_failed %s", type(exc).__name__)
        return {"status": "busy", "bytes_before": before}
    return {"status": "done", "bytes_before": before, "bytes_after": _db_bytes(db)}


def run_storage_cleanup(db, *, force: bool = False, actor: str | None = None) -> dict | None:
    """每日一次存储清理 + 每周一次 VACUUM；force=设置页「立即清理」。未到时间返回 None。"""
    last = _setting(db, STORAGE_LAST_KEY)
    now = datetime.now(UTC)

    def older(field: str, span: timedelta) -> bool:
        try:
            return datetime.fromisoformat(last[field]) <= now - span
        except (KeyError, TypeError, ValueError):
            return True

    # The in-process maintenance loop calls this every few minutes; the slack keeps a 03:30 beat run from being skipped.
    if not force and not older("at", timedelta(hours=23)):
        return None
    days = storage_days(db)
    batch = DEFAULTS["batch"]
    stats: dict = {}
    for name, step, field in (
        ("source_documents", _clear_source_texts, "source_document_text_days"),
        ("generation_results", _clean_generation_results, "generation_result_days"),
        ("candidate_materials", _clean_candidate_materials, "candidate_material_days"),
    ):
        try:
            stats.update(step(db, cutoff=_cutoff(days[field]), batch=batch))
        except Exception:  # noqa: BLE001 One failing rule must not block the others.
            db.rollback()
            logger.exception("storage_cleanup_%s_failed", name)
            stats[f"{name}_error"] = True
    result = {**last, "at": now.isoformat(), "trigger": "manual" if force else "schedule", "stats": stats, "days": days}
    if force or older("vacuum_at", timedelta(days=7) - timedelta(hours=1)):
        vacuum = _vacuum(db)
        result["vacuum"] = vacuum
        if vacuum["status"] != "busy":
            result["vacuum_at"] = now.isoformat()
    _put_setting(db, STORAGE_LAST_KEY, result, actor or "system:maintenance")
    logger.info("storage_cleanup %s", stats)
    return result


def _folder_bytes(path: Path | None) -> int | None:
    if path is None or not path.is_dir():
        return None
    total = 0
    for base, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.lstat(os.path.join(base, name)).st_size
            except OSError:
                pass
    return total


def storage_overview(db) -> dict:
    from ..models import MaterialRevision, ProjectMaterialReference, SourceDocument
    from .asset_media import MEDIA_ROOT
    from .storage_locations import common_root

    connector = SourceDocument.source_type == "connector"
    candidates = MaterialRevision.status == "candidate"
    return {
        "sizes": {
            "database": _db_bytes(db),
            "generation_results": _folder_bytes(MEDIA_ROOT / "generation"),
            "local_materials": _folder_bytes(MEDIA_ROOT / "material"),
            "common_library": _folder_bytes(common_root()),
            "source_texts": db.scalar(select(func.coalesce(func.sum(func.length(cast(SourceDocument.raw_text, LargeBinary))), 0)).where(connector)),
        },
        "counts": {
            "source_documents": db.scalar(select(func.count(SourceDocument.id)).where(connector)),
            "source_documents_with_text": db.scalar(select(func.count(SourceDocument.id)).where(connector, SourceDocument.raw_text.is_not(None))),
            "candidate_materials": db.scalar(select(func.count(MaterialRevision.id)).where(candidates)),
            "candidate_materials_unattached": db.scalar(select(func.count(MaterialRevision.id)).where(
                candidates, ~select(ProjectMaterialReference.id).where(
                    ProjectMaterialReference.material_revision_id == MaterialRevision.id).exists())),
        },
        "days": storage_days(db),
        "defaults": STORAGE_DEFAULTS,
        "last": _setting(db, STORAGE_LAST_KEY) or None,
    }
