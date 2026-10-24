"""Explicit Persona policy identity and immutable research diagnostics."""

from sqlalchemy import select

from ..models import ContentPersona, ContentPersonaRevision

TECH = "technology.v1"
LEGACY = "discovery.v2"
BLUEPRINT = "starter.ai-tech-engineer.v1"


def revision_policy(revision):
    data = revision.profile_json if revision else {}
    return TECH if any(
        ((data.get(field) or {}).get("provenance") or {}).get("blueprint_key") == BLUEPRINT
        for field in ("text_creative_profile", "graphic_creative_profile", "audio_creative_profile", "video_creative_profile")
    ) else LEGACY


def persona_policy(db, owner_id, persona_id):
    persona = db.get(ContentPersona, persona_id)
    if not persona or persona.owner_user_id != owner_id:
        return LEGACY
    revision = db.scalar(select(ContentPersonaRevision).where(
        ContentPersonaRevision.persona_id == persona_id).order_by(ContentPersonaRevision.revision_no.desc()).limit(1))
    return revision_policy(revision)


def tech_persona_ids(db, owner_id):
    return [p.id for p in db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == owner_id)).all()
            if persona_policy(db, owner_id, p.id) == TECH]


def freeze_policy(db, run):
    stored = (run.input_json or {}).get("opportunity_policy")
    if stored:
        return stored
    # Resuming old model checkpoints must not reinterpret their frozen prompts/results.
    started = any(key in (run.output_json or {}) for key in ("event_groups", "topic_candidates", "scores_a"))
    policy = LEGACY if started else revision_policy(db.get(ContentPersonaRevision, run.persona_revision_id))
    run.input_json = {**run.input_json, "opportunity_policy": policy}
    db.commit()
    return policy


def diagnostic(db, run, *, counts=None, rejections=None):
    current = (run.output_json or {}).get("diagnostics") or {}
    value = {"version": "opportunity.diagnostics.v1",
             "policy_version": (run.input_json or {}).get("opportunity_policy", LEGACY),
             "counts": {**current.get("counts", {}), **(counts or {})},
             "rejections": rejections if rejections is not None else current.get("rejections", [])}
    run.output_json = {**(run.output_json or {}), "diagnostics": value}
    db.commit()


def diagnostic_projection(run):
    value = (run.output_json or {}).get("diagnostics")
    if not isinstance(value, dict):
        return None
    keys = {"eligible_items", "body_reads_succeeded", "body_reads_failed", "budget_unexamined_items",
            "proposed_candidates", "pre_score_rejected", "scored_candidates", "score_rejected",
            "deduplicated_candidates", "source_cap_excluded", "daily_cap_excluded", "persisted_opportunities"}
    return {"version": value.get("version"), "policy_version": value.get("policy_version"),
            "counts": {k: v for k, v in value.get("counts", {}).items() if k in keys and type(v) is int and v >= 0},
            "rejections": [{k: row[k] for k in ("candidate_id", "title", "stage", "reason") if k in row}
                           for row in value.get("rejections", [])[:30] if isinstance(row, dict)]}
