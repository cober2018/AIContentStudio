"""Candidate manifest hash shared by Master / Variant candidates and delivery."""

import hashlib
import json


def candidate_hash(manifest: dict) -> str:
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
