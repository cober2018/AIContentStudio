"""小工具 page: lists what the third-party model ran through the MCP small tools; nothing is started from here."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..services import media_transcription

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.get("/media-transcriptions")
def media_transcriptions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return media_transcription.listing(db)


@router.post("/media-transcriptions/{job_id}/reveal")
def reveal_media_transcription(job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    import sys

    if sys.platform != "darwin":
        raise HTTPException(409, {"code": "reveal_unsupported", "message": "只能在 Mac 本机上打开访达"})
    return media_transcription.reveal(db, job_id)
