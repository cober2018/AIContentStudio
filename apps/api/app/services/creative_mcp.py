"""Restricted MCP projections and delegation to the existing creative domain."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import threading
import unicodedata
from dataclasses import dataclass, field
from typing import Annotated, Literal
from urllib.parse import unquote

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from ..models import User
from . import (
    agent_review,
    capability_memory,
    channel_variants,
    content_masters,
    creative_executions,
    creative_packages,
)
from .creative_contracts import bounded_json
from .project_brief import current_brief
from .project_evidence import current_boundary

log = logging.getLogger(__name__)
PROTOCOL_VERSION = "2025-11-25"
MAX_REQUEST_BYTES = 256 * 1024
MAX_ARGUMENT_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 24
ID = Annotated[int, Field(ge=1, le=2**53 - 1)]
IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$"
HASH = r"^[0-9a-f]{64}$"


class MCPError(Exception):
    def __init__(self, code: str, category: str, *, status: int = 400, rpc_code: int = -32600):
        self.code, self.category, self.status, self.rpc_code = code, category, status, rpc_code


@dataclass(frozen=True)
class Binding:
    owner_id: int
    fingerprint: str
    token: str = field(repr=False)


def authenticate(authorization: str | None) -> Binding:
    token = os.environ.get("AICS_CREATIVE_MCP_TOKEN", "")
    owner = os.environ.get("AICS_CREATIVE_MCP_OWNER_USER_ID", "")
    if (not re.fullmatch(r"[A-Za-z0-9._~+/-]{32,512}", token)
            or not re.fullmatch(r"[1-9][0-9]{0,15}", owner) or int(owner) > 2**53 - 1):
        raise MCPError("creative_mcp_not_configured", "unavailable", status=503, rpc_code=-32000)
    candidate = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
    # Hash both sides so compare_digest always compares fixed-length values.
    if not hmac.compare_digest(hashlib.sha256(candidate.encode()).digest(), hashlib.sha256(token.encode()).digest()):
        raise MCPError("creative_mcp_unauthorized", "unauthorized", status=401, rpc_code=-32000)
    fingerprint = hashlib.sha256(f"{owner}:{token}".encode()).hexdigest()
    return Binding(int(owner), fingerprint, token)


def resolve_owner(db: Session, binding: Binding) -> User:
    user = db.scalar(select(User).where(User.id == binding.owner_id).execution_options(populate_existing=True))
    if user is None or not user.is_active or user.role not in {"editor", "admin"}:
        raise MCPError("creative_mcp_owner_unavailable", "forbidden", status=403, rpc_code=-32000)
    return user


@dataclass
class Lifecycle:
    """One credential's process readiness; no transport sessions or business state."""

    fingerprint: str | None = None
    phase: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def check(self, binding: Binding, method: str) -> None:
        with self.lock:
            if self.fingerprint != binding.fingerprint:
                self.fingerprint, self.phase = binding.fingerprint, 0
            if method == "initialize":
                self.phase = 1
            elif method == "notifications/initialized":
                if self.phase == 0:
                    raise MCPError("creative_mcp_initialize_required", "lifecycle", rpc_code=-32002)
                self.phase = 2
            elif method != "ping" and self.phase != 2:
                raise MCPError("creative_mcp_initialized_required", "lifecycle", rpc_code=-32002)


class Input(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Scope(Input):
    project_id: ID
    unit_id: ID


class ContextInput(Scope):
    variant_key: str | None = Field(default=None, min_length=1, max_length=150, pattern=IDENTIFIER)


class PackageInput(Scope):
    package_id: ID


class ExecutionInput(Scope):
    execution_id: ID


class CapabilityDiscoveryInput(Scope):
    execution_id: ID | None = None
    kind: Literal["prompt_skill", "recipe", "creative_pattern", "preference", "execution_template", "tool"] | None = None
    q: str | None = Field(default=None, max_length=200)
    tag: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=20, ge=1, le=50)
    offset: int = Field(default=0, ge=0, le=10000)


class CapabilityUseInput(Scope):
    execution_id: ID | None = None
    artifact_id: ID | None = None
    artifact_revision_id: ID | None = None
    stage: str | None = Field(default=None, min_length=1, max_length=50, pattern=IDENTIFIER)
    expected_revision: ID | None = None
    executor_kind: str | None = Field(default=None, min_length=1, max_length=30, pattern=IDENTIFIER)
    executor_key: str | None = Field(default=None, min_length=1, max_length=150, pattern=IDENTIFIER)
    executor_version: str | None = Field(default=None, min_length=1, max_length=50, pattern=IDENTIFIER)
    arguments: dict = Field(default_factory=dict, max_length=30)


class MutationInput(ExecutionInput):
    expected_revision: ID
    executor_kind: str = Field(min_length=1, max_length=30, pattern=IDENTIFIER)
    executor_key: str = Field(min_length=1, max_length=150, pattern=IDENTIFIER)
    executor_version: str = Field(min_length=1, max_length=50, pattern=IDENTIFIER)


class ClaimInput(MutationInput):
    metadata: dict = Field(default_factory=dict, max_length=20)


class ReportInput(ClaimInput):
    dispatch_certainty: Literal["not_dispatched", "possibly_dispatched", "confirmed_dispatched"] | None = None
    safe_reason: Literal["executor_blocked", "input_unavailable", "validation_failed", "dispatch_uncertain",
                         "reconciliation_needed", "executor_failed"] | None = None


class CheckpointInput(MutationInput):
    checkpoint: dict = Field(max_length=20)


class MaterializeInput(MutationInput):
    material_revision_ids: list[ID] | None = Field(default=None, max_length=100)


class OutputInput(MutationInput):
    role_id: str = Field(min_length=1, max_length=100, pattern=IDENTIFIER)
    output_index: int = Field(ge=1, le=20)
    attempt_no: int | None = Field(default=None, ge=1, le=20)
    relative_path: str | None = Field(default=None, min_length=1, max_length=500,
                                      pattern=r"^outputs/[A-Za-z0-9][A-Za-z0-9_.-]{0,149}$")
    path: str | None = Field(default=None, min_length=2, max_length=500, pattern=r"^/")
    mime_type: str = Field(min_length=3, max_length=100, pattern=r"^[a-z0-9.+-]+/[a-z0-9.+-]+$")
    content_hash: str | None = Field(default=None, pattern=HASH)
    metadata: dict = Field(default_factory=dict, max_length=20)


class ReconcileInput(MutationInput):
    observation_hash: str = Field(pattern=HASH)
    summary: str = Field(min_length=1, max_length=2000)
    resolution: Literal["in_progress", "blocked", "result_ready", "failed_before_dispatch"]
    dispatch_certainty: Literal["not_dispatched", "confirmed_dispatched"]
    recovery: dict | None = Field(default=None, max_length=20)


class StagesInput(Scope):
    run_id: ID | None = None


class StageInput(Scope):
    run_id: ID
    node_id: str = Field(min_length=1, max_length=100, pattern=IDENTIFIER)


class StagePreviewInput(StageInput):
    instruction: str | None = Field(default=None, min_length=1, max_length=4000)


class StageRunInput(StagePreviewInput):
    expected_resolution_hash: str = Field(pattern=HASH)
    invocation_key: str = Field(min_length=1, max_length=200, pattern=IDENTIFIER)


class StageResultInput(StageInput):
    attempt_id: ID | None = None
    invocation_key: str | None = Field(default=None, min_length=1, max_length=200, pattern=IDENTIFIER)


class StageDecisionInput(StageResultInput):
    wait_seconds: int = Field(default=0, ge=0, le=agent_review.MAX_WAIT_SECONDS)


class MatchShotInput(Input):
    id: str = Field(min_length=1, max_length=100)
    label: str | None = Field(default=None, max_length=120)
    text: str = Field(min_length=1, max_length=4000)


class MatchStartInput(Input):
    scope: Literal["script", "shots"]
    text: str | None = Field(default=None, min_length=1, max_length=20000)
    shots: list[MatchShotInput] | None = Field(default=None, min_length=1, max_length=40)
    title: str | None = Field(default=None, max_length=300)
    project_id: ID | None = None
    unit_id: ID | None = None
    aspect: Literal["9:16", "16:9", "3:4", "1:1", "4:3"] = "9:16"
    min_short_side: Literal[540, 720, 1080] = 720
    strict_aspect: bool = False
    providers: list[str] | None = Field(default=None, max_length=10)


class ShotSlotsInput(Scope):
    pass


class CraftSkillInput(Scope):
    skill: str = Field(min_length=1, max_length=150, pattern=r"^(craft-ae|craft-resolve|studio\.[a-z0-9_.-]+@[1-9][0-9]{0,5})$")
    entry: str | None = Field(default=None, min_length=1, max_length=200)


class TemplateListInput(Input):
    pass


class TemplateRenderInput(Scope):
    template: str = Field(min_length=1, max_length=60)
    version: str = Field(min_length=1, max_length=20)
    content: dict[str, str | int | float]
    images: dict[str, ID] | None = None
    duration_ms: int | None = Field(default=None, ge=1, le=600000)
    aspect: Literal["9:16", "16:9"] = "9:16"


class MatchReadInput(Input):
    run_id: ID
    wait_seconds: int = Field(default=0, ge=0, le=agent_review.MAX_WAIT_SECONDS)


class VideoDraftInput(Scope):
    payload: dict
    note: str | None = Field(default=None, max_length=2000)


class VideoMaterialsInput(Scope):
    picks: dict[Annotated[str, Field(min_length=1, max_length=100)], ID] = Field(default_factory=dict, max_length=100)
    music: ID | None = None
    silent_durations: dict[Annotated[str, Field(min_length=1, max_length=100)], Annotated[int, Field(ge=1000, le=15000)]] = Field(default_factory=dict, max_length=10)


