"""Bounded local-media transport for explicitly opted-in execution contracts."""

import hashlib
import json
import math
import os
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from contextvars import ContextVar
from fractions import Fraction

_TRANSFER = ContextVar("creative_transfer", default=None)

from fastapi import HTTPException

from . import creative_execution_files as files

CHUNK = 1024 * 1024
MEDIA_DECODE_TIMEOUT_SECONDS = 300


def fail(code, status=409):
    raise HTTPException(status, {"code": code})


def policy(package):
    return (package.package_json.get("output_contract") or {}).get("media_transfer_policy")


@contextmanager
def transfer(owner, execution):
    if _TRANSFER.get() == (owner, execution):
        yield
        return
    with files.root_fd(owner, execution, create=True) as root:
        import fcntl
        try:
            fcntl.flock(root, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fail("creative_transfer_in_progress")
        token = _TRANSFER.set((owner, execution))
        try:
            yield
        finally:
            _TRANSFER.reset(token)
            fcntl.flock(root, fcntl.LOCK_UN)


@contextmanager
def execution_file(owner, execution, key, maximum):
    parts = files._parts(key)
    if parts[0] not in {"inputs", "outputs", "staging"}:
        fail("execution_path_invalid", 422)
    with files.root_fd(owner, execution) as root, files._parent_fd(root, parts) as parent:
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
        with os.fdopen(descriptor, "rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= maximum:
                fail("execution_file_size_invalid", 413)
            yield source
            after = os.fstat(source.fileno())
            if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                fail("execution_file_changed")


@contextmanager
def _external_file(revision, maximum):
    from .material_external import ExternalMaterialError, _lookup, open_verified

    try:
        source_row, _revision = _lookup(revision.file_path)
        with open_verified(source_row, revision, full_hash=True) as source:
            if not 0 < os.fstat(source.fileno()).st_size <= maximum:
                fail("execution_file_size_invalid", 413)
            before = os.fstat(source.fileno())
            yield source
            after = os.fstat(source.fileno())
    except ExternalMaterialError as exc:
        fail("execution_input_hash_changed" if exc.code == "material_external_changed" else "execution_input_unavailable")
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        fail("execution_file_changed")


def external_target(revision):
    from .material_external import ExternalMaterialError, _lookup, path_of

    try:
        source_row, _revision = _lookup(revision.file_path)
    except ExternalMaterialError:
        fail("execution_input_unavailable")
    return path_of(source_row, revision)


def link_external(owner, execution, key, revision, expected_hash):
    """Expose a drive file by symbolic link: a clone cannot cross volumes and a copy is what linking avoids."""
    from .material_external import is_external

    parts = files._parts(key)
    if len(parts) != 2 or parts[0] != "inputs" or not is_external(revision.file_path) or revision.content_hash != expected_hash:
        fail("execution_path_invalid", 422)
    target = str(external_target(revision))
    with files.root_fd(owner, execution, create=True) as root, files._parent_fd(root, parts) as parent, files._locked(parent, exclusive=True):
        try:
            os.symlink(target, parts[-1], dir_fd=parent)
        except FileExistsError:
            if os.readlink(parts[-1], dir_fd=parent) != target:
                fail("execution_file_conflict")
        os.fsync(parent)
    return "external_link", None


@contextmanager
def material_file(revision, maximum):
    from .material_external import is_external
    from .material_storage import LocalMaterialStorage, provider
    if is_external(revision.file_path):
        with _external_file(revision, maximum) as source:
            yield source
        return
    storage = provider()
    if not isinstance(storage, LocalMaterialStorage):
        fail("execution_local_storage_required")
    files._parts(revision.file_path)
    base, parts = storage.locate(revision.file_path)
    descriptor = os.open("/", files._DIRECTORY)
    try:
        for part in base.parts[1:]:
            child = os.open(part, files._DIRECTORY, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        with files._parent_fd(descriptor, parts) as parent:
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(fd, "rb") as source:
                info = os.fstat(source.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= maximum:
                    fail("execution_file_size_invalid", 413)
                before = os.fstat(source.fileno())
                _size, digest = inspect(source, maximum)
                if digest != revision.content_hash:
                    fail("execution_input_hash_changed")
                yield source
                after = os.fstat(source.fileno())
                if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    fail("execution_file_changed")
    finally:
        os.close(descriptor)


def inspect(source, maximum):
    before = os.fstat(source.fileno())
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum:
        fail("execution_file_size_invalid", 413)
    source.seek(0)
    size, digest = 0, hashlib.sha256()
    while chunk := source.read(CHUNK):
        size += len(chunk)
        if size > maximum:
            fail("execution_file_size_invalid", 413)
        digest.update(chunk)
    source.seek(0)
    after = os.fstat(source.fileno())
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) or size != before.st_size:
        fail("execution_file_changed")
    if size < 1:
        fail("execution_file_size_invalid", 413)
    return size, digest.hexdigest()


def copy_private(owner, execution, key, source, maximum, *, expected_hash=None):
    parts = files._parts(key)
    if len(parts) != 2 or parts[0] not in {"inputs", "staging"}:
        fail("execution_path_invalid", 422)
    source.seek(0)
    size, digest = inspect(source, maximum)
    if expected_hash is not None and digest != expected_hash:
        fail("execution_file_changed")
    with files.root_fd(owner, execution, create=True) as root, files._parent_fd(root, parts) as parent, files._locked(parent, exclusive=True):
        temporary = "pending-" + os.urandom(16).hex()
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, "wb") as target:
                copied, actual = 0, hashlib.sha256()
                while chunk := source.read(CHUNK):
                    copied += len(chunk)
                    if copied > maximum:
                        fail("execution_file_size_invalid", 413)
                    actual.update(chunk)
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
            if (copied, actual.hexdigest()) != (size, digest):
                fail("execution_file_changed")
            try:
                os.link(temporary, parts[-1], src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
            except FileExistsError:
                fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                with os.fdopen(fd, "rb") as existing:
                    if (not stat.S_ISREG(os.fstat(existing.fileno()).st_mode) or os.fstat(existing.fileno()).st_nlink != 1) or inspect(existing, maximum) != (size, digest):
                        fail("execution_file_conflict")
            os.fsync(parent)
        finally:
            os.unlink(temporary, dir_fd=parent)
            os.fsync(parent)
    return size, digest


def _clone_function():
    import ctypes
    import ctypes.util

    try:
        function = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True).fclonefileat
    except (OSError, AttributeError):
        return None
    function.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    return function


def clone_private(owner, execution, key, source, maximum, *, expected_hash):
    """Expose a library file as a copy-on-write clone: no duplicated bytes, and writes never reach the library."""
    parts = files._parts(key)
    if len(parts) != 2 or parts[0] != "inputs":
        fail("execution_path_invalid", 422)
    clone = _clone_function()
    if clone is None:
        return (*copy_private(owner, execution, key, source, maximum, expected_hash=expected_hash), "copy", "clone_unsupported_platform")
    with files.root_fd(owner, execution, create=True) as root, files._parent_fd(root, parts) as parent, files._locked(parent, exclusive=True):
        temporary = "pending-" + os.urandom(16).hex()
        if clone(source.fileno(), parent, temporary.encode(), 0) != 0:
            import ctypes

            reason = os.strerror(ctypes.get_errno())
        else:
            reason = None
            try:
                fd = os.open(temporary, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                with os.fdopen(fd, "rb") as cloned:
                    size, digest = inspect(cloned, maximum)
                    os.fchmod(cloned.fileno(), 0o400)
                if digest != expected_hash:
                    fail("execution_file_changed")
                try:
                    os.link(temporary, parts[-1], src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
                except FileExistsError:
                    fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                    with os.fdopen(fd, "rb") as existing:
                        if (not stat.S_ISREG(os.fstat(existing.fileno()).st_mode) or os.fstat(existing.fileno()).st_nlink != 1) or inspect(existing, maximum) != (size, digest):
                            fail("execution_file_conflict")
                os.fsync(parent)
            finally:
                os.unlink(temporary, dir_fd=parent)
                os.fsync(parent)
    if reason is not None:
        return (*copy_private(owner, execution, key, source, maximum, expected_hash=expected_hash), "copy", f"clone_failed: {reason}")
    return size, digest, "clone", None


def validate(source, mime, kind, package, *, role_id=None):
    size = os.fstat(source.fileno()).st_size
    source.seek(0)
    head = source.read(64)
    source.seek(0)
    if kind != "video":
        from .materials import validate_execution_file
        if kind == "other" and mime in {"application/x-resolve-project", "application/x-after-effects-project"}:
            if not head or not any(head):
                fail("creative_project_file_invalid", 422)
            return {}
        if size > 30 * CHUNK:
            fail("execution_file_size_invalid", 413)
        if mime == "application/json" and size > 2_000_000:
            fail("creative_json_bounds", 422)
        validate_execution_file(source.read(30 * CHUNK + 1), mime, kind)
        source.seek(0)
        return {}
    detected_mime = "video/quicktime" if head[8:12] == b"qt  " else "video/mp4"
    if mime not in {"video/mp4", "video/quicktime"} or head[4:8] != b"ftyp" or mime != detected_mime:
        fail("creative_video_mime_invalid", 422)
    try:
        with tempfile.TemporaryFile() as result:
            subprocess.run(["ffprobe", "-v", "error", "-max_alloc", "67108864", "-protocol_whitelist", "file,pipe", "-probesize", "5000000", "-analyzeduration", "5000000", "-show_entries", "stream=codec_type,width,height,r_frame_rate,avg_frame_rate,pix_fmt,duration:format=duration", "-of", "json", f"/dev/fd/{source.fileno()}"], pass_fds=(source.fileno(),), stdout=result, stderr=subprocess.DEVNULL, timeout=30, check=True)
            result.seek(0)
            raw = result.read(64001)
            if len(raw) > 64000:
                fail("creative_video_probe_bounds", 422)
            info = json.loads(raw)
        video = next(item for item in info["streams"] if item["codec_type"] == "video")
        video_duration = float(video.get("duration") or info["format"]["duration"])
        durations = [video_duration]
        for value in [info.get("format", {}).get("duration"), *(stream.get("duration") for stream in info["streams"])]:
            if value not in {None, "N/A"}:
                durations.append(float(value))
        if any(not math.isfinite(value) or value <= 0 for value in durations):
            raise ValueError()
        duration = round(max(durations) * 1000)
        video_duration_ms = round(video_duration * 1000)
        width, height = int(video["width"]), int(video["height"])
        numerator, denominator = map(int, video["r_frame_rate"].split("/"))
        average_rate = Fraction(video.get("avg_frame_rate") or video["r_frame_rate"])
        if average_rate <= 0:
            raise ValueError()
        pix_fmt = video.get("pix_fmt")
        if not isinstance(pix_fmt, str) or not pix_fmt:
            raise ValueError()
        if min(duration, width, height, numerator, denominator) <= 0:
            raise ValueError()
    except (OSError, ValueError, ZeroDivisionError, KeyError, StopIteration, subprocess.SubprocessError):
        fail("creative_video_decode_invalid", 422)
    finally:
        source.seek(0, os.SEEK_END)
        source.seek(0)
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-max_alloc", "67108864", "-xerror", "-protocol_whitelist", "file,pipe", "-threads", "1", "-i", f"/dev/fd/{source.fileno()}", "-f", "null", "-"], pass_fds=(source.fileno(),), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=MEDIA_DECODE_TIMEOUT_SECONDS, check=True)
    except (OSError, subprocess.SubprocessError):
        fail("creative_video_decode_invalid", 422)
    finally:
        source.seek(0, os.SEEK_END)
        source.seek(0)
    audio = any(item["codec_type"] == "audio" for item in info["streams"])
    web = package.package_json.get("web_video")
    if web:
        aw, ah = web["aspect_ratio"]
        if abs(width / height - aw / ah) > 0.025:
            fail("creative_video_aspect_mismatch", 422)
        if duration + 100 < web["use_duration_ms"] or duration > web["requested_generation_duration_ms"] + 1000:
            fail("creative_video_duration_mismatch", 422)
        if web["audio_intent"] in {"keep", "required", "generated_audio"} and not audio:
            fail("creative_video_audio_required", 422)
    director = package.package_json.get("director") or {}
    post = director.get("postproduction")
    if post:
        composition = next((item for item in post.get("ae_compositions", []) if item["role_id"] == role_id), None)
        is_render = role_id in {"rough_cut", "final"}
        if role_id is None or (role_id.startswith("ae_intermediate") and composition is None):
            fail("creative_video_output_role_required", 422)
        contract = post if is_render else composition
        if contract:
            expected_rate = Fraction(str(contract["fps"]))
            tolerance_ms = math.ceil(1000 / expected_rate) + 1
            target_duration = director["timeline"]["duration_ms"] if is_render else contract["duration_ms"]
            if abs(duration - target_duration) > tolerance_ms or abs(video_duration_ms - target_duration) > tolerance_ms:
                fail("creative_video_duration_mismatch", 422)
            if [width, height] != contract["resolution"]:
                fail("creative_video_resolution_mismatch", 422)
            if Fraction(numerator, denominator) != expected_rate or average_rate != expected_rate:
                fail("creative_video_frame_rate_mismatch", 422)
            if is_render and director.get("voice", {}).get("mode", "none") != "none" and not audio:
                fail("creative_video_audio_required", 422)
            if composition and composition["alpha_required"]:
                alpha = pix_fmt.startswith(("yuva", "gbrap", "rgba", "argb", "bgra", "abgr", "ya8", "ya16", "ayuv64")) or pix_fmt == "vuya"
                if mime != "video/quicktime" or not alpha:
                    fail("creative_video_alpha_required", 422)
    result = {"width": width, "height": height, "duration_ms": duration,
            "video_duration_ms": video_duration_ms if video.get("duration") not in {None, "N/A"} else None,
            "frame_rate": numerator / denominator,
            "average_frame_rate": float(average_rate), "has_audio": audio, "pix_fmt": pix_fmt}
    if post and role_id in {"rough_cut", "final"} and audio:
        result["loudness"] = loudness(source)
    return result


LOUDNESS_WINDOW_LUFS = (-18.0, -12.0)
TRUE_PEAK_CEILING_DBTP = -1.0


def loudness(source):
    """EBU R128 reading for review; a clipping or quiet mix is a warning, never a rejection."""
    try:
        done = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-max_alloc", "67108864", "-protocol_whitelist", "file,pipe", "-threads", "1",
                               "-i", f"/dev/fd/{source.fileno()}", "-vn", "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                              pass_fds=(source.fileno(),), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                              timeout=MEDIA_DECODE_TIMEOUT_SECONDS, check=True)
        text = done.stderr[-8192:].decode("utf-8", "replace")
        data = json.loads(text[text.rindex("{"):text.rindex("}") + 1])
        integrated, peak, spread = float(data["input_i"]), float(data["input_tp"]), float(data["input_lra"])
        if not all(math.isfinite(value) for value in (integrated, peak, spread)):
            raise ValueError()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return {"status": "unmeasured"}
    finally:
        source.seek(0)
    warnings = [code for code, hit in (("true_peak_above_ceiling", peak > TRUE_PEAK_CEILING_DBTP),
                                       ("loudness_below_window", integrated < LOUDNESS_WINDOW_LUFS[0]),
                                       ("loudness_above_window", integrated > LOUDNESS_WINDOW_LUFS[1])) if hit]
    return {"status": "measured", "integrated_lufs": integrated, "true_peak_dbtp": peak, "lra_lu": spread,
            "window_lufs": list(LOUDNESS_WINDOW_LUFS), "true_peak_ceiling_dbtp": TRUE_PEAK_CEILING_DBTP, "warnings": warnings}


def budget(db, row, package, incoming):
    from sqlalchemy import select

    from ..models import CreativeExecutionOutput, MaterialRevision
    from .material_storage import provider
    storage = provider()
    authorized_ids = {item["material_revision_id"] for item in package.package_json.get("assets", [])}
    authorized_bytes = 0
    for revision_id in authorized_ids:
        revision = db.get(MaterialRevision, revision_id)
        if revision is None:
            fail("creative_input_unavailable")
        size = storage.size(revision.file_path)
        if size > policy(package)["max_file_bytes"]:
            fail("execution_file_size_invalid", 413)
        authorized_bytes += size
    total = max(authorized_bytes, sum(item["size_bytes"] for item in row.materialized_inputs_json or []))
    # Every attempt consumes its frozen allowance, even after rejection/cleanup.
    total += sum(db.scalars(select(CreativeExecutionOutput.size_bytes).where(CreativeExecutionOutput.execution_id == row.id)))
    recorded = {item.staging_key for item in db.scalars(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id == row.id))}
    with files.root_fd(row.owner_user_id, row.id, create=True) as root, files._parent_fd(root, ["staging", "manifest"]) as parent, os.scandir(parent) as entries:
        for index, entry in enumerate(entries):
            if index > 1000:
                fail("creative_execution_output_history_limit")
            if f"staging/{entry.name}" not in recorded:
                total += entry.stat(follow_symlinks=False).st_size
    if total + incoming > policy(package)["max_total_bytes"]:
        fail("creative_execution_total_bytes_exceeded", 413)
