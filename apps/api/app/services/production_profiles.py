"""Exact saved work configuration used by prompts and handoff packages."""
from sqlalchemy import select

from ..models import ProductionProfileRevision


def profile_snapshot(db, unit_id):
    row = db.scalar(select(ProductionProfileRevision).where(ProductionProfileRevision.unit_id == unit_id)
        .order_by(ProductionProfileRevision.revision.desc()).limit(1))
    if not row:
        return None
    return {"id": row.id, "revision": row.revision, "settings_hash": row.settings_hash,
            "settings": {k: v for k, v in row.settings_json.items() if k != "feedback"}}


def capture_profile_projection(settings):
    # Post-production sound changes do not require shooting the same images again.
    fields = ("shared_references", "work_type", "creation_mode", "reference_notes",
              "visual_style", "continuity_notes", "target_duration_seconds")
    result = {key: settings.get(key) for key in fields}
    on_camera = settings.get("speech_mode") in {"lip_sync", "mixed"}
    result["on_camera_speech"] = on_camera
    if on_camera:
        result.update({key: settings.get(key) for key in ("speech_mode", "dialogue", "dialogue_language")})
    profile = settings.get("video_creative_profile") or {}
    result["video_creative_profile"] = {key: value for key, value in profile.items() if key != "production_stages"}
    stages = settings.get("production_stages")
    if stages is None:
        stages = profile.get("production_stages") or {}
    capture_stages = {"research", "script", "storyboard"}
    result["production_stages"] = {key: value for key, value in stages.items() if key in capture_stages}
    frozen = (settings.get("product_production_methods") or {}).get("video") or {}
    result["production_methods"] = [
        {key: value for key, value in stage.items() if key not in {"origin", "title"}}
        for stage in frozen.get("stages", []) if stage.get("stage") in capture_stages
    ]
    return result


def capture_profile_current(db, unit_id, confirmed_profile_id, current_profile=None):
    confirmed = db.get(ProductionProfileRevision, confirmed_profile_id) if confirmed_profile_id else None
    current = current_profile if current_profile is not None else profile_snapshot(db, unit_id)
    if confirmed is None or confirmed.unit_id != unit_id or current is None:
        return False
    return capture_profile_projection(confirmed.settings_json) == capture_profile_projection(current["settings"])