class VideoImageInput(Scope):
    prompt: str = Field(min_length=1, max_length=2000)
    label: str = Field(min_length=1, max_length=120)
    aspect_ratio: Literal["1:1", "4:3", "3:4", "16:9", "9:16"] | None = None


class VoiceoverInput(Scope):
    lines: list[Annotated[str, Field(min_length=1, max_length=100, pattern=IDENTIFIER)]] | None = Field(default=None, min_length=1, max_length=20)


class MaterialFolderInput(Scope):
    path: str = Field(min_length=1, max_length=1000)


class ShotInput(Scope):
    shot_id: str = Field(min_length=1, max_length=100, pattern=IDENTIFIER)


class ShotModeInput(ShotInput):
    mode: Literal["manual", "auto"]


class ShotFrameInput(ShotInput):
    material_revision_id: ID | None = None


class ShotImageInput(ShotInput):
    prompt: str = Field(min_length=1, max_length=2000)
    extra_reference_revision_id: ID | None = None
    as_first_frame: bool = True


class FactDraftItem(Input):
    statement: str = Field(min_length=1, max_length=500)
    kind: Literal["fact", "event", "quote", "opinion"]
    template: str = Field(min_length=1, max_length=30, pattern=IDENTIFIER)
    source_url: str = Field(min_length=8, max_length=2000, pattern=r"^https?://")
    source_title: str | None = Field(default=None, max_length=300)
    excerpt: str = Field(min_length=1, max_length=1000)
    source_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    attribution: str | None = Field(default=None, max_length=200)


class FactsInput(Scope):
    templates: list[Annotated[str, Field(min_length=1, max_length=30, pattern=IDENTIFIER)]] | None = Field(default=None, max_length=7)
    items: list[FactDraftItem] = Field(min_length=1, max_length=60)


class PublishCopyInput(Scope):
    # Upper bounds only; the work's own format and limits are checked when saving.
    title: str = Field(default="", max_length=30)
    hashtags: list[str] = Field(default_factory=list, max_length=5)
    cover_text: str = Field(default="", max_length=12)
    interaction: str = Field(default="", max_length=60)
    description: str = Field(default="", max_length=300)
    lead: str = Field(default="", max_length=120)


class VideoCandidateInput(Scope):
    run_id: ID
    segment_id: str = Field(min_length=1, max_length=100)
    candidate_id: str = Field(min_length=1, max_length=200)


class VideoCommonInput(Scope):
    material_revision_id: ID


class WebSearchInput(Scope):
    query: str | None = Field(default=None, min_length=2, max_length=120)


class WebSearchReadInput(Scope):
    search_id: ID


class LessonInput(Scope):
    title: str = Field(min_length=1, max_length=200)
    rule: str = Field(min_length=1, max_length=2000)
    scope: str = Field(min_length=1, max_length=200)
    record_ids: list[ID] = Field(default_factory=list, max_length=50)
    same_as_lesson_id: ID | None = None


class ArticleDraftInput(Scope):
    payload: dict
    note: str | None = Field(default=None, max_length=2000)


class ReviewIssue(Input):
    severity: Annotated[str, Field(pattern=r"^(warning|blocker)$")]
    span: str = Field(default="", max_length=120)
    reason: str = Field(min_length=1, max_length=500)


class ReviewSubmitInput(Scope):
    master_id: ID
    purpose: Annotated[str, Field(min_length=1, max_length=40, pattern=IDENTIFIER)]
    input_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    model: str = Field(min_length=1, max_length=120)
    issues: list[ReviewIssue] = Field(default_factory=list, max_length=50)


class WarningJudgmentInput(Scope):
    check_id: ID
    input_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    model: str = Field(min_length=1, max_length=120)
    verdict: Annotated[str, Field(pattern=r"^(accept|reject)$")]
    reason: str = Field(min_length=1, max_length=1000)


class ReferenceVideoInput(Scope):
    material_revision_id: ID


class TimelineItem(Input):
    start_ms: int = Field(ge=0, le=600_000)
    end_ms: int = Field(ge=1, le=600_000)
    speech: str = Field(default="", max_length=600)
    picture: str = Field(default="", max_length=600)
    overlays: str = Field(default="", max_length=600)
    purpose: str = Field(default="", max_length=600)


class ShootItem(Input):
    shot_id: str = Field(default="", max_length=100)
    what: str = Field(min_length=1, max_length=400)
    who: str = Field(default="", max_length=400)
    framing: str = Field(default="", max_length=400)
    camera: str = Field(default="", max_length=400)
    seconds: float = Field(default=0, ge=0, le=600)
    notes: str = Field(default="", max_length=400)


class ReferenceBreakdownInput(Scope):
    analysis: str = Field(min_length=1, max_length=6000)
    timeline: list[TimelineItem] = Field(min_length=1, max_length=80)
    shot_list: list[ShootItem] = Field(default_factory=list, max_length=40)
    brand_material: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(default_factory=list, max_length=20)


class StoryboardGridInput(Scope):
    group_id: str = Field(min_length=1, max_length=100, pattern=IDENTIFIER)
    reference_revision_id: ID | None = None


class VideoEditInput(Scope):
    phase: Literal["rough_cut", "final"]
    ae_shot_ids: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(default_factory=list, max_length=15)
    alpha_shot_ids: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(default_factory=list, max_length=15)
    notes: str | None = Field(default=None, max_length=2000)


class SubjectDraftInput(Input):
    subject_id: ID | None = None
    subject: dict


class SubjectRefInput(Input):
    subject_id: ID


class LibraryInput(Input):
    subject_id: ID
    library: dict


class OpenProjectsInput(Input):
    subject_id: ID
    items: list[dict] = Field(min_length=1, max_length=5)


class SearchProjectInput(Input):
    project_id: ID


class VersionTemplateInput(Scope):
    channel_id: str = Field(min_length=1, max_length=100, pattern=IDENTIFIER)
    content_form: str = Field(min_length=1, max_length=100, pattern=IDENTIFIER)


class VersionInput(VersionTemplateInput):
    payload: dict


class EmptyInput(Input):
    pass


class MediaTranscriptionInput(Input):
    path: str = Field(min_length=1, max_length=2000)
    output_dir: str | None = Field(default=None, min_length=1, max_length=2000)


class MediaTranscriptionReadInput(Input):
    job_id: str = Field(pattern=r"^[0-9a-f]{12}$")


class TopicLink(Input):
    url: str = Field(min_length=1, max_length=1000, pattern=r"^https?://")
    title: str | None = Field(default=None, max_length=300)


class ProjectCreateInput(Input):
    title: str = Field(min_length=1, max_length=300)
    objective: str = Field(min_length=1, max_length=2000)
    rationale: str = Field(min_length=1, max_length=2000)
    core_message: str | None = Field(default=None, max_length=1000)
    angle: str | None = Field(default=None, max_length=1000)
    links: list[TopicLink] = Field(default_factory=list, max_length=10)


class UnitCreateInput(Input):
    project_id: ID
    persona_id: ID
    modality: Literal["video", "graphic", "text"]
    title: str = Field(min_length=1, max_length=300)
    channel_id: str | None = Field(default=None, min_length=1, max_length=100, pattern=IDENTIFIER)



class AccountImportSource(Input):
    kind: Literal["screenshot", "copied_text", "export_file"]
    name: str = Field(min_length=1, max_length=300)
    checksum: str = Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9:_-]+$")


class AccountMetricRow(Input):
    title: str = Field(min_length=1, max_length=500)
    published_at: str = Field(min_length=10, max_length=40)
    content_form: str | None = Field(default=None, min_length=1, max_length=50)
    url: str | None = Field(default=None, max_length=2000, pattern=r"^https?://")
    metrics: dict[Annotated[str, Field(min_length=1, max_length=60)], Annotated[float, Field(allow_inf_nan=False)]] = Field(min_length=1, max_length=20)
    uncertain: list[Annotated[str, Field(min_length=1, max_length=60)]] = Field(default_factory=list, max_length=20)


class AccountMetricsInput(Input):
    account_id: ID
    source: AccountImportSource
    rows: list[AccountMetricRow] = Field(min_length=1, max_length=200)


def _metric_key_text() -> str:
    from .account_metrics_import import PLATFORM_METRICS

    return "; ".join(f"{channel}: " + ", ".join(f"{key}({label})" for key, (label, _unit) in metrics.items())
                     for channel, metrics in PLATFORM_METRICS.items())

