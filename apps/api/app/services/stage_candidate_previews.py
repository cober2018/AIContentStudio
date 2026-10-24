"""Preview-only PNGs of graphic stage candidates, so the user decides on real images before acceptance."""

from __future__ import annotations

import copy
import io
import threading

from fastapi import HTTPException
from PIL import Image

from ..models import MaterialRevision
from . import materials, provider_calls
from .content_harness import providers
from .asset_media import MEDIA_ROOT
from .stage_contracts import digest

RENDERER = ("graphic.chromium", "1")
_locks: dict[str, threading.Lock] = {}
_guard = threading.Lock()


def _candidate(db, user, project_id, unit_id, node_id, run_id, attempt_id, candidate_id):
    from .creation_recipes import stage_result

    result = stage_result(db, project_id, unit_id, node_id, user, run_id=run_id, attempt_id=attempt_id)
    candidate = next((item for item in (result.get("output") or {}).get("candidates") or []
                      if item.get("candidate_id") == candidate_id), None)
    if candidate is None or candidate.get("payload_schema") != "graphic.master.v2":
        raise HTTPException(404, {"code": "graphic_preview_candidate_not_found"})
    return candidate


def _render(db, candidate, canvas_id, render_hash):
    from .media_renderers import resolve_renderer

    try:
        renderer, _ = resolve_renderer(*RENDERER)
    except HTTPException:
        raise HTTPException(422, {"code": "graphic_preview_unavailable"}) from None
    sources, seen, total = [], set(), 0
    for ref in candidate.get("asset_refs", []):
        if ref["material_revision_id"] in seen:
            continue
        seen.add(ref["material_revision_id"])
        revision = db.get(MaterialRevision, ref["material_revision_id"])
        if revision is None or revision.content_hash != ref.get("content_hash", revision.content_hash):
            raise HTTPException(409, {"code": "graphic_preview_source_unavailable"})
        content = materials.read_bytes_checked(db, revision)
        total += len(content)
        if total > 30 * 1024 * 1024:
            raise HTTPException(413, {"code": "graphic_preview_input_too_large"})
        sources.append({"revision_id": revision.id, "content_hash": revision.content_hash, "mime_type": revision.mime_type, "content": content})
    request = {"payload": copy.deepcopy(candidate["payload"]), "payload_schema": "graphic.master.v2", "render_input_hash": render_hash,
               "canvas_id": canvas_id, "source_assets": sources, "timeout_seconds": 30, "max_output_bytes": 30 * 1024 * 1024}
    try:
        output = provider_calls.call(renderer.render_master, request)
    except Exception:  # noqa: BLE001 Renderer diagnostics may contain local paths.
        raise HTTPException(502, {"code": "graphic_preview_failed"}) from None
    if not isinstance(output, providers.MediaRenderOutput) or output.status != "succeeded" or output.mime_type != "image/png":
        raise HTTPException(502, {"code": "graphic_preview_failed"})
    return output.content


def png(db, user, project_id, unit_id, node_id, *, run_id, attempt_id, candidate_id, canvas_id, width=None) -> bytes:
    """Cached by payload and canvas; nothing is attested, saved as material or bound to a Master."""
    candidate = _candidate(db, user, project_id, unit_id, node_id, run_id, attempt_id, candidate_id)
    canvas = next((item for item in candidate["payload"].get("canvases", []) if item.get("id") == canvas_id), None)
    if canvas is None:
        raise HTTPException(404, {"code": "graphic_preview_canvas_not_found"})
    render_hash = digest({"payload_hash": candidate.get("payload_hash") or digest(candidate["payload"]), "canvas_id": canvas_id, "renderer": list(RENDERER)})
    folder = MEDIA_ROOT / ".derivatives" / "stage-candidates" / render_hash[:2]
    full = folder / f"{render_hash}.png"
    db.rollback()
    with _guard:
        lock = _locks.setdefault(render_hash, threading.Lock())
    with lock:
        if not full.exists():
            content = _render(db, candidate, canvas_id, render_hash)
            folder.mkdir(parents=True, exist_ok=True)
            temporary = full.with_suffix(".tmp")
            temporary.write_bytes(content)
            temporary.replace(full)
    if not width:
        return full.read_bytes()
    small = folder / f"{render_hash}-w{width}.png"
    if not small.exists():
        with Image.open(full) as image:
            image.thumbnail((width, width * 4))
            buffer = io.BytesIO()
            image.save(buffer, "PNG", optimize=True)
        small.write_bytes(buffer.getvalue())
    return small.read_bytes()
