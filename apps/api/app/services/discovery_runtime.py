"""Existing owner search settings used by product research; no daily jobs."""

import hashlib
import json

from sqlalchemy import select

from ..models import SystemSetting

DEFAULTS = {"enabled": False, "public_processing_allowed": False, "search_provider": "minimax",
            "credential_source": "environment", "timezone": "Asia/Taipei", "daily_hour": 8,
            "daily_limit": 5, "bootstrap_searches": 8, "weekly_searches": 4, "daily_searches": 4,
            "source_validations": 40, "active_sources": 24, "model_requests": 12,
            "input_tokens": 120000, "output_tokens": 24000, "paused_persona_ids": []}



def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()



def settings(db, owner_id: int) -> dict:
    row = db.scalar(select(SystemSetting).where(SystemSetting.key == f"discovery.{owner_id}").execution_options(populate_existing=True))
    return {**DEFAULTS, **(row.value if row else {})}