TOOLS = {
    "start_media_transcription": (MediaTranscriptionInput, "Small tool, not tied to any project: transcribe one local audio or video file (full path on this Mac or the material drive) with the platform's local speech recognition (no network, no cost). Writes one folder with <name>.txt (plain text), <name>.srt (subtitles) and <name>.md (notes split at scene changes, each part with its screenshot in images/ by relative path; audio gets text only). Default folder: 自媒体素材/AIContentStudio/转写/<name>/ on the material drive; output_dir (full path) writes elsewhere; earlier results are never overwritten. Runs in the background one job at a time and returns job_id at once; read it with get_media_transcription.", False),
    "get_media_transcription": (MediaTranscriptionReadInput, "Read a job started with start_media_transcription: status (queued / running / done / failed with reason), output folder, files (txt, srt, md, images), duration, cue and screenshot counts and the opening text. While queued or running, call again after a while.", True),
    "list_personas": (EmptyInput, "Start of a self-sourced topic: read the owner's active personas (id, name, positioning) and the channels a work can target. A project takes no persona; each work picks one.", True),
    "create_project": (ProjectCreateInput, "Create a content project from a topic you researched yourself, with revision 1 of its brief. rationale (why this topic, now) is required; links are optional because a topic drawn from many sources may have no single source. Then call create_unit. Not for product works.", False),
    "create_unit": (UnitCreateInput, "Create a work in a project for one persona (video, graphic or text; channel optional, from list_personas). Returns unit_id; continue with the normal flow, e.g. get_video_brief, where the 导演稿, 小样 and 成片 stops wait for the user.", False),
    "list_accounts": (EmptyInput, "Before importing account data: list the owner's active platform accounts (id, name, platform channel and label, persona id and name, whether the platform accepts imports) and the metric keys each platform accepts.", True),
    "import_account_metrics": (AccountMetricsInput, "Import one account's works data that you read yourself from the user's screenshots, copied text or platform export (the files are never uploaded). FIRST show the extracted table to the user in chat and get their OK; only then call this. Never guess a number you cannot read clearly: leave it out or keep your best reading and list its key in uncertain. Rates are 0–1 fractions (23.18% -> 0.2318), durations in seconds, counts as plain numbers (1.2万 -> 12000). published_at as shown on the platform, YYYY-MM-DD HH:MM[:SS], China time unless it carries an offset. source.checksum is the file's sha256 (or of the copied text); the same source for the same account is skipped. At most 200 rows per call: split a bigger table and suffix the checksum with :part2, :part3. Metric keys per platform, anything else rejects the whole import: " + _metric_key_text() + ". Works match by account + title + publish time, otherwise new external works are created; a metric imported again the same day replaces that day's value. Returns created / updated / skipped counts and the 效果复盘 batch link, where the user can undo the whole batch.", False),
    "list_promotion_subjects": (EmptyInput, "搜索推广 start: list promotion subjects (推广对象) with their confirmed version and whether a draft waits for the person to confirm. Only a confirmed version can be used.", True),
    "save_promotion_subject_draft": (SubjectDraftInput, "Draft or redraft a promotion subject from the material the user gave (name, links, files) and your own research. subject = {name, category_id or proposed_category {top_key: physical|digital|service|org, name}, audiences [individual|business|government], brand, url, description, facts [{text, url, excerpt, source}], brand_statement, banned_words}. Every fact needs the page url and an exact excerpt from it: the platform opens the link, drops facts whose excerpt is not there (returned in rejected_facts) and marks unreachable pages for a manual check. Saves a DRAFT; then STOP and tell the user to confirm it on the page — you cannot confirm it.", False),
    "get_search_subject": (SubjectRefInput, "Read one promotion subject: confirmed and draft versions, the question library with each question's coverage (none / in_progress / done), its projects, category hints and the genre list.", True),
    "save_question_library": (LibraryInput, "Save a new version of the subject's question library (needs a confirmed subject). library = {questions [{id (keep existing ids), text, intent, priority 1-3, source_url (a search result page; leave empty only when inferred)}], keywords {primary, long_tail, brand}}. No confirmation needed.", False),
    "open_search_projects": (OpenProjectsInput, "Open up to 5 promotion projects, one per question: items [{question_id, forms [text|graphic|video], tone, reader_level, genre (definition|buying-guide|comparison|shortlist|how-to|price-spec|case-study|faq), writer (external|platform), title}]. Questions already in progress or done are skipped. Each project gets a core text work plus derived graphic / video works; facts are frozen at this moment.", False),
    "get_search_project": (SearchProjectInput, "Read a promotion project: question, settings, each work's role / modality / chain state, its platform versions and the person's review decisions.", True),
    "adopt_search_draft": (Scope, "搜索推广 only: after your saved draft passes its checks (and you judged any warnings), adopt it yourself; for a graphic piece call it again once its images are rendered and you checked them. Videos follow the video chain, where the person reviews.", False),
    "get_search_version_template": (VersionTemplateInput, "The platform's mechanical adaptation of an adopted 搜索推广 work for one platform (e.g. zhihu/article, toutiao/article, wechat/article), as the payload format to rewrite, plus titles already used in the project.", True),
    "save_search_version": (VersionInput, "Save your rewritten platform version (new angle and title for that platform's readers, same facts and brand wording); a title used by another version is refused. Runs its checks and returns them.", False),
    "submit_search_batch": (SearchProjectInput, "Send every new platform version of the project to the person's batch review page; versions whose checks fail are listed in blocked. Then STOP until the person decides; read the result with get_search_review.", False),
    "get_search_review": (SearchProjectInput, "Read the person's decision on each platform version: approved ones are handed off; changes_requested ones carry a comment to revise, then save_search_version and submit_search_batch again.", True),
    "get_context": (ContextInput, "Read current owned unit context and content metadata.", True),
    "get_package": (PackageInput, "Read an exact frozen package, including its authorized input manifest.", True),
    "get_execution": (ExecutionInput, "Read exact execution state, contract, counts and staged output metadata.", True),
    "find_capabilities": (CapabilityDiscoveryInput, "Read every applicable saved/pinned method with exact scope/revision. Ordering is not automatic selection.", True),
    "use_capability": (CapabilityUseInput, "Render an exact applicable capability, or supply stage plus execution_id, exact executor and expected_revision to load only that frozen production stage and record delivery. No automatic skills or quality acceptance.", False),
    "claim_execution": (ClaimInput, "Claim an already prepared current execution with its exact executor and CAS.", False),
    "start_execution": (ClaimInput, "Start a claimed current execution; possible dispatch cannot be auto-retried.", False),
    "materialize_inputs": (MaterializeInput, "Reserve only authorized exact package inputs. Video-chain edit tasks get each input's original absolute path on the drive (use it read-only, never copy it; proxy_path too when the 代理素材 switch is on: edit with the proxy, export from the original), plus work_dir (<项目>/工作/<作品>/任务<N>/ for renders, AE shots, Resolve / AE projects, manifest) and export_dir (导出/小样 or 导出/成片). Other executors get inputs/<name> in their private work root.", False),
    "report_progress": (ReportInput, "Record safe progress metadata through the existing transition/CAS service.", False),
    "report_blocker": (ReportInput, "Record a proven blocker; possible side effects require Unknown reconciliation.", False),
    "report_checkpoint": (CheckpointInput, "Record a bounded checkpoint through the shared execution transition.", False),
    "submit_output": (OutputInput, "Stage one output; never accept or bind it to content. Video-chain edit tasks give path: the absolute path of the file where you exported it (rough_cut / final in export_dir, every other role in work_dir; no shortcuts); the platform checks and registers it in place without copying, so do not move or change it afterwards. Other executors give relative_path outputs/<filename>. A rough_cut / final may carry metadata.shot_sources: a JSON string of [{\"shot_id\",\"material_revision_id\",\"source_in_ms\"}], one per live-picture shot, source_in_ms being the clip's source in-point on the Resolve timeline; the platform compares brightness with the source at that moment. A cover (and cover_vertical / cover_43 on landscape 成片 tasks) may be submitted again before the task is accepted (the newest is shown); every other role is final once submitted.", False),
    "mark_unknown": (ReportInput, "Record dispatch uncertainty without resending or starting another execution.", False),
    "reconcile_unknown": (ReconcileInput, "Reconcile Unknown using an observation hash/summary and explicit certainty.", False),
    "request_human_review": (MutationInput, "Record a human-review request for result_ready; cannot accept outputs.", False),
    "get_stages": (StagesInput, "Read the unit's production stages, their status and the current run, with the platform review URL.", True),
    "start_run": (Scope, "Start a new production run for the unit (e.g. after an Unknown attempt); never accepts anything.", False),
    "preview_stage": (StagePreviewInput, "Check whether a stage is ready and get its exact resolution hash; instruction is the only tunable field.", True),
    "run_stage": (StageRunInput, "Run one stage once with the previewed resolution hash; options then wait for the user on the platform.", False),
    "get_stage_result": (StageResultInput, "Read a stage attempt's options as excerpts, its quality and the review URL to send the user to.", True),
    "get_stage_decision": (StageDecisionInput, "Read the user's decision on an attempt (waiting_for_you/accepted/accepted_with_edits/rejected/rerun_requested/commented) with note; wait_seconds waits up to 25s.", True),
    "start_material_match": (MatchStartInput, "Search own and open libraries for a script or shots; the user picks or rejects on the platform.", False),
    "get_material_match": (MatchReadInput, "Read a material search with the user's picks and rejections per segment; wait_seconds returns early on any change.", True),
    "get_craft_skill": (CraftSkillInput, "Read a platform skill for this work. craft-resolve (DaVinci Resolve edit and finishing) and craft-ae (After Effects templates and components) are always readable: read the index first, then only the entry you need. A studio.* writing skill (scripts, copy, shot plans) is readable only when the brief's platform_skills lists it; when the user switched writing skills off the platform refuses with platform_skills_disabled and you write on your own.", True),
    "list_ae_templates": (TemplateListInput, "List AE template manifests: category, use, fields, images, duration range, aspects (9:16 project, landscape in variants), preview_files, fonts and status (ready after two checked renders, else draft; do not auto-use drafts). Choose templates yourself by shot content; when the user explicitly names an effect while fine-tuning, use that template, and tell the user first if it lacks the film's aspect or is not ready.", True),
    "render_ae_template": (TemplateRenderInput, "Render one AE template version with content (and optional project image revisions) through local aerender into a new candidate video material of the project, in the film's aspect (9:16 default, 16:9 when the template has a landscape variant; never stretched). Never binds it to a shot.", False),
    "start_material_autofill": (ShotSlotsInput, "Fill every empty storyboard row: licensed stock picked when eligible, else a ready AE template rendered from the row, else a gap with the reason. Never replaces the user's picks or saves the master; read progress with get_material_match and the result with get_shot_slots.", False),
    "get_video_brief": (Scope, "Video chain step 0: project, brief, facts, source article text, voice settings, library materials (外部 / 通用 / this project, with folder and duration), the current video master payload and the chain state. You lead the whole video; the platform calls no model. When `search` is present this is a 搜索推广 work: the script answers search.question and cites only search.facts.", True),
    "save_director_draft": (VideoDraftInput, "Save a full video.master.v2 payload as the new 导演稿: shots with board {message, visual, camera, speaker, sound, notes, material_request; product works may add camera_presets (≤2 motion-library ids), look, intensity, chain_from_previous, character; any work may add source_kind (shoot | product_image | generated | ae_template | library: where the picture comes from, shoot shots make the shooting list) and attitude (the person's attitude and who they speak to, written with studio.video.prompt-direction; it leads the video prompt); dub_persona (a persona name or id: only that shot's line is voiced, in that persona's own voice, for live-sound videos with a few voice-over shots)} and script.blocks. Optional voice.pronunciation: up to 50 strings like \"去重/(qu4)(chong2)\" (the words as written, then one bracket of pinyin with tone number per character) for polyphonic words MiniMax misreads; the line text stays as written. Optional spoken-audio track: at most one timeline track with kind dialogue, items {id, order, material_revision_id, trim_start_ms, trim_end_ms, start_ms, end_ms, script_block_id?, speed_percent?} = play that span of the clip at that time on the cut, for that line; speed_percent (50–200, default 100) plays it faster or slower, so trim length = placement length × speed_percent / 100 — keep it when re-saving, the user set it; segments may cross shot boundaries, must not overlap, and trimmed length must equal placed length × speed_percent / 100 (no shot_id); the edit lays the voice from it while pictures still cut per shot, without it each shot keeps its own sound. material_request says what footage the shot needs (must show, shot size, length, real footage or graphic, orientation). A saved 导演稿 is adopted at once (the user may still send it back later): go on to materials without waiting.", False),
    "submit_video_materials": (Scope, "Before the work's first 小样: after every shot has its material, or for shots to be generated a first frame and a mode (set_shot_video_mode; manual shots get their prompts), hand the materials to the user and STOP. Send the user review_url. Wait with get_video_decision for 素材 approval (then generate the auto clips, voice and cut the 小样) or notes (rework the materials and submit again). Only once per work: after the first 小样 there is no materials stop.", False),
    "get_video_decision": (Scope, "Read the chain state and the user's latest decisions and notes (素材 / 小样 / 成片; the user may also send a 导演稿 back, state draft_changes). Continue only after approval; notes mean a new version. cover_redo {note} on a 小样 / 成片 under review means the user wants only the cover redone: redo it per the note and submit role cover again on the same task (a landscape 成片 task: every cover role it lists), without resubmitting the cut.", True),
    "set_shot_materials": (VideoMaterialsInput, "After the 导演稿 is saved: put material revisions on shots {shot_id: material_revision_id}, optionally the music bed (music: an audio material_revision_id) and the length of shots without a line (silent_durations, ms; e.g. a closing that must stay long enough to read its text). Picture content stays as approved.", False),
    "accept_material_candidate": (VideoCandidateInput, "Import one stock candidate from a start_material_match run into the library and this project; returns its material_revision_id.", False),
    "generate_video_image": (VideoImageInput, "Generate one still with the model chosen as 封面生图 in settings into this project's folder. aspect_ratio 1:1 / 4:3 / 3:4 / 16:9 / 9:16, default the work's 导演稿 aspect (9:16 without one); made at the size a cover uses (16:9 1920×1080, 3:4 1080×1440, 9:16 1080×1920, 4:3 1440×1080, 1:1 1440×1440), smaller only when the model cannot. Returns material_revision_id, width, height, provider, model_id, and model_note when it fell back.", False),
    "import_material_folder": (MaterialFolderInput, "Register every media file of one folder on the material drive into this project, the same as 引入原始素材文件夹 on the project's 素材 page: path is the folder's full path on the drive (e.g. under 外部素材库/), never a project folder or 通用素材. Files are linked in place, attached to this project only and never bound to a shot. Returns counts plus files [{relative_path, material_revision_id}] for new and already attached files; use those ids for render_ae_template image slots. Calling again with the same folder registers nothing twice.", False),
    "get_shot_video_prompt": (ShotInput, "Product and persona works: one shot's prompts (zh and en, built from the shot's board — picture, camera, the person's attitude — plus the group's shared person and setting when the shot is in a consistency group), the first-frame still prompt, first / last frame revisions, ratio and seconds, and whether the shot is manual or auto. Persona works also get t2v_prompt / t2v_prompt_en for making the clip from text alone; their prompts never mention a product. Without a persona portrait every prompt says no person appears (setting only, hands when something is handled), except that a shot whose board names other_people (people who are not the persona, e.g. 宝宝) may show them as hands, feet, part of the body or from behind, never the face.", True),
    "set_shot_video_mode": (ShotModeInput, "Product and persona works, after the 导演稿 is saved and the user's materials are mapped, only for shots without one: switch one shot to manual (the user makes the clip on a website from the prompt — text-to-video, or image-to-video with the platform's still — and uploads it) or auto (the image-to-video model in 用途路由). Use manual when an auto clip failed or the user did not like it.", False),
    "generate_shot_image": (ShotImageInput, "Product and persona works, after the 导演稿 is saved and the user's materials are mapped, only for shots without one and not in a consistency group (grouped shots use generate_storyboard_grid): generate one shot's still with the image model in 用途路由 → 镜头生图. Product works: the product photo goes as reference with the persona's portrait (or the work's own shared references, which win; plus an optional extra reference), each still is checked against the product photo (shape, colour, material, logo, accessories) and redrawn with the problems up to 3 times, only a passing still becomes the first frame, and reveal / CTA shots are refused. Persona works: no product reference and no check; the portrait goes along when there is one, and the still becomes the first frame as drawn. Without a portrait no person is drawn (hands only) and people shots return a notice; a persona shot whose board names other_people may show those people without a face. Write the scene, light and framing in prompt; the person rule is added for you.", False),
    "set_shot_first_frame": (ShotFrameInput, "Product and persona works, after the 导演稿 is saved and the user's materials are mapped, only for shots without one: pick the picture one shot's image-to-video starts from, e.g. a still made with generate_video_image or a storyboard-grid candidate (material_revision_id); null goes back to the 导演稿 keyframe (product works: or the product photo). Product reveal and CTA shots keep the original product photo.", False),
    "generate_shot_video": (ShotInput, "Product and persona works, after the 导演稿 is saved and the user's materials are mapped, only for shots without one, auto shots only, after the user has approved the materials (submit_video_materials): submit image-to-video with the shot's first (and chained last) frame. Persona works have no product photo to fall back on, so generate the first frame first. Billed per clip; never resubmit an unclear call. Read the result with get_shot_video.", False),
    "get_shot_video": (ShotInput, "Product and persona works: poll the shot's automatic image-to-video; when done returns the material_revision_id (a candidate for set_shot_materials).", False),
    "save_publish_copy": (PublishCopyInput, "Save the work's one publish copy (no per-platform copies). Video works: title, hashtags, cover_text, interaction, description — product videos with studio.product.publish-copy (title ≤15, 3–5 hashtags, cover_text ≤8, description ≤50), persona videos with studio.persona.publish-copy (title ≤30, cover_text ≤12, description ≤300); save it before submitting the 成片. Graphic works: title, lead, hashtags, interaction with studio.persona.graphic-copy (title ≤30, lead ≤120), before the piece is final. A copy in the wrong format is refused. The user can edit it on the 交付 (delivery) page.", False),
    "generate_video_voiceover": (VoiceoverInput, "Generate the voiceover with the saved MiniMax settings, align shot timing to it; returns duration and SRT lines. voice.pronunciation in the 导演稿 is applied. Optional lines (script block ids, 1–20): voice only those lines again and splice each into the current whole voiceover at its own start, keeping every other line, the total length, shot lengths and other subtitles; only those lines are billed. It fails rather than guesses: voiceover_line_split_unclear (cannot place the lines in the current voice), voiceover_line_too_long (says how many seconds are missing; shorten the line or regenerate the whole voice), voiceover_redub_too_large (checked before any MiniMax call, nothing billed: the spliced voice would exceed the 30 MB material limit; states length and expected size); works with dub_persona shots or a dialogue track are refused. The spliced voice is saved as lossless stereo-preserving FLAC (same sample rate, channels and length; untouched lines sample-identical), fitting voices up to about 10 minutes. Returns redub with each line's old and new start/end and seam positions. If any shot has board.dub_persona, only those shots' lines are voiced in their personas' voices, placed at their shots on one full-length track (silence elsewhere), and no shot timing changes.", False),
    "file_as_common": (VideoCommonInput, "Move a material this project uses into 通用素材库 on the Mac, only when it is generic (effects, transitions, textures, BGM / sound effects nearly every video could use). Project-specific material stays in the project folder.", False),
    "search_web_materials": (WebSearchInput, "Search readable web pages (brand sites, dealers, small shops, official news and review sites; Taobao, Tmall, JD and Pinduoduo are skipped) for pictures of this work's subject. Product works search the product's name and variant by default and the user's picks join the product's info images; other works need query (the product or subject name) and picks join the project's materials. Send the user review_url to pick; you cannot pick or save pictures.", False),
    "get_web_materials": (WebSearchReadInput, "Read a web material search started with search_web_materials: status, each page's site, title and picture count, and which pictures the user has saved (material_revision_id).", True),
    "propose_lesson": (LessonInput, "Call after delivering a revision that addressed sent-back notes (brief lessons.open_rework_records): generalize the cause into a reusable rule (title = short cause, rule = what to do from now on, scope = which videos it fits, e.g. iPhone HLG 实拍 / 商品视频 / 全部视频) and name the record_ids it came from. When an active or pending lesson in the brief has the same cause, pass same_as_lesson_id: it counts one more occurrence instead of a duplicate. The user approves in Settings before a lesson reaches briefs.", False),
    "prepare_video_edit": (VideoEditInput, "Record which shots use AE (alpha_shot_ids need alpha) and open the edit task: phase rough_cut = 小样 (after the user approved the materials), final = 排版 + 成片 (after 小样 approval). Then claim and work it with the execution tools in DaVinci Resolve and After Effects. The result names work_dir and export_dir: export the 小样 / 成片 straight into export_dir and keep everything else in work_dir; materials stay where they are. When files asks for cover_vertical (16:9 成片), deliver two covers: cover 1920×1080 is laid over the first 0.5 s of the 成片 and cut from the rendered 成片; cover_vertical 1080×1440 is the same design laid out vertically, made separately and not placed in the 成片; when files also asks for cover_43 (required: the 成片 cannot be approved without it), cut it 1440×1080 from the centre of cover (240 px off each side), keeping the title inside that centre. cover_template, when set, is the persona's AE 封面 template: render the cover text layer with it (render_ae_template, only its fields) and submit the cover with metadata.cover_template_render = that render's material_revision_id.", False),
    "redo_work_covers": (Scope, "Only when the user asks to redo the covers of a finished (已定稿) landscape work: open a cover-only task that takes cover_vertical 1080×1440 and cover_43 1440×1080 (both required); the 成片 and the 16:9 cover stay. cover_portrait, when set, is the persona's cover portrait: cut the figure out of its background and put it on both covers. Claim and work it like an edit task, export to cover_dir, then ask the user to look at them on the 成片 page; get_video_decision's cover_task says review / changes (redo both with its notes) / done. Never approve them yourself.", False),
    "analyze_reference_video": (ReferenceVideoInput, "Start the free local breakdown of a reference video (a video material_revision_id from the library; the user can also upload one on the 导演稿 page): timed transcript, scene cuts, time-labelled frame grids per segment and loudness, written to <项目>/工作/<作品>/参考拆解/. Runs in the background; read it with get_reference_video. The reference never becomes project material and never enters the cut.", False),
    "get_reference_video": (Scope, "Read the work's reference breakdown: status (running / done / failed), the local summary with transcript, cuts, loudness and the absolute paths of transcript.json, cuts.json and the grid images to look at, the saved breakdown and the shooting list.", True),
    "save_reference_breakdown": (ReferenceBreakdownInput, "After reading the local breakdown with studio.video.reference-breakdown: save the whole-piece analysis, the timeline (per segment: speech, picture, overlays, purpose, source ms), the shooting list of 需要实拍 shots and brand_material (certificates, hospitals, ingredients seen in the reference: they need the brand's real material, never generated). Then write the 导演稿 with save_director_draft.", False),
    "generate_storyboard_grid": (StoryboardGridInput, "Product and persona works, after the 导演稿 is saved: draw one consistency group (group_id from the 导演稿's consistency_groups — shots that must keep the same person or setting) in 3×3 storyboard sheets so people, place and light stay consistent; the group's person and setting go into the prompt, and the persona's portrait (product works: plus the product's primary image; the work's own shared references win) goes along as reference. Unrelated shots are not grouped and are made one by one instead. The platform cuts each sheet, upscales each cell and registers it as that shot's first-frame candidate (not adopted; the user or set_shot_first_frame picks). Product works check each cell against the product photo and redraw a failing cell alone (up to 3 tries); persona works have no product check. Without a portrait no person is drawn (hands only); in persona works only cells whose board names other_people may show those people, never their face; person_notices lists the people shots affected. More than nine shots make more sheets, each later one referencing the first. Billed like generate_shot_image.", False),
    "get_article_brief": (Scope, "Text / graphic piece written by you (the page switch must be 第三方模型): project, brief, facts, source texts, the writer setting, chain state and the current version as the payload format example (text.master.v2 or graphic.master.v2). When `search` is present this is a 搜索推广 work: answer search.question, cite only search.facts with their sources, and follow search.rules.", True),
    "save_article_draft": (ArticleDraftInput, "Save one full version of the piece (text.master.v2 for text, graphic.master.v2 for graphic; image layers name material_revision_id from the library or generate_video_image; no citations or claims). Refused when the page switch is 平台模型 or the piece is final. Graphic pieces also need their publish copy (save_publish_copy, graphic format) before they are final. Then STOP: the user approves or writes notes on the page.", False),
    "get_fact_template": (Scope, "Persona works, before the 导演稿 or article: the project's topic templates for its fact boundary (which claims need a source, accepted sources and domains, freshness, red lines, opinion-only content), suggested templates when none is chosen, the brief and the current boundary. Product works use the product brief instead.", True),
    "submit_facts": (FactsInput, "Persona works, before saving the 导演稿 or article: submit every claim the piece states as fact, found by the project's topic templates. Each item is the statement, kind (fact / event / quote / opinion), template id, source_url, the excerpt copied word for word from that page, source_date, and attribution for quotes and opinions; templates records your topic choice when the project has none. The platform opens every source: unreachable sources and excerpts not on the page come back with reasons and are not kept; the rest (labelled when outside the template's usual sites or possibly out of date) are frozen automatically as the project's new fact boundary, replacing the previous one. Save the draft after this; the user only reviews the draft.", False),
    "get_review_tasks": (Scope, "Third-party writer only: the fact and identity reviews the platform is waiting for on the current version. Read each item's request.text and request.context, judge it against the sources and identity rules given, then call submit_review with the item's master_id, purpose and input_hash. For a graphic identity review, request.context.images lists the rendered card files: open and look at every image, and report anything in the picture that breaks the identity rules (faces passed off as the persona, other brands, products, misleading scenes) as an issue.", True),
    "submit_review": (ReviewSubmitInput, "Third-party writer only: submit your judgement for one waiting review. issues lists each problem you found (severity warning or blocker, the exact span, the reason); an empty list means no problem. The platform reruns the checks and records your model name. It does not accept or approve the piece.", False),
    "submit_warning_judgment": (WarningJudgmentInput, "Third-party writer only: judge one check warning listed in get_review_tasks warning_judgments. Read request.report (what the check could not confirm) and request.content; verdict accept means the piece has no problem this check guards against, reject means it has one or you cannot confirm. reason is one or two plain sentences. Only when every warning is accepted can the user approve; this does not approve for the user.", False),
    "get_article_decision": (Scope, "Read the piece's state and the user's latest decision and notes. Approved means final: save nothing more. Notes mean a new version.", True),
    "get_shot_slots": (ShotSlotsInput, "Read every shot of a video as a material slot: narration, visual, brief (search words; gen_mode text|frame chosen on the platform; t2v_prompt for direct text-to-video; frame_prompt for the first-frame still and prompt for image-to-video from it; route), status missing/candidates/chosen, the user's picks and the review link. Add candidates with start_material_match; only the user binds a shot.", True),
}
_ACTIONS = {"claim_execution": "claim", "start_execution": "start", "report_progress": "progress",
            "report_blocker": "block", "report_checkpoint": "progress", "mark_unknown": "unknown",
            "reconcile_unknown": "reconcile", "request_human_review": "progress"}
