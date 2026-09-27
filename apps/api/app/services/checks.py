"""统一检查服务（D12/§6.17）：所有检查落 DraftCheckRun，incomplete 不是 pass。

兼容期：`Draft.fact_check_json` 继续写（old clients 不破），同时镜像一条
check_kind='fact' 的记录；新 Review Gate 只读 DraftCheckRun。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CheckKind, CheckStatus, Draft, DraftCheckRun, utcnow
from .content_harness import rules as harness_rules
from .content_harness.channel_registry import resolve_content_form

# 各 check_kind 的 profile 标识（服务层内置；profile_version 随内置实现演进而 +1）
_PROFILES: dict[str, tuple[str, str]] = {
    CheckKind.fact.value: ("profile.check.fact", "1"),
    CheckKind.platform.value: ("profile.check.platform", "1"),
    CheckKind.rights.value: ("profile.check.rights", "1"),
    CheckKind.media.value: ("profile.check.media", "1"),
    CheckKind.seo.value: ("profile.check.seo", "1"),
    CheckKind.domain.value: ("profile.check.domain", "1"),
    CheckKind.safety.value: ("profile.check.safety", "1"),
}

# 规则 key → check_kind 归属
RULE_KIND_MAP: dict[str, str] = {
    "rule.fact.bound": CheckKind.fact.value,
    "rule.media.required": CheckKind.media.value,
    "rule.media.public_rights": CheckKind.rights.value,
    "rule.media.order": CheckKind.media.value,
    "rule.platform.required_fields": CheckKind.platform.value,
    "rule.seo.required_fields": CheckKind.seo.value,
    "rule.finance.as_of": CheckKind.domain.value,
    "rule.finance.no_return_guarantee": CheckKind.domain.value,
    "rule.tech.code_provenance": CheckKind.domain.value,
}


def record_check_run(
    db: Session,
    draft: Draft,
    *,
    check_kind: str,
    status: str,
    report: dict,
    input_hash: str | None = None,
    provider_key: str | None = None,
    provider_version: str | None = None,
    profile_key: str | None = None,
    profile_version: str | None = None,
) -> DraftCheckRun:
    row = DraftCheckRun(
        draft_id=draft.id,
        check_kind=check_kind,
        profile_key=profile_key or _PROFILES.get(check_kind, ("", "?"))[0] or None,
        profile_version=profile_version or _PROFILES.get(check_kind, ("", "?"))[1],
        input_hash=input_hash,
        status=status,
        report_json=report,
        provider_key=provider_key,
        provider_version=provider_version,
        created_at=utcnow(),
    )
    db.add(row)
    db.flush()
    return row


def current_checks(db: Session, draft: Draft) -> list[DraftCheckRun]:
    """每个 check_kind 只取最新一条（Review Gate 读这里）。"""
    rows = db.scalars(
        select(DraftCheckRun).where(DraftCheckRun.draft_id == draft.id).order_by(DraftCheckRun.id)
    ).all()
    latest: dict[str, DraftCheckRun] = {}
    for row in rows:
        latest[row.check_kind] = row  # id 升序，后写覆盖
    return list(latest.values())


def checks_current_for_input(db: Session, draft: Draft) -> bool:
    """现有 check runs 是否仍绑定当前输入（input_hash 一致且非 stale）。"""
    checks = current_checks(db, draft)
    if not checks:
        return False
    for row in checks:
        if row.status == CheckStatus.stale.value:
            return False
        if row.input_hash and draft.input_hash and row.input_hash != draft.input_hash:
            return False
    return True


def missing_mandatory_kinds(db: Session, draft: Draft, required: list[str] | None = None) -> list[str]:
    """缺破坏性检查项：默认至少 fact + platform。incomplete/failed 视为未完成。"""
    required = required or [CheckKind.fact.value, CheckKind.platform.value]
    by_kind = {row.check_kind: row for row in current_checks(db, draft)}
    missing = []
    for kind in required:
        row = by_kind.get(kind)
        if row is None or row.status in {CheckStatus.incomplete.value, CheckStatus.blocker.value, CheckStatus.stale.value}:
            missing.append(kind)
    return missing


def mark_all_stale(db: Session, draft: Draft, reason: str) -> int:
    """输入变化后：旧 check runs 全部标 stale（不删除历史）。"""
    rows = db.scalars(select(DraftCheckRun).where(DraftCheckRun.draft_id == draft.id)).all()
    count = 0
    for row in rows:
        if row.status not in {CheckStatus.stale.value}:
            row.status = CheckStatus.stale.value
            row.report_json = {**(row.report_json or {}), "stale_reason": reason}
            count += 1
    return count


def mark_kinds_stale(db: Session, draft: Draft, kinds: set[str], reason: str) -> int:
    """R2-M8：只失效指定 kind 的 check runs（如换图只失效 media/rights，不动正文 fact）。"""
    rows = db.scalars(select(DraftCheckRun).where(DraftCheckRun.draft_id == draft.id)).all()
    count = 0
    for row in rows:
        if row.check_kind in kinds and row.status != CheckStatus.stale.value:
            row.status = CheckStatus.stale.value
            row.report_json = {**(row.report_json or {}), "stale_reason": reason}
            count += 1
    return count


# ---------- 各类检查实现 ----------


def run_fact_check(db: Session, draft: Draft, result_json: dict, input_hash: str | None) -> DraftCheckRun:
    """FactCheck 镜像写入（实际计算复用 services/factchecker，由调用方传入结果）。"""
    result = (result_json or {}).get("result") or "incomplete"
    status = {
        "pass": CheckStatus.pass_.value,
        "warning": CheckStatus.warning.value,
        "blocker": CheckStatus.blocker.value,
    }.get(result, CheckStatus.incomplete.value)
    return record_check_run(
        db, draft, check_kind=CheckKind.fact.value, status=status,
        report=result_json, input_hash=input_hash,
        provider_key=(result_json or {}).get("provider"),
    )


def run_rule_set(db: Session, draft: Draft, rule_keys: list[str] | None = None) -> list[DraftCheckRun]:
    """确定性规则集 → 按归属 check_kind 聚合写 DraftCheckRun。"""
    form_spec: dict[str, Any] = {}
    try:
        spec = resolve_content_form(db, draft.content_job.channel, getattr(draft, "content_form", None) or draft.content_job.content_form)
        form_spec = spec.to_dict()
    except Exception:  # noqa: BLE001 渠道下线等：按无 profile 求值
        form_spec = {}
    keys = rule_keys or harness_rules.rules_for_draft(db, draft, form_spec=form_spec)
    ctx = harness_rules.RuleContext(
        draft=draft,
        channel=form_spec.get("channel", draft.content_job.channel),
        content_form=form_spec.get("content_form", ""),
        media_requirements=harness_rules.media_requirements_for(db, draft),
    )
    results = harness_rules.evaluate_rule_set(db, keys, ctx)
    input_hash = draft.input_hash

    by_kind: dict[str, list] = {}
    for result in results:
        kind = RULE_KIND_MAP.get(result.key, CheckKind.domain.value)
        by_kind.setdefault(kind, []).append(result)

    written = []
    for kind, items in by_kind.items():
        status = harness_rules.worst_status(items)
        written.append(
            record_check_run(
                db, draft, check_kind=kind, status=status,
                report={"rules": [{ "key": r.key, "version": r.version, "status": r.status, "details": r.details} for r in items]},
                input_hash=input_hash,
            )
        )
    return written


def run_seo_check(db: Session, draft: Draft, report: dict | None = None) -> DraftCheckRun:
    """SEO 必备字段确定性检查（不依赖 LLM 报告时仍可运行）。"""
    from .content_harness.seo_rules import evaluate_seo_fields

    outcome = evaluate_seo_fields(draft)
    status = {"pass": CheckStatus.pass_.value, "warning": CheckStatus.warning.value, "blocker": CheckStatus.blocker.value}.get(
        outcome["status"], CheckStatus.incomplete.value
    )
    payload = {**(report or {}), **outcome}
    return record_check_run(db, draft, check_kind=CheckKind.seo.value, status=status, report=payload, input_hash=draft.input_hash)


def run_domain_checks(db: Session, draft: Draft, content_form: str | None = None) -> list[DraftCheckRun]:
    """财务/技术领域规则（deterministic）：按 content_form 选择。"""
    from .content_harness.domain_rules import rules_for_form

    keys = rules_for_form(content_form or getattr(draft, "content_form", None) or draft.content_job.content_form)
    if not keys:
        return []
    return run_rule_set(db, draft, rule_keys=keys)
