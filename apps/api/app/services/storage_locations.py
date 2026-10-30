"""User-configurable storage locations.

- 素材库位置: a registered MaterialSource folder. New material bytes are written under
  ``<root>/AIContentStudio/<视频|图片|音频|其他>/``; the user's own folders are never written.
- 通用素材库: material nearly every video can use, on the Mac (default ``~/自媒体素材/通用素材库``) so it works
  with the drive unplugged. Project-specific material stays on the drive with its project.
- 本地工作位置: MEDIA_ROOT (previews, executions, older materials). Read at process start, so a
  move takes effect after the API restarts; the old folder is kept.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time
from pathlib import Path

from fastapi import HTTPException

from .. import runtime_config

KEY = "storage"
LIBRARY_DIR = "AIContentStudio"
LOCAL_FILE = Path(__file__).resolve().parents[2] / "storage_location.json"
_KIND_DIRS = {
    "视频": {".mp4", ".mov", ".m4v", ".webm"},
    "图片": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"},
    "音频": {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"},
}


def configured_local_root() -> str | None:
    try:
        value = json.loads(LOCAL_FILE.read_text("utf-8")).get("local_root")
    except (OSError, ValueError):
        return None
    return value if isinstance(value, str) and os.path.isabs(value) else None


def library_root() -> Path | None:
    root = (runtime_config.get_runtime(KEY) or {}).get("library_root")
    return Path(root) if isinstance(root, str) and root else None


DEFAULT_COMMON = Path.home() / "自媒体素材" / "通用素材库"


def common_root() -> Path:
    root = (runtime_config.get_runtime(KEY) or {}).get("common_root")
    return Path(root) if isinstance(root, str) and root else DEFAULT_COMMON


def set_common(db, path: str, user) -> dict:
    from sqlalchemy import String, cast, select

    from ..models import MaterialRevision

    target = Path(os.path.expanduser(path))
    if not target.is_absolute():
        raise HTTPException(422, {"code": "storage_path_invalid", "message": "请填完整路径"})
    library = library_root()
    if library is not None and target.is_relative_to(library):
        raise HTTPException(422, {"code": "common_on_drive", "message": "通用素材库要放在 Mac 本地，不放在移动硬盘上"})
    # Moving the folder's contents is not supported; switching is only safe while nothing is filed there.
    if db.scalar(select(MaterialRevision.id).where(cast(MaterialRevision.metadata_json, String).like('%"root": "common"%')).limit(1)):
        raise HTTPException(409, {"code": "common_not_empty", "message": "通用素材库里已有素材，不能直接换位置"})
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise HTTPException(422, {"code": "storage_path_unreachable", "message": "这个位置建不了文件夹"}) from None
    _save(db, {"common_root": str(target)}, user.email)
    db.commit()
    from .project_folders import ensure_library_dirs

    ensure_library_dirs()
    return {"path": str(target)}


def edit_proxy_enabled() -> bool:
    # Off by default, like 剪映: proxies cost disk and a transcode, and only large footage needs them.
    return (runtime_config.get_runtime(KEY) or {}).get("edit_proxy_enabled") is True


def set_edit_proxy(db, enabled: bool, user) -> dict:
    _save(db, {"edit_proxy_enabled": enabled}, user.email)
    db.commit()
    return {"enabled": edit_proxy_enabled()}


def library_source_id() -> int | None:
    return (runtime_config.get_runtime(KEY) or {}).get("library_source_id")


def library_path(key: str) -> Path:
    """``material/ab/<hash>.ext`` → ``<library>/AIContentStudio/<type>/ab/<hash>.ext``."""
    root = library_root()
    if root is None:
        raise ValueError("material_library_not_configured")
    parts = Path(key).parts
    if len(parts) != 3 or parts[0] != "material":
        raise ValueError("storage_key_invalid")
    suffix = Path(key).suffix.lower()
    folder = next((name for name, suffixes in _KIND_DIRS.items() if suffix in suffixes), "其他")
    return root / LIBRARY_DIR / folder / parts[1] / parts[2]


_probe: dict = {}
_seen: dict = {}


def library_reachable() -> bool:
    """Read-only check used on every page and file read; it never writes to the drive."""
    root = library_root()
    if root is None:
        return False
    now = time.monotonic()
    if _seen.get("root") == root and now - _seen.get("at", 0) < 5:
        return _seen["ok"]
    try:
        # A half-dropped drive stays mounted but lists its folders as empty, so the platform folder must be listed.
        ok = root.is_dir() and os.access(root, os.R_OK | os.X_OK) and LIBRARY_DIR in os.listdir(root)
    except OSError:
        ok = False
    _seen.update(root=root, at=now, ok=ok)
    return ok


def library_writable() -> bool:
    """Write probe, run only right before the platform writes to the drive."""
    root = library_root()
    if not library_reachable() or not os.access(root, os.W_OK):
        return False
    now = time.monotonic()
    if _probe.get("root") == root and now - _probe.get("at", 0) < 5:
        return _probe["ok"]
    try:
        folder = root / LIBRARY_DIR
        folder.mkdir(exist_ok=True)
        target = folder / f".probe-{os.getpid()}"
        target.write_bytes(b"ok")
        ok = target.read_bytes() == b"ok"
        target.unlink()
    except OSError:
        ok = False
    _probe.update(root=root, at=now, ok=ok)
    return ok


def _save(db, value: dict, user_email: str | None) -> None:
    from ..models import SystemSetting

    row = db.get(SystemSetting, KEY)
    if row is None:
        row = SystemSetting(key=KEY)
        db.add(row)
    # One setting holds the drive library and the common library; changing one keeps the other.
    value = {**(runtime_config.get_runtime(KEY) or {}), **value}
    row.value = value
    row.updated_by = user_email
    db.flush()
    runtime_config.set_runtime(KEY, value)


def ensure_default(db) -> None:
    """The first registered material folder is the library until the user picks another."""
    from ..models import MaterialSource

    if runtime_config.get_runtime(KEY):
        return
    source = db.query(MaterialSource).order_by(MaterialSource.id).first()
    if source is not None:
        _save(db, {"library_source_id": source.id, "library_root": source.root_path}, None)
        db.commit()


def _reachable(path: Path) -> bool:
    return path.is_dir() and os.access(path, os.R_OK | os.W_OK | os.X_OK)


def view(db) -> dict:
    from ..models import MaterialSource
    from .asset_media import MEDIA_ROOT

    value = runtime_config.get_runtime(KEY) or {}
    source = db.get(MaterialSource, value["library_source_id"]) if value.get("library_source_id") else None
    root = library_root()
    env_locked = bool(os.environ.get("AI_STUDIO_MEDIA_ROOT"))
    pending = configured_local_root()
    return {
        "library": {"source_id": source.id if source else None, "label": source.label if source else None,
                    "path": str(root) if root else None, "write_folder": str(root / LIBRARY_DIR) if root else None,
                    "reachable": library_reachable()},
        "common": {"path": str(common_root()), "reachable": _reachable(common_root())},
        "local": {"path": str(MEDIA_ROOT), "reachable": _reachable(MEDIA_ROOT), "env_locked": env_locked,
                  "next_path": pending if pending and pending != str(MEDIA_ROOT) else None},
        "move": dict(_move),
        "edit_proxy": {"enabled": edit_proxy_enabled()},
    }


def _linked_files(db, source_id: int) -> list:
    from ..models import MaterialRevision

    prefix = f"external/{source_id}/"
    return db.query(MaterialRevision).filter(MaterialRevision.file_path.like(prefix + "%")).all()


def set_library(db, path: str, *, confirm: bool, user) -> dict:
    from ..models import MaterialSource
    from .material_external import ExternalMaterialError, http_error, normalize_root, parse_key, volume_uuid

    try:
        root = normalize_root(path)
    except ExternalMaterialError as exc:
        raise http_error(exc) from None
    if not _reachable(Path(root)):
        raise HTTPException(422, {"code": "storage_path_unreachable", "message": "这个文件夹不存在或没有读写权限"})
    value = runtime_config.get_runtime(KEY) or {}
    source = db.get(MaterialSource, value["library_source_id"]) if value.get("library_source_id") else None
    if source is None:
        source = MaterialSource(owner_user_id=user.id, label=Path(root).name, root_path=root,
                                volume_uuid=volume_uuid(root), created_by=user.email)
        db.add(source)
        db.flush()
        _save(db, {"library_source_id": source.id, "library_root": root}, user.email)
        db.commit()
        return {"switched": True, "matched": 0, "total": 0}
    # Linked files keep their relative path; count which ones are really there, unchanged in size.
    revisions = _linked_files(db, source.id)
    matched = 0
    for revision in revisions:
        relative = parse_key(revision.file_path)[2]
        expected = ((revision.metadata_json or {}).get("external") or {}).get("size_bytes")
        candidate = Path(root) / relative
        if candidate.is_file() and candidate.stat().st_size == expected:
            matched += 1
    if not confirm:
        return {"switched": False, "matched": matched, "total": len(revisions)}
    source.root_path = root
    source.volume_uuid = volume_uuid(root)
    _save(db, {"library_source_id": source.id, "library_root": root}, user.email)
    db.commit()
    return {"switched": True, "matched": matched, "total": len(revisions)}


_move: dict = {"state": "idle"}
_move_lock = threading.Lock()


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_and_verify(source: Path, target: Path) -> None:
    files = [path for path in source.rglob("*") if path.is_file() and not path.is_symlink()]
    _move.update(state="copying", total=len(files), done=0, target=str(target), error=None)
    try:
        for path in files:
            destination = target / path.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            if _digest(path) != _digest(destination):
                raise OSError(f"校验不一致：{path.relative_to(source)}")
            _move["done"] += 1
        LOCAL_FILE.write_text(json.dumps({"local_root": str(target)}, ensure_ascii=False), "utf-8")
        _move.update(state="done")
    except OSError as exc:
        _move.update(state="failed", error=str(exc))


def start_local_move(path: str) -> dict:
    from .asset_media import MEDIA_ROOT

    if os.environ.get("AI_STUDIO_MEDIA_ROOT"):
        raise HTTPException(409, {"code": "storage_env_locked", "message": "本地工作位置由启动参数 AI_STUDIO_MEDIA_ROOT 指定，请先去掉它"})
    if not os.path.isabs(path):
        raise HTTPException(422, {"code": "storage_path_invalid", "message": "请填写完整路径"})
    target = Path(path).resolve()
    if target == MEDIA_ROOT or target.is_relative_to(MEDIA_ROOT) or MEDIA_ROOT.is_relative_to(target):
        raise HTTPException(422, {"code": "storage_path_invalid", "message": "新位置不能和当前位置重叠"})
    if target.exists() and any(target.iterdir()):
        raise HTTPException(422, {"code": "storage_path_not_empty", "message": "请选一个空文件夹"})
    with _move_lock:
        if _move.get("state") == "copying":
            raise HTTPException(409, {"code": "storage_move_running", "message": "已经在复制了"})
        target.mkdir(parents=True, exist_ok=True)
        _move.clear()
        _move.update(state="copying", total=0, done=0, target=str(target), error=None)
        threading.Thread(target=_copy_and_verify, args=(MEDIA_ROOT, target), daemon=True).start()
    return dict(_move)