_META_FIELDS = ("id", "project_id", "content_unit_id", "revision_no", "payload_schema", "payload_hash",
                "context_hash", "creative_intent", "creative_intent_hash", "modality", "channel_id",
                "content_form", "variant_key", "source_master_revision_id", "readiness")
_SAFE_CODES = {
    "material_library_unavailable", "creative_metadata_field_invalid", "platform_skills_disabled", "creative_execution_revision_conflict", "creative_execution_executor_mismatch", "creative_execution_terminal",
    "creative_execution_reconciliation_required", "creative_execution_transition_denied",
    "creative_execution_idempotency_conflict", "creative_execution_not_found", "creative_package_not_found",
    "creative_source_not_current", "creative_package_stale", "master_context_conflict", "creative_input_model_use_denied",
    "creative_input_rights_changed", "creative_execution_required_outputs_missing",
    "creative_execution_output_replacement_required", "creative_execution_output_hash_mismatch",
    "creative_execution_output_replacement_denied", "creative_execution_checkpoint_observation_required",
    "creative_execution_predispatch_not_proven", "execution_path_invalid", "execution_regular_file_required",
    "creative_execution_input_not_in_package", "creative_execution_rights_escalation",
    "creative_execution_checkpoint_binding_invalid", "creative_execution_checkpoint_requires_claim",
    "creative_execution_observation_required", "creative_execution_reconcile_certainty_required",
    "creative_execution_descriptor_conflict", "creative_execution_descriptor_requires_prepare",
    "creative_execution_descriptor_incomplete", "creative_execution_output_kinds_invalid",
    "creative_execution_checkpoint_unsupported", "creative_execution_recovery_unsupported",
    "creative_execution_recovery_observation_required", "creative_execution_recovery_checkpoint_mismatch",
    "creative_execution_recovery_action_invalid",
}
_CATEGORIES = {403: "forbidden", 404: "not_found", 409: "conflict", 413: "bounds", 422: "invalid_arguments"}


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def safe_value(value: object, binding: Binding, *, maximum: int) -> object:
    pending = [value]
    seen = 0
    while pending:
        item = pending.pop()
        seen += 1
        if seen > 20_000:
            raise MCPError("creative_mcp_payload_bounds", "bounds")
        if isinstance(item, dict):
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
        elif isinstance(item, str):
            if len(item) > 8192:
                # Bound strings before decoding or scanning credentials.
                raise MCPError("creative_mcp_string_bounds", "bounds")
            scanned = unicodedata.normalize("NFKC", item)
            for _ in range(MAX_DEPTH):
                if binding.token in scanned:
                    raise MCPError("creative_mcp_sensitive_payload", "redaction", rpc_code=-32602)
                decoded = unicodedata.normalize("NFKC", unquote(scanned))
                if decoded == scanned:
                    break
                scanned = decoded
            else:
                # Do not echo a value whose bounded credential scan is incomplete.
                raise MCPError("creative_mcp_encoding_bounds", "bounds", rpc_code=-32602)
    value = bounded_json(value, max_bytes=maximum)
    if binding.token in dumps(value):
        raise MCPError("creative_mcp_sensitive_payload", "redaction", rpc_code=-32602)
    return value


