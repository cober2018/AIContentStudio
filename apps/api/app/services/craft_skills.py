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
SKILLS = {"craft-ae", "craft-resolve"}
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


SWITCH_KEY = "unit_platform_skills"
# Skill families a third-party model may write with, per kind of work; editing / effects skills are always on.
_WRITING_FAMILIES = {"video": {"research", "text", "audio", "video"}, "audio": {"research", "text", "audio"},
                     "text": {"research", "text"}, "graphic": {"research", "text", "graphic"}}
_NOT_WRITING = {"studio.audio.tts"}  # runs a provider task, not guidance a model can follow


def writing_skills_on(db: Session, unit_id: int) -> bool:
    from ..models import SystemSetting

    row = db.get(SystemSetting, SWITCH_KEY)
    return str(unit_id) not in ((row.value or {}) if row else {})


def set_writing_skills(db: Session, user: User, project_id: int, unit_id: int, on: bool) -> dict:
    from sqlalchemy.orm.attributes import flag_modified

    from ..models import SystemSetting
    from .content_masters import owned_unit
    from .project_events import record_project_event

    owned_unit(db, project_id, unit_id, user, mutate=True)
    row = db.get(SystemSetting, SWITCH_KEY)
    if row is None:
        row = SystemSetting(key=SWITCH_KEY, value={})
        db.add(row)
    # Only closed works are recorded, so a work nobody touched stays on.
    value = dict(row.value or {})
    if on:
        value.pop(str(unit_id), None)
    else:
        value[str(unit_id)] = {"by": user.email}
    row.value, row.updated_by = value, user.email
    flag_modified(row, "value")
    record_project_event(db, project_id=project_id, event_type="unit.updated", actor=user.email, entity_type="content_unit",
                         entity_id=unit_id, payload={"platform_writing_skills": "on" if on else "off"})
    db.commit()
    return {"writing_skills": "on" if on else "off"}


def writing_skills(unit) -> list[dict]:
    from .studio_creative_catalog import SKILLS as STUDIO
    from .studio_creative_catalog import skill_system

    families = _WRITING_FAMILIES.get(unit.modality, {"research", "text"})
    system = "product" if unit.production_domain == "product" else "persona"
    latest: dict[str, dict] = {}
    for item in STUDIO.values():
        if (item["kind"] == "skill" and item["modality"] in families and item["key"] not in _NOT_WRITING
                and skill_system(item["key"]) in {system, "shared"}
                and (item["key"] not in latest or int(item["version"]) > int(latest[item["key"]]["version"]))):
            latest[item["key"]] = item
    return [{"skill": item["ref"], "purpose": item["purpose"]} for item in latest.values()]


def platform_skills(db: Session, unit) -> dict:
    """What the brief tells a third-party model it may read."""
    on = writing_skills_on(db, unit.id)
    readable = [{"skill": "craft-resolve", "purpose": "DaVinci Resolve 剪辑与收尾，含选用表 choose.md"},
                {"skill": "craft-ae", "purpose": "After Effects 包装、组件与模板说明"}] if unit.modality == "video" else []
    if on:
        readable += writing_skills(unit)
    return {"writing_skills": "on" if on else "off", "always_on": ["craft-resolve", "craft-ae"],
            "readable": [{**item, "read": f"get_craft_skill(skill=\"{item['skill']}\")"} for item in readable],
            "rule": "只用 readable 里列出的平台 skill；writing_skills 为 off 时写文案、脚本不用平台 skill，靠自己写。剪辑、特效 skill 一直可用。"}


def read_skill(db: Session, user: User, project_id: int, unit_id: int, skill: str, entry: str | None) -> dict:
    from .content_masters import owned_unit

    _project, unit = owned_unit(db, project_id, unit_id, user)
    if skill in SKILLS:
        if entry is None:
            return {"skill": skill, "index": skill_index(skill)}
        return {"skill": skill, "entry": entry, "text": skill_entry(skill, entry)}
    if not writing_skills_on(db, unit_id):
        _fail("platform_skills_disabled", 403, message="这条作品的平台写作 skill 已被关闭，请自己写")
    if skill not in {item["skill"] for item in writing_skills(unit)} or entry is not None:
        _fail("craft_skill_not_found", 404)
    from .studio_creative_catalog import load_skill

    try:
        package = load_skill(skill)
    except ValueError:
        _fail("craft_skill_unavailable", 409)
    return {"skill": skill, "text": package["instruction"],
            "references": [{"name": ref["name"], "content": ref["content"]} for ref in package.get("references", [])]}


