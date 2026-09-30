"""Request-local batch reads for the existing project projections."""

from collections import defaultdict
from collections.abc import Iterable

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased, joinedload, load_only

from ..models import (
    ChannelVariantRevision,
    ContentAsset,
    ContentMasterRevision,
    ContentPersona,
    ContentUnit,
    CreativeBriefRevision,
    DeliveryAttempt,
    DeliveryReceipt,
    DeliveryTarget,
    Draft,
    DraftMedia,
    FactPack,
    FactPackItem,
    IdentitySnapshot,
    MaterialRevision,
    ProjectFactBoundaryRevision,
    Review,
    WorkflowRun,
    WorkflowStep,
)


def _group(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[getattr(row, key)].append(row)
    return grouped


def _latest(db, model, project_ids):
    revisions = select(model.project_id, func.max(model.revision_no).label("revision_no")).where(
        model.project_id.in_(project_ids)
    ).group_by(model.project_id).subquery()
    rows = db.scalars(select(model).join(revisions, (model.project_id == revisions.c.project_id) & (
        model.revision_no == revisions.c.revision_no
    ))).all()
    return {row.project_id: row for row in rows}


class _LoadedRows:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return list(self.rows)


class _LiveValidationReads:
    """Only the existing live gates' known reads are served from this request.

    Unexpected queries raise instead of silently skipping a new safety check.
    """

    def __init__(self, context, project_id):
        self.context = context
        self.project_id = project_id

    def get(self, model, identity):
        return self.context.live_rows[model].get(identity)

    def scalar(self, statement):
        expected = select(ProjectFactBoundaryRevision).where(
            ProjectFactBoundaryRevision.project_id == self.project_id
        ).order_by(ProjectFactBoundaryRevision.revision_no.desc()).limit(1)
        if not statement.compare(expected):
            raise ValueError("Unsupported batched live-validation query")
        return self.context.boundaries.get(self.project_id)

    def scalars(self, statement):
        boundary = self.context.boundaries.get(self.project_id)
        if boundary is None or not statement.compare(select(FactPackItem).where(
            FactPackItem.fact_pack_id == boundary.fact_pack_id
        )):
            raise ValueError("Unsupported batched live-validation query")
        return _LoadedRows(self.context.pack_items.get(boundary.fact_pack_id, []))


class ProjectProjectionContext:
    """Loaded facts only; status decisions remain in Overview and Review."""

    def __init__(self, db: Session, project_ids: Iterable[int], *, summary_only: bool = False):
        self.project_ids = tuple(dict.fromkeys(project_ids))
        self.summary_only = summary_only
        self.briefs = {}
        self.boundaries = {}
        self.units = {}
        self.personas = {}
        self.snapshots = {}
        self.runs = {}
        self.masters = {}
        self.step_statuses = defaultdict(set)
        self.candidates = {}
        self.variant_keys = {}
        self.targets = {}
        self.reviews = {}
        self.attempts = {}
        self.receipts = {}
        self.drafts = {}
        self.draft_revisions = {}
        self.pack_items = {}
        self.live_rows = {model: {} for model in (FactPack, DraftMedia, MaterialRevision)}
        if not self.project_ids:
            return

        self.briefs = _latest(db, CreativeBriefRevision, self.project_ids)
        self.boundaries = _latest(db, ProjectFactBoundaryRevision, self.project_ids)
        units = db.scalars(select(ContentUnit).where(
            ContentUnit.project_id.in_(self.project_ids)
        ).order_by(ContentUnit.id)).all()
        self.units = _group(units, "project_id")
        active = [unit for unit in units if unit.status != "archived"]
        if not active:
            return
        unit_ids = [unit.id for unit in active]
        latest_masters = select(func.max(ContentMasterRevision.id)).where(ContentMasterRevision.content_unit_id.in_(unit_ids)).group_by(ContentMasterRevision.content_unit_id)
        self.masters = {row.content_unit_id: row for row in db.scalars(select(ContentMasterRevision).where(ContentMasterRevision.id.in_(latest_masters))).all()}
        persona_ids = {unit.persona_id for unit in active}
        self.personas = self._rows(db, ContentPersona, persona_ids)
        self.snapshots = self._rows(db, IdentitySnapshot, {unit.identity_snapshot_id for unit in active})
        latest_runs = select(func.max(WorkflowRun.id)).where(
            WorkflowRun.content_unit_id.in_(unit_ids)
        ).group_by(WorkflowRun.content_unit_id)
        runs = db.scalars(select(WorkflowRun).where(WorkflowRun.id.in_(latest_runs)).options(
            load_only(WorkflowRun.id, WorkflowRun.content_unit_id, WorkflowRun.status)
        )).all()
        self.runs = {row.content_unit_id: row for row in runs}
        if runs:
            for run_id, status in db.execute(select(WorkflowStep.run_id, WorkflowStep.status).where(
                WorkflowStep.run_id.in_([run.id for run in runs]),
                WorkflowStep.status.in_(["stale", "failed", "waiting_input"]),
            )).all():
                self.step_statuses[run_id].add(status)
        candidate_query = select(ContentAsset).where(
            ContentAsset.content_unit_id.in_(unit_ids)
        )
        if summary_only:
            candidate = aliased(ContentAsset)
            latest_candidate = select(func.max(candidate.id)).where(
                candidate.content_unit_id == ContentAsset.content_unit_id
            ).correlate(ContentAsset).scalar_subquery()
            latest_legacy = select(func.max(candidate.id)).where(
                candidate.content_unit_id == ContentAsset.content_unit_id,
                candidate.channel_variant_revision_id.is_(None),
            ).correlate(ContentAsset).scalar_subquery()
            series_heads = (select(func.max(ContentAsset.id)).join(
                ChannelVariantRevision, ContentAsset.channel_variant_revision_id == ChannelVariantRevision.id,
            ).where(ContentAsset.content_unit_id.in_(unit_ids)).group_by(
                ContentAsset.content_unit_id, ChannelVariantRevision.variant_key,
            ))
            candidate_query = candidate_query.where(or_(ContentAsset.id == latest_candidate, ContentAsset.id == latest_legacy, ContentAsset.id.in_(series_heads))).options(load_only(
                ContentAsset.id, ContentAsset.content_unit_id, ContentAsset.draft_id,
                ContentAsset.channel_variant_revision_id,
                ContentAsset.channel, ContentAsset.content_form,
                ContentAsset.candidate_manifest_json, ContentAsset.candidate_hash,
                ContentAsset.approved_candidate_hash, ContentAsset.status, ContentAsset.title,
            ))
        candidates = db.scalars(candidate_query.order_by(ContentAsset.id.desc())).all()
        self.candidates = _group(candidates, "content_unit_id")
        variant_ids = {row.channel_variant_revision_id for row in candidates if row.channel_variant_revision_id is not None}
        variant_keys = dict(db.execute(select(ChannelVariantRevision.id, ChannelVariantRevision.variant_key).where(
            ChannelVariantRevision.id.in_(variant_ids),
        )).all()) if variant_ids else {}
        self.variant_keys = {row.id: variant_keys[row.channel_variant_revision_id] for row in candidates
                             if row.channel_variant_revision_id in variant_keys}
        current = []
        for rows in self.candidates.values():
            seen = set()
            legacy_head_id = next((item.id for item in rows if item.channel_variant_revision_id is None), None)
            for row in rows:
                key = self.variant_keys.get(row.id)
                if row is rows[0] or key is not None and key not in seen or row.id == legacy_head_id:
                    current.append(row)
                if key is not None:
                    seen.add(key)
        if not current:
            return
        candidate_ids = [row.id for row in current]
        targets = db.scalars(select(DeliveryTarget).where(
            DeliveryTarget.content_asset_id.in_(candidate_ids)
        ).order_by(DeliveryTarget.id.desc())).all()
        self.targets = _group(targets, "content_asset_id")
        self.reviews = _group(db.scalars(select(Review).where(
            Review.content_asset_id.in_(candidate_ids)
        ).order_by(Review.id.desc())).all(), "content_asset_id")
        if targets:
            target_ids = [target.id for target in targets]
            if summary_only:
                self.attempts = _group(db.execute(select(
                    DeliveryAttempt.target_id, DeliveryAttempt.status, DeliveryAttempt.response_metadata_json,
                ).where(DeliveryAttempt.target_id.in_(target_ids), DeliveryAttempt.status == "unknown")).all(), "target_id")
            else:
                self.attempts = _group(db.scalars(select(DeliveryAttempt).where(
                    DeliveryAttempt.target_id.in_(target_ids)
                ).order_by(DeliveryAttempt.attempt_no)).all(), "target_id")
                self.receipts = _group(db.scalars(select(DeliveryReceipt).where(
                    DeliveryReceipt.target_id.in_(target_ids)
                ).order_by(DeliveryReceipt.created_at)).all(), "target_id")
        self.drafts = self._rows(db, Draft, {row.draft_id for row in current}, load_only(
            Draft.id, Draft.content_job_id, Draft.revision_no,
        ))
        if self.drafts:
            self.draft_revisions = dict(db.execute(select(Draft.content_job_id, func.max(Draft.revision_no)).where(
                Draft.content_job_id.in_({row.content_job_id for row in self.drafts.values()})
            ).group_by(Draft.content_job_id)).all())
        pack_ids = {self.boundaries[row.project_id].fact_pack_id for row in active
                    if row.id in self.candidates and row.project_id in self.boundaries}
        self.live_rows[FactPack] = self._rows(db, FactPack, pack_ids)
        if pack_ids:
            self.pack_items = _group(db.scalars(select(FactPackItem).where(
                FactPackItem.fact_pack_id.in_(pack_ids)
            )).all(), "fact_pack_id")
        media = [entry for row in current for entry in (row.candidate_manifest_json or {}).get("media", [])]
        use_ids = {entry.get("draft_media_id") for entry in media if isinstance(entry.get("draft_media_id"), int)}
        revision_ids = {entry.get("material_revision_id") for entry in media
                        if isinstance(entry.get("material_revision_id"), int)}
        self.live_rows[DraftMedia] = self._rows(db, DraftMedia, use_ids, joinedload(DraftMedia.material_revision))
        self.live_rows[MaterialRevision] = self._rows(db, MaterialRevision, revision_ids)

    @staticmethod
    def _rows(db, model, ids, *options):
        ids = {identity for identity in ids if identity is not None}
        if not ids:
            return {}
        return {row.id: row for row in db.scalars(select(model).where(model.id.in_(ids)).options(*options)).all()}

    def live_reads(self, project_id):
        return _LiveValidationReads(self, project_id)
