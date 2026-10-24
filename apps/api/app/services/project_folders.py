"""Per-project material folders on the library drive.

The library drive holds 外部素材库 (new files wait here) and one folder per project with the standard layout.
通用素材库 (material nearly every video can use) lives on the Mac itself so it works with the drive unplugged. When a project adopts its draft, the files it uses move into
its folder. Storage keys never change because execution packages hash them; the current location is kept as
``metadata_json["placement"]`` on every revision of that file and read first by the storage layer.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
import re
import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import ContentProject, Material, MaterialRevision, SystemSetting

EXTERNAL_DIR, COMMON_DIR, PLATFORM_DIR = "外部素材库", "通用素材库", "AIContentStudio"
STRUCTURE = ("导演稿", "视频/Aroll", "视频/Broll", "视频/其他素材", "图片/图片素材", "图片/包装设计素材",
             "音频/BGM", "音频/音效", "导出/小样", "导出/成片")
FOLDERS = "project_folders"
PENDING = "project_folders_pending"
# Folders already on the drive that are not projects; a project never takes these names.
RESERVED = {EXTERNAL_DIR, COMMON_DIR, PLATFORM_DIR, "项目1"}
_PACKAGING = re.compile(r"logo|标志|卡片|包装|封面|字幕条|角标|片头|片尾|title|card", re.IGNORECASE)
_TYPE_DIRS = {"video": "视频", "image": "图片", "audio": "音频"}
COMMON_STRUCTURE = tuple(name for name in STRUCTURE if not name.startswith(("导演稿", "导出")))
OUTPUT_ROLES = {"rough_cut", "final", "subtitles", "resolve_project", "ae_project", "edit_manifest"}


def common_root() -> Path:
    from .storage_locations import common_root as root

    return root()


def _is_output(source_kind: str | None, source_metadata: dict | None, metadata: dict | None) -> bool:
    if source_kind == "external_execution" and (source_metadata or {}).get("role_id") in OUTPUT_ROLES:
        return True
    where = (metadata or {}).get("placement") or {}
    parts = Path(where.get("path") or "").parts
    return where.get("root") != "common" and len(parts) > 1 and parts[1] == "导出"


def is_output(revision: MaterialRevision) -> bool:
    """小样 / 成片 and the files that rebuild them are what a project produced, not material."""
    return _is_output(revision.source_kind, revision.source_metadata_json, revision.metadata_json)


def _root() -> Path | None:
    from .storage_locations import library_reachable, library_root

    return library_root() if library_reachable() else None


def _setting(db: Session, key: str) -> dict:
    row = db.get(SystemSetting, key)
    return dict(row.value or {}) if row else {}


def _put_setting(db: Session, key: str, value: dict) -> None:
    row = db.get(SystemSetting, key)
    if row is None:
        row = SystemSetting(key=key)
        db.add(row)
    row.value = value
    flag_modified(row, "value")
    db.flush()


def _clean(name: str) -> str:
    name = re.sub(r"[\x00-\x1f/\\:]", "", name).strip().strip(".")
    return name[:80]


def folder_names(db: Session) -> dict[str, str]:
    return _setting(db, FOLDERS)


def folder_name(db: Session, project_id: int) -> str:
    """Short project name (title before the first ｜), saved once so a later rename moves nothing."""
    names = folder_names(db)
    if str(project_id) in names:
        return names[str(project_id)]
    project = db.get(ContentProject, project_id)
    base = _clean(re.split(r"[｜|]", project.title or "")[0]) or f"项目{project_id}"
    taken = set(names.values()) | RESERVED
    name = base if base not in taken else f"{base} (#{project_id})"
    names[str(project_id)] = name
    _put_setting(db, FOLDERS, names)
    return name


def ensure_library_dirs() -> None:
    root = _root()
    if root is not None:
        (root / EXTERNAL_DIR).mkdir(exist_ok=True)
    for sub in COMMON_STRUCTURE:
        (common_root() / sub).mkdir(parents=True, exist_ok=True)


def ensure_project_dir(db: Session, project_id: int) -> Path:
    root = _root()
    if root is None:
        raise FileNotFoundError("material_library_unavailable")
    folder = root / folder_name(db, project_id)
    for sub in STRUCTURE:
        (folder / sub).mkdir(parents=True, exist_ok=True)
    return folder


def placed_path(key: str) -> Path | None:
    """Current location of a moved file, for storage reads that miss the default places."""
    from ..db import SessionLocal

    root = _library_root()
    if root is None:
        return None
    with SessionLocal() as db:
        metadata = db.scalar(select(MaterialRevision.metadata_json).where(MaterialRevision.file_path == key)
                             .where(MaterialRevision.content_hash == Path(key).stem).limit(1))
    where = (metadata or {}).get("placement") or {}
    if not where.get("path"):
        return None
    return (common_root() if where.get("root") == "common" else root) / where["path"]


def _library_root() -> Path | None:
    from .storage_locations import library_root

    return library_root()


def placement(revision: MaterialRevision) -> dict:
    return (revision.metadata_json or {}).get("placement") or {}


def current_path(db: Session, revision: MaterialRevision) -> Path | None:
    from ..models import MaterialSource
    from .material_external import is_external, parse_key
    from .material_storage import LocalMaterialStorage, provider

    root = _library_root()
    if placement(revision).get("root") == "common":
        return common_root() / placement(revision)["path"]
    if placement(revision).get("path") and root is not None:
        return root / placement(revision)["path"]
    if not revision.file_path:
        return None
    if is_external(revision.file_path):
        source_id, _hash, relative = parse_key(revision.file_path)
        source = db.get(MaterialSource, source_id)
        return Path(source.root_path) / relative if source else None
    storage = provider()
    return storage._path(revision.file_path) if isinstance(storage, LocalMaterialStorage) else None


def location(revision: MaterialRevision, names: dict[str, str], root: Path | None, path: Path | None) -> dict:
    """Which library a file is in, from its path below the library root."""
    common = common_root()
    if path is not None and path.is_relative_to(common):
        return {"library": "common", "group": COMMON_DIR, "project_id": None, "folder": "/".join(path.relative_to(common).parts[:-1]) or None}
    if root is None or path is None or not path.is_relative_to(root):
        return {"library": "external", "group": "平台本地", "project_id": None, "folder": None}
    parts = path.relative_to(root).parts
    top = parts[0] if parts else ""
    projects = {name: int(pid) for pid, name in names.items()}
    if top == COMMON_DIR:
        return {"library": "common", "group": COMMON_DIR, "project_id": None, "folder": "/".join(parts[1:-1]) or None}
    if top in projects:
        return {"library": "project", "group": top, "project_id": projects[top], "folder": "/".join(parts[1:-1]) or None}
    return {"library": "external", "group": top, "project_id": None, "folder": None}


def subfolder(revision: MaterialRevision, role: str, shot: dict | None, auto_source: str | None) -> str:
    kind = revision.material.kind
    if role == "voice_audio":
        return "音频"
    if role == "music_audio":
        return "音频/BGM"
    if kind == "audio":
        return "音频/音效"
    if kind == "video":
        if auto_source in {"ae_template", "ai_image"} or revision.source_kind in {"ai_generated", "external_execution"}:
            return "视频/其他素材"
        speaker = ((shot or {}).get("board") or {}).get("speaker") or ""
        # Narration-only shots are cutaways; a named on-camera speaker makes it main footage.
        return "视频/Aroll" if speaker and speaker not in {"narration", "旁白", "无"} else "视频/Broll"
    text = f"{revision.material.title} {' '.join(revision.material.tags_json or [])}"
    return "图片/包装设计素材" if role == "cover_image" or _PACKAGING.search(text) else "图片/图片素材"


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _original(root: Path, names: dict[str, str], revision: MaterialRevision, size: int) -> Path | None:
    """The user's own copy of a platform file (same bytes, outside projects), so its real name is kept."""
    skip = set(names.values()) | {COMMON_DIR, PLATFORM_DIR, "项目1"}
    for directory, folders, files in os.walk(root):
        if Path(directory) == root:
            folders[:] = [name for name in folders if name not in skip and not name.startswith(".")]
        for name in files:
            path = Path(directory) / name
            if name.startswith(".") or path.is_symlink():
                continue
            try:
                if path.stat().st_size == size and _digest(path) == revision.content_hash:
                    return path
            except OSError:
                continue
    return None


