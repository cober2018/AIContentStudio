"""Deterministic official article projection, created only before Candidate approval."""

import hashlib
import html
import json
import re
from urllib.parse import parse_qsl, urlsplit

from .channel_variant_documents import canonical_payload


def validate_short_draft_body(content: object) -> int:
    if not isinstance(content, str) or not content:
        raise ValueError("official_experiment_body_limit")
    try:
        size = len(content.encode("utf-8"))
    except UnicodeEncodeError:
        raise ValueError("official_experiment_body_limit") from None
    if size >= 2048:
        raise ValueError("official_experiment_body_limit")
    return size


def validate_short_draft_render_bound(render: dict) -> int:
    if (not isinstance(render, dict) or render.get("status") != "local_ready"
            or not isinstance(render.get("html_template"), str)
            or not isinstance(render.get("asset_slots"), list)):
        raise ValueError("official_experiment_body_limit")
    content = render["html_template"]
    for slot in render["asset_slots"]:
        if slot.get("usage") == "inline":
            placeholder = f'src="aics-resource:{slot["slot_key"]}"'
            if content.count(placeholder) != 1:
                raise ValueError("official_resource_mapping_invalid")
            # Existing URL validation permits 2048 characters; HTML escaping expands at most sixfold.
            content = content.replace(placeholder, 'src="' + "x" * (2048 * 6) + '"', 1)
    return validate_short_draft_body(content)


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate_upload_filename(value: object) -> str:
    if (not isinstance(value, str) or not value or value in {".", ".."}
            or any(ord(char) < 32 or ord(char) == 127 or char in '/\\"' for char in value)):
        raise ValueError("official_asset_filename_invalid")
    try:
        if len(value.encode("utf-8")) > 255:
            raise ValueError("official_asset_filename_invalid")
    except UnicodeEncodeError:
        raise ValueError("official_asset_filename_invalid") from None
    return value


def upload_asset_metadata(revision) -> dict:
    metadata = revision.metadata_json if isinstance(revision.metadata_json, dict) else {}
    return {"filename": metadata.get("filename"), "mime_type": revision.mime_type}


def build_material_article_render(db, content: dict, assets: list[dict], evidence_refs: list[dict]) -> dict:
    from ..models import MaterialRevision

    metadata = {}
    for ref in assets:
        revision = db.get(MaterialRevision, ref["material_revision_id"], populate_existing=True)
        metadata[ref["material_revision_id"]] = upload_asset_metadata(revision) if revision else {}
    return build_article_render(content, assets, evidence_refs, asset_metadata=metadata)


def build_article_render(content: dict, assets: list[dict], evidence_refs: list[dict], *, asset_metadata: dict | None = None) -> dict:
    canonical = canonical_payload("wechat.article.v1", content, asset_refs=assets, evidence_refs=evidence_refs)
    reasons = []
    if len(canonical["title"]) > 32:
        reasons.append("title_limit")
    slots = []
    covers = [ref for ref in assets if ref.get("role") == "cover" and ref.get("slot_key") == "cover" and ref.get("placement") == {"usage": "cover"}]
    if len(covers) != 1:
        reasons.append("cover_required")
    for ref in covers:
        slots.append({"slot_key": "cover", "usage": "cover", "material_revision_id": ref["material_revision_id"],
                      "content_hash": ref["content_hash_snapshot"]})
    parts = []
    tags = {"heading": "h2", "paragraph": "p", "quote": "blockquote", "list": "p"}
    for block in canonical["blocks"]:
        if block["kind"] == "image":
            ref = next(item for item in assets if item["slot_key"] == block["image_ref_key"])
            slots.append({"slot_key": ref["slot_key"], "usage": "inline", "block_id": block["id"],
                          "material_revision_id": ref["material_revision_id"], "content_hash": ref["content_hash_snapshot"]})
            alt = html.escape(block["alt_text"], quote=True)
            caption = html.escape(block["text"], quote=True).replace("\n", "<br>")
            parts.append(f'<figure data-block-id="{block["id"]}"><img src="aics-resource:{ref["slot_key"]}" alt="{alt}"><figcaption>{caption}</figcaption></figure>')
            continue
        tag = tags[block["kind"]]
        escaped = html.escape(block["text"], quote=True).replace("\n", "<br>")
        parts.append(f'<{tag} data-block-id="{block["id"]}">{escaped}</{tag}>')
    for declaration in canonical["declarations"]:
        escaped = html.escape(declaration["text"], quote=True).replace("\n", "<br>")
        parts.append(f'<p data-declaration-id="{declaration["id"]}">{escaped}</p>')
    if asset_metadata is not None:
        for slot in slots:
            metadata = asset_metadata.get(slot["material_revision_id"], {})
            try:
                filename = validate_upload_filename(metadata.get("filename"))
            except ValueError:
                filename = None
                if "asset_filename_required" not in reasons:
                    reasons.append("asset_filename_required")
            mime = metadata.get("mime_type")
            if mime not in {"image/png", "image/jpeg"}:
                mime = None
                if "asset_mime_unsupported" not in reasons:
                    reasons.append("asset_mime_unsupported")
            slot.update(filename=filename, mime_type=mime)
    result = {"schema": "wechat.official.article.v1", "renderer": "wechat.official.html", "renderer_version": "2" if asset_metadata is not None else "1",
              "status": "unavailable" if reasons else "local_ready", "reasons": reasons,
              "title": canonical["title"], "digest": "", "author": "", "html_template": "".join(parts),
              "asset_slots": slots, "content_hash": _hash(canonical), "structure_hash": _hash(canonical["blocks"]),
              "citations": canonical["citations"], "declarations": canonical["declarations"],
              "remote_contract": "unresolved_body_limits"}
    return {**result, "render_hash": _hash(result)}


