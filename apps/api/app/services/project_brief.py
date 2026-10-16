"""Append-only CreativeBrief revisions."""

import hashlib
import json
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CreativeBriefRevision

BRIEF_FIELDS = (
    "objective", "primary_audience", "core_message", "angle", "required_evidence",
    "content_constraints", "identity_scope", "modality_scope", "channel_scope", "cta", "references",
)


class ProductSourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: int = Field(gt=0)
    checksum: str = Field(min_length=64, max_length=64)


class ProductMaterialRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_revision_id: int = Field(gt=0)
    content_hash: str = Field(min_length=64, max_length=64)
    categories: list[Literal["front", "side", "back", "detail", "dimensions", "real_product", "real_demo", "measurement", "comparison", "specification", "authorized_feedback", "ai_scene"]] = Field(default_factory=list, max_length=12)


class ProductClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=2000)
    source_id: int = Field(gt=0)
    fact_id: int | None = Field(default=None, gt=0)
    status: Literal["provided", "confirmed"] = "provided"


class ProductOffer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(default="", max_length=1000)
    checked_at: datetime | None = None
    valid_until: datetime | None = None
    sku: str | None = Field(default=None, max_length=300)
    currency: str | None = Field(default=None, max_length=3)
    original_price: Decimal | None = Field(default=None, max_digits=18, decimal_places=6, allow_inf_nan=False)
    sale_price: Decimal | None = Field(default=None, max_digits=18, decimal_places=6, allow_inf_nan=False)
    source_id: int | None = Field(default=None, gt=0)
    conditions: str | None = Field(default=None, max_length=2000)
    timezone: str | None = Field(default=None, max_length=100)
    promotion_status: str = "unavailable"
    promotion_issues: list[str] = Field(default_factory=list)
    savings: Decimal | None = None
    claimed_discount_percent: Decimal | None = None
    discount_percent: Decimal | None = None
    price_ratio: Decimal | None = None

    @model_validator(mode="before")
    @classmethod
    def preserve_discount_claim(cls, value):
        if isinstance(value, dict) and value.get("claimed_discount_percent") is None and value.get("discount_percent") is not None:
            try:
                original, sale = Decimal(str(value.get("original_price"))), Decimal(str(value.get("sale_price")))
                derived = ((original - sale) * 100 / original).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if Decimal(str(value["discount_percent"])) != derived:
                    value = {**value, "claimed_discount_percent": value["discount_percent"]}
            except (ArithmeticError, ValueError):
                value = {**value, "claimed_discount_percent": value["discount_percent"]}
        return value

    @model_validator(mode="after")
    def derive_promotion(self):
        # Missing or conflicting commercial facts disable only price animation.
        self.savings = self.discount_percent = self.price_ratio = None
        issues = []
        precision = {**dict.fromkeys(("CNY", "USD", "EUR", "GBP", "HKD", "TWD", "AUD", "CAD", "SGD", "CHF", "INR"), 2),
                     **dict.fromkeys(("JPY", "KRW", "VND"), 0), **dict.fromkeys(("BHD", "KWD", "OMR"), 3)}
        digits = precision.get(self.currency)
        if digits is None:
            issues.append("currency_required_or_unsupported")
        if self.sale_price is None:
            issues.append("sale_price_required")
        for price in (self.original_price, self.sale_price):
            if price is not None and (price < 0 or (digits is not None and price != price.quantize(Decimal(1).scaleb(-digits)))):
                issues.append("price_currency_precision_invalid")
        if self.source_id is None or self.checked_at is None or self.checked_at.tzinfo is None:
            issues.append("verified_source_and_check_time_required")
        if self.original_price is not None and self.sale_price is not None and self.original_price < self.sale_price:
            issues.append("original_price_less_than_sale_price")
        if self.valid_until is not None:
            if self.valid_until.tzinfo is None or not self.timezone:
                issues.append("deadline_timezone_required")
            else:
                try:
                    ZoneInfo(self.timezone)
                except (ZoneInfoNotFoundError, ValueError):
                    issues.append("deadline_timezone_invalid")
            if self.checked_at is not None and self.checked_at.tzinfo is not None and self.valid_until.tzinfo is not None and self.valid_until <= self.checked_at:
                issues.append("deadline_not_after_check_time")
        if self.claimed_discount_percent is not None:
            if self.original_price is None or self.original_price <= 0 or self.sale_price is None:
                issues.append("discount_claim_unverifiable")
            elif self.claimed_discount_percent != ((self.original_price - self.sale_price) * 100 / self.original_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):
                issues.append("discount_claim_conflict")
        self.promotion_issues = list(dict.fromkeys(issues))
        self.promotion_status = "unavailable" if issues else "price_verified"
        if not issues and self.original_price is not None and self.original_price > 0:
            self.savings = (self.original_price - self.sale_price).quantize(Decimal(1).scaleb(-digits))
            self.price_ratio = (self.sale_price / self.original_price).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            self.discount_percent = ((self.original_price - self.sale_price) * 100 / self.original_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return self


class ProductStyleRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact_id: int = Field(gt=0)
    revision_id: int = Field(gt=0)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class ProductContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=300)
    category: str = Field(default="", max_length=300)
    style_ref: ProductStyleRef | None = None
    production_stages: dict | None = None
    variant: str = Field(default="", max_length=1000)
    description: str = Field(default="", max_length=12000)
    url: str | None = Field(default=None, max_length=1000)
    claims: list[ProductClaim] = Field(default_factory=list, max_length=30)
    selling_points: list[str] = Field(default_factory=list, max_length=20)
    excluded_claims: list[str] = Field(default_factory=list, max_length=20)
    source_refs: list[ProductSourceRef] = Field(default_factory=list, max_length=30)
    material_refs: list[ProductMaterialRef] = Field(default_factory=list, max_length=30)
    offer: ProductOffer | None = None
    buyer_situation: str = Field(default="", max_length=2000)
    purchase_reason_evidence: str = Field(default="", max_length=2000)
    purchase_reason_source_ids: list[int] = Field(default_factory=list, max_length=30)
    purchase_reason_material_revision_ids: list[int] = Field(default_factory=list, max_length=30)
    main_objection: str = Field(default="", max_length=2000)
    objection_answer: str = Field(default="", max_length=2000)
    unsuitable_for: str = Field(default="", max_length=2000)
    seller_advantage: str = Field(default="", max_length=2000)
    target_duration_seconds: int | None = Field(default=None, gt=0, le=3600)
    expression_test: Literal["scene", "demo", "compare", "faq", "selection"] | None = None


    @model_validator(mode="after")
    def validate_explicit_stages(self):
        if self.production_stages is not None:
            from .studio_creative_catalog import validate_production_stages

            validate_production_stages(self.production_stages)
        return self


