"""Rework records and the lessons the editing model draws from them.

Every note on a sent-back 小样 / 成片 is kept; the editor proposes a reusable rule after fixing it, the user approves it,
and active rules go out with every video brief.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentProject, ContentUnit, User, VideoLesson, VideoReworkRecord

_OPEN = ("proposed", "active")


def _fail(code: str, message: str, status: int = 422):
    raise HTTPException(status, {"code": code, "message": message})


def record_notes(db: Session, user: User, project_id: int, unit_id: int, stage: str, target_id: int, notes: list[dict]) -> None:
    for item in notes:
        text = str(item.get("note") or "").strip()
        if text:
            db.add(VideoReworkRecord(owner_user_id=user.id, project_id=project_id, unit_id=unit_id, stage=stage, target_id=target_id,
                                     time_ms=item.get("time_ms"), note=text[:2000], created_by=user.email))
    db.flush()


def _record_view(row: VideoReworkRecord) -> dict:
    return {"id": row.id, "project_id": row.project_id, "unit_id": row.unit_id, "stage": row.stage, "time_ms": row.time_ms,
            "note": row.note, "lesson_id": row.lesson_id, "created_at": row.created_at.isoformat() if row.created_at else None}


def _sources(db: Session, unit_ids: list[int]) -> list[dict]:
    if not unit_ids:
        return []
    rows = db.execute(select(ContentUnit.id, ContentUnit.title, ContentProject.id, ContentProject.title)
                      .join(ContentProject, ContentProject.id == ContentUnit.project_id).where(ContentUnit.id.in_(unit_ids))).all()
    found = {unit_id: {"project_id": project_id, "project_title": project_title, "unit_id": unit_id, "unit_title": unit_title}
             for unit_id, unit_title, project_id, project_title in rows}
    return [found[unit_id] for unit_id in unit_ids if unit_id in found]


def _lesson_view(db: Session, row: VideoLesson) -> dict:
    return {"id": row.id, "title": row.title, "rule": row.rule, "scope": row.scope, "status": row.status, "occurrences": row.occurrences,
            "source_record_ids": row.source_record_ids or [], "sources": _sources(db, row.source_unit_ids or []),
            "proposed_by": row.proposed_by, "decided_by": row.decided_by,
            "decided_at": row.decided_at.isoformat() if row.decided_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None}


def propose(db: Session, user: User, project_id: int, unit_id: int, title: str, rule: str, scope: str,
            record_ids: list[int], same_as_lesson_id: int | None) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    records = list(db.scalars(select(VideoReworkRecord).where(VideoReworkRecord.id.in_(record_ids)))) if record_ids else []
    if len(records) != len(set(record_ids)) or any(row.owner_user_id != user.id or row.unit_id != unit_id for row in records):
        _fail("video_chain_lesson_records_invalid", "record_ids 只能是这条作品的返修记录")
    if same_as_lesson_id is not None:
        lesson = db.get(VideoLesson, same_as_lesson_id)
        if lesson is None or lesson.owner_user_id != user.id or lesson.status not in _OPEN:
            _fail("video_chain_lesson_not_found", "same_as_lesson_id 不是一条待确认或已生效的经验", 404)
    else:
        lesson = db.scalar(select(VideoLesson).where(VideoLesson.owner_user_id == user.id, VideoLesson.status.in_(_OPEN),
                                                     VideoLesson.title == title.strip(), VideoLesson.scope == scope.strip()).limit(1))
    if any(row.lesson_id is not None and (lesson is None or row.lesson_id != lesson.id) for row in records):
        _fail("video_chain_lesson_records_taken", "有返修记录已经挂在别的经验上")
    attached = lesson is not None
    if lesson is None:
        lesson = VideoLesson(owner_user_id=user.id, title=title.strip()[:200], rule=rule.strip(), scope=scope.strip()[:200], status="proposed",
                             occurrences=max(1, len(records)), source_record_ids=[row.id for row in records], source_unit_ids=[unit_id],
                             proposed_by=user.email)
        db.add(lesson)
        db.flush()
    else:
        new_records = [row.id for row in records if row.id not in (lesson.source_record_ids or [])]
        new_unit = unit_id not in (lesson.source_unit_ids or [])
        # Repeating a proposal for the same notes must not inflate the count.
        if new_records or new_unit:
            lesson.occurrences += 1
            lesson.source_record_ids = [*(lesson.source_record_ids or []), *new_records]
            lesson.source_unit_ids = [*(lesson.source_unit_ids or []), *([unit_id] if new_unit else [])]
            lesson.updated_at = datetime.now(UTC)
    for row in records:
        row.lesson_id = lesson.id
    db.commit()
    return {"lesson": _lesson_view(db, lesson), "attached_to_existing": attached,
            "note": "等用户在 设置 → 经验库 同意后才会随任务书下发" if lesson.status == "proposed" else "这条经验已生效"}


def brief_view(db: Session, user: User, unit_id: int) -> dict:
    lessons = db.scalars(select(VideoLesson).where(VideoLesson.owner_user_id == user.id, VideoLesson.status == "active")
                         .order_by(VideoLesson.occurrences.desc(), VideoLesson.id))
    records = db.scalars(select(VideoReworkRecord).where(VideoReworkRecord.unit_id == unit_id, VideoReworkRecord.lesson_id.is_(None))
                         .order_by(VideoReworkRecord.id))
    return {"active": [{key: getattr(row, key) for key in ("id", "title", "rule", "scope", "occurrences")} for row in lessons],
            "open_rework_records": [{"id": row.id, "stage": row.stage, "time_ms": row.time_ms, "note": row.note} for row in records]}


def list_lessons(db: Session, user: User, status: str | None) -> dict:
    query = select(VideoLesson).where(VideoLesson.owner_user_id == user.id)
    if status:
        query = query.where(VideoLesson.status == status)
    return {"items": [_lesson_view(db, row) for row in db.scalars(query.order_by(VideoLesson.updated_at.desc(), VideoLesson.id.desc()))]}


def list_records(db: Session, user: User, unit_id: int | None, unlinked: bool, limit: int) -> dict:
    query = select(VideoReworkRecord).where(VideoReworkRecord.owner_user_id == user.id)
    if unit_id is not None:
        query = query.where(VideoReworkRecord.unit_id == unit_id)
    if unlinked:
        query = query.where(VideoReworkRecord.lesson_id.is_(None))
    rows = list(db.scalars(query.order_by(VideoReworkRecord.id.desc()).limit(limit)))
    sources = {item["unit_id"]: item for item in _sources(db, sorted({row.unit_id for row in rows}))}
    return {"items": [{**_record_view(row), "unit_title": (sources.get(row.unit_id) or {}).get("unit_title"),
                       "project_title": (sources.get(row.unit_id) or {}).get("project_title")} for row in rows]}


_MOVES = {"approve": ("proposed", "active"), "reject": ("proposed", "rejected"), "retire": ("active", "retired")}


def update_lesson(db: Session, user: User, lesson_id: int, changes: dict, action: str | None) -> dict:
    lesson = db.get(VideoLesson, lesson_id)
    if lesson is None or lesson.owner_user_id != user.id:
        _fail("video_lesson_not_found", "经验不存在", 404)
    if lesson.status not in _OPEN:
        _fail("video_lesson_closed", "这条经验已不同意或已停用", 409)
    if action:
        before, after = _MOVES[action]
        if lesson.status != before:
            _fail("video_lesson_state", "这条经验现在不能这样操作", 409)
        lesson.status, lesson.decided_by, lesson.decided_at = after, user.email, datetime.now(UTC)
    for key in ("title", "rule", "scope"):
        if changes.get(key) is not None:
            value = str(changes[key]).strip()
            if not value:
                _fail("video_lesson_empty", "原因、做法和适用范围都不能为空")
            setattr(lesson, key, value[:200] if key != "rule" else value)
    lesson.updated_at = datetime.now(UTC)
    db.commit()
    return _lesson_view(db, lesson)


def ensure_active(db: Session, owner_user_id: int, title: str, rule: str, scope: str, occurrences: int, actor: str) -> dict:
    """Records a lesson the user already confirmed outside the editor; running it again changes nothing."""
    lesson = db.scalar(select(VideoLesson).where(VideoLesson.owner_user_id == owner_user_id, VideoLesson.title == title,
                                                 VideoLesson.scope == scope).limit(1))
    if lesson is None:
        now = datetime.now(UTC)
        lesson = VideoLesson(owner_user_id=owner_user_id, title=title, rule=rule, scope=scope, status="active", occurrences=occurrences,
                             source_record_ids=[], source_unit_ids=[], proposed_by=actor, decided_by=actor, decided_at=now)
        db.add(lesson)
        db.commit()
    return {"id": lesson.id, "status": lesson.status, "occurrences": lesson.occurrences}