def _move_file(source: Path, target: Path, expected_hash: str) -> None:
    try:
        os.rename(source, target)
    except OSError as exc:
        if exc.errno != 18:  # EXDEV: different drive, copy and check before removing the source.
            raise
        shutil.copy2(source, target)
        if _digest(target) != expected_hash:
            target.unlink(missing_ok=True)
            raise OSError("copy_hash_mismatch") from None
        source.unlink()


_EXTENSIONS = {"application/x-resolve-project": ".drp", "application/x-after-effects-project": ".aep",
               "application/x-subrip": ".srt", "application/json": ".json", "video/mp4": ".mp4", "video/quicktime": ".mov"}


def _suffix(path: Path, mime: str | None) -> str:
    # Accepted edit outputs are stored as <hash>.bin; the declared type gives the real extension.
    if path.suffix.lower() != ".bin":
        return path.suffix
    return _EXTENSIONS.get(mime or "") or mimetypes.guess_extension(mime or "") or ".bin"


def _free_name(folder: Path, title: str, suffix: str, content_hash: str) -> Path:
    stem = _clean(Path(title).stem if Path(title).suffix.lower() == suffix.lower() else title) or content_hash[:12]
    target = folder / f"{stem}{suffix}"
    return target if not target.exists() else folder / f"{stem}-{content_hash[:6]}{suffix}"


