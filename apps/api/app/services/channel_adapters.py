"""Exact published-form capability boundary for F6E ChannelAdapters."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from ..models import ChannelTemplateVersion
from .channel_form_descriptors import MODERN_ARTICLE_SCHEMAS, form_descriptor_for
from .content_harness.channel_registry import ChannelRegistryError, resolve_content_form


class AdapterUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class AdapterContract:
    key: str
    version: str
    accepted_master_schemas: frozenset[str]
    channel: str
    content_form: str
    artifact_kind: str
    payload_schema: str


class ChannelAdapter(Protocol):
    contract: AdapterContract

    def capabilities(self) -> dict: ...

    def canonicalize(self, payload: object, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict: ...

    def validate(self, payload: dict, asset_refs: list[dict], evidence_refs: list[dict]) -> None: ...

    def adapt(self, source_payload: dict, *, asset_refs: list[dict], evidence_refs: list[dict]) -> dict: ...

    def preview(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict: ...

    def render(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict: ...

    def required_checks(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> tuple[str, ...]: ...

    def package_projection(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict: ...


FIRST_BATCH: dict[tuple[str, str], AdapterContract] = {
    ("wechat", "article"): AdapterContract("wechat.article", "1", frozenset({"text.master.v2"}), "wechat", "article", "text", "wechat.article.v1"),
    ("x", "thread"): AdapterContract("x.thread", "1", frozenset({"text.master.v2"}), "x", "thread", "text", "x.thread.v1"),
    ("x", "single"): AdapterContract("x.single", "1", frozenset({"text.master.v2"}), "x", "single", "text", "x.single.v1"),
    ("xiaohongshu", "image_note"): AdapterContract("xiaohongshu.image_note", "1", frozenset({"graphic.master.v2"}), "xiaohongshu", "image_note", "image", "xiaohongshu.image_note.v1"),
    ("douyin", "spoken_script"): AdapterContract("douyin.spoken_script", "1", frozenset({"video.master.v2"}), "douyin", "spoken_script", "script", "douyin.spoken_script.v1"),
    ("toutiao", "article"): AdapterContract("toutiao.article", "1", frozenset({"text.master.v2"}), "toutiao", "article", "text", "toutiao.article.v1"),
    ("baijia", "article"): AdapterContract("baijia.article", "1", frozenset({"text.master.v2"}), "baijia", "article", "text", "baijia.article.v1"),
    ("zhihu", "article"): AdapterContract("zhihu.article", "1", frozenset({"text.master.v2"}), "zhihu", "article", "text", "zhihu.article.v1"),
    ("zhihu", "answer"): AdapterContract("zhihu.answer", "1", frozenset({"text.master.v2"}), "zhihu", "answer", "text", "zhihu.answer.v1"),
    ("bilibili", "article"): AdapterContract("bilibili.article", "1", frozenset({"text.master.v2"}), "bilibili", "article", "text", "bilibili.article.v1"),
    ("sohu", "article"): AdapterContract("sohu.article", "1", frozenset({"text.master.v2"}), "sohu", "article", "text", "sohu.article.v1"),
    ("penguin", "article"): AdapterContract("penguin.article", "1", frozenset({"text.master.v2"}), "penguin", "article", "text", "penguin.article.v1"),
    ("netease", "article"): AdapterContract("netease.article", "1", frozenset({"text.master.v2"}), "netease", "article", "text", "netease.article.v1"),
    ("weibo", "single"): AdapterContract("weibo.single", "1", frozenset({"text.master.v2"}), "weibo", "single", "text", "weibo.single.v1"),
    ("xueqiu", "quant_research"): AdapterContract("xueqiu.quant_research", "1", frozenset({"text.master.v2"}), "xueqiu", "quant_research", "text", "xueqiu.quant_research.v1"),
    ("xueqiu", "market_recap"): AdapterContract("xueqiu.market_recap", "1", frozenset({"text.master.v2"}), "xueqiu", "market_recap", "text", "xueqiu.market_recap.v1"),
    ("juejin", "tech_article"): AdapterContract("juejin.tech_article", "1", frozenset({"text.master.v2"}), "juejin", "tech_article", "text", "juejin.tech_article.v1"),
    ("bilibili", "image_note"): AdapterContract("bilibili.image_note", "1", frozenset({"graphic.master.v2"}), "bilibili", "image_note", "image", "bilibili.image_note.v1"),
    ("x", "long_post"): AdapterContract("x.long_post", "1", frozenset({"text.master.v2"}), "x", "long_post", "text", "x.long_post.v1"),
    ("x", "articles"): AdapterContract("x.articles", "1", frozenset({"text.master.v2"}), "x", "articles", "text", "x.articles.v1"),
}


# Registration means the executable implementation passed its own acceptance gates.
_EXECUTABLE_ADAPTERS: dict[tuple[str, str], ChannelAdapter] = {}


def _adapt_modern_text(schema: str, source_payload: dict, asset_refs: list[dict], evidence_refs: list[dict]) -> dict:
    from .channel_variant_documents import VariantDocumentError, canonical_payload
    from .text_documents import TextDocumentError
    from .text_documents import canonical_payload as canonical_text_payload

    if not isinstance(source_payload, dict):
        raise AdapterUnavailable("invalid_source_document")
    question = source_payload.get("_target_question")
    if schema == "zhihu.answer.v1" and (not isinstance(question, dict) or question.get("confirmed") is not True):
        raise AdapterUnavailable("question_confirmation_required")
    try:
        source = canonical_text_payload({key: value for key, value in source_payload.items() if key != "_target_question"})
    except TextDocumentError as exc:
        raise AdapterUnavailable("invalid_source_document") from exc
    article = schema in MODERN_ARTICLE_SCHEMAS
    refs = {ref.get("slot_key"): ref for ref in asset_refs if isinstance(ref, dict)}
    if len(refs) != len(asset_refs):
        raise AdapterUnavailable("source_refs_require_explicit_mapping")
    blocks, images, offsets, parts, used = [], [], {}, [], {ref["slot_key"] for ref in asset_refs if ref.get("role") == "cover" and article}
    if schema == "weibo.single.v1" and "cover" in refs:
        cover = refs["cover"]
        if cover.get("role") != "post_image":
            raise AdapterUnavailable("source_refs_require_explicit_mapping")
        images.append({"id": "cover", "order": 0, "image_ref_key": "cover"})
        used.add("cover")
    for source_block in source["document"]["blocks"]:
        kind = source_block["type"]
        block = {"id": source_block["id"], "order": len(blocks), "kind": kind}
        if kind in {"paragraph", "heading", "quote", "callout"}:
            if any(run["marks"] for run in source_block["content"]):
                raise AdapterUnavailable("source_structure_requires_explicit_mapping")
            block["text"] = "".join(run["text"] for run in source_block["content"])
            if kind == "quote" and source_block.get("attribution"):
                block["text"] += "\n" + source_block["attribution"]
            for key in ("level", "tone"):
                if key in source_block:
                    block[key] = source_block[key]
        elif kind in {"bullet_list", "ordered_list"} and article:
            if any(run["marks"] for child in source_block["items"] for run in child["content"]):
                raise AdapterUnavailable("source_structure_requires_explicit_mapping")
            block.update(kind="list", ordered=kind == "ordered_list", items=[
                {"id": child["id"], "order": index, "text": "".join(run["text"] for run in child["content"])}
                for index, child in enumerate(source_block["items"])])
        elif kind == "code" and article:
            block.update(text=source_block["code"], language=source_block["language"])
        elif kind == "divider" and article:
            pass
        elif kind in {"image", "chart"} and (article or schema == "weibo.single.v1"):
            ref = refs.get(source_block["id"])
            expected_role = "inline_image" if article else "post_image"
            if not ref or ref.get("role") != expected_role or ref.get("material_revision_id") != source_block["material_revision_id"]:
                raise AdapterUnavailable("source_refs_require_explicit_mapping")
            used.add(source_block["id"])
            if article:
                block.update(kind="image", image_ref_key=source_block["id"], text=source_block.get("caption", ""),
                             alt_text=source_block.get("alt_text", ""))
            else:
                images.append({"id": source_block["id"], "order": len(images), "image_ref_key": source_block["id"]})
                continue
        else:
            raise AdapterUnavailable("source_structure_requires_explicit_mapping")
        if not article:
            if kind != "paragraph":
                raise AdapterUnavailable("source_structure_requires_explicit_mapping")
            offsets[block["id"]] = sum(len(part) + 2 for part in parts)
            parts.append(block["text"])
        blocks.append(block)
    if set(refs) != used:
        raise AdapterUnavailable("source_refs_require_explicit_mapping")
    if article:
        if schema == "zhihu.answer.v1":
            if not blocks or blocks[0]["kind"] != "paragraph":
                raise AdapterUnavailable("direct_answer_requires_explicit_mapping")
            blocks[0]["kind"] = "direct_answer"
        proposal = {"title": source["title"], "summary": "", "tags": [], "blocks": blocks}
        if schema == "zhihu.answer.v1":
            proposal["question"] = question
    else:
        proposal = {"text": "\n\n".join(parts)}
        if schema == "weibo.single.v1":
            proposal.update(tags=[], images=images)
    citations = source["document"]["citations"]
    if len(evidence_refs) != len(citations):
        raise AdapterUnavailable("source_citations_require_explicit_mapping")
    mapped = []
    for citation, ref in zip(citations, evidence_refs, strict=True):
        location = citation.get("list_item_id", citation["block_id"]) if article else "single"
        offset = 0 if article else offsets[citation["block_id"]]
        locator = {"location_id": location, "start": citation["start"] + offset, "end": citation["end"] + offset}
        if not isinstance(ref, dict) or ref.get("fact_pack_item_id") != citation["fact_pack_item_id"] or ref.get("content_locator_json") != locator:
            raise AdapterUnavailable("source_citations_require_explicit_mapping")
        mapped.append({"id": citation["id"], "location_id": location, "fact_pack_item_id": citation["fact_pack_item_id"],
                       "snapshot_checksum": ref["snapshot_checksum"], "locator": {"start": locator["start"], "end": locator["end"]}})
    proposal["citations"] = mapped
    try:
        return canonical_payload(schema, proposal, asset_refs=asset_refs, evidence_refs=evidence_refs)
    except VariantDocumentError as exc:
        raise AdapterUnavailable("adapted_payload_invalid") from exc


class TextChannelAdapter:
    """Conservative deterministic subset; unsupported structure requires explicit editing."""

    def __init__(self, channel: str, content_form: str):
        contract = FIRST_BATCH.get((channel, content_form))
        if contract is None or "text.master.v2" not in contract.accepted_master_schemas:
            raise AdapterUnavailable("unsupported_text_target")
        self.contract = contract

    def capabilities(self) -> dict:
        return {"deterministic_subset": True, "model_assisted": False, "remote_verified": False,
                "form_descriptor": form_descriptor_for(self.contract.payload_schema, self.contract.channel, self.contract.content_form)}

    def canonicalize(self, payload: object, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        from .channel_variant_documents import canonical_payload

        return canonical_payload(self.contract.payload_schema, payload, asset_refs=asset_refs, evidence_refs=evidence_refs)

    def validate(self, payload: dict, asset_refs: list[dict], evidence_refs: list[dict]) -> None:
        from .channel_variant_documents import canonical_payload

        canonical_payload(self.contract.payload_schema, payload, asset_refs=asset_refs, evidence_refs=evidence_refs)

    def adapt(self, source_payload: dict, *, asset_refs: list[dict], evidence_refs: list[dict]) -> dict:
        from .channel_variant_documents import (
            ARTICLE_SCHEMAS,
            SINGLE_TEXT_SCHEMAS,
            VariantDocumentError,
            canonical_payload,
        )
        from .text_documents import TextDocumentError
        from .text_documents import canonical_payload as canonical_text_payload

        if self.contract.payload_schema in MODERN_ARTICLE_SCHEMAS | {"x.long_post.v1", "weibo.single.v1"}:
            return _adapt_modern_text(self.contract.payload_schema, source_payload, asset_refs, evidence_refs)

        cover_only = (self.contract.payload_schema == "wechat.article.v1" and len(asset_refs) == 1
                      and isinstance(asset_refs[0], dict)
                      and all(asset_refs[0].get(key) == value for key, value in {
                          "role": "cover", "slot_key": "cover", "sort_order": 0, "placement": {"usage": "cover"},
                      }.items()))
        official_article = self.contract.payload_schema == "wechat.article.v1"
        if asset_refs and not cover_only and not official_article:
            raise AdapterUnavailable("source_refs_require_explicit_mapping")
        if not isinstance(source_payload, dict) or not isinstance(source_payload.get("document"), dict):
            raise AdapterUnavailable("invalid_source_document")
        try:
            source = canonical_text_payload(source_payload)
        except TextDocumentError as exc:
            raise AdapterUnavailable("invalid_source_document") from exc
        blocks = source["document"]["blocks"]
        if not blocks or any((block["type"] != "paragraph" and not (official_article and block["type"] == "image"))
                             or block["type"] == "paragraph" and any(run["marks"] for run in block["content"]) for block in blocks):
            raise AdapterUnavailable("source_structure_requires_explicit_mapping")
        text_blocks = []
        for index, block in enumerate(blocks):
            if block["type"] == "image":
                ref = next((ref for ref in asset_refs if ref.get("role") == "inline_image" and ref.get("slot_key") == block["id"]), None)
                if ref is None or ref.get("material_revision_id") != block["material_revision_id"]:
                    raise AdapterUnavailable("source_refs_require_explicit_mapping")
                text_blocks.append({"id": block["id"], "order": index, "kind": "image", "image_ref_key": block["id"],
                                    "text": block.get("caption", ""), "alt_text": block.get("alt_text", "")})
            else:
                text_blocks.append({"id": block["id"], "order": index, "text": "".join(run["text"] for run in block["content"])})
        if self.contract.payload_schema == "wechat.article.v1":
            if asset_refs and not cover_only and not any(block["type"] == "image" for block in blocks):
                raise AdapterUnavailable("source_refs_require_explicit_mapping")
            proposal = {"title": source["title"], "blocks": [{"kind": "paragraph", **block} for block in text_blocks]}
        elif self.contract.payload_schema in ARTICLE_SCHEMAS:
            proposal = {"title": source["title"], "blocks": [{"kind": "paragraph", **block} for block in text_blocks]}
        elif self.contract.payload_schema == "x.thread.v1":
            proposal = {"posts": text_blocks}
        elif self.contract.payload_schema in SINGLE_TEXT_SCHEMAS:
            if len(text_blocks) != 1:
                raise AdapterUnavailable("single_post_requires_one_block")
            proposal = {"text": text_blocks[0]["text"]}
        else:
            raise AdapterUnavailable("unsupported_text_target")
        citations = source["document"]["citations"]
        if len(evidence_refs) != len(citations):
            raise AdapterUnavailable("source_citations_require_explicit_mapping")
        mapped = []
        for citation, ref in zip(citations, evidence_refs, strict=True):
            source_locator = ref.get("content_locator_json") if isinstance(ref, dict) else None
            location_id = "single" if self.contract.payload_schema in SINGLE_TEXT_SCHEMAS else citation["block_id"]
            expected_locator = {"location_id": location_id, "start": citation["start"], "end": citation["end"]}
            if (citation.get("list_item_id") is not None or not isinstance(ref, dict)
                    or ref.get("fact_pack_item_id") != citation["fact_pack_item_id"]
                    or source_locator != expected_locator):
                raise AdapterUnavailable("source_citations_require_explicit_mapping")
            mapped.append({"id": citation["id"], "location_id": location_id,
                           "fact_pack_item_id": citation["fact_pack_item_id"],
                           "snapshot_checksum": ref["snapshot_checksum"],
                           "locator": {"start": citation["start"], "end": citation["end"]}})
        proposal["citations"] = mapped
        try:
            return canonical_payload(self.contract.payload_schema, proposal, asset_refs=asset_refs, evidence_refs=evidence_refs)
        except VariantDocumentError as exc:
            raise AdapterUnavailable("adapted_payload_invalid") from exc

    def preview(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        return {"schema": self.contract.payload_schema, "payload": self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)}

    def render(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        item = self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)
        if "blocks" in item:
            if self.contract.payload_schema in MODERN_ARTICLE_SCHEMAS:
                parts = [item["title"]]
                if item["summary"]:
                    parts.append(item["summary"])
                for block in item["blocks"]:
                    if block["kind"] == "list":
                        parts.append("\n".join((f"{index + 1}. " if block["ordered"] else "- ") + child["text"]
                                               for index, child in enumerate(block["items"])))
                    elif block["kind"] == "divider":
                        parts.append("---")
                    else:
                        parts.append(block.get("text", ""))
                text = "\n\n".join(parts)
            else:
                text = item["title"] + "\n\n" + "\n\n".join(block["text"] for block in item["blocks"])
        elif "posts" in item:
            text = "\n\n".join(post["text"] for post in item["posts"])
        else:
            text = item["text"]
        return {"artifact_kind": "text", "text": text}

    def required_checks(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> tuple[str, ...]:
        self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)
        return ("variant_schema", "variant_evidence", "variant_rights", "variant_profile")

    def package_projection(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        return self.render(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)


class GraphicImageNoteAdapter:
    """Map verified per-canvas final render refs to ordered image cards."""

    contract = FIRST_BATCH[("xiaohongshu", "image_note")]

    def __init__(self, channel: str = "xiaohongshu"):
        self.contract = FIRST_BATCH[(channel, "image_note")]

    def capabilities(self) -> dict:
        return {"deterministic_subset": True, "model_assisted": False, "remote_verified": False,
                "form_descriptor": form_descriptor_for(self.contract.payload_schema, self.contract.channel, self.contract.content_form)}

    def canonicalize(self, payload: object, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        from .channel_variant_documents import canonical_payload

        return canonical_payload(self.contract.payload_schema, payload, asset_refs=asset_refs, evidence_refs=evidence_refs)

    def validate(self, payload: dict, asset_refs: list[dict], evidence_refs: list[dict]) -> None:
        self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)

    def adapt(self, source_payload: dict, *, asset_refs: list[dict], evidence_refs: list[dict]) -> dict:
        from .channel_variant_documents import VariantDocumentError
        from .graphic_documents import GraphicDocumentError
        from .graphic_documents import canonical_payload as canonical_graphic_payload

        if evidence_refs:
            raise AdapterUnavailable("source_evidence_requires_explicit_mapping")
        try:
            source = canonical_graphic_payload(source_payload)
        except GraphicDocumentError as exc:
            raise AdapterUnavailable("invalid_graphic_source") from exc
        title = source["title"].strip()
        canvases = source["canvases"]
        if not title:
            raise AdapterUnavailable("image_note_title_required")
        refs = {item.get("slot_key"): item for item in asset_refs if isinstance(item, dict)}
        if len(refs) != len(canvases) or set(refs) != {canvas["id"] for canvas in canvases}:
            raise AdapterUnavailable("render_canvas_coverage_missing")
        cards = []
        for index, canvas in enumerate(canvases):
            caption = "\n".join(run["text"] for layer in canvas["layers"] if layer["type"] == "text" for run in layer["runs"])
            cards.append({"id": canvas["id"], "order": index, "image_ref_key": canvas["id"], "caption": caption})
        try:
            return self.canonicalize({"title": title, "cards": cards}, asset_refs=asset_refs)
        except VariantDocumentError as exc:
            raise AdapterUnavailable("adapted_payload_invalid") from exc

    def preview(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        return {"schema": self.contract.payload_schema, "payload": self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)}

    def render(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        item = self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)
        result = {"artifact_kind": "image", "cards": item["cards"], "title": item["title"]}
        if self.contract.payload_schema == "bilibili.image_note.v1":
            result.update(description=item["description"], tags=item["tags"])
        return result

    def required_checks(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> tuple[str, ...]:
        self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)
        return ("variant_schema", "variant_evidence", "variant_rights", "variant_profile", "variant_render")

    def package_projection(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        return self.render(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)


class VideoSpokenScriptAdapter:
    """Project script and voice copy without a finished-video claim."""

    contract = FIRST_BATCH[("douyin", "spoken_script")]

    def capabilities(self) -> dict:
        return {"deterministic_subset": True, "model_assisted": False, "remote_verified": False,
                "form_descriptor": form_descriptor_for(self.contract.payload_schema, self.contract.channel, self.contract.content_form)}

    def canonicalize(self, payload: object, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        from .channel_variant_documents import canonical_payload

        return canonical_payload(self.contract.payload_schema, payload, asset_refs=asset_refs, evidence_refs=evidence_refs)

    def validate(self, payload: dict, asset_refs: list[dict], evidence_refs: list[dict]) -> None:
        self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)

    def adapt(self, source_payload: dict, *, asset_refs: list[dict], evidence_refs: list[dict]) -> dict:
        from .channel_variant_documents import VariantDocumentError
        from .video_documents import VideoDocumentError
        from .video_documents import canonical_payload as canonical_video_payload

        if evidence_refs:
            raise AdapterUnavailable("source_evidence_requires_explicit_mapping")
        if any(ref.get("role") != "b_roll" for ref in asset_refs):
            raise AdapterUnavailable("source_refs_require_explicit_mapping")
        try:
            source = canonical_video_payload(source_payload)
        except VideoDocumentError as exc:
            raise AdapterUnavailable("invalid_video_source") from exc
        if source["voice"]["mode"] != "none" or source["subtitles"]["cues"] or source["overlays"] or source["music"] or source["cover"] or source.get("render_asset_ref"):
            raise AdapterUnavailable("video_media_or_timing_requires_explicit_mapping")
        blocks = {block["id"]: block["text"] for block in source["script"]["blocks"]}
        if not source["shots"] or any("script_block_id" not in shot or not blocks[shot["script_block_id"]].strip() for shot in source["shots"]):
            raise AdapterUnavailable("script_scene_mapping_incomplete")
        if {shot["script_block_id"] for shot in source["shots"]} != set(blocks):
            raise AdapterUnavailable("script_block_coverage_incomplete")
        refs_by_shot = {ref["slot_key"]: ref for ref in asset_refs}
        if len(refs_by_shot) != len(asset_refs) or set(refs_by_shot) - {shot["id"] for shot in source["shots"]}:
            raise AdapterUnavailable("b_roll_shot_mapping_invalid")
        if {shot["id"] for shot in source["shots"] if "source_material_revision_id" in shot} != set(refs_by_shot):
            raise AdapterUnavailable("b_roll_shot_mapping_incomplete")
        scenes = [
            {"id": shot["id"], "order": index, "script": blocks[shot["script_block_id"]],
             "voice_text": blocks[shot["script_block_id"]], "b_roll_ref_keys": [shot["id"]] if shot["id"] in refs_by_shot else []}
            for index, shot in enumerate(source["shots"])
        ]
        elapsed_ms = 0
        estimated_cues = []
        for index, shot in enumerate(source["shots"], start=1):
            start_ms = elapsed_ms
            elapsed_ms += shot["duration_ms"]
            estimated_cues.append(f"{index}\n{self._srt_time(start_ms)} --> {self._srt_time(elapsed_ms)}\n{blocks[shot['script_block_id']]}")
        try:
            return self.canonicalize({"scenes": scenes, "estimated_srt": {"estimated": True, "text": "\n\n".join(estimated_cues)}}, asset_refs=asset_refs)
        except VariantDocumentError as exc:
            raise AdapterUnavailable("adapted_payload_invalid") from exc

    @staticmethod
    def _srt_time(milliseconds: int) -> str:
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        seconds, millis = divmod(remainder, 1_000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

    def preview(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        return {"schema": self.contract.payload_schema, "payload": self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)}

    def render(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        item = self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)
        return {"artifact_kind": "script", "scenes": item["scenes"], "estimated_srt": item.get("estimated_srt"), "finished_video": False}

    def required_checks(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> tuple[str, ...]:
        self.canonicalize(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)
        return ("variant_schema", "variant_evidence", "variant_rights", "variant_profile")

    def package_projection(self, payload: dict, *, asset_refs: list[dict] | None = None, evidence_refs: list[dict] | None = None) -> dict:
        return self.render(payload, asset_refs=asset_refs, evidence_refs=evidence_refs)


for _text_target, _text_contract in FIRST_BATCH.items():
    if "text.master.v2" in _text_contract.accepted_master_schemas:
        _EXECUTABLE_ADAPTERS[_text_target] = TextChannelAdapter(*_text_target)
_EXECUTABLE_ADAPTERS[("xiaohongshu", "image_note")] = GraphicImageNoteAdapter()
_EXECUTABLE_ADAPTERS[("bilibili", "image_note")] = GraphicImageNoteAdapter("bilibili")
_EXECUTABLE_ADAPTERS[("douyin", "spoken_script")] = VideoSpokenScriptAdapter()


def capability_for(db: Session, source_schema: str, channel: str, content_form: str) -> dict:
    contract = FIRST_BATCH.get((channel, content_form))
    descriptor = form_descriptor_for(contract.payload_schema, channel, content_form) if contract else None
    if contract is None or source_schema not in contract.accepted_master_schemas:
        return {
            "configured": False,
            "supported_source": False,
            "executable": False,
            "verified": False,
            "reason": "unsupported_source_or_target",
            "form_descriptor": descriptor,
        }
    try:
        form = resolve_content_form(db, channel, content_form)
    except ChannelRegistryError:
        return {
            "configured": False,
            "supported_source": True,
            "executable": False,
            "verified": False,
            "reason": "published_profile_missing",
            "form_descriptor": descriptor,
        }
    if form.source != "profile" or form.profile_version_id is None:
        return {
            "configured": False,
            "supported_source": True,
            "executable": False,
            "verified": False,
            "reason": "published_profile_missing",
            "form_descriptor": descriptor,
        }
    if form.artifact_kind != contract.artifact_kind:
        raise AdapterUnavailable("artifact_kind_mismatch")
    template = db.get(ChannelTemplateVersion, form.profile_version_id)
    if template is None or template.status != "published":
        raise AdapterUnavailable("published_profile_missing")
    profile = (template.profile_json or {}).get("content_forms", {}).get(content_form)
    if not isinstance(profile, dict):
        raise AdapterUnavailable("published_profile_missing")
    declared = {"payload_schema": contract.payload_schema, "adapter_key": contract.key, "adapter_version": contract.version}
    if any(key in profile and profile[key] != value for key, value in declared.items()):
        raise AdapterUnavailable("profile_contract_mismatch")
    instructions = profile.get("adaptation_instructions", "")
    if not isinstance(instructions, str) or len(instructions) > 16000:
        raise AdapterUnavailable("invalid_profile_instructions")
    profile_hash = hashlib.sha256(json.dumps(profile, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    adapter = _EXECUTABLE_ADAPTERS.get((channel, content_form))
    executable = adapter is not None and adapter.contract == contract
    return {
        "configured": True,
        "supported_source": True,
        "executable": executable,
        "verified": False,
        "reason": None if executable else "adapter_not_implemented",
        "profile_version_id": template.id,
        "profile_version": template.version,
        "profile_hash": profile_hash,
        "artifact_kind": contract.artifact_kind,
        "adapter_key": contract.key,
        "adapter_version": contract.version,
        "payload_schema": contract.payload_schema,
        "form_descriptor": descriptor,
        "effective_instructions": instructions,
    }


def executable_adapter_for(db: Session, source_schema: str, channel: str, content_form: str) -> tuple[ChannelAdapter, dict]:
    capability = capability_for(db, source_schema, channel, content_form)
    if not capability["executable"]:
        raise AdapterUnavailable(capability["reason"] or "adapter_unavailable")
    return _EXECUTABLE_ADAPTERS[(channel, content_form)], capability
