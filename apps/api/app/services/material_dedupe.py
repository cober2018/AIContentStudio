"""One material entry per file: merge entries holding the same bytes, and reuse instead of adding twice.

The oldest entry stays; the others are archived, never deleted, so old drafts and edit packages still
resolve. Only the latest draft of each unit is re-saved to point at the kept entry.
"""

from __future__ import annotations

import hashlib
import os
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import AuditLog, ContentMasterRevision, Material, MaterialRevision, ProjectMaterialReference, User

_FLAGS = ("public_use_allowed", "model_use_allowed", "commercial_use_allowed")


def existing_revision(db: Session, content_hash: str) -> MaterialRevision | None:
    """The kept entry for these bytes, if the library already has them."""
    return db.scalar(select(MaterialRevision).join(Material).where(
        MaterialRevision.content_hash == content_hash, Material.status == "active",
        MaterialRevision.status.not_in(("revoked", "archived"))).order_by(Material.id, MaterialRevision.revision_no.desc()).limit(1))


def _latest(db: Session) -> dict[int, MaterialRevision]:
    rows = db.scalars(select(MaterialRevision).join(Material).where(Material.status == "active")
                      .order_by(MaterialRevision.material_id, MaterialRevision.revision_no)).all()
    latest: dict[int, MaterialRevision] = {}
    for row in rows:
        latest[row.material_id] = row
    return latest


def _at_least(a: MaterialRevision, b: MaterialRevision) -> bool:
    # Unset and False both mean "not granted".
    return all(getattr(a, flag) is True or getattr(b, flag) is not True for flag in _FLAGS)


def _rights_plan(kept: MaterialRevision, others: list[MaterialRevision]) -> MaterialRevision | None | bool:
    """None: rights equal. A revision: copy its rights onto the kept one. False: conflict, leave the group."""
    # Different credits do not block a merge: the kept entry carries every credit line (see merge).
    same_terms = all(row.rights_status == kept.rights_status for row in others)
    if not same_terms:
        return False
    widest = kept
    for row in others:
        if _at_least(row, widest):
            widest = row
        elif not _at_least(widest, row):
            return False
    return None if widest is kept or all((getattr(widest, f) is True) == (getattr(kept, f) is True) for f in _FLAGS) else widest


def _replace(value, mapping: dict[int, int]):
    if isinstance(value, dict):
        return {key: (mapping.get(item, item) if key.endswith("material_revision_id") and isinstance(item, int) else _replace(item, mapping))
                for key, item in value.items()}
    if isinstance(value, list):
        return [_replace(item, mapping) for item in value]
    return value


def _resave_drafts(db: Session, user: User, mapping: dict[int, int]) -> list[dict]:
    from ..models import ContentUnit
    from .edit_handoff import _save
    from .video_documents import _expected_media

    done = []
    latest = {}
    for master in db.scalars(select(ContentMasterRevision).where(ContentMasterRevision.payload_schema == "video.master.v2")
                             .order_by(ContentMasterRevision.content_unit_id, ContentMasterRevision.revision_no)):
        latest[master.content_unit_id] = master
    for unit_id, master in latest.items():
        used = {ref["material_revision_id"] for ref in _expected_media(master.payload_json)}
        if not used & mapping.keys():
            continue
        unit = db.get(ContentUnit, unit_id)
        for kept_id in {mapping[rid] for rid in used & mapping.keys()}:
            ref = db.scalar(select(ProjectMaterialReference).where(ProjectMaterialReference.project_id == unit.project_id,
                                                                   ProjectMaterialReference.material_revision_id == kept_id))
            if ref is not None:
                ref.status = "active"
            else:
                db.add(ProjectMaterialReference(project_id=unit.project_id, material_revision_id=kept_id, origin="system_reference",
                                                status="active", attached_by=user.email, note="合并重复素材"))
        db.flush()
        document = _replace(master.payload_json, mapping)
        changed = {str(old): new for old, new in mapping.items() if old in used}
        master_id = _save(db, user, unit.project_id, unit_id, master, document, {}, edit_summary={"dedupe": changed})
        done.append({"unit_id": unit_id, "master_id": master_id, "replaced": changed})
    return done


def merge(db: Session, user: User) -> dict:
    groups: dict[str, list[MaterialRevision]] = defaultdict(list)
    for revision in _latest(db).values():
        groups[revision.content_hash].append(revision)
    mapping: dict[int, int] = {}
    merged, conflicts = [], []
    for rows in groups.values():
        if len(rows) < 2:
            continue
        rows.sort(key=lambda row: row.material_id)
        kept, others = rows[0], rows[1:]
        plan = _rights_plan(kept, others)
        titles = [row.material.title for row in rows]
        if plan is False:
            conflicts.append({"material_ids": [row.material_id for row in rows], "titles": titles})
            continue
        if plan is not None:
            for flag in _FLAGS:
                setattr(kept, flag, getattr(plan, flag))
        credits = list(dict.fromkeys(filter(None, (row.attribution_text for row in rows))))
        if len(credits) > 1:
            kept.attribution_text = "\n".join(credits)[:4000]
        for row in others:
            row.material.status = "archived"
            row.metadata_json = {**(row.metadata_json or {}), "merged_into": kept.material_id}
            flag_modified(row, "metadata_json")
            # Every revision of the retired entry with these bytes maps to the kept one.
            for old in row.material.revisions:
                if old.content_hash == kept.content_hash:
                    mapping[old.id] = kept.id
            db.add(AuditLog(event="material.merged", actor=user.email, entity_type="material", entity_id=str(row.material_id),
                            detail_json={"merged_into": kept.material_id, "content_hash": kept.content_hash}))
        merged.append({"kept": kept.material_id, "retired": [row.material_id for row in others], "title": kept.material.title,
                       "rights_widened": plan is not None})
    db.flush()
    drafts = _resave_drafts(db, user, mapping) if mapping else []
    db.commit()
    return {"merged": merged, "conflicts": conflicts, "drafts": drafts}


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def dedupe_folders(db: Session) -> list[str]:
    """Identical files in one folder of the project / 外部 / 通用 libraries: keep the one in use (or the oldest)."""
    from . import project_folders

    root = project_folders._root()
    if root is None:
        return []
    used = set()
    for revision in db.scalars(select(MaterialRevision).where(MaterialRevision.file_path.is_not(None))):
        path = project_folders.current_path(db, revision)
        if path is not None:
            used.add(path)
    tops = [root / name for name in (project_folders.EXTERNAL_DIR, project_folders.COMMON_DIR, *project_folders.folder_names(db).values())]
    removed = []
    for top in tops:
        for directory, _folders, files in os.walk(top):
            by_size: dict[int, list[Path]] = defaultdict(list)
            for name in files:
                path = Path(directory) / name
                if not name.startswith(".") and path.is_file() and not path.is_symlink():
                    by_size[path.stat().st_size].append(path)
            for same_size in by_size.values():
                if len(same_size) < 2:
                    continue
                by_hash: dict[str, list[Path]] = defaultdict(list)
                for path in same_size:
                    by_hash[_digest(path)].append(path)
                for copies in by_hash.values():
                    copies.sort(key=lambda path: (path not in used, path.stat().st_mtime))
                    for extra in copies[1:]:
                        if extra not in used:
                            extra.unlink()
                            removed.append(str(extra))
    return removed