def tools_list() -> dict:
    return {"tools": [{"name": name, "description": description, "inputSchema": model.model_json_schema(),
                      "annotations": {"readOnlyHint": readonly, "destructiveHint": not readonly,
                                      "idempotentHint": readonly, "openWorldHint": False}}
                     for name, (model, description, readonly) in TOOLS.items()]}


def _context(db: Session, args: ContextInput, user: User) -> dict:
    project, unit = content_masters.owned_unit(db, args.project_id, args.unit_id, user)
    masters = content_masters.list_revisions(db, project.id, unit.id, user, limit=1)
    variant = channel_variants.current_revision(db, project.id, unit.id, args.variant_key, user) if args.variant_key else None
    brief = current_brief(db, project.id)
    boundary = current_boundary(db, project.id)
    pointers = content_masters._context(db, project, unit, content_form=masters[0]["content_form"] if masters else None)
    return {"project": {"id": project.id, "status": project.status},
            "unit": {"id": unit.id, "status": unit.status, "channel_id": unit.channel_id},
            "context": pointers,
            "brief": {"id": brief.id, "revision_no": brief.revision_no, "checksum": brief.checksum,
                      "objective": brief.objective, "primary_audience": brief.primary_audience,
                      "core_message": brief.core_message, "angle": brief.angle} if brief else None,
            "fact_boundary": {"id": boundary.id, "revision_no": boundary.revision_no,
                              "fact_pack_id": boundary.fact_pack_id, "fact_pack_version": boundary.fact_pack_version,
                              "checksum": boundary.fact_pack_checksum} if boundary else None,
            "master": {key: masters[0][key] for key in _META_FIELDS if key in masters[0]} if masters else None,
            "variant": {key: variant[key] for key in _META_FIELDS if key in variant} if variant else None}


