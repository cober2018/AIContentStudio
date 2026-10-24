"""Craft skills (After Effects, DaVinci Resolve) and the AE template library, served through the creative MCP.

The files live once under apps/api/craft_skills. Templates are XML AE projects in a local store outside git;
their manifests here name each project's file and SHA256. Rendering never scripts the running After Effects:
it rewrites the embedded data literal in a copy of the project and calls aerender.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import html
import json
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import AuditLog, MaterialRevision, ProjectMaterialReference, User

ROOT = Path(__file__).resolve().parents[2] / "craft_skills"
SKILLS = {"ae-motion", "resolve-edit"}
_DATA = re.compile(r"/\*AICS_DATA\*/.*?/\*AICS_END\*/", re.S)
_ENTRY = re.compile(r"^[a-z0-9][a-z0-9_-]{0,60}(/[a-z0-9][a-z0-9_.-]{0,80})*\.(md|json)$")


def _fail(code: str, status: int = 422, **detail):
    raise HTTPException(status, {"code": code, **detail})


def skill_index(skill: str) -> str:
    if skill not in SKILLS:
        _fail("craft_skill_not_found", 404)
    return (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")


def skill_entry(skill: str, entry: str) -> str:
    if skill not in SKILLS or not _ENTRY.fullmatch(entry or ""):
        _fail("craft_entry_not_found", 404)
    path = (ROOT / skill / entry).resolve()
    if not path.is_relative_to((ROOT / skill).resolve()) or not path.is_file():
        _fail("craft_entry_not_found", 404)
    return path.read_text(encoding="utf-8")


def _store() -> Path:
    return Path(get_settings().ae_template_store).expanduser()


def _manifests() -> list[dict]:
    items = []
    for path in sorted((ROOT / "ae-motion" / "templates").glob("*/*/manifest.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        project = _store() / manifest["id"] / manifest["version"] / manifest["project"]["file"]
        # Two checked renders with different content are what makes a template safe to pick automatically.
        manifest["status"] = "ready" if len(manifest.get("checks") or []) >= 2 else "draft"
        manifest["installed"] = project.is_file()
        items.append(manifest)
    return items


def list_templates() -> dict:
    return {"store": str(_store()), "templates": _manifests()}


def _manifest(template_id: str, version: str) -> dict:
    found = next((item for item in _manifests() if item["id"] == template_id and item["version"] == version), None)
    if found is None:
        _fail("ae_template_not_found", 404)
    return found


def _content(manifest: dict, content: dict) -> dict:
    if not isinstance(content, dict) or set(content) - {field["name"] for field in manifest["fields"]}:
        _fail("ae_template_content_invalid")
    result = {}
    for field in manifest["fields"]:
        value = content.get(field["name"])
        if value in (None, ""):
            if field.get("required"):
                _fail("ae_template_field_required", field=field["name"])
            result[field["name"]] = "" if field["kind"] == "text" else 0
            continue
        if field["kind"] == "text" and (not isinstance(value, str) or len(value) > field["max"]):
            _fail("ae_template_field_invalid", field=field["name"])
        if field["kind"] == "number" and (type(value) not in (int, float) or not field["min"] <= value <= field["max"]):
            _fail("ae_template_field_invalid", field=field["name"])
        result[field["name"]] = value
    return result


def _font_installed(name: str) -> bool:
    # CoreText falls back to another face for a missing font, so compare the PostScript name it actually used.
    ct = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreText"))
    cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreFoundation"))
    cf.CFStringCreateWithCString.restype = ctypes.c_void_p
    cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
    cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
    cf.CFRelease.argtypes = [ctypes.c_void_p]
    ct.CTFontCreateWithName.restype = ctypes.c_void_p
    ct.CTFontCreateWithName.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_void_p]
    ct.CTFontCopyPostScriptName.restype = ctypes.c_void_p
    ct.CTFontCopyPostScriptName.argtypes = [ctypes.c_void_p]
    wanted = cf.CFStringCreateWithCString(None, name.encode(), 0x08000100)
    font = ct.CTFontCreateWithName(wanted, 12.0, None)
    actual = ct.CTFontCopyPostScriptName(font)
    buffer = ctypes.create_string_buffer(256)
    cf.CFStringGetCString(actual, buffer, 256, 0x08000100)
    for ref in (actual, font, wanted):
        cf.CFRelease(ref)
    return buffer.value.decode() == name


def _image_bytes(db: Session, project_id: int, revision_id: int) -> tuple[bytes, MaterialRevision]:
    from .material_storage import provider

    revision = db.get(MaterialRevision, revision_id)
    attached = db.query(ProjectMaterialReference).filter_by(project_id=project_id, material_revision_id=revision_id, status="active").first()
    if revision is None or attached is None or not (revision.mime_type or "").startswith("image/"):
        _fail("ae_template_image_invalid")
    return provider().read(revision.file_path), revision


def render(db: Session, user: User, *, project_id: int, unit_id: int, template_id: str, version: str,
           content: dict, images: dict | None = None, duration_ms: int | None = None) -> dict:
    from .content_masters import owned_unit
    from .materials import create_material, create_revision
    from .project_events import record_project_event

    owned_unit(db, project_id, unit_id, user, mutate=True)
    manifest = _manifest(template_id, version)
    data = _content(manifest, content)
    bounds = manifest["duration_ms"]
    duration = bounds["default"] if duration_ms is None else duration_ms
    if type(duration) is not int or not bounds["min"] <= duration <= bounds["max"]:
        _fail("ae_template_duration_invalid")
    images = images or {}
    slots = {item["name"]: item for item in manifest.get("images", [])}
    if set(images) - set(slots) or any(type(value) is not int for value in images.values()):
        _fail("ae_template_image_invalid")
    if any(slot.get("required") and name not in images for name, slot in slots.items()):
        _fail("ae_template_image_required")
    # Templates show an image panel only for the slots actually supplied.
    data["_images"] = sorted(images)
    folder = _store() / template_id / version
    project = folder / manifest["project"]["file"]
    if not project.is_file() or hashlib.sha256(project.read_bytes()).hexdigest() != manifest["project"]["sha256"]:
        _fail("ae_template_project_changed", 409)
    missing = [name for name in manifest["fonts"] if not _font_installed(name)]
    if missing:
        _fail("ae_template_font_missing", 409, fonts=missing)
    aerender = Path(get_settings().aerender_path)
    if not aerender.is_file():
        _fail("ae_render_unavailable", 409)

    job = _store().parent / "ae-jobs" / uuid.uuid4().hex
    job.mkdir(parents=True)
    try:
        inputs = []
        for name, slot in slots.items():
            target = job / slot["file"]
            if name in images:
                raw, revision = _image_bytes(db, project_id, images[name])
                (job / "source").write_bytes(raw)
                # AE reads footage by extension, so every supplied image becomes the PNG the template expects.
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(job / "source"), str(target)], check=True, timeout=60)
                inputs.append(revision)
            else:
                shutil.copyfile(folder / slot["file"], target)
        literal = html.escape(json.dumps(data, ensure_ascii=False), quote=False)
        xml = project.read_text(encoding="utf-8").replace(str(folder), str(job))
        xml = _DATA.sub(lambda _: "/*AICS_DATA*/" + literal + "/*AICS_END*/", xml)
        (job / "job.aepx").write_text(xml, encoding="utf-8")
        output = job / "out.mp4"
        frames = round(duration * manifest["fps"] / 1000)
        done = subprocess.run([str(aerender), "-project", str(job / "job.aepx"), "-comp", manifest["comp"], "-s", "0",
                               "-e", str(frames - 1), "-output", str(output)], capture_output=True, timeout=600)
        if done.returncode != 0 or not output.is_file():
            _fail("ae_render_failed", 502)
        body = output.read_bytes()
        content_hash = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        material = create_material(db, kind="video", title=f"{manifest['name']} · {str(data.get(manifest['fields'][0]['name']))[:40]}", created_by=user.email)
        revision = create_revision(
            db, material, content=body, suffix=".mp4", declared_mime="video/mp4", source_kind="chart",
            source_metadata={"ae_template": template_id, "version": version, "project_sha256": manifest["project"]["sha256"],
                             "content_hash": content_hash, "image_revision_ids": [item.id for item in inputs]},
            rights_status="cleared", public_use_allowed=all(item.public_use_allowed for item in inputs),
            model_use_allowed=all(item.model_use_allowed for item in inputs), commercial_use_allowed=all(item.commercial_use_allowed is not False for item in inputs),
            width=manifest["size"][0], height=manifest["size"][1], duration_ms=duration, created_by=user.email)
        reference = ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id, origin="ae_template", status="active",
                                             attached_by=user.email, note=f"AE 模板 {template_id} {version}；候选，未绑定镜头")
        db.add(reference)
        db.flush()
        db.add(AuditLog(event="material.ae_template_rendered", actor=user.email, entity_type="material", entity_id=str(material.id),
                        detail_json={"template": template_id, "version": version, "content_hash": content_hash, "hash": revision.content_hash}))
        record_project_event(db, project_id=project_id, event_type="asset.attached", actor=user.email, entity_type="material_revision",
                             entity_id=revision.id, payload={"reference_id": reference.id, "origin": "ae_template", "content_hash": revision.content_hash})
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        shutil.rmtree(job, ignore_errors=True)
    return {"material_id": material.id, "material_revision_id": revision.id, "content_hash": revision.content_hash,
            "template": template_id, "version": version, "duration_ms": duration, "data_hash": content_hash}