def _store() -> Path:
    return Path(get_settings().ae_template_store).expanduser()


def _manifests() -> list[dict]:
    items = []
    for path in sorted((ROOT / "craft-ae" / "templates").glob("*/*/manifest.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        project = _store() / manifest["id"] / manifest["version"] / manifest["project"]["file"]
        # Two checked renders with different content are what makes a template safe to pick automatically.
        manifest["status"] = "ready" if len(manifest.get("checks") or []) >= 2 else "draft"
        manifest["installed"] = project.is_file()
        folder = project.parent
        # Previews let people and models see the motion before choosing; only files that exist are offered.
        manifest["preview_files"] = {aspect: str(folder / name) for aspect, name in (manifest.get("previews") or {}).items()
                                     if (folder / name).is_file()}
        items.append(manifest)
    return items


def list_templates() -> dict:
    return {"store": str(_store()), "templates": _manifests()}


def _manifest(template_id: str, version: str) -> dict:
    found = next((item for item in _manifests() if item["id"] == template_id and item["version"] == version), None)
    if found is None:
        _fail("ae_template_not_found", 404)
    return found


def _variant(manifest: dict, aspect: str) -> tuple[dict, list[int]]:
    """The 9:16 project is the manifest's own; other aspects live in variants and are never stretched from it."""
    if aspect == "9:16":
        return manifest["project"], manifest["size"]
    variant = (manifest.get("variants") or {}).get(aspect)
    if variant is None:
        _fail("ae_template_aspect_unavailable", 409, aspect=aspect)
    return variant["project"], variant["size"]


def preview_file(template_id: str, version: str, aspect: str) -> Path:
    manifest = _manifest(template_id, version)
    path = manifest["preview_files"].get(aspect)
    if path is None:
        _fail("ae_template_preview_missing", 404)
    return Path(path)


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
           content: dict, images: dict | None = None, duration_ms: int | None = None, aspect: str = "9:16") -> dict:
    from .content_masters import owned_unit
    from .materials import create_material, create_revision
    from .project_events import record_project_event

    owned_unit(db, project_id, unit_id, user, mutate=True)
    manifest = _manifest(template_id, version)
    project_info, size = _variant(manifest, aspect)
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
    # Exit animations are timed from the end, and the render length is chosen per call.
    data["_duration_ms"] = duration
    folder = _store() / template_id / version
    project = folder / project_info["file"]
    if not project.is_file() or hashlib.sha256(project.read_bytes()).hexdigest() != project_info["sha256"]:
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
        # The safe-area guide layer never renders, but aerender still expects its footage beside the project.
        for extra in folder.glob("guide-*.png"):
            shutil.copyfile(extra, job / extra.name)
        literal = html.escape(json.dumps(data, ensure_ascii=False), quote=False)
        xml = project.read_text(encoding="utf-8").replace(str(folder), str(job))
        xml = _DATA.sub(lambda _: "/*AICS_DATA*/" + literal + "/*AICS_END*/", xml)
        (job / "job.aepx").write_text(xml, encoding="utf-8")
        # Overlay templates carry their own render-queue item with an alpha output module, since aerender
        # only accepts output template names in After Effects' interface language.
        alpha = manifest.get("alpha") is True
        output = job / ("out.mov" if alpha else "out.mp4")
        frames = round(duration * manifest["fps"] / 1000)
        target = ["-rqindex", "1"] if alpha else ["-comp", manifest["comp"]]
        done = subprocess.run([str(aerender), "-project", str(job / "job.aepx"), *target, "-s", "0",
                               "-e", str(frames - 1), "-output", str(output)], capture_output=True, timeout=600)
        if done.returncode != 0 or not output.is_file():
            _fail("ae_render_failed", 502)
        body = output.read_bytes()
        content_hash = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        material = create_material(db, kind="video", title=f"{manifest['name']} · {str(data.get(manifest['fields'][0]['name']))[:40]}", created_by=user.email)
        revision = create_revision(
            db, material, content=body, suffix=output.suffix, declared_mime="video/quicktime" if alpha else "video/mp4", source_kind="chart",
            source_metadata={"ae_template": template_id, "version": version, "aspect": aspect, "project_sha256": project_info["sha256"],
                             "content_hash": content_hash, "image_revision_ids": [item.id for item in inputs]},
            rights_status="cleared", public_use_allowed=all(item.public_use_allowed for item in inputs),
            model_use_allowed=all(item.model_use_allowed for item in inputs), commercial_use_allowed=all(item.commercial_use_allowed is not False for item in inputs),
            width=size[0], height=size[1], duration_ms=duration, created_by=user.email)
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
