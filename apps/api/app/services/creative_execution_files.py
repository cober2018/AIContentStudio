"""Private execution transport, anchored to directory descriptors."""

from __future__ import annotations

import fcntl
import hashlib
import os
import re
import stat
from contextlib import contextmanager
from pathlib import Path

from fastapi import HTTPException

from .creative_contracts import MAX_FILE_BYTES, MAX_INPUTS, MAX_OUTPUT_ROWS

_DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,149}\Z")


def _error(code: str, status: int = 422) -> HTTPException:
    return HTTPException(status, {"code": code})


def _parts(key: str) -> list[str]:
    if not isinstance(key, str) or len(key) > 500:
        raise _error("execution_path_invalid")
    parts = key.split("/")
    if not 1 <= len(parts) <= 8 or any(not _COMPONENT.fullmatch(part) or part in {".", ".."} for part in parts):
        raise _error("execution_path_invalid")
    return parts


def work_root(owner_id: int, execution_id: int) -> Path:
    from .asset_media import MEDIA_ROOT

    if any(type(item) is not int or item < 1 for item in (owner_id, execution_id)):
        raise _error("execution_identity_invalid")
    return MEDIA_ROOT / ".creative-executions" / str(owner_id) / str(execution_id)


def _private_child(parent: int, name: str, create: bool) -> int:
    if create:
        try:
            os.mkdir(name, 0o700, dir_fd=parent)
        except FileExistsError:
            pass
    descriptor = os.open(name, _DIRECTORY, dir_fd=parent)
    try:
        info = os.fstat(descriptor)
        if info.st_uid != os.geteuid() or not stat.S_ISDIR(info.st_mode):
            raise _error("execution_directory_invalid", 409)
        if create:
            os.fchmod(descriptor, 0o700)
            os.fsync(parent)
        elif stat.S_IMODE(info.st_mode) != 0o700:
            raise _error("execution_directory_invalid", 409)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


