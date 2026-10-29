"""Materials linked in place from user folders (for example an external drive).

Bytes never enter the platform media folder. A linked revision's key is
``external/<source_id>/<content_hash>/<relative path>``; every open re-checks
the folder's volume and the file's fingerprint.
"""

from __future__ import annotations

import hashlib
import os
import plistlib
import re
import stat
import subprocess
import unicodedata
from contextlib import contextmanager
from pathlib import Path

from fastapi import HTTPException

KEY = re.compile(r"external/(\d+)/([0-9a-f]{64})/(.+)\Z", re.S)
_DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
CHUNK = 1024 * 1024
MAX_LINK_BYTES = 8 * 1024 * 1024 * 1024
MAX_SCAN_ENTRIES = 2000
MAX_SCAN_DEPTH = 8
EXTENSIONS = {
    "jpg": ("image", "image/jpeg"), "jpeg": ("image", "image/jpeg"), "png": ("image", "image/png"),
    "webp": ("image", "image/webp"), "gif": ("image", "image/gif"),
    "mp4": ("video", "video/mp4"), "mov": ("video", "video/quicktime"), "m4v": ("video", "video/mp4"),
    "mp3": ("audio", "audio/mpeg"), "wav": ("audio", "audio/wav"), "m4a": ("audio", "audio/mp4"),
}


class ExternalMaterialError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def is_external(key) -> bool:
    return isinstance(key, str) and key.startswith("external/")


def http_error(exc: ExternalMaterialError) -> HTTPException:
    return HTTPException(404 if exc.code.endswith("_not_found") else 409, {"code": exc.code})


def _mount_point(path: str) -> str:
    current = Path(path)
    device = current.stat().st_dev
    while current.parent != current and current.parent.stat().st_dev == device:
        current = current.parent
    return str(current)


def volume_uuid(path: str) -> str | None:
    # diskutil only answers for a mount point, not for a folder inside it.
    try:
        output = subprocess.run(["diskutil", "info", "-plist", _mount_point(path)], capture_output=True, timeout=10, check=True).stdout
        return plistlib.loads(output).get("VolumeUUID")
    except (OSError, subprocess.SubprocessError, plistlib.InvalidFileException):
        return None


def _components(path: str, *, absolute: bool) -> list[str]:
    if not isinstance(path, str) or "\x00" in path or len(path.encode()) > 1000:
        raise ExternalMaterialError("material_external_path_invalid")
    # macOS file names are decomposed on disk; requests usually arrive composed.
    path = unicodedata.normalize("NFC", path)
    if absolute != path.startswith("/"):
        raise ExternalMaterialError("material_external_path_invalid")
    parts = [part for part in path.strip("/").split("/")]
    if not parts or any(part in {"", ".", ".."} or len(part.encode()) > 255 for part in parts):
        raise ExternalMaterialError("material_external_path_invalid")
    return parts


def normalize_root(path: str) -> str:
    return "/" + "/".join(_components(path.rstrip("/") or "/", absolute=True))


def normalize_relative(path: str) -> str:
    return "/".join(_components(path, absolute=False))