def _same_file(db: Session, revision: MaterialRevision) -> list[MaterialRevision]:
    return db.scalars(select(MaterialRevision).where(MaterialRevision.file_path == revision.file_path)).all() if revision.file_path else [revision]


def _set_placement(db: Session, revision: MaterialRevision, relative: str, library: str, project_id: int | None) -> None:
    where = {"path": relative, "library": library, "project_id": project_id}
    if library == "common":
        where["root"] = "common"
    for row in _same_file(db, revision):
        row.metadata_json = {**(row.metadata_json or {}), "placement": where}
        flag_modified(row, "metadata_json")
    db.flush()


def _use_elsewhere(db: Session, revision: MaterialRevision, path: Path, where: dict, folder: str, project_id: int, root: Path) -> dict:
    """A project reusing another project's file gets a shortcut in its own folder; common files are just recorded."""
    used = sorted({*((revision.metadata_json or {}).get("used_by") or []), project_id})
    links = dict((revision.metadata_json or {}).get("links") or {})
    if where["library"] == "project" and str(project_id) not in links:
        target_dir = root / folder_name(db, project_id) / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        link = target_dir / path.name
        if link.exists() or link.is_symlink():
            link = target_dir / f"{path.stem}-{revision.content_hash[:6]}{path.suffix}"
        if not link.is_symlink():
            link.symlink_to(path)
        links[str(project_id)] = link.relative_to(root).as_posix()
    for row in _same_file(db, revision):
        row.metadata_json = {**(row.metadata_json or {}), "used_by": used, "links": links}
        flag_modified(row, "metadata_json")
    db.commit()
    return {"state": "referenced", "path": str(path), "link": links.get(str(project_id))}