def _execute(db: Session, name: str, args: Input, user: User) -> dict:
    if name == "get_context":
        return _context(db, args, user)
    if name == "get_package":
        return creative_packages.get_package(db, args.project_id, args.unit_id, args.package_id, user)
    if name == "get_execution":
        return creative_executions.get_execution(db, args.project_id, args.unit_id, args.execution_id, user)
    if name == "find_capabilities":
        return capability_memory.discover(db, user, args.model_dump(exclude_none=True))
    if name == "use_capability":
        if args.stage is not None:
            if args.execution_id is None or args.artifact_id is not None or args.artifact_revision_id is not None or args.arguments:
                raise MCPError("production_method_selection_invalid", "validation", rpc_code=-32602)
            return creative_executions.load_production_methods(db, args.project_id, args.unit_id, args.execution_id,
                args.model_dump(exclude_none=True, exclude={"project_id", "unit_id", "execution_id", "artifact_id", "artifact_revision_id", "arguments"}), user)
        return capability_memory.use_artifact(db, user, args.artifact_id,
            args.model_dump(exclude_none=True, exclude={"artifact_id"}))
    if name in {"get_craft_skill", "list_ae_templates", "render_ae_template"}:
        from . import craft_skills

        if name == "get_craft_skill":
            return craft_skills.read_skill(db, user, args.project_id, args.unit_id, args.skill, args.entry)
        if name == "list_ae_templates":
            return craft_skills.list_templates()
        return craft_skills.render(db, user, project_id=args.project_id, unit_id=args.unit_id, template_id=args.template,
                                   version=args.version, content=args.content, images=args.images, duration_ms=args.duration_ms,
                                   aspect=args.aspect)
    if name in {"start_media_transcription", "get_media_transcription"}:
        from . import media_transcription

        if name == "start_media_transcription":
            return media_transcription.start(db, user, args.path, args.output_dir)
        return media_transcription.result(db, args.job_id)
    if name in {"list_personas", "create_project", "create_unit"}:
        return _self_sourced(db, name, args, user)
    if name in _SEARCH_TOOLS:
        return _search(db, name, args, user)
    if name in {"list_accounts", "import_account_metrics"}:
        from . import account_metrics_import

        if name == "list_accounts":
            return account_metrics_import.list_accounts(db, user)
        return account_metrics_import.import_metrics(db, user, args.account_id, args.source.model_dump(),
                                                     [row.model_dump() for row in args.rows])
    if name in {"search_web_materials", "get_web_materials"}:
        return _web_materials(db, name, args, user)
    if name in _REVIEW_TOOLS:
        return _review(db, name, args, user)
    if name in _VIDEO_TOOLS:
        return _video(db, name, args, user)
    if name in {"get_fact_template", "submit_facts"}:
        from . import fact_templates

        if name == "get_fact_template":
            return fact_templates.for_model(db, user, args.project_id, args.unit_id)
        return fact_templates.submit(db, user, args.project_id, args.unit_id, [item.model_dump() for item in args.items], args.templates)
    if name in _ARTICLE_TOOLS:
        from . import article_chain

        if name == "get_article_brief":
            return article_chain.brief(db, user, args.project_id, args.unit_id)
        if name == "save_article_draft":
            return article_chain.save_draft(db, user, args.project_id, args.unit_id, args.payload, args.note)
        if name == "get_review_tasks":
            from . import third_party_review

            return third_party_review.pending_tasks(db, user, args.project_id, args.unit_id)
        if name == "submit_review":
            from . import third_party_review

            return third_party_review.submit(db, user, args.project_id, args.unit_id, args.master_id, args.purpose, args.input_hash, args.model,
                                             [issue.model_dump() for issue in args.issues])
        if name == "submit_warning_judgment":
            from . import warning_judgment

            return warning_judgment.submit(db, user, args.project_id, args.unit_id, args.check_id, args.input_hash, args.model, args.verdict, args.reason)
        return article_chain.state(db, user, args.project_id, args.unit_id)
    payload = args.model_dump(exclude_none=True, exclude={"project_id", "unit_id", "execution_id"})
    if name in _ACTIONS:
        payload["action"] = _ACTIONS[name]
        if name == "request_human_review":
            current = creative_executions.get_execution(db, args.project_id, args.unit_id, args.execution_id, user)
            if current["state"] != "result_ready":
                raise MCPError("creative_mcp_result_not_ready", "conflict", status=409)
            payload["metadata"] = {"summary": "Human review requested"}
        return creative_executions.transition_execution(db, args.project_id, args.unit_id, args.execution_id, payload, user)
    if name == "materialize_inputs":
        return creative_executions.materialize_inputs(db, args.project_id, args.unit_id, args.execution_id, payload, user)
    if name == "submit_output":
        return creative_executions.submit_output(db, args.project_id, args.unit_id, args.execution_id, payload, user)
    raise MCPError("creative_mcp_unknown_tool", "invalid_arguments", rpc_code=-32602)


# Marks a brief whose topic the third-party model chose itself, so the project page can say so.
MODEL_TOPIC = "third_party_model_topic"


def _self_sourced(db: Session, name: str, args: Input, user: User) -> dict:
    from ..models import ContentPersona
    from ..routers import content_projects as projects
    from .content_harness import channel_registry
    from .content_identity import current_revision

    if name == "list_personas":
        personas = []
        for persona in db.scalars(select(ContentPersona).where(ContentPersona.owner_user_id == user.id,
                                                               ContentPersona.status == "active").order_by(ContentPersona.id)):
            revision = current_revision(db, "persona", persona.id)
            personas.append({"id": persona.id, "name": persona.name,
                             "positioning": ((revision.profile_json or {}).get("positioning") if revision else None)})
        return {"personas": personas, "channels": [{"channel": c["channel"], "label": c["label"]}
                                                   for c in channel_registry.list_channels(db)]}
    if name == "create_project":
        project = projects.create_project(projects.ProjectIn(title=args.title, objective=args.objective), db=db, user=user)
        reference = {"kind": MODEL_TOPIC, "rationale": args.rationale, "links": [link.model_dump(exclude_none=True) for link in args.links]}
        brief = projects.save_project_brief(projects.BriefRevisionIn(expected_revision=0, objective=args.objective,
            core_message=args.core_message, angle=args.angle, references=[reference]), project["id"], db=db, user=user)
        return {"project_id": project["id"], "brief_revision": brief["revision_no"]}
    unit = projects.create_unit(projects.UnitIn(title=args.title, persona_id=args.persona_id, modality=args.modality,
                                                channel_id=args.channel_id), args.project_id, db=db, user=user)
    return {"project_id": unit["project_id"], "unit_id": unit["id"], "persona_id": unit["persona_id"], "modality": unit["modality"]}


