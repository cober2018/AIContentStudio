"""Library preview derivatives and playback reads; originals are only ever read, never rewritten."""

from __future__ import annotations

import io
import os
import re
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path

from fastapi import HTTPException

from .asset_media import MEDIA_ROOT

THUMB_WIDTH = 640
STRIP_FRAMES = 8
STRIP_WIDTH = 240
FFMPEG_TIMEOUT = 60
CHUNK = 1024 * 1024
_guard = threading.Lock()
_locks: dict[str, threading.Lock] = {}


def media_kind(revision) -> str | None:
    mime = revision.mime_type or ""
    return next((kind for kind in ("image", "video", "audio") if mime.startswith(kind + "/")), None)


@contextmanager
def source_path(db, revision):
    """Yield a filesystem path for the revision bytes, checked without rehashing large drive files."""
    from .material_external import ExternalMaterialError, _lookup, http_error, is_external, open_verified, path_of
    from .material_storage import LocalMaterialStorage, provider

    if revision.status in {"revoked", "archived"} or revision.material.status != "active":
        raise HTTPException(409, {"code": "material_revision_inactive"})
    if is_external(revision.file_path):
        try:
            source, linked = _lookup(revision.file_path)
            # Size and mtime match the linked record or the file is hashed again; the handle pins it while in use.
            with open_verified(source, linked):
                yield path_of(source, linked)
        except ExternalMaterialError as exc:
            raise http_error(exc) from None
        return
    storage = provider()
    if isinstance(storage, LocalMaterialStorage) and revision.file_path:
        try:
            path = storage._path(revision.file_path)
        except ValueError:
            path = None
        # Stored keys are content addressed, so a matching size is enough to trust local bytes for previews.
        if path is not None and path.is_file() and not path.is_symlink():
            yield path
            return
    from .materials import read_bytes_checked

    with tempfile.NamedTemporaryFile(suffix=".bin") as handle:
        handle.write(read_bytes_checked(db, revision))
        handle.flush()
        yield Path(handle.name)


def _ffmpeg(*args: str) -> bytes:
    try:
        result = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", *args], capture_output=True, timeout=FFMPEG_TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise HTTPException(422, {"code": "material_preview_unavailable"}) from None
    return result.stdout if result.returncode == 0 else b""


def _duration(path: Path) -> float:
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                                capture_output=True, text=True, timeout=FFMPEG_TIMEOUT, check=False)
        return max(float(result.stdout.strip()), 0.0)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return 0.0


def _frame(path: Path, at: float, width: int) -> bytes:
    scale = f"scale='min({width},iw)':-2"
    return (_ffmpeg("-ss", f"{at:.3f}", "-i", str(path), "-frames:v", "1", "-vf", scale, "-f", "image2", "-c:v", "mjpeg", "-q:v", "4", "pipe:1")
            or _ffmpeg("-i", str(path), "-frames:v", "1", "-vf", scale, "-f", "image2", "-c:v", "mjpeg", "-q:v", "4", "pipe:1"))


def _render(kind: str, variant: str, path: Path, duration_ms: int | None) -> tuple[bytes, str]:
    from PIL import Image, ImageOps

    duration = (duration_ms or 0) / 1000 or (_duration(path) if kind in {"video", "audio"} else 0)
    if kind == "image" and variant == "thumb":
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((THUMB_WIDTH, THUMB_WIDTH * 2))
            output = io.BytesIO()
            image.save(output, "JPEG", quality=82, optimize=True)
            return output.getvalue(), "image/jpeg"
    if kind == "video" and variant == "thumb":
        content = _frame(path, min(1.0, duration * 0.1), THUMB_WIDTH)
        if content:
            return content, "image/jpeg"
    if kind == "video" and variant == "strip":
        frames = []
        for index in range(STRIP_FRAMES):
            content = _frame(path, duration * (index + 0.5) / STRIP_FRAMES, STRIP_WIDTH)
            if content:
                with Image.open(io.BytesIO(content)) as image:
                    frames.append(image.convert("RGB"))
        if frames:
            sheet = Image.new("RGB", (frames[0].width * len(frames), frames[0].height))
            for index, image in enumerate(frames):
                sheet.paste(image.resize(frames[0].size), (index * frames[0].width, 0))
            output = io.BytesIO()
            sheet.save(output, "JPEG", quality=78, optimize=True)
            return output.getvalue(), "image/jpeg"
    if kind == "audio" and variant == "thumb":
        content = _ffmpeg("-i", str(path), "-filter_complex", "aformat=channel_layouts=mono,showwavespic=s=640x120:scale=sqrt:colors=0x9a3b2a",
                          "-frames:v", "1", "-f", "image2", "-c:v", "png", "pipe:1")
        if content:
            return content, "image/png"
    raise HTTPException(422, {"code": "material_preview_unavailable"})


def derivative(db, revision, variant: str) -> tuple[bytes, str]:
    kind = media_kind(revision)
    if kind is None or variant not in {"thumb", "strip"} or not re.fullmatch(r"[0-9a-f]{64}", revision.content_hash or ""):
        raise HTTPException(422, {"code": "material_preview_unavailable"})
    folder = MEDIA_ROOT / ".derivatives" / revision.content_hash[:2]
    cached = {suffix: folder / f"{revision.content_hash}-{variant}.{suffix}" for suffix in ("jpg", "png")}
    for suffix, path in cached.items():
        if path.is_file():
            return path.read_bytes(), "image/jpeg" if suffix == "jpg" else "image/png"
    with _guard:
        lock = _locks.setdefault(f"{revision.content_hash}:{variant}", threading.Lock())
    with lock:
        for suffix, path in cached.items():
            if path.is_file():
                return path.read_bytes(), "image/jpeg" if suffix == "jpg" else "image/png"
        with source_path(db, revision) as path:
            content, mime = _render(kind, variant, path, revision.duration_ms)
        folder.mkdir(parents=True, exist_ok=True)
        target = cached["jpg" if mime == "image/jpeg" else "png"]
        descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=folder)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        os.replace(temporary, target)
        return content, mime


def probe(path: Path) -> tuple[int | None, int | None, int | None]:
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                                 "-of", "json", str(path)], capture_output=True, text=True, timeout=FFMPEG_TIMEOUT, check=False)
        import json

        data = json.loads(result.stdout or "{}")
        stream = (data.get("streams") or [{}])[0]
        seconds = float((data.get("format") or {}).get("duration") or 0)
        return stream.get("width"), stream.get("height"), int(seconds * 1000) or None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None, None, None


def ranged(path: Path, header: str | None) -> tuple[int, int, int]:
    size = path.stat().st_size
    start, end = 0, size - 1
    if header:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", header)
        if not match or not any(match.groups()):
            raise HTTPException(416, headers={"Content-Range": f"bytes */{size}"})
        low, high = match.groups()
        if not low:
            start = max(0, size - int(high))
        else:
            start, end = int(low), min(int(high), end) if high else end
        if start > end or start >= size:
            raise HTTPException(416, headers={"Content-Range": f"bytes */{size}"})
    return size, start, end