def validate_article_render(render: dict, content: dict, assets: list[dict], evidence_refs: list[dict]) -> None:
    metadata = None
    if render.get("renderer_version") == "2":
        slots = render.get("asset_slots")
        if not isinstance(slots, list) or any(not isinstance(slot, dict) for slot in slots):
            raise ValueError("official_render_mismatch")
        metadata = {slot.get("material_revision_id"): {"filename": slot.get("filename"), "mime_type": slot.get("mime_type")}
                    for slot in slots}
    if render != build_article_render(content, assets, evidence_refs, asset_metadata=metadata):
        raise ValueError("official_render_mismatch")


def remote_image_url(value: object) -> str:
    if not isinstance(value, str) or len(value) > 2048 or any(ord(char) < 33 for char in value):
        raise ValueError("official_resource_mapping_invalid")
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in {"http", "https"} or parsed.hostname != "mmbiz.qpic.cn"
                or parsed.username or parsed.password or parsed.port is not None or parsed.fragment
                or not parsed.path.startswith("/") or "\\" in value
                or any(key != "wx_fmt" or item not in {"png", "jpeg", "jpg"} for key, item in parse_qsl(parsed.query, keep_blank_values=True))):
            raise ValueError
    except ValueError:
        raise ValueError("official_resource_mapping_invalid") from None
    return value


def prepare_article(manifest: dict, runtime, mapping: list[dict]) -> dict:
    if (not isinstance(manifest, dict) or manifest.get("schema_version") != 5
            or not isinstance(manifest.get("official_render"), dict)):
        raise ValueError("official_render_required")
    render = manifest["official_render"]
    validate_article_render(render, manifest["content"], manifest["assets"], manifest["evidence_refs"])
    if render["status"] != "local_ready" or not isinstance(mapping, list) or len(mapping) != len(render["asset_slots"]):
        raise ValueError("official_resource_mapping_invalid")
    content, cover = render["html_template"], None
    for slot, resolved in zip(render["asset_slots"], mapping, strict=True):
        if (not isinstance(resolved, dict) or set(resolved) != set(slot) | {"account_id", "appid", "runtime_fingerprint", "remote_ref"}
                or any(resolved.get(key) != value for key, value in slot.items())
                or resolved["account_id"] != runtime.account_id or resolved["appid"] != runtime.appid
                or resolved["runtime_fingerprint"] != runtime.fingerprint):
            raise ValueError("official_resource_mapping_invalid")
        value = resolved["remote_ref"]
        if slot["usage"] == "cover":
            if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value) or cover is not None:
                raise ValueError("official_resource_mapping_invalid")
            cover = value
        else:
            value = remote_image_url(value)
            placeholder = f'src="aics-resource:{slot["slot_key"]}"'
            if content.count(placeholder) != 1:
                raise ValueError("official_resource_mapping_invalid")
            content = content.replace(placeholder, f'src="{html.escape(value, quote=True)}"', 1)
    if cover is None:
        raise ValueError("official_resource_mapping_invalid")
    return {"title": render["title"], "author": render["author"], "digest": render["digest"],
            "content": content, "thumb_media_id": cover}


def match_readback(article: dict, returned: dict) -> str:
    if returned != article:
        raise ValueError("official_readback_mismatch")
    return _hash(article)