def _web_materials(db: Session, name: str, args: Input, user: User) -> dict:
    from ..models import ContentUnit, ProductSku, ProductSkuRevision
    from . import product_video, web_material_search
    from .project_authorization import lock_project_context

    lock_project_context(db, args.project_id, user)
    unit = db.get(ContentUnit, args.unit_id)
    if unit is None or unit.project_id != args.project_id:
        raise HTTPException(404, {"code": "content_unit_not_found", "message": "作品不存在"})
    link = product_video.work(db, args.unit_id)
    if name == "get_web_materials":
        data = web_material_search.read(db, user, args.search_id)
        if data["project_id"] != args.project_id and not (link and data["sku_id"] == link.sku_id):
            raise HTTPException(404, {"code": "web_material_search_not_found", "message": "搜索记录不存在"})
        return {"search_id": data["id"], "status": data["status"], "progress": data["progress"], "error_code": data["error_code"],
                "pages": [{"site": page["site"], "title": page["title"], "url": page["url"], "readable": page["readable"],
                           "images": len(page["images"]), "variant_found": page["variant_found"],
                           "saved": [image["accepted"]["material_revision_id"] for image in page["images"] if image.get("accepted")]}
                          for page in data["pages"]], "skipped": len(data["skipped"])}
    if link is not None:
        sku = db.get(ProductSku, link.sku_id)
        revision = db.scalar(select(ProductSkuRevision).where(ProductSkuRevision.sku_id == sku.id, ProductSkuRevision.revision == sku.revision))
        product = (revision.product_json or {}) if revision else {}
        query = args.query or " ".join(filter(None, [product.get("name"), product.get("variant")]))[:120]
        data = web_material_search.start(db, user, query=query, sku_id=sku.id)
        review = f"/production?workspace=product&sku={sku.id}&tab=facts"
    else:
        if not args.query:
            raise HTTPException(422, {"code": "web_material_search_query_invalid", "message": "非商品作品要给 query（产品或主题名）"})
        data = web_material_search.start(db, user, query=args.query, project_id=args.project_id, unit_id=args.unit_id)
        review = f"/projects/{args.project_id}/units/{args.unit_id}/production?workstep=materials"
    return {"search_id": data["id"], "status": data["status"], "query": data["query"], "review_url": review}


_REVIEW_TOOLS = {"get_stages", "start_run", "preview_stage", "run_stage", "get_stage_result", "get_stage_decision",
                 "start_material_match", "get_material_match", "get_shot_slots", "start_material_autofill"}


_SEARCH_TOOLS = {"list_promotion_subjects", "save_promotion_subject_draft", "get_search_subject", "save_question_library", "open_search_projects",
                 "get_search_project", "adopt_search_draft", "get_search_version_template", "save_search_version", "submit_search_batch", "get_search_review"}


def _search(db: Session, name: str, args: Input, user: User) -> dict:
    from pydantic import ValidationError as PydanticError

    from . import search_promotion as sp

    try:
        if name == "list_promotion_subjects":
            return {"subjects": sp.list_subjects(db, user)}
        if name == "save_promotion_subject_draft":
            return sp.save_subject(db, user, args.subject_id, sp.SubjectIn.model_validate(args.subject), origin="ai")
        if name == "get_search_subject":
            return sp.get_subject(db, user, args.subject_id)
        if name == "save_question_library":
            return sp.save_library(db, user, args.subject_id, sp.LibraryIn.model_validate(args.library), origin="ai")
        if name == "open_search_projects":
            return sp.open_projects(db, user, args.subject_id, [sp.ProjectItem.model_validate(item) for item in args.items])
    except PydanticError as exc:
        raise HTTPException(422, {"code": "search_input_invalid", "message": "；".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()[:10])}) from None
    if name == "get_search_project":
        return sp.get_project(db, user, args.project_id)
    if name == "adopt_search_draft":
        return sp.adopt_draft(db, user, args.project_id, args.unit_id)
    if name == "get_search_version_template":
        return sp.version_template(db, user, args.project_id, args.unit_id, args.channel_id, args.content_form)
    if name == "save_search_version":
        return sp.save_version(db, user, args.project_id, args.unit_id, args.channel_id, args.content_form, args.payload)
    if name == "submit_search_batch":
        return sp.submit_batch(db, user, args.project_id)
    return sp.review_feedback(db, user, args.project_id)


_ARTICLE_TOOLS = {"get_article_brief", "save_article_draft", "get_article_decision", "get_review_tasks", "submit_review", "submit_warning_judgment"}
_VIDEO_TOOLS = {"get_video_brief", "save_director_draft", "get_video_decision", "set_shot_materials", "submit_video_materials",
                "get_shot_video_prompt", "set_shot_video_mode", "set_shot_first_frame", "generate_shot_image", "generate_shot_video", "get_shot_video", "save_publish_copy",
                "accept_material_candidate", "generate_video_image", "generate_video_voiceover", "prepare_video_edit", "file_as_common", "propose_lesson",
                "redo_work_covers", "import_material_folder", "analyze_reference_video", "get_reference_video", "save_reference_breakdown", "generate_storyboard_grid"}


def _video(db: Session, name: str, args: Input, user: User) -> dict:
    from . import video_chain as chain

    p, u = args.project_id, args.unit_id
    if name == "get_video_brief":
        return chain.brief(db, user, p, u)
    if name == "save_director_draft":
        return chain.save_draft(db, user, p, u, args.payload, args.note)
    if name == "get_video_decision":
        return chain.decisions(db, user, p, u)
    if name == "submit_video_materials":
        return chain.submit_materials(db, user, p, u)
    if name == "set_shot_materials":
        return chain.set_materials(db, user, p, u, args.picks, args.music, args.silent_durations)
    if name == "accept_material_candidate":
        return chain.accept_candidate(db, user, p, args.run_id, args.segment_id, args.candidate_id)
    if name == "generate_video_image":
        return chain.generate_image(db, user, p, u, args.prompt, args.label, args.aspect_ratio)
    if name == "generate_video_voiceover":
        return chain.voiceover(db, user, p, u, args.lines)
    if name == "import_material_folder":
        from ..routers.content_projects import mutable_project
        from . import content_masters, project_folders

        content_masters.owned_unit(db, p, u, user)
        mutable_project(db, p, user)
        return project_folders.import_folder(db, user, p, args.path)
    if name in {"get_shot_video_prompt", "set_shot_video_mode", "set_shot_first_frame", "generate_shot_image", "generate_shot_video", "get_shot_video"}:
        from . import product_video

        if name == "get_shot_video_prompt":
            return product_video.shot_prompt(db, user, p, u, args.shot_id)
        if name == "generate_shot_image":
            return product_video.generate_shot_image(db, user, p, u, args.shot_id, args.prompt, args.extra_reference_revision_id, args.as_first_frame)
        if name == "set_shot_first_frame":
            return product_video.set_shot_first_frame(db, user, p, u, args.shot_id, args.material_revision_id)
        if name == "set_shot_video_mode":
            return product_video.set_shot_mode(db, user, p, u, args.shot_id, args.mode)
        if name == "generate_shot_video":
            return product_video.start_shot_video(db, user, p, u, args.shot_id)
        if name == "get_shot_video":
            return product_video.get_shot_video(db, user, p, u, args.shot_id)
    if name == "save_publish_copy":
        from . import publish_copy

        return publish_copy.save(db, user, p, u, args.model_dump(exclude={"project_id", "unit_id"}))
    if name == "file_as_common":
        return chain.file_as_common(db, user, p, u, args.material_revision_id)
    if name == "redo_work_covers":
        return chain.redo_covers(db, user, p, u)
    if name == "propose_lesson":
        from . import video_lessons

        return video_lessons.propose(db, user, p, u, args.title, args.rule, args.scope, args.record_ids, args.same_as_lesson_id)
    if name in {"analyze_reference_video", "get_reference_video", "save_reference_breakdown"}:
        from . import reference_video

        if name == "analyze_reference_video":
            return reference_video.start(db, user, p, u, material_revision_id=args.material_revision_id)
        if name == "get_reference_video":
            return reference_video.result(db, user, p, u)
        return reference_video.save_breakdown(db, user, p, u, args.model_dump(exclude={"project_id", "unit_id"}))
    if name == "generate_storyboard_grid":
        from . import shot_image

        return shot_image.grid(db, user, p, u, args.group_id, args.reference_revision_id)
    return chain.prepare_edit(db, user, p, u, args.phase, args.ae_shot_ids, args.alpha_shot_ids, args.notes)


def _review(db: Session, name: str, args: Input, user: User) -> dict:
    from .stage_contracts import StageContractError
    from .stage_invocations import StageInvocationError

    try:
        return _review_call(db, name, args, user)
    except StageInvocationError as exc:
        raise HTTPException(exc.status_code, exc.body) from None
    except StageContractError as exc:
        raise HTTPException(422, {"code": str(exc)}) from None