def validate_product_context(db, value, *, user=None, project_id=None):
    from ..models import Fact, MaterialRevision, SourceDocument
    from .discovery_search import canonical_url

    if value is None:
        return None
    data = ProductContext.model_validate(value).model_dump(mode="json")
    if any(len(v) > 2000 for v in data["selling_points"] + data["excluded_claims"]):
        raise HTTPException(422, "商品描述过长")
    if data.get("style_ref"):
        from ..models import CapabilityArtifact, CapabilityArtifactRevision

        ref = data["style_ref"]
        selected = db.get(CapabilityArtifact, ref["artifact_id"])
        revision = db.get(CapabilityArtifactRevision, ref["revision_id"])
        if (not selected or not revision or revision.artifact_id != selected.id
                or revision.content_hash != ref["content_hash"] or selected.status not in {"saved", "pinned"}
                or revision.content_json.get("content_schema") != "product.presentation-style.v1"):
            raise HTTPException(409, "商品风格版本不可用")
        if user is not None:
            from .form_assistance import method_reference

            method_reference(db, user, ref, project_id, context=data)
        categories = revision.content_json.get("categories", [])
        if categories and data["category"] not in categories:
            raise HTTPException(422, "当前品类不在已选风格适用范围内")
    if data["url"]:
        try:
            data["url"] = canonical_url(data["url"])
        except ValueError:
            raise HTTPException(422, "商品链接格式无效，请使用公开HTTP或HTTPS链接") from None
    sources = {}
    for ref in data["source_refs"]:
        source = db.get(SourceDocument, ref["source_id"])
        if not source or source.is_archived or source.sha256 != ref["checksum"]:
            raise HTTPException(409, "商品来源不存在、已归档或版本已变化")
        sources[source.id] = source
    if data["offer"] and data["offer"]["source_id"] not in sources:
        data["offer"]["promotion_status"] = "unavailable"
        data["offer"]["promotion_issues"].append("offer_source_not_selected")
        for key in ("savings", "discount_percent", "price_ratio"):
            data["offer"][key] = None
    for claim in data["claims"]:
        if claim["source_id"] not in sources:
            raise HTTPException(422, "商品说法必须引用已选择的来源版本")
        if claim["status"] == "confirmed":
            fact = db.get(Fact, claim["fact_id"]) if claim["fact_id"] else None
            if not fact or fact.source_document_id != claim["source_id"] or fact.status != "confirmed" or fact.statement != claim["text"]:
                raise HTTPException(422, "商品确认状态必须来自已有确认事实")
    for ref in data["material_refs"]:
        revision = db.get(MaterialRevision, ref["material_revision_id"])
        if (not revision or not revision.material or revision.material.status != "active"
                or revision.status in {"revoked", "archived"} or revision.content_hash != ref["content_hash"]):
            raise HTTPException(409, "商品素材不存在、已撤销或版本已变化")
    if not set(data["purchase_reason_source_ids"]).issubset(sources):
        raise HTTPException(422, "购买理由依据必须引用已选择的来源版本")
    if not set(data["purchase_reason_material_revision_ids"]).issubset({r["material_revision_id"] for r in data["material_refs"]}):
        raise HTTPException(422, "购买理由依据必须引用已选择的素材版本")
    return data


def current_brief(db: Session, project_id: int) -> CreativeBriefRevision | None:
    return db.scalar(select(CreativeBriefRevision).where(CreativeBriefRevision.project_id == project_id).order_by(CreativeBriefRevision.revision_no.desc()).limit(1))


def checksum_brief(payload: dict) -> str:
    canonical = {key: payload.get(key) for key in BRIEF_FIELDS}
    if payload.get("product_context"):
        canonical["product_context"] = payload["product_context"]
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def serialize_brief(row: CreativeBriefRevision) -> dict:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "revision_no": row.revision_no,
        "parent_revision_id": row.parent_revision_id,
        "objective": row.objective,
        "primary_audience": row.primary_audience,
        "core_message": row.core_message,
        "angle": row.angle,
        "required_evidence": row.required_evidence_json,
        "content_constraints": row.content_constraints_json,
        "identity_scope": row.identity_scope_json,
        "modality_scope": row.modality_scope_json,
        "channel_scope": row.channel_scope_json,
        "cta": row.cta,
        "references": row.references_json,
        **({"product_context": row.product_context_json} if row.product_context_json is not None else {}),
        "checksum": row.checksum,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
