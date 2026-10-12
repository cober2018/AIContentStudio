"""Explicit adoption of exact existing-domain Stage results."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_editor
from ..models import User
from ..services.stage_contracts import StageContractError
from ..services.stage_domain_adoptions import accept_result
from ..services.stage_invocations import StageInvocationError
from .content_projects import StagePreviewRoute

router = APIRouter(
    prefix="/api/v1/content-projects/{project_id}/units/{unit_id}/creation-recipe/stages/{node_id}",
    tags=["creation-recipe-domains"], route_class=StagePreviewRoute,
)


class MediaRightsIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    confirmed: Literal[True]
    title: str = Field(min_length=1, max_length=255)
    license_code: str = Field(min_length=1, max_length=100)
    license_evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    public_use_allowed: bool
    model_use_allowed: bool
    commercial_use_allowed: bool
    attribution_text: str | None = Field(default=None, max_length=2000)


class StageResultAcceptanceIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    domain: Literal["media", "audio_asr", "variant", "professional", "checks", "human"]
    run_id: int = Field(ge=1)
    attempt_id: int = Field(ge=1)
    expected_output_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_resolution_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_context_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    adoption_key: str = Field(min_length=1, max_length=150, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
    expected_revision: int = Field(ge=0)
    decision: Literal["accepted", "accepted_with_edits"] = "accepted"
    note: str = Field(default="", max_length=2000)
    reason_tags: list[str] = Field(default_factory=list, max_length=10)
    task_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    candidate_index: int | None = Field(default=None, ge=0, le=3)
    expected_result_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    rights: MediaRightsIn | None = None
    payload: dict | None = None
    asset_refs: list[dict] | None = Field(default=None, max_length=100)
    evidence_refs: list[dict] | None = Field(default=None, max_length=100)
    package_id: int | None = Field(default=None, ge=1)
    execution_id: int | None = Field(default=None, ge=1)
    warning_dispositions: dict[str, str] | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def exact_domain_fields(self):
        choices = {
            "media": {"task_id", "candidate_index", "expected_result_hash", "rights"},
            "variant": {"payload", "asset_refs", "evidence_refs"},
            "professional": {"package_id", "execution_id"},
            "checks": {"warning_dispositions"}, "human": set(), "audio_asr": set(),
        }
        supplied = {key for key in set().union(*choices.values()) if getattr(self, key) is not None}
        allowed = choices[self.domain]
        required = (allowed - {"execution_id"} if self.domain == "professional" else
                    allowed - {"candidate_index"} if self.domain == "media" else
                    set() if self.domain == "checks" else allowed)
        if supplied - allowed or required - supplied:
            raise ValueError("stage_domain_choice_invalid")
        if self.domain != "variant" and self.decision != "accepted":
            raise ValueError("stage_domain_edits_unavailable")
        if self.domain in {"checks", "human", "audio_asr"} and self.expected_revision != 0:
            raise ValueError("stage_review_revision_invalid")
        if any(len(tag) > 80 for tag in self.reason_tags):
            raise ValueError("stage_feedback_bounds")
        return self


@router.post("/accept-result")
def accept_stage_result(project_id: int, unit_id: int, node_id: str, body: StageResultAcceptanceIn,
                        db: Session = Depends(get_db), user: User = Depends(require_editor)):
    try:
        return accept_result(db, project_id, unit_id, node_id, user, body.model_dump(exclude_none=True))
    except StageInvocationError as exc:
        raise HTTPException(exc.status_code, {"code": exc.code}) from exc
    except StageContractError as exc:
        raise HTTPException(422, {"code": str(exc)}) from exc
    except (ValueError, KeyError, TypeError):
        raise HTTPException(422, {"code": "stage_domain_adoption_invalid"}) from None
