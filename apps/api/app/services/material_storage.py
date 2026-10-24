"""Infrastructure storage for immutable MaterialRevision bytes.

Business IDs and content hashes remain database truth.  This adapter only
changes where bytes live; production mode must choose one provider explicitly.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import tempfile
from contextlib import contextmanager
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


@contextmanager
def _external(key: str, *, full_hash: bool = False):
    # Linked drive files keep the storage error contract: missing is OSError, changed is ValueError.
    from .material_external import ExternalMaterialError, open_key

    try:
        with open_key(key, full_hash=full_hash) as source:
            yield source
    except ExternalMaterialError as exc:
        if exc.code == "material_external_unavailable":
            raise FileNotFoundError(exc.code) from None
        raise ValueError(exc.code) from None


class LocalMaterialStorage:
    name = "local"

    def __init__(self, root: Path, *, legacy_absolute_reads: bool = False, library: bool = False):
        self.root = root.resolve()
        self.legacy_absolute_reads = legacy_absolute_reads
        self.library = library

    def _local(self, key: str) -> Path:
        path = (self.root / _safe_key(key)).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("storage_key_invalid")
        return path

    def _path(self, key: str) -> Path:
        # Material bytes made before the library existed stay where they are; new ones live in the library.
        local = self._local(key)
        if not self.library or not re.fullmatch(r"material/[0-9a-f]{2}/[^/]+", key):
            return local
        from .project_folders import placed_path
        from .storage_locations import library_path, library_root

        if local.exists():
            return local
        default = library_path(key) if library_root() is not None else local
        if default.exists():
            return default
        # Files archived into a project folder keep their key; the revision records where they went.
        return placed_path(key) or default

    def locate(self, key: str) -> tuple[Path, list[str]]:
        """Directory to walk from, and the components below it, for descriptor-safe opens."""
        path = self._path(key)
        if path.is_relative_to(self.root):
            return self.root, list(Path(_safe_key(key)).parts)
        return path.parent.parent, list(path.parts[-2:])

    def _writable(self, path: Path) -> None:
        from .storage_locations import library_reachable

        # An unplugged drive must fail loudly, never fall back to a second home or create /Volumes/<drive>.
        if not path.is_relative_to(self.root) and not library_reachable():
            raise FileNotFoundError("material_library_unavailable")

    def put(self, key: str, content: bytes) -> None:
        if len(content) > MAX_BYTES:
            raise ValueError("storage_object_too_large")
        if key.startswith("external/"):
            raise ValueError("storage_key_invalid")
        if key.startswith("material/"):
            _validate_material_key(key, _content_hash(content))
        if key.startswith("legacy/") and not re.fullmatch(r"legacy/" + _content_hash(content) + r"\.[A-Za-z0-9]+", key):
            raise ValueError("storage_key_invalid")
        path = self._path(key)
        self._writable(path)
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

    def put_stream(self, key: str, source, *, maximum: int, expected_hash: str) -> None:
        from .creative_media_stream import CHUNK, inspect
        _validate_material_key(key, expected_hash)
        size, digest = inspect(source, maximum)
        if digest != expected_hash:
            raise ValueError("storage_object_hash_mismatch")
        path = self._path(key)
        self._writable(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as target:
                os.fchmod(target.fileno(), 0o600)
                copied, actual = 0, hashlib.sha256()
                while chunk := source.read(CHUNK):
                    copied += len(chunk)
                    if copied > maximum:
                        raise ValueError("storage_object_too_large")
                    actual.update(chunk)
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
            if (copied, actual.hexdigest()) != (size, digest):
                raise ValueError("storage_object_hash_mismatch")
            try:
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError:
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, "rb") as existing:
                    import stat
                    if not stat.S_ISREG(os.fstat(existing.fileno()).st_mode) or inspect(existing, maximum) != (size, digest):
                        raise ValueError("storage_object_conflict")
            _sync_directory(path.parent)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def read(self, key: str) -> bytes:
        if key.startswith("external/"):
            with _external(key, full_hash=True) as source:
                content = source.read(MAX_BYTES + 1)
            if len(content) > MAX_BYTES:
                raise ValueError("storage_object_too_large")
            return content
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
        if key.startswith("external/"):
            try:
                with _external(key):
                    return True
            except (OSError, ValueError):
                return False
        return self._path(key).is_file()

    def size(self, key: str) -> int:
        if key.startswith("external/"):
            with _external(key) as source:
                return os.fstat(source.fileno()).st_size
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


class MinioMaterialStorage:
    name = "minio"

    def __init__(self):
        from minio import Minio
        from urllib3 import PoolManager, Timeout

        settings = get_settings()
        self.bucket = settings.minio_bucket
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            http_client=PoolManager(timeout=Timeout(connect=2, read=5), retries=False),
        )

    def put(self, key: str, content: bytes) -> None:
        key = _safe_key(key)
        if len(content) > MAX_BYTES:
            raise ValueError("storage_object_too_large")
        digest = _content_hash(content)
        if key.startswith("material/"):
            _validate_material_key(key, digest)
        elif (key.startswith("legacy/") and not re.fullmatch(r"legacy/" + digest + r"\.[A-Za-z0-9]+", key)) or (key.startswith("generation/") and (
            not re.fullmatch(r"generation/[0-9a-f]{32}/[0-9a-f]{64}\.bin", key)
            or Path(key).stem != digest
        )):
            raise ValueError("storage_key_invalid")
        if self.exists(key):
            if self.read(key) != content:
                raise ValueError("storage_object_conflict")
            return
        self.client.put_object(self.bucket, key, io.BytesIO(content), len(content))

    def read(self, key: str) -> bytes:
        key = _safe_key(key)
        response = self.client.get_object(self.bucket, key)
        try:
            content = response.read(MAX_BYTES + 1)
        finally:
            response.close()
            response.release_conn()
        if len(content) > MAX_BYTES:
            raise ValueError("storage_object_too_large")
        return content

    def exists(self, key: str) -> bool:
        from minio.error import S3Error

        try:
            self.client.stat_object(self.bucket, _safe_key(key))
            return True
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                return False
            raise

    def size(self, key: str) -> int:
        try:
            return self.client.stat_object(self.bucket, _safe_key(key)).size
        except Exception as exc:
            from minio.error import S3Error

            if isinstance(exc, S3Error) and exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                raise FileNotFoundError("storage_object_missing") from None
            raise

    def probe(self) -> bool:
        return self.client.bucket_exists(self.bucket)

    def delete_if_unreferenced(self, key: str, *, expected_hash: str) -> bool:
        if not key.startswith("material/") or Path(key).stem != expected_hash:
            raise ValueError("material_storage_key_invalid")
        if not self.exists(key):
            return False
        if _content_hash(self.read(key)) != expected_hash:
            raise ValueError("storage_object_hash_mismatch")
        self.client.remove_object(self.bucket, _safe_key(key))
        return True


def provider() -> MaterialStorage:
    from .asset_media import MEDIA_ROOT

    settings = get_settings()
    if settings.material_storage_backend == "local":
        return LocalMaterialStorage(MEDIA_ROOT, legacy_absolute_reads=settings.app_env in {"development", "test"}, library=True)
    if settings.material_storage_backend == "minio":
        return MinioMaterialStorage()
    raise ValueError("storage_backend_invalid")


def read_legacy_bytes(key: str, *, expected_hash: str | None = None) -> bytes:
    """Historical DB paths use the selected store, never a second local fallback."""
    try:
        content = provider().read(key)
    except (OSError, ValueError):
        raise
    except Exception:  # noqa: BLE001 External stores must not leak credential-bearing diagnostics.
        raise ValueError("storage_unavailable") from None
    key_hash = Path(key).stem if key.startswith("legacy/") else None
    digest = expected_hash or key_hash
    if digest and _content_hash(content) != digest:
        raise ValueError("storage_object_hash_mismatch")
    return content
