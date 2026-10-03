"""Infrastructure storage for immutable MaterialRevision bytes.

Business IDs and content hashes remain database truth.  This adapter only
changes where bytes live; production mode must choose one provider explicitly.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import Protocol

from ..config import get_settings

MAX_BYTES = 30 * 1024 * 1024


class MaterialStorage(Protocol):
    name: str

    def put(self, key: str, content: bytes) -> None: ...
    def read(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...
    def size(self, key: str) -> int: ...
    def probe(self) -> bool: ...
    def delete_if_unreferenced(self, key: str, *, expected_hash: str) -> bool: ...


def _content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _validate_material_key(key: str, content_hash: str) -> None:
    path = Path(key)
    if (not re.fullmatch(r"material/[0-9a-f]{2}/[0-9a-f]{64}(?:\.[A-Za-z0-9]+)?", key)
            or path.stem != content_hash):
        raise ValueError("material_storage_key_invalid")


def _safe_key(key: str) -> str:
    path = Path(key)
    if not key or path.is_absolute() or ".." in path.parts or "\\" in key or any(ord(char) < 32 or ord(char) == 127 for char in key):
        raise ValueError("storage_key_invalid")
    return path.as_posix()


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class LocalMaterialStorage:
    name = "local"

    def __init__(self, root: Path, *, legacy_absolute_reads: bool = False):
        self.root = root.resolve()
        self.legacy_absolute_reads = legacy_absolute_reads

    def _path(self, key: str) -> Path:
        path = (self.root / _safe_key(key)).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("storage_key_invalid")
        return path

    def put(self, key: str, content: bytes) -> None:
        if len(content) > MAX_BYTES:
            raise ValueError("storage_object_too_large")
        if key.startswith("material/"):
            _validate_material_key(key, _content_hash(content))
        if key.startswith("legacy/") and not re.fullmatch(r"legacy/" + _content_hash(content) + r"\.[A-Za-z0-9]+", key):
            raise ValueError("storage_key_invalid")
        path = self._path(key)
        if key.startswith("generation/"):
            if (not re.fullmatch(r"generation/[0-9a-f]{32}/[0-9a-f]{64}\.bin", key)
                    or path != self.root / key
                    or path.stem != hashlib.sha256(content).hexdigest()):
                raise ValueError("storage_key_invalid")
            # Pending generated results are not public library assets. Publish
            # only a fully fsynced private file, without replacing prior bytes.
            missing = []
            ancestor = self.root
            while not ancestor.exists():
                missing.append(ancestor)
                ancestor = ancestor.parent
            for directory in reversed(missing):
                directory.mkdir(exist_ok=True)
                _sync_directory(directory.parent)
            for directory in (self.root / "generation", path.parent):
                directory.mkdir(mode=0o700, exist_ok=True)
                if directory.is_symlink():
                    raise ValueError("storage_key_invalid")
                directory.chmod(0o700)
                _sync_directory(directory)
                _sync_directory(directory.parent)
            descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
            try:
                with os.fdopen(descriptor, "wb") as target:
                    os.fchmod(target.fileno(), 0o600)
                    target.write(content)
                    target.flush()
                    os.fsync(target.fileno())
                try:
                    os.link(temporary, path, follow_symlinks=False)
                except FileExistsError:
                    if path.is_symlink() or not path.is_file() or self.read(key) != content:
                        raise ValueError("storage_object_conflict") from None
                    path.chmod(0o600)
                _sync_directory(path.parent)
            finally:
                Path(temporary).unlink(missing_ok=True)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.is_symlink() or not path.is_file() or self.read(key) != content:
                raise ValueError("storage_object_conflict")
            return
        descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as target:
                os.fchmod(target.fileno(), 0o600)
                target.write(content)
                target.flush()
                os.fsync(target.fileno())
            try:
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError:
                if path.is_symlink() or not path.is_file() or self.read(key) != content:
                    raise ValueError("storage_object_conflict") from None
            _sync_directory(path.parent)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def read(self, key: str) -> bytes:
        # Pre-F8 local revisions may reference an absolute fixture/import path.
        # Only authenticated DB revision reads in dev/test retain this bridge;
        # writes and production/object-storage paths remain root-constrained.
        path = Path(key).resolve() if self.legacy_absolute_reads and Path(key).is_absolute() else self._path(key)
        if not path.is_file():
            raise FileNotFoundError("storage_object_missing")
        with path.open("rb") as source:
            content = source.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise ValueError("storage_object_too_large")
        return content

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def size(self, key: str) -> int:
        path = self._path(key)
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError("storage_object_missing")
        return path.stat().st_size

    def probe(self) -> bool:
        return self.root.is_dir() and os.access(self.root, os.R_OK | os.W_OK | os.X_OK)

    def delete_if_unreferenced(self, key: str, *, expected_hash: str) -> bool:
        path = self._path(key)
        if not key.startswith("material/") or Path(key).stem != expected_hash:
            raise ValueError("material_storage_key_invalid")
        if not path.exists():
            return False
        if path.is_symlink() or not path.is_file() or _content_hash(self.read(key)) != expected_hash:
            raise ValueError("storage_object_hash_mismatch")
        path.unlink()
        _sync_directory(path.parent)
        return True


def provider() -> MaterialStorage:
    from .asset_media import MEDIA_ROOT

    settings = get_settings()
    if settings.material_storage_backend == "local":
        return LocalMaterialStorage(MEDIA_ROOT, legacy_absolute_reads=settings.app_env in {"development", "test"})
    raise ValueError("storage_backend_invalid")
