"""Coordinate hash-addressed material writes with orphan-byte cleanup."""

from __future__ import annotations

import fcntl
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import event
from sqlalchemy.orm import Session


def _lock_path(content_hash: str) -> Path:
    from .asset_media import MEDIA_ROOT

    return MEDIA_ROOT / "material" / ".locks" / f"{content_hash[:2]}.lock"


def _acquire(content_hash: str):
    path = _lock_path(content_hash)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    except BaseException:
        handle.close()
        raise
    return handle


def hold_until_transaction_end(db: Session, content_hash: str) -> None:
    """A writer keeps the lock until its revision is committed or rolled back."""
    stripe = content_hash[:2]
    handles = db.info.setdefault("material_byte_locks", {})
    if stripe not in handles:
        handles[stripe] = _acquire(content_hash)


@event.listens_for(Session, "after_transaction_end")
def _release_after_outer_transaction(db: Session, transaction) -> None:
    if transaction.parent is not None:
        return
    for handle in db.info.pop("material_byte_locks", {}).values():
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


@contextmanager
def locked_hash(content_hash: str) -> Iterator[None]:
    handle = _acquire(content_hash)
    try:
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