def _relink(revision: MaterialRevision, root: Path | None, target: Path) -> None:
    # Shortcuts in other projects follow the file when it moves (for example into 通用素材库).
    for relative in ((revision.metadata_json or {}).get("links") or {}).values():
        link = root / relative if root is not None else None
        if link is not None and link.is_symlink():
            link.unlink()
            link.symlink_to(target)


def move_into(db: Session, revision: MaterialRevision, folder: str, *, project_id: int | None = None, refile: bool = False) -> dict:
    """Move one file into a project subfolder (or 通用素材库/<type>); never copies, rolls back on failure."""
    from .material_external import is_external, parse_key
    from .storage_locations import library_source_id

    root = _root()
    if root is None and project_id is not None:
        return {"state": "pending", "reason": "素材库未连接"}
    names = folder_names(db)
    path = current_path(db, revision)
    where = location(revision, names, root, path)
    # refile: an output of this project's own edit goes to its proper subfolder even if it already sits in the project.
    own = refile and where["library"] == "project" and where["project_id"] == project_id
    if where["library"] == "common" and project_id is None:
        return {"state": "referenced", "path": str(path)}
    if project_id is not None and (where["library"] == "common" or (where["library"] == "project" and not own)):
        return _use_elsewhere(db, revision, path, where, folder, project_id, root)
    if path is None or not path.is_file():
        return {"state": "pending", "reason": "找不到文件"}
    if is_external(revision.file_path) and parse_key(revision.file_path)[0] != library_source_id():
        return {"state": "pending", "reason": "文件不在素材库盘上"}
    duplicate = None
    if root is not None and not is_external(revision.file_path) and not placement(revision):
        original = _original(root, names, revision, path.stat().st_size)
        if original is not None:
            duplicate, path = path, original
    base = root / folder_name(db, project_id) if project_id is not None else common_root()
    target_dir = base / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    # Hash-named platform files take the material title; the user's own files keep their name.
    suffix = _suffix(path, revision.mime_type)
    stem = revision.material.title if path.stem == revision.content_hash or path.suffix.lower() == ".bin" else path.name
    target = _free_name(target_dir, stem, suffix, revision.content_hash)
    if target == path:
        return {"state": "referenced", "path": str(path)}
    try:
        _move_file(path, target, revision.content_hash)
    except OSError as exc:
        return {"state": "pending", "reason": f"移动失败：{exc.strerror or exc}"}
    try:
        _set_placement(db, revision, target.relative_to(base.parent if project_id is not None else base).as_posix(),
                       "project" if project_id is not None else "common", project_id)
        db.commit()
    except Exception:
        db.rollback()
        os.rename(target, path)
        raise
    _relink(revision, root, target)
    if duplicate is not None and _digest(target) == revision.content_hash:
        # The platform kept a byte-identical copy of the user's file; one home is enough.
        duplicate.unlink(missing_ok=True)
    elif path.parent.parent.parent.name == PLATFORM_DIR and not any(path.parent.iterdir()):
        path.parent.rmdir()  # empty <type>/<xx>/ left behind in the platform folder
    return {"state": "moved", "path": str(target), "dropped_copy": str(duplicate) if duplicate else None}


def archive_master(db: Session, project_id: int, document: dict, slots: dict | None = None) -> dict:
    """Move every file the adopted draft uses into the project folder; failures wait for the next 准备剪辑."""
    from .video_documents import _expected_media

    try:
        ensure_project_dir(db, project_id)
        db.commit()
    except FileNotFoundError:
        return {"moved": [], "referenced": [], "pending": [{"material_revision_id": None, "reason": "素材库未连接"}]}
    shots = {shot["id"]: shot for shot in document.get("shots", [])}
    done, result = set(), {"moved": [], "referenced": [], "pending": []}
    pending = _setting(db, PENDING)
    for ref in _expected_media(document):
        revision_id = ref["material_revision_id"]
        revision = db.get(MaterialRevision, revision_id)
        if revision is None or revision.file_path in done:
            continue
        done.add(revision.file_path)
        shot_id = ref["placement"].get("shot_id")
        picks = ((slots or {}).get(shot_id) or {}).get("picks") or []
        auto = next(((pick.get("auto") or {}).get("source") for pick in picks if pick.get("material_revision_id") == revision_id), None)
        outcome = move_into(db, revision, subfolder(revision, ref["role"], shots.get(shot_id), auto), project_id=project_id)
        entry = {"material_revision_id": revision_id, **outcome}
        result.get(outcome["state"], result["pending"]).append(entry)
    waiting = [row for row in result["pending"] if row["material_revision_id"]]
    pending[str(project_id)] = waiting
    if not waiting:
        pending.pop(str(project_id), None)
    _put_setting(db, PENDING, pending)
    db.commit()
    return result


