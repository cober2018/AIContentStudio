"""Source Library API（STU-020~025）。"""

import hashlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import AuditLog, Fact, ParseStatus, SourceDocument, User
from ..services import fact_extractor
from ..services.parsers import get_parser
from ..services.url_fetch import UnsafeUrlError, safe_fetch

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])

ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".pdf"}


class TextSourceIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    as_of: str | None = None
    trust_level: float = 0.8


class UrlSourceIn(BaseModel):
    url: str
    title: str | None = None
    as_of: str | None = None
    trust_level: float = 0.6


class SourceUpdateIn(BaseModel):
    title: str | None = None
    trust_level: float | None = None
    is_archived: bool | None = None


def _parse_and_store(db: Session, doc: SourceDocument, content: bytes, mime: str | None, extension: str) -> None:
    doc.parse_status = ParseStatus.parsing.value
    db.flush()
    try:
        parser = get_parser(mime, extension)
        parsed = parser.parse(content)
        doc.raw_text = parsed.text
        doc.parsed_json = {
            "blocks": [{"type": b.type, "text": b.text, "locator": b.locator} for b in parsed.blocks],
            "metadata": parsed.metadata,
        }
        doc.parse_status = ParseStatus.done.value
        doc.parse_error = None
    except Exception as exc:  # noqa: BLE001 解析失败必须落库展示给用户，而不是 500
        doc.parse_status = ParseStatus.failed.value
        doc.parse_error = str(exc)
    db.flush()


def _serialize(doc: SourceDocument, fact_count: bool = True) -> dict:
    data = {
        "id": doc.id,
        "title": doc.title,
        "source_type": doc.source_type,
        "source_url": doc.source_url,
        "mime_type": doc.mime_type,
        "as_of": doc.as_of,
        "trust_level": doc.trust_level,
        "parse_status": doc.parse_status,
        "parse_error": doc.parse_error,
        "sha256": doc.sha256,
        "is_archived": doc.is_archived,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "fact_count": len(doc.facts) if doc.facts else 0,
    }
    return data


