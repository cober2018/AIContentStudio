"""Discoverability profiles: the per-channel SEO check items that Master checks read."""

from __future__ import annotations

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DiscoverabilityProfileVersion

PRE_FIELDS = ["search_intent", "primary_queries", "secondary_queries", "entities", "questions", "content_gaps", "outline_suggestions"]
POST_FIELDS = ["title_suggestions", "keyword_coverage", "description", "tags", "alt_suggestions", "issues"]


def seed_default_profiles(db: Session) -> int:
    """基础 discoverability profiles（幂等）。"""
    created = 0
    defaults = [
        ("seo.default", None, None, {"pre_fields": PRE_FIELDS, "post_fields": POST_FIELDS}),
        ("seo.wechat.article", "wechat", "article", {"title_length": [8, 64], "description_length": [40, 120], "pre_fields": PRE_FIELDS, "post_fields": POST_FIELDS}),
    ]
    for key, channel, form, config in defaults:
        exists = db.scalar(select(DiscoverabilityProfileVersion.id).where(DiscoverabilityProfileVersion.profile_key == key).limit(1))
        if exists:
            continue
        db.add(
            DiscoverabilityProfileVersion(
                profile_key=key, version=1, channel=channel or "", content_form=form,
                config_json=config, status="published",
                checksum=hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
            )
        )
        created += 1
    db.flush()
    return created