def store_new(db: Session, revision: MaterialRevision, project_id: int, folder: str) -> dict:
    """Material made for a project after adoption (voiceover, AI picture, AE render) goes straight in."""
    return move_into(db, revision, folder, project_id=project_id)


def export_copy(db: Session, project_id: int, source: Path, kind: str, name: str, suffix: str) -> Path | None:
    """Rough cut → 导出/小样, accepted cut → 导出/成片. A copy: the execution keeps its own file."""
    try:
        folder = ensure_project_dir(db, project_id) / "导出" / kind
        db.commit()
    except FileNotFoundError:
        return None
    target = folder / f"{_clean(name)}{suffix}"
    if not target.exists():
        shutil.copy2(source, target)
    return target


def write_director_draft(db: Session, project_id: int, revision_no: int, document: dict) -> Path | None:
    try:
        folder = ensure_project_dir(db, project_id) / "导演稿"
        db.commit()
    except FileNotFoundError:
        return None
    target = folder / f"导演稿-v{revision_no}.md"
    if target.exists():
        return target
    columns = ("message", "visual", "camera", "sound", "notes", "material_request")
    lines_by_block = {block.get("id"): str(block.get("text") or "") for block in (document.get("script") or {}).get("blocks") or []}
    lines = [f"# 导演稿 v{revision_no}", "", "| 镜头 | 台词 | 信息 | 画面 | 景别 / 运镜 | 声音 | 备注 | 素材需求 |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for index, shot in enumerate(document.get("shots", []), 1):
        board = shot.get("board") or {}
        values = {key: str(board.get(key) or "") for key in columns}
        values["camera"] = " / ".join(filter(None, (shot.get("framing"), values["camera"])))
        cells = [lines_by_block.get(shot.get("script_block_id"), "")] + [values[key] for key in columns]
        lines.append(f"| {index} | " + " | ".join(cell.replace("|", "／").replace("\n", " ") for cell in cells) + " |")
    target.write_text("\n".join(lines) + "\n", "utf-8")
    return target


def to_common(db: Session, revision: MaterialRevision) -> dict:
    names = folder_names(db)
    root = _root()
    where = location(revision, names, root, current_path(db, revision))
    if where["library"] == "common":
        return {"state": "referenced"}
    return move_into(db, revision, subfolder(revision, "", None, None), project_id=None)


def listing(db: Session, material_ids: list[int]) -> dict[int, dict]:
    """Library / project / subfolder of each material's latest revision, for the material pages."""
    root, names = _library_root(), folder_names(db)
    rows = db.scalars(select(MaterialRevision).join(Material).where(MaterialRevision.material_id.in_(material_ids))
                      .order_by(MaterialRevision.revision_no)).all() if material_ids else []
    latest = {row.material_id: row for row in rows}
    return {material_id: location(row, names, root, current_path(db, row)) for material_id, row in latest.items()}


def sample_name(db: Session, row, output) -> tuple[str, str]:
    from ..models import ContentUnit

    unit = db.get(ContentUnit, row.content_unit_id)
    name = f"{re.split(r'[｜|]', unit.title if unit else '')[0] or '粗剪'}-粗剪-任务{row.id}"
    # Staged files are named <hash>.bin; the extension comes from the declared type.
    return name, mimetypes.guess_extension(output.mime_type) or ".mp4"


def sample_copy(db: Session, row, output) -> Path | None:
    """The 导出/小样 copy of a returned rough cut, when it was made."""
    root, names = _root(), folder_names(db)
    if root is None or str(row.project_id) not in names:
        return None
    name, suffix = sample_name(db, row, output)
    target = root / names[str(row.project_id)] / "导出" / "小样" / f"{_clean(name)}{suffix}"
    return target if target.is_file() else None


def after_execution(db: Session, execution_id: int) -> None:
    """Rough cut returned → copy to 导出/小样; accepted → its files move into the project folder (cut → 导出/成片)."""
    from ..models import ContentUnit, CreativeExecution, CreativeExecutionOutput
    from .creative_execution_files import work_root

    try:
        row = db.get(CreativeExecution, execution_id)
        if row is None or row.executor_key != "codex-video-production" or row.state not in {"result_ready", "accepted"}:
            return
        outputs = db.scalars(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id == row.id)
                             .order_by(CreativeExecutionOutput.attempt_no)).all()
        if row.state == "result_ready":
            cut = [output for output in outputs if output.role_id == "rough_cut"]
            if cut:
                name, suffix = sample_name(db, row, cut[-1])
                export_copy(db, row.project_id, work_root(row.owner_user_id, row.id) / cut[-1].staging_key, "小样", name, suffix)
            return
        for output in outputs:
            revision = db.get(MaterialRevision, output.material_revision_id) if output.material_revision_id else None
            if revision is not None and output.state == "accepted":
                # The cut, its subtitles and the projects that rebuild it belong together under 导出/成片.
                if output.role_id in {"rough_cut", "final", "subtitles", "resolve_project", "ae_project", "edit_manifest"}:
                    folder = "导出/成片"
                else:
                    folder = subfolder(revision, "", None, "ae_template")
                move_into(db, revision, folder, project_id=row.project_id, refile=True)
    except Exception:  # noqa: BLE001 Archiving must never undo or fail the edit task itself.
        db.rollback()


