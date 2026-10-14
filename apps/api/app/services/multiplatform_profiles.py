"""Reviewed additive profile versions without global seeding or old-row writes."""

import hashlib
import json
from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..models import ChannelTemplateVersion
from .channel_adapters import FIRST_BATCH

DECLARED_TARGETS = tuple(target for target in FIRST_BATCH if target[0] not in {"xueqiu", "juejin"})
_INSTRUCTIONS = {
    "wechat": "公众号文章：用清晰标题和完整正文，保留来源声明；草稿箱另需精确授权。",
    "toutiao": "头条文章：标题交代事件与读者收益，概要直述重点，正文解释背景和事实。",
    "baijia": "百家号文章：标题明确主题，概要提供检索线索，正文按主题分节并保留来源。",
    "zhihu": "知乎：文章逐步论证并说明证据边界；回答先直接回应用户确认的问题，再展开依据。",
    "bilibili": "B站：专栏使用分节解释和必要技术细节；图文用有序成品图卡、说明和标签。",
    "sohu": "搜狐号文章：新闻背景、事实经过、影响分析顺序清楚，保留来源与声明。",
    "penguin": "企鹅号文章：面向普通读者解释主题，标题与概要准确，段落短且易读。",
    "netease": "网易号文章：说明事件背景和观点依据，区分事实与评论，保留出处。",
    "xiaohongshu": "小红书图文：用自然个人表达、清晰标题和真实有序图卡，避免履历式文案。",
    "x": "X：单帖简明；推串各帖可独立读且顺序连贯；长帖连续正文；Articles 用标题和分节。",
    "weibo": "微博：正文直述重点，标签与内容相关，配图保持精确顺序，来源和声明可见。",
    "douyin": "抖音口播：分镜与口播对应，B-roll 仅引用实际素材，字幕明确标为估算，交付为脚本。",
}
_FORM_INSTRUCTIONS = {
    ("zhihu", "article"): "知乎文章：先提出清楚的论点，再按证据和推理分节展开，说明适用边界。",
    ("zhihu", "answer"): "知乎回答：仅回应用户确认的具体问题；首段直接回答，再解释依据和限制。",
    ("bilibili", "article"): "B站专栏：以主题标题和概要引入，用分节、列表和代码解释技术细节。",
    ("bilibili", "image_note"): "B站图文：用有序真实成品图卡逐步说明主题，正文说明和标签与图卡对应。",
    ("x", "single"): "X 单帖：用一个简洁完整段落陈述重点，保留必要来源和声明。",
    ("x", "thread"): "X 推串：拆成有序短帖，每帖可独立理解，整串保持递进逻辑和精确引用。",
    ("x", "long_post"): "X 长帖：保持连续文字和自然段落，不拆为推串，不添加 Articles 标题结构。",
    ("x", "articles"): "X Articles：用独立标题、概要和 typed 正文段落展开主题，保留标签与来源。",
}


class ProfilePlanError(ValueError):
    pass


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _rows(db, channel):
    return db.scalars(select(ChannelTemplateVersion).where(ChannelTemplateVersion.channel == channel)
                      .order_by(ChannelTemplateVersion.version.desc())).all()


def _current(rows):
    return next((row for row in rows if row.status == "published" and isinstance(row.profile_json, dict)
                 and row.profile_json.get("content_forms")), next((row for row in rows if row.status == "published"), None))


def _defaults(channel, form):
    contract = FIRST_BATCH[(channel, form)]
    result = {"artifact_kind": contract.artifact_kind, "payload_schema": contract.payload_schema,
              "adapter_key": contract.key, "adapter_version": contract.version,
              "adaptation_instructions": _FORM_INSTRUCTIONS.get((channel, form), _INSTRUCTIONS[channel]), "publisher_candidates": [],
              "delivery_actions": ["copy_package", "manual_handoff"], "remote_verified": False,
              "platform_limits_verified": False}
    if contract.artifact_kind == "image":
        result["media_requirements"] = {"required_roles": ["card_image"]}
    if channel == "x" and form in {"long_post", "articles"}:
        result["account_eligibility"] = "unverified"
    return result


def _diff(before, after, path=""):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before) | set(after)):
            result.extend(_diff(before.get(key), after.get(key), f"{path}.{key}".strip(".")))
        return result
    return [] if before == after else [{"path": path, "before": before, "after": after}]


