"""OpenAI-compatible Videos API (POST /videos, GET /videos/{id}, GET /videos/{id}/content), for any vendor that offers it.

Vendors relay the same models (e.g. MiniMax H3) behind this one shape, so a video model is configured, not coded per vendor.
Frames go up as files (image_1, image_2): relays refuse inline images and otherwise want a public URL.
"""

from __future__ import annotations

import httpx

DONE = {"completed", "succeeded", "success", "finished"}
FAILED = {"failed", "failure", "cancelled", "canceled", "error", "expired"}
# Output sizes from the relay's size table (uuapi.io/docs/video), keyed by clarity and frame shape.
SIZES = {"16:9": ("864x480", "1376x768", "1920x1088"), "4:3": ("736x576", "1184x896", "1664x1248"),
         "3:2": ("800x544", "1248x832", "1760x1184"), "21:9": ("992x416", "1568x672", "2208x960"),
         "1:1": ("640x640", "1024x1024", "1440x1440"), "3:4": ("576x736", "896x1184", "1248x1664"),
         "2:3": ("544x800", "832x1248", "1184x1760"), "9:16": ("480x864", "768x1376", "1088x1920")}
CLARITY = ("480p", "768p", "1080p")


def size(resolution: str, aspect_ratio: str) -> str:
    return SIZES.get(aspect_ratio, SIZES["9:16"])[CLARITY.index(resolution)]


def _headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}"}


def submit(base_url: str, api_key: str, model: str, prompt: str, *, seconds: int, aspect_ratio: str, first_frame: bytes | None,
           last_frame: bytes | None = None, resolution: str = "480p") -> dict:
    """Returns {"job_id"} or {"error": reason}; a refused request is never resent automatically."""
    ratio = aspect_ratio if aspect_ratio in SIZES else "9:16"
    data = {"model": model, "prompt": prompt, "seconds": str(seconds), "size": size(resolution, ratio), "aspect_ratio": ratio}
    # Files go up as image_1 / image_2; with both, the fl2v workflow pins them as first and last frame.
    files = []
    if first_frame:
        files.append(("image_1", ("first-frame.png", first_frame, "image/png")))
        if last_frame:
            files.append(("image_2", ("last-frame.png", last_frame, "image/png")))
            data["workflow_id"] = "fl2v"
    try:
        response = httpx.post(base_url.rstrip("/") + "/videos", headers=_headers(api_key), data=data, files=files or None, timeout=60)
        body = response.json()
    except (httpx.HTTPError, ValueError):
        return {"error": "视频接口没有回应"}
    job = body.get("id") or body.get("task_id") if isinstance(body, dict) else None
    if response.status_code == 200 and isinstance(job, str) and job:
        return {"job_id": job}
    error = body.get("error") if isinstance(body, dict) else None
    message = error.get("message") if isinstance(error, dict) else body.get("message") if isinstance(body, dict) else None
    return {"error": str(message or f"视频接口拒绝（{response.status_code}）")[:300]}


def query(base_url: str, api_key: str, job_id: str) -> dict:
    """{"state": "running" | "failed" | "succeeded", "content"?: bytes, "reason"?: str}."""
    root = base_url.rstrip("/") + f"/videos/{job_id}"
    try:
        body = httpx.get(root, headers=_headers(api_key), timeout=30).json()
    except (httpx.HTTPError, ValueError):
        return {"state": "running"}
    status = str(body.get("status") or "").lower() if isinstance(body, dict) else ""
    if status in FAILED:
        error = body.get("error")
        return {"state": "failed", "reason": str((error.get("message") if isinstance(error, dict) else error) or status)[:300]}
    if status not in DONE:
        return {"state": "running"}
    try:
        content = httpx.get(root + "/content", headers=_headers(api_key), timeout=180, follow_redirects=True)
    except httpx.HTTPError:
        return {"state": "running"}
    # Some relays label the file application/octet-stream; an MP4 carries "ftyp" right after its first box size.
    if content.status_code != 200 or content.content[4:8] != b"ftyp":
        return {"state": "running"}
    return {"state": "succeeded", "content": content.content}