def output_material_ids(db: Session) -> list[int]:
    # Only the columns the check needs: the library list stays a light query.
    rows = db.execute(select(MaterialRevision.material_id, MaterialRevision.source_kind, MaterialRevision.source_metadata_json,
                             MaterialRevision.metadata_json).where((MaterialRevision.source_kind == "external_execution")
                                                                   | MaterialRevision.metadata_json.is_not(None))).all()
    return sorted({row[0] for row in rows if _is_output(row[1], row[2], row[3])})


def tree(db: Session) -> dict:
    """All library materials with where they sit, for the 外部 / 通用 / 项目 views."""
    rows = db.scalars(select(MaterialRevision).join(Material).where(Material.status == "active", Material.kind.in_(_TYPE_DIRS))
                      .order_by(Material.created_at.desc(), MaterialRevision.revision_no)).all()
    latest: dict[int, MaterialRevision] = {}
    for row in rows:
        latest[row.material_id] = row
    root, names = _library_root(), folder_names(db)
    items = []
    for revision in latest.values():
        if revision.status in {"revoked", "archived"} or is_output(revision):
            continue
        items.append({"material_id": revision.material_id, "material_revision_id": revision.id, "title": revision.material.title,
                      "kind": revision.material.kind, "mime_type": revision.mime_type,
                      "used_by": (revision.metadata_json or {}).get("used_by") or [],
                      **location(revision, names, root, current_path(db, revision))})
    pending = _setting(db, PENDING)
    return {"projects": [{"project_id": int(pid), "name": name, "pending": len(pending.get(pid, []))} for pid, name in names.items()],
            "folders": list(STRUCTURE), "items": items}