def dry_run_profiles(db, channels: list[str]) -> dict:
    if not isinstance(channels, list) or not channels or len(channels) > 12 or len(set(channels)) != len(channels):
        raise ValueError("profile_channels_invalid")
    if any(not isinstance(channel, str) or channel not in _INSTRUCTIONS for channel in channels):
        raise ValueError("profile_channels_invalid")
    changes = []
    for channel in channels:
        rows = _rows(db, channel)
        current = _current(rows)
        before = deepcopy(current.profile_json) if current and current.profile_json else {}
        after = deepcopy(before)
        forms = after.setdefault("content_forms", {})
        if not isinstance(forms, dict):
            raise ProfilePlanError("profile_content_forms_invalid")
        for target_channel, form in DECLARED_TARGETS:
            if target_channel != channel:
                continue
            existing = forms.setdefault(form, {})
            if not isinstance(existing, dict):
                raise ProfilePlanError("profile_content_form_invalid")
            for key, value in _defaults(channel, form).items():
                if key in {"artifact_kind", "payload_schema", "adapter_key", "adapter_version"}:
                    existing[key] = value
                else:
                    existing.setdefault(key, value)
        changes.append({"channel_id": channel, "expected_profile_version_id": current.id if current else None,
                        "expected_profile_hash": _hash(before), "expected_max_version": rows[0].version if rows else 0,
                        "before": before, "after": after, "differences": _diff(before, after),
                        "action": "append_version" if before != after else "unchanged"})
    plan = {"plan_version": 1, "changes": changes}
    return {**plan, "plan_hash": _hash(plan)}


def apply_profiles(db, plan: dict, *, expected_plan_hash: str) -> dict:
    if not isinstance(plan, dict) or set(plan) != {"plan_version", "changes", "plan_hash"} or plan.get("plan_version") != 1:
        raise ValueError("profile_plan_invalid")
    reviewed_hash = _hash({"plan_version": plan["plan_version"], "changes": plan["changes"]})
    if reviewed_hash != expected_plan_hash or reviewed_hash != plan["plan_hash"]:
        raise ValueError("profile_plan_changed")
    changes = plan["changes"]
    if not isinstance(changes, list) or not changes or len(changes) > 12:
        raise ValueError("profile_plan_invalid")
    channels = [change.get("channel_id") for change in changes if isinstance(change, dict)]
    if len(channels) != len(changes) or len(set(channels)) != len(channels) or any(channel not in _INSTRUCTIONS for channel in channels):
        raise ValueError("profile_plan_invalid")
    pending, unchanged = [], []
    for change in changes:
        rows = _rows(db, change["channel_id"])
        current = _current(rows)
        current_profile = current.profile_json if current and current.profile_json else {}
        if current_profile == change["after"]:
            unchanged.append(change["channel_id"])
            continue
        if ((current.id if current else None) != change["expected_profile_version_id"]
                or _hash(current_profile) != change["expected_profile_hash"]
                or (rows[0].version if rows else 0) != change["expected_max_version"]):
            raise ValueError("profile_stale")
        # Reconstruct the server-approved additive proposal rather than trusting a caller-supplied replacement.
        fresh = dry_run_profiles(db, [change["channel_id"]])["changes"][0]
        if fresh != change:
            raise ValueError("profile_plan_changed")
        pending.append((change, rows, current))
    created = []
    try:
        with db.begin_nested():
            for change, rows, current in pending:
                row = ChannelTemplateVersion(channel=change["channel_id"], version=(rows[0].version if rows else 0) + 1,
                    name=current.name if current else f"{change['channel_id']} handoff profile",
                    structure=deepcopy(current.structure) if current else [],
                    length_guidance=deepcopy(current.length_guidance) if current else {},
                    forbidden_patterns=deepcopy(current.forbidden_patterns) if current else [],
                    output_schema=deepcopy(current.output_schema) if current else {},
                    profile_schema_version=current.profile_schema_version if current else 1,
                    profile_json=deepcopy(change["after"]), status="published")
                from ..routers.templates import _checksum, _demote_other_published

                row.checksum = _checksum({"structure": row.structure, "output_schema": row.output_schema,
                                          "profile_schema_version": row.profile_schema_version, "profile_json": row.profile_json})
                db.add(row)
                db.flush()
                _demote_other_published(db, ChannelTemplateVersion, {"channel": row.channel}, keep_id=row.id)
                created.append({"channel_id": row.channel, "profile_version_id": row.id,
                                "version": row.version, "profile_hash": _hash(row.profile_json)})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("profile_stale") from exc
    return {"plan_hash": reviewed_hash, "created": created, "unchanged": unchanged}