@contextmanager
def _directory(parts: list[str]):
    # Walking with O_NOFOLLOW keeps a symlink inside the folder from reaching elsewhere.
    descriptor = os.open("/", _DIRECTORY)
    try:
        for part in parts:
            child = os.open(part, _DIRECTORY, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor
    except OSError:
        raise ExternalMaterialError("material_external_unavailable") from None
    finally:
        os.close(descriptor)


def source_status(source) -> str:
    root = Path(source.root_path)
    if not root.is_dir() or not os.access(root, os.R_OK | os.X_OK):
        return "unavailable"
    if source.volume_uuid and volume_uuid(source.root_path) != source.volume_uuid:
        return "different_volume"
    return "available"


def _require_available(source) -> None:
    status = source_status(source)
    if status != "available":
        raise ExternalMaterialError("material_external_unavailable" if status == "unavailable" else "material_external_volume_changed")


@contextmanager
def open_file(source, relative: str):
    _require_available(source)
    parts = _components(relative, absolute=False)
    with _directory(_components(source.root_path, absolute=True) + parts[:-1]) as parent:
        try:
            fd = os.open(parts[-1], _FILE, dir_fd=parent)
        except FileNotFoundError:
            raise ExternalMaterialError("material_external_unavailable") from None
        except OSError:
            raise ExternalMaterialError("material_external_path_invalid") from None
        with os.fdopen(fd, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ExternalMaterialError("material_external_path_invalid")
            yield handle


def fingerprint(handle, maximum: int = MAX_LINK_BYTES) -> tuple[int, str]:
    handle.seek(0)
    size, digest = 0, hashlib.sha256()
    while chunk := handle.read(CHUNK):
        size += len(chunk)
        if size > maximum:
            raise ExternalMaterialError("material_external_too_large")
        digest.update(chunk)
    handle.seek(0)
    return size, digest.hexdigest()


def key_for(source_id: int, content_hash: str, relative: str) -> str:
    return f"external/{source_id}/{content_hash}/{relative}"


def parse_key(key: str) -> tuple[int, str, str]:
    match = KEY.fullmatch(key or "")
    if not match:
        raise ExternalMaterialError("material_external_path_invalid")
    return int(match.group(1)), match.group(2), match.group(3)


def _record(revision) -> dict:
    return ((revision.metadata_json or {}).get("external") or {}) if revision is not None else {}


@contextmanager
def open_verified(source, revision, *, full_hash: bool = False):
    """Yield the linked file only when it still holds the revision's bytes."""
    _source_id, content_hash, _relative = parse_key(revision.file_path)
    with open_file(source, relative_of(revision)) as handle:
        info = os.fstat(handle.fileno())
        record = _record(revision)
        if full_hash or info.st_size != record.get("size_bytes") or info.st_mtime_ns != record.get("mtime_ns"):
            if fingerprint(handle)[1] != content_hash:
                raise ExternalMaterialError("material_external_changed")
        yield handle


def _lookup(key: str):
    from ..db import SessionLocal
    from ..models import MaterialRevision, MaterialSource

    source_id, _hash, _relative = parse_key(key)
    with SessionLocal() as db:
        source = db.get(MaterialSource, source_id)
        revision = db.query(MaterialRevision).filter(MaterialRevision.file_path == key).first()
        if source is None or revision is None:
            raise ExternalMaterialError("material_external_unavailable")
        db.expunge_all()
    return source, revision


@contextmanager
def open_key(key: str, *, full_hash: bool = False):
    source, revision = _lookup(key)
    with open_verified(source, revision, full_hash=full_hash) as handle:
        yield handle


def relative_of(revision) -> str:
    # Archived files moved within the library drive; only library-source files are ever moved.
    return ((revision.metadata_json or {}).get("placement") or {}).get("path") or parse_key(revision.file_path)[2]


def path_of(source, revision) -> Path:
    return Path(source.root_path) / relative_of(revision)


def scan(db, source, subpath: str = "") -> dict:
    from sqlalchemy import String, cast, select

    from ..models import MaterialRevision
    from .storage_locations import library_source_id

    _require_available(source)
    base = Path(source.root_path)
    start = base / normalize_relative(subpath) if subpath else base
    linked: dict[str, list[dict]] = {}
    for revision in db.scalars(select(MaterialRevision).where(MaterialRevision.file_path.like(f"external/{source.id}/%"))):
        linked.setdefault(relative_of(revision), []).append(
            {"material_id": revision.material_id, "material_revision_id": revision.id, "content_hash": revision.content_hash})
    if source.id == library_source_id():
        # Platform files archived into project folders are already in the library, not new finds.
        for revision in db.scalars(select(MaterialRevision).where(MaterialRevision.file_path.like("material/%"),
                                                                  cast(MaterialRevision.metadata_json, String).like('%"placement"%'))):
            linked.setdefault(relative_of(revision), []).append(
                {"material_id": revision.material_id, "material_revision_id": revision.id, "content_hash": revision.content_hash})
    files, truncated = [], False
    for directory, names, filenames in os.walk(start, followlinks=False):
        depth = len(Path(directory).relative_to(base).parts)
        names[:] = sorted(name for name in names if not name.startswith(".")) if depth < MAX_SCAN_DEPTH else []
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            path = Path(directory) / name
            kind_mime = EXTENSIONS.get(path.suffix.lower().lstrip("."))
            if kind_mime is None or path.is_symlink():
                continue
            if len(files) >= MAX_SCAN_ENTRIES:
                truncated = True
                break
            info = path.stat()
            relative = unicodedata.normalize("NFC", path.relative_to(base).as_posix())
            files.append({"relative_path": relative, "kind": kind_mime[0], "mime_type": kind_mime[1],
                          "size_bytes": info.st_size, "modified_at": int(info.st_mtime), "linked": linked.get(relative, [])})
        if truncated:
            break
    return {"source_id": source.id, "root_path": source.root_path, "subpath": subpath, "files": files, "truncated": truncated}


def _media_type(handle, relative: str, kind: str) -> tuple[str, dict]:
    from types import SimpleNamespace

    from .materials import sniff_mime

    expected = EXTENSIONS.get(Path(relative).suffix.lower().lstrip("."))
    if expected is None or expected[0] != kind:
        raise ExternalMaterialError("material_external_type_unsupported")
    head = handle.read(64)
    handle.seek(0)
    sniffed = sniff_mime(head, None)
    mime = expected[1]
    compatible = sniffed == mime or (mime == "audio/mp4" and sniffed == "video/mp4") or (mime == "video/mp4" and sniffed == "video/quicktime")
    if not compatible:
        raise ExternalMaterialError("material_external_type_mismatch")
    # Phones save QuickTime files as .MP4; the bytes decide the type.
    mime = sniffed if kind == "video" else mime
    if kind != "video":
        return mime, {}
    from .creative_media_stream import validate

    info = validate(handle, mime, "video", SimpleNamespace(package_json={}))
    handle.seek(0)
    if not info.get("video_duration_ms"):
        raise ExternalMaterialError("material_external_video_invalid")
    return mime, info


def link(db, source, *, relative_path: str, kind: str, title: str | None, material_id: int | None,
         source_kind: str, source_url: str | None, rights_status: str, public_use_allowed: bool,
         model_use_allowed: bool, commercial_use_allowed: bool | None, attribution_text: str | None,
         tags: list[str], user):
    from sqlalchemy import select

    from ..models import AuditLog, Material, MaterialRevision
    from .materials import create_material

    relative = normalize_relative(relative_path)
    with open_file(source, relative) as handle:
        info = os.fstat(handle.fileno())
        size, content_hash = fingerprint(handle)
        mime, probe = _media_type(handle, relative, kind)
        after = os.fstat(handle.fileno())
        if (info.st_size, info.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ExternalMaterialError("material_external_changed")
    key = key_for(source.id, content_hash, relative)
    if len(key) > 500:
        raise ExternalMaterialError("material_external_path_invalid")
    parent = None
    if material_id is None:
        from .material_dedupe import existing_revision

        existing = existing_revision(db, content_hash)
        if existing is not None:
            return existing.material, existing
        material = create_material(db, kind=kind, title=title or Path(relative).name, tags=tags, created_by=user.email)
    else:
        material = db.get(Material, material_id)
        if material is None:
            raise ExternalMaterialError("material_not_found")
        parent = db.scalar(select(MaterialRevision).where(MaterialRevision.material_id == material.id)
                           .order_by(MaterialRevision.revision_no.desc()).limit(1))
        # A new version continues the same drive file; anything else is a different material.
        if parent is None or material.kind != kind or not is_external(parent.file_path) or parse_key(parent.file_path)[0] != source.id or parse_key(parent.file_path)[2] != relative:
            raise ExternalMaterialError("material_external_relink_mismatch")
        if parent.content_hash == content_hash:
            raise ExternalMaterialError("material_external_unchanged")
    if db.scalar(select(MaterialRevision.id).where(MaterialRevision.file_path == key).limit(1)):
        raise ExternalMaterialError("material_external_already_linked")
    revision = MaterialRevision(
        material_id=material.id, revision_no=(parent.revision_no + 1) if parent else 1,
        parent_revision_id=parent.id if parent else None, source_kind=source_kind, source_url=source_url,
        source_metadata_json={"material_source_id": source.id, "relative_path": relative},
        content_hash=content_hash, file_path=key, mime_type=mime,
        width=probe.get("width"), height=probe.get("height"), duration_ms=probe.get("video_duration_ms"),
        rights_status=rights_status, public_use_allowed=public_use_allowed, model_use_allowed=model_use_allowed,
        commercial_use_allowed=commercial_use_allowed, attribution_text=attribution_text,
        metadata_json={"filename": Path(relative).name, "external": {"material_source_id": source.id, "relative_path": relative,
                       "size_bytes": size, "mtime_ns": info.st_mtime_ns}, **({"media_probe": probe} if probe else {})},
        created_by=user.email,
    )
    db.add(revision)
    db.flush()
    db.add(AuditLog(event="material.external_linked", actor=user.email, entity_type="material", entity_id=str(material.id),
                    detail_json={"material_revision_id": revision.id, "material_source_id": source.id, "hash": content_hash,
                                 "size_bytes": size, "parent_revision_id": parent.id if parent else None}))
    return material, revision