def _review_call(db: Session, name: str, args: Input, user: User) -> dict:
    if name == "get_stages":
        return agent_review.stages(db, user, args.project_id, args.unit_id, args.run_id)
    if name == "start_run":
        return agent_review.start_run(db, user, args.project_id, args.unit_id)
    if name in {"preview_stage", "run_stage"}:
        override = {"instruction": args.instruction} if args.instruction else {}
        if name == "preview_stage":
            return agent_review.preview(db, user, args.project_id, args.unit_id, args.run_id, args.node_id, override)
        return agent_review.run(db, user, args.project_id, args.unit_id, args.run_id, args.node_id,
                                expected_resolution_hash=args.expected_resolution_hash, invocation_key=args.invocation_key, override=override)
    if name in {"get_stage_result", "get_stage_decision"}:
        if (args.attempt_id is None) == (args.invocation_key is None):
            raise MCPError("stage_result_selector_required", "invalid_arguments", status=422, rpc_code=-32602)
        if name == "get_stage_result":
            return agent_review.result_view(db, user, args.project_id, args.unit_id, args.node_id, args.run_id,
                                            attempt_id=args.attempt_id, invocation_key=args.invocation_key)
        return agent_review.decision(db, user, args.project_id, args.unit_id, args.node_id, args.run_id,
                                     attempt_id=args.attempt_id, invocation_key=args.invocation_key, wait_seconds=args.wait_seconds)
    if name == "start_material_autofill":
        from . import material_autofill

        return material_autofill.start(db, user, args.project_id, args.unit_id)
    if name == "get_shot_slots":
        from . import shot_slots

        return shot_slots.view(db, user, args.project_id, args.unit_id)
    if name == "start_material_match":
        payload = args.model_dump()
        payload["shots"] = [shot.model_dump() for shot in args.shots] if args.shots else None
        if (payload["scope"] == "script") != (payload["text"] is not None) or (payload["scope"] == "shots") != (payload["shots"] is not None):
            raise MCPError("material_match_source_invalid", "invalid_arguments", status=422, rpc_code=-32602)
        return agent_review.start_match(db, user, payload)
    return agent_review.read_match(db, user, args.run_id, args.wait_seconds)


def error_data(code: str, category: str, trace_id: str, **extra) -> dict:
    return {"code": code, "category": category, "trace_id": trace_id, **extra}


def domain_error(exc: HTTPException, trace_id: str) -> dict:
    category = _CATEGORIES.get(exc.status_code, "unavailable")
    code = exc.detail.get("code") if isinstance(exc.detail, dict) else None
    # Stage and material codes are fixed identifiers the agent needs to recover; other domain codes stay masked.
    known = code in _SAFE_CODES or bool(code and re.fullmatch(r"(stage|material_match|material_autofill|graphic|shot_slot|ae_template|ae_render|craft|video_chain|article_chain|video|voiceover|edit_handoff|reference_video|shot_grid|account_import|product_persona|web_material|media_transcription|search|promotion|fact_boundary|variant)_[a-z0-9_]{1,80}", code))
    data = error_data(code if known else f"creative_domain_{category}", category, trace_id,
                      status=exc.status_code if exc.status_code in _CATEGORIES else 503)
    # Video and article chain messages are written for the model so it can correct its own draft.
    if known and code.startswith(("material_library_unavailable", "media_transcription_", "video_asset_", "video_chain_", "video_edit_queue_", "article_chain_", "search_", "promotion_", "reference_video_", "shot_grid_", "account_import_", "voiceover_", "product_persona_", "web_material_")) and isinstance(exc.detail.get("message"), str):
        data["message"] = exc.detail["message"][:1000]
    return data


def _argument_problems(exc: ValidationError) -> list[dict]:
    """Which field broke which limit and by how much, so the model can fix its call; the submitted value itself is never echoed."""
    problems = []
    for error in exc.errors(include_url=False)[:20]:
        item = {"field": ".".join(str(part) for part in error["loc"]) or "(arguments)", "rule": error["type"]}
        for key in ("max_length", "min_length", "ge", "gt", "le", "lt", "expected"):
            if key in (error.get("ctx") or {}):
                item[key] = str(error["ctx"][key])[:200]
        value = error.get("input")
        if isinstance(value, (str, list, dict)):
            item["actual_length"] = len(value)
        if error["type"] in {"string_too_long", "too_long"} and "max_length" in item and "actual_length" in item:
            item["message"] = f"{item['field']} 最多 {item['max_length']}，这次 {item['actual_length']}，超了 {item['actual_length'] - int(item['max_length'])}"
        elif error["type"] == "extra_forbidden":
            item["message"] = f"{item['field']} 不是这个工具的参数"
        elif error["type"] == "missing":
            item["message"] = f"缺少 {item['field']}"
        problems.append(item)
    return problems


def tool_result(data: dict, *, failed: bool = False) -> dict:
    return {"content": [{"type": "text", "text": dumps(data)}], "structuredContent": data, "isError": failed}


def call_tool(db: Session, user: User, binding: Binding, params: dict, trace_id: str) -> dict:
    if set(params) - {"name", "arguments", "_meta"} or not isinstance(params.get("name"), str):
        raise MCPError("creative_mcp_call_invalid", "invalid_arguments", rpc_code=-32602)
    name = params["name"]
    if name not in TOOLS:
        raise MCPError("creative_mcp_unknown_tool", "invalid_arguments", rpc_code=-32602)
    mutated = False
    cause = None
    try:
        raw = safe_value(params.get("arguments", {}), binding, maximum=MAX_ARGUMENT_BYTES)
        args = TOOLS[name][0].model_validate(raw)
        mutated = not TOOLS[name][2]
        data = _execute(db, name, args, user)
        data = safe_value(data, binding, maximum=MAX_RESPONSE_BYTES // 2 - 4096)
        result = tool_result(data)
        if len(dumps(result).encode()) > MAX_RESPONSE_BYTES - 4096:
            raise MCPError("creative_mcp_response_too_large", "bounds")
        result["_meta"] = {"aics/trace_id": trace_id}
        return result
    except ValidationError as exc:
        data = error_data("creative_mcp_arguments_invalid", "invalid_arguments", trace_id, status=422, problems=_argument_problems(exc))
    except HTTPException as exc:
        data = domain_error(exc, trace_id)
        cause = exc.detail.get("code") if isinstance(exc.detail, dict) else None
    except MCPError as exc:
        data = error_data(exc.code, exc.category, trace_id, status=exc.status)
        if exc.code == "creative_capability_unavailable":
            data["required_phase"] = 10
    except Exception:  # noqa: BLE001 MCP must never serialize an internal exception or its inputs.
        data = error_data("creative_mcp_internal_error", "internal", trace_id, status=500)
    db.rollback()
    # A failed tool still answers 200, so the log is the only place a lost hand-back can be traced; never the arguments.
    execution_id = (params.get("arguments") or {}).get("execution_id") if isinstance(params.get("arguments"), dict) else None
    # The platform-written message (never the arguments) is logged too, so a lost explanation can be read back.
    log.warning("creative mcp tool failed: tool=%s execution_id=%s code=%s cause=%s status=%s trace=%s message=%s", name,
                execution_id if type(execution_id) is int else None, data.get("code"),
                cause if isinstance(cause, str) and re.fullmatch(r"[a-z0-9_]{1,100}", cause) else None, data.get("status"), trace_id,
                data.get("message"))
    if mutated:
        data["read_capability_use_before_retry" if name == "use_capability" else "read_execution_before_retry"] = True
    return tool_result(data, failed=True)


RESOURCE_TEMPLATES = {
    "context": ("get_context", "aics://projects/{project_id}/units/{unit_id}/context"),
    "package": ("get_package", "aics://projects/{project_id}/units/{unit_id}/packages/{package_id}"),
    "execution": ("get_execution", "aics://projects/{project_id}/units/{unit_id}/executions/{execution_id}"),
    "capabilities": ("find_capabilities", "aics://projects/{project_id}/units/{unit_id}/capabilities"),
}
STATUS_URI = "aics://creative-mcp/status"


def resources_list() -> dict:
    return {"resources": [{"uri": STATUS_URI, "name": "Creative MCP availability", "mimeType": "application/json"}]}


def resource_templates_list() -> dict:
    return {"resourceTemplates": [{"uriTemplate": uri, "name": name, "mimeType": "application/json"}
                                  for name, (_, uri) in RESOURCE_TEMPLATES.items()]}


def read_resource(db: Session, user: User, binding: Binding, params: dict, trace_id: str) -> dict:
    if set(params) - {"uri", "_meta"} or not isinstance(params.get("uri"), str) or len(params["uri"]) > 500:
        raise MCPError("creative_mcp_resource_invalid", "invalid_arguments", rpc_code=-32602)
    uri = params["uri"]
    if uri == STATUS_URI:
        available = all(inspect(db.get_bind()).has_table(table) for table in (
            "capability_artifact", "capability_artifact_revision", "capability_use"))
        data = {"protocol_version": PROTOCOL_VERSION, "transport_sessions": False,
                "capability_memory": {"available": available, "execution": False,
                    "explicit_selection_required": True,
                    "code": None if available else "capability_memory_unavailable"}}
    else:
        match = re.fullmatch(r"aics://projects/([1-9][0-9]{0,15})/units/([1-9][0-9]{0,15})/"
                             r"(context|capabilities|packages/([1-9][0-9]{0,15})|executions/([1-9][0-9]{0,15}))", uri)
        if match is None:
            raise MCPError("creative_mcp_resource_not_found", "not_found", rpc_code=-32002)
        project, unit, kind, package, execution = match.groups()
        values = {"project_id": int(project), "unit_id": int(unit)}
        resource = "package" if package else "execution" if execution else kind
        if package:
            values["package_id"] = int(package)
        if execution:
            values["execution_id"] = int(execution)
        name = RESOURCE_TEMPLATES[resource][0]
        try:
            args = TOOLS[name][0].model_validate(values)
        except ValidationError:
            raise MCPError("creative_mcp_resource_invalid", "invalid_arguments", rpc_code=-32602) from None
        data = _execute(db, name, args, user)
    data = safe_value(data, binding, maximum=MAX_RESPONSE_BYTES // 2 - 4096)
    return {"contents": [{"uri": uri, "mimeType": "application/json", "text": dumps(data)}],
            "_meta": {"aics/trace_id": trace_id}}