@contextmanager
def root_fd(owner_id: int, execution_id: int, *, create: bool = False):
    from .asset_media import MEDIA_ROOT

    work_root(owner_id, execution_id)
    descriptor = os.open("/", _DIRECTORY)
    try:
        # Walk the configured root without resolving caller-controlled symlinks.
        for position, component in enumerate(MEDIA_ROOT.parts[1:], start=1):
            try:
                child = os.open(component, _DIRECTORY, dir_fd=descriptor)
            except FileNotFoundError:
                if not create or position != len(MEDIA_ROOT.parts) - 1:
                    raise
                try:
                    os.mkdir(component, 0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                child = os.open(component, _DIRECTORY, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        for component in (".creative-executions", str(owner_id), str(execution_id)):
            child = _private_child(descriptor, component, create)
            os.close(descriptor)
            descriptor = child
        if create:
            for component in ("inputs", "outputs", "staging"):
                child = _private_child(descriptor, component, True)
                os.close(child)
        yield descriptor
    except OSError:
        raise _error("execution_storage_unavailable", 409) from None
    finally:
        os.close(descriptor)


@contextmanager
def _parent_fd(root: int, parts: list[str]):
    descriptor = os.dup(root)
    try:
        for component in parts[:-1]:
            child = os.open(component, _DIRECTORY, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor
    finally:
        os.close(descriptor)


@contextmanager
def _locked(parent: int, *, exclusive: bool = False):
    fcntl.flock(parent, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
    try:
        yield
    finally:
        fcntl.flock(parent, fcntl.LOCK_UN)


def _read(parent: int, name: str, maximum: int, *, links: int = 1, allow_empty: bool = False) -> bytes:
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != links:
            raise _error("execution_regular_file_required")
        if not (0 if allow_empty else 1) <= before.st_size <= maximum:
            raise _error("execution_file_size_invalid", 413)
        chunks = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        content = b"".join(chunks)
        if len(content) > maximum:
            raise _error("execution_file_size_invalid", 413)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_nlink) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink
        ) or len(content) != before.st_size:
            raise _error("execution_file_changed", 409)
        return content
    finally:
        os.close(descriptor)


def read_file(owner_id: int, execution_id: int, key: str, *, maximum: int = MAX_FILE_BYTES, output: bool = False) -> bytes:
    parts = _parts(key)
    if parts[0] not in ({"outputs"} if output else {"inputs", "staging"}):
        raise _error("execution_path_invalid")
    if type(maximum) is not int or not 1 <= maximum <= MAX_FILE_BYTES:
        raise _error("execution_file_size_invalid")
    with root_fd(owner_id, execution_id) as root, _parent_fd(root, parts) as parent, _locked(parent):
        return _read(parent, parts[-1], maximum)


def _pending_name(name: str, content: bytes) -> str:
    return f"pending-{hashlib.sha256(name.encode()).hexdigest()}-{hashlib.sha256(content).hexdigest()}"


def _recover_pending(parent: int, name: str, content: bytes) -> None:
    expected_pending = _pending_name(name, content)
    with os.scandir(parent) as entries:
        for index, entry in enumerate(entries):
            if index >= MAX_OUTPUT_ROWS * 2 + MAX_INPUTS + 1:
                raise _error("execution_recovery_bounds", 409)
            current_write = entry.name == expected_pending
            if not current_write and not re.fullmatch(r"pending-[0-9a-f]{32}", entry.name):
                continue
            before = entry.stat(follow_symlinks=False)
            if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.geteuid()
                    or stat.S_IMODE(before.st_mode) != 0o600
                    or before.st_nlink not in {1, 2} or before.st_size > len(content)
                    or (not current_write and before.st_size != len(content))):
                continue
            if before.st_nlink == 2:
                try:
                    published = os.stat(name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if (before.st_dev, before.st_ino) != (published.st_dev, published.st_ino):
                    continue
            # A partial write is removable only with its exact destination/hash binding.
            pending_content = _read(parent, entry.name, len(content), links=before.st_nlink, allow_empty=current_write)
            if (pending_content != content
                    and (not current_write or before.st_nlink != 1 or not content.startswith(pending_content))):
                continue
            after = os.stat(entry.name, dir_fd=parent, follow_symlinks=False)
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
                    before.st_ctime_ns, before.st_nlink) != (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
                    after.st_ctime_ns, after.st_nlink):
                raise _error("execution_file_changed", 409)
            os.unlink(entry.name, dir_fd=parent)
            os.fsync(parent)


def write_file(owner_id: int, execution_id: int, key: str, content: bytes) -> None:
    parts = _parts(key)
    if len(parts) != 2 or parts[0] not in {"inputs", "staging"} or not 0 < len(content) <= MAX_FILE_BYTES:
        raise _error("execution_path_invalid")
    with (root_fd(owner_id, execution_id, create=True) as root,
          _parent_fd(root, parts) as parent, _locked(parent, exclusive=True)):
        _recover_pending(parent, parts[-1], content)
        temporary = _pending_name(parts[-1], content)
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
        try:
            with os.fdopen(descriptor, "wb") as target:
                os.fchmod(target.fileno(), 0o600)
                target.write(content)
                target.flush()
                os.fsync(target.fileno())
            try:
                os.link(temporary, parts[-1], src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
            except FileExistsError:
                if _read(parent, parts[-1], MAX_FILE_BYTES) != content:
                    raise _error("execution_file_conflict", 409) from None
            os.fsync(parent)
        finally:
            os.unlink(temporary, dir_fd=parent)
            os.fsync(parent)


def check_input_manifest(owner_id: int, execution_id: int, filenames: set[str]) -> None:
    with (root_fd(owner_id, execution_id) as root,
          _parent_fd(root, ["inputs", "manifest"]) as parent,
          _locked(parent),
          os.scandir(parent) as entries):
        for index, entry in enumerate(entries):
            if index >= 100 or entry.name not in filenames:
                raise _error("execution_input_not_recorded", 409)
            info = entry.stat(follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise _error("execution_regular_file_required", 409)


def cleanup_staging(owner_id: int, execution_id: int, key: str, *, content_hash: str, size_bytes: int) -> str:
    if (not isinstance(content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", content_hash)
            or key != f"staging/{content_hash}.bin" or type(size_bytes) is not int
            or not 0 < size_bytes <= MAX_FILE_BYTES):
        raise _error("execution_cleanup_target_invalid", 409)
    with (root_fd(owner_id, execution_id) as root,
          _parent_fd(root, _parts(key)) as parent, _locked(parent, exclusive=True)):
        name = _parts(key)[-1]
        try:
            before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            # A retry after unlink/fsync failure must still sync the directory.
            os.fsync(parent)
            return "already_absent"
        content = _read(parent, name, size_bytes)
        after = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                or len(content) != size_bytes or hashlib.sha256(content).hexdigest() != content_hash):
            raise _error("execution_cleanup_file_changed", 409)
        os.unlink(name, dir_fd=parent)
        os.fsync(parent)
        return "removed"


def read_material(revision, *, maximum: int = MAX_FILE_BYTES) -> bytes:
    from .material_storage import LocalMaterialStorage, provider

    storage = provider()
    if not isinstance(storage, LocalMaterialStorage):
        raise _error("execution_local_storage_required", 409)
    key = revision.file_path
    parts = _parts(key)
    descriptor = os.open("/", _DIRECTORY)
    try:
        for component in storage.root.parts[1:]:
            child = os.open(component, _DIRECTORY, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        with _parent_fd(descriptor, parts) as parent:
            content = _read(parent, parts[-1], maximum)
    except OSError:
        raise _error("execution_input_unavailable", 409) from None
    finally:
        os.close(descriptor)
    if hashlib.sha256(content).hexdigest() != revision.content_hash:
        raise _error("execution_input_hash_changed", 409)
    return content