@router.post("/text", status_code=201)
def create_text_source(
    payload: TextSourceIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    doc = SourceDocument(
        title=payload.title,
        source_type="text",
        mime_type="text/plain",
        as_of=payload.as_of,
        trust_level=payload.trust_level,
        sha256=hashlib.sha256(payload.content.encode()).hexdigest(),
    )
    db.add(doc)
    db.flush()
    _parse_and_store(db, doc, payload.content.encode(), "text/plain", ".txt")
    db.commit()
    return _serialize(doc)


@router.post("/url", status_code=201)
def create_url_source(
    payload: UrlSourceIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    try:
        content, mime = safe_fetch(payload.url)
    except UnsafeUrlError as exc:
        raise HTTPException(400, f"URL 抓取被拒绝：{exc}")
    except Exception as exc:  # noqa: BLE001 网络错误统一转为 502 带原因
        raise HTTPException(502, f"URL 抓取失败：{exc}")

    doc = SourceDocument(
        title=payload.title or payload.url[:200],
        source_type="url",
        source_url=payload.url,
        mime_type=mime,
        as_of=payload.as_of,
        trust_level=payload.trust_level,
        sha256=hashlib.sha256(content).hexdigest(),
        metadata_json={"final_url": payload.url},
    )
    db.add(doc)
    db.flush()
    extension = ".html" if "html" in mime else ".txt"
    _parse_and_store(db, doc, content, mime, extension)
    db.commit()
    return _serialize(doc)


@router.post("/upload", status_code=201)
async def upload_source(
    file: UploadFile = File(...),
    as_of: str | None = None,
    trust_level: float = 0.8,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    # 扩展名与 MIME 双校验（STU-022）
    filename = file.filename or ""
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件类型 {extension}，允许：{sorted(ALLOWED_EXTENSIONS)}")

    from ..config import get_settings

    content = await file.read()
    if len(content) > get_settings().upload_max_bytes:
        raise HTTPException(413, "文件超过大小限制")
    if not content:
        raise HTTPException(400, "空文件")

    doc = SourceDocument(
        title=filename,
        source_type="file",
        original_uri=filename,
        mime_type=file.content_type,
        as_of=as_of,
        trust_level=trust_level,
        sha256=hashlib.sha256(content).hexdigest(),
    )
    db.add(doc)
    db.flush()
    _parse_and_store(db, doc, content, file.content_type, extension)
    db.commit()
    return _serialize(doc)


@router.get("")
def list_sources(
    source_type: str | None = None,
    parse_status: str | None = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(SourceDocument).order_by(SourceDocument.created_at.desc())
    if not include_archived:
        stmt = stmt.where(SourceDocument.is_archived.is_(False))
    if source_type:
        stmt = stmt.where(SourceDocument.source_type == source_type)
    if parse_status:
        stmt = stmt.where(SourceDocument.parse_status == parse_status)
    docs = list(db.scalars(stmt))
    return [_serialize(d) for d in docs]


@router.get("/{source_id}")
def get_source(source_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.get(SourceDocument, source_id)
    if not doc:
        raise HTTPException(404, "Source 不存在")
    data = _serialize(doc)
    data["raw_text"] = doc.raw_text
    data["parsed"] = doc.parsed_json
    data["facts"] = [
        {
            "id": f.id,
            "statement": f.statement,
            "subject": f.subject,
            "predicate": f.predicate,
            "value": (f.value_json or {}).get("value") if f.value_json else None,
            "unit": f.unit,
            "as_of": f.as_of,
            "confidence": f.confidence,
            "status": f.status,
            "source_locator": f.source_locator_json,
        }
        for f in doc.facts
    ]
    return data


@router.patch("/{source_id}")
def update_source(
    source_id: int,
    payload: SourceUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    doc = db.get(SourceDocument, source_id)
    if not doc:
        raise HTTPException(404, "Source 不存在")
    if payload.title is not None:
        doc.title = payload.title
    if payload.trust_level is not None:
        doc.trust_level = payload.trust_level
    if payload.is_archived is not None:
        doc.is_archived = payload.is_archived
    db.commit()
    return _serialize(doc)


@router.post("/{source_id}/extract-facts", status_code=201)
def extract_facts(
    source_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_editor),
):
    """抽取候选 Facts（STU-031）。重复调用幂等：清空旧候选后重抽。"""
    doc = db.get(SourceDocument, source_id)
    if not doc:
        raise HTTPException(404, "Source 不存在")
    if doc.parse_status != ParseStatus.done.value:
        raise HTTPException(409, f"Source 解析未完成（当前 {doc.parse_status}）")
    if not doc.parsed_json or not doc.raw_text:
        raise HTTPException(409, "Source 无可解析内容")

    from ..services.parsers import ParsedBlock, ParsedDocument

    blocks = [ParsedBlock(**b) for b in doc.parsed_json.get("blocks", [])]
    parsed = ParsedDocument(text=doc.raw_text, blocks=blocks, metadata=doc.parsed_json.get("metadata", {}))

    doc.facts.clear()
    db.flush()

    candidates = fact_extractor.extract_candidate_facts(parsed, doc.as_of)
    for c in candidates:
        db.add(
            Fact(
                source_document_id=doc.id,
                statement=c.statement,
                fact_type=c.fact_type,
                subject=c.subject,
                predicate=c.predicate,
                value_json={"value": c.value},
                unit=c.unit,
                as_of=c.as_of,
                confidence=min(c.confidence, doc.trust_level),
                source_locator_json=c.source_locator,
                created_by=user.email,
            )
        )
    db.add(AuditLog(event="facts.extracted", actor=user.email, entity_type="source_document", entity_id=str(doc.id),
                    detail_json={"count": len(candidates)}))
    db.commit()
    return {"source_id": doc.id, "candidates": len(candidates)}
