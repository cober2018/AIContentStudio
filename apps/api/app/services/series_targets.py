"""Series × Account × Content Form 投放绑定。

绑定是"默认投放目标"，不是授权书：启用/停用不改变 Candidate 审核、
Delivery Authorization 或平台 CapabilityVerification 的任何门槛。
同平台多个账号是不同绑定行，永远不会被 platform_channel 折叠成同一身份。
"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import AuditLog, ContentAccount, ContentSeries, SeriesAccountTarget, User
from .content_identity import owned_entity


def _editable_series(db: Session, user: User, series_id: int) -> ContentSeries:
    series = owned_entity(db, user, "series", series_id, mutable=True)
    if series.scope != "persona_editorial":
        raise HTTPException(422, "series_scope_unsupported: 投放绑定只适用于角色级跨平台栏目")
    return series


def _target(db: Session, series: ContentSeries, target_id: int) -> SeriesAccountTarget:
    row = db.get(SeriesAccountTarget, target_id)
    if row is None or row.series_id != series.id:
        raise HTTPException(404, "投放绑定不存在")
    return row


def _account_json(db: Session, row: SeriesAccountTarget) -> dict:
    account = db.get(ContentAccount, row.account_id)
    return {
        "id": row.id,
        "series_id": row.series_id,
        "account_id": row.account_id,
        "account_name": account.name if account else None,
        "platform_channel": account.platform_channel if account else None,
        "content_form": row.content_form,
        "enabled": bool(row.enabled),
        "version": row.version,
    }


def list_targets(db: Session, user: User, series_id: int) -> list[dict]:
    series = owned_entity(db, user, "series", series_id)
    if series.scope != "persona_editorial":
        return []
    rows = db.scalars(select(SeriesAccountTarget).where(SeriesAccountTarget.series_id == series.id).order_by(SeriesAccountTarget.id)).all()
    return [_account_json(db, row) for row in rows]


def bind_target(db: Session, user: User, series_id: int, *, account_id: int, content_form: str) -> dict:
    series = _editable_series(db, user, series_id)
    account = db.get(ContentAccount, account_id)
    if account is None or account.persona_id != series.persona_id:
        raise HTTPException(422, "series_target_persona_mismatch: 只能绑定同一角色名下的账号")
    if account.status != "active":
        raise HTTPException(409, "series_target_account_archived")
    if not account.platform_channel:
        raise HTTPException(422, "series_target_account_unbound: 账号尚未登记平台公开身份")
    from .content_harness.channel_registry import ChannelRegistryError, ensure_channel_in_service, resolve_content_form

    try:
        ensure_channel_in_service(account.platform_channel)
        resolve_content_form(db, account.platform_channel, content_form)
    except ChannelRegistryError as exc:
        raise HTTPException(422, str(exc)) from None
    row = SeriesAccountTarget(series_id=series.id, account_id=account.id, content_form=content_form, enabled=True, version=1, created_by=user.email)
    db.add(row)
    try:
        db.flush()
        db.add(AuditLog(event="series_target.bound", actor=user.email, entity_type="series_account_target", entity_id=row.id,
                        detail_json={"series_id": series.id, "account_id": account.id, "platform_channel": account.platform_channel,
                                     "content_form": content_form, "note": "binding_is_not_authorization"}))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "series_target_conflict: 该账号与内容形态已绑定") from None
    db.refresh(row)
    return _account_json(db, row)


def update_target(db: Session, user: User, series_id: int, target_id: int, *, expected_version: int, enabled: bool) -> dict:
    series = _editable_series(db, user, series_id)
    row = _target(db, series, target_id)
    if row.version != expected_version:
        raise HTTPException(409, "series_target_version_conflict")
    row.enabled = enabled
    row.version += 1
    try:
        db.add(AuditLog(event="series_target.updated" if enabled else "series_target.disabled", actor=user.email,
                        entity_type="series_account_target", entity_id=row.id,
                        detail_json={"series_id": series.id, "account_id": row.account_id, "content_form": row.content_form, "version": row.version}))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "series_target_version_conflict") from None
    db.refresh(row)
    return _account_json(db, row)


def unbind_target(db: Session, user: User, series_id: int, target_id: int) -> None:
    series = _editable_series(db, user, series_id)
    row = _target(db, series, target_id)
    detail = {"series_id": series.id, "account_id": row.account_id, "content_form": row.content_form}
    db.delete(row)
    db.add(AuditLog(event="series_target.unbound", actor=user.email, entity_type="series_account_target", entity_id=target_id, detail_json=detail))
    db.commit()


def guard_enabled_binding(db: Session, *, series_id: int | None, account_id: int, content_form: str) -> None:
    """停用的绑定阻断新的投放授权；未建过绑定的显式一次性投放仍允许（绑定不是授权书）。"""
    if series_id is None:
        return
    row = db.scalar(select(SeriesAccountTarget).where(
        SeriesAccountTarget.series_id == series_id,
        SeriesAccountTarget.account_id == account_id,
        SeriesAccountTarget.content_form == content_form,
    ))
    if row is not None and not row.enabled:
        raise HTTPException(409, "series_target_disabled: 该栏目投放绑定已停用，请先重新启用或改用其他目标")
