from fastapi import HTTPException
from sqlalchemy import Boolean, Float, Integer, String, case, cast, func, literal, select, union_all

from ..models import (
    Fact,
    FactPack,
    FactPackItem,
    KnowledgeCollection,
    KnowledgeCollectionItem,
    Material,
    MaterialCollectionItem,
    MaterialRevision,
    SourceDocument,
)

RESOURCE_MODELS = {
    "source": SourceDocument,
    "material": Material,
    "fact_pack": FactPack,
    "knowledge_collection": KnowledgeCollection,
}


def permission(value, revoked=None):
    branches = [] if revoked is None else [(revoked, "revoked")]
    return case(*branches, (value.is_(True), "allowed"), (value.is_(False), "denied"), else_="unknown")


def pack_aggregate():
    item = FactPackItem
    pack = FactPack
    # Extract only permission scalars in SQL; never transfer full immutable snapshots.
    snapshot_public = item.snapshot_json["public_use_allowed"].as_boolean()
    snapshot_model = item.snapshot_json["model_use_allowed"].as_boolean()
    public = case((pack.status != "draft", snapshot_public), else_=item.public_use_allowed)
    model = case((pack.status != "draft", snapshot_model), else_=item.model_use_allowed)
    pub_state = permission(public, item.public_use_revoked_at.is_not(None))
    model_state = permission(model)
    columns = [
        item.fact_pack_id.label("pack_id"),
        func.count(item.id).label("item_count"),
        func.count(func.distinct(Fact.source_document_id)).label("source_count"),
    ]
    for prefix, state in (("public", pub_state), ("model", model_state)):
        for name in ("allowed", "denied", "unknown", "revoked"):
            columns.append(func.sum(case((state == name, 1), else_=0)).label(f"{prefix}_{name}_count"))
    columns.extend(
        [
            func.sum(case((snapshot_public.is_(True), 1), else_=0)).label("snapshot_public_allowed_count"),
            func.sum(case((snapshot_model.is_(True), 1), else_=0)).label("snapshot_model_allowed_count"),
        ]
    )
    for kind in ("fact", "event", "third_party_quote", "author_opinion", "legacy_untyped"):
        columns.append(func.sum(case((item.evidence_kind == kind, 1), else_=0)).label(f"evidence_{kind}"))
    return (
        select(*columns)
        .join(pack, pack.id == item.fact_pack_id)
        .outerjoin(Fact, Fact.id == item.fact_id)
        .group_by(item.fact_pack_id)
        .subquery()
    )


EXTRA_COLUMNS = (
    (
        "revision_id",
        "revision_no",
        "revision_status",
        "checksum",
        "source_kind",
        "source_url",
        "provider_key",
        "provider_version",
        "rights_status",
        "public_use",
        "model_use",
        "commercial_use",
        "attribution_present",
        "mime_type",
        "public_use_allowed",
        "model_use_allowed",
        "commercial_use_allowed",
        "parse_status",
        "trust_level",
        "as_of",
        "created_by",
        "item_count",
        "source_count",
        "snapshot_public_allowed_count",
        "snapshot_model_allowed_count",
        "drive_source_id",
        "width",
        "height",
        "duration_ms",
    )
    + tuple(f"{p}_{s}_count" for p in ("public", "model") for s in ("allowed", "denied", "unknown", "revoked"))
    + tuple(f"evidence_{k}" for k in ("fact", "event", "third_party_quote", "author_opinion", "legacy_untyped"))
)


def projection(kind, model, title, status, subtype, **extras):
    def empty(key):
        datatype = (
            Integer
            if key.endswith("_count") or key.startswith("evidence_") or key in {"revision_id", "revision_no", "width", "height", "duration_ms", "drive_source_id"}
            else Boolean
            if key == "attribution_present" or key.endswith("_use_allowed")
            else Float
            if key == "trust_level"
            else String
        )
        # Typed NULLs keep PostgreSQL's left-associative UNION resolution portable.
        return cast(literal(None), datatype)

    return select(
        literal(kind).label("type"),
        model.id.label("id"),
        title.label("title"),
        status.label("status"),
        subtype.label("subtype"),
        model.created_at.label("created_at"),
        *(extras.get(key, empty(key)).label(key) for key in EXTRA_COLUMNS),
    )


def library_query(filters):
    material, revision = Material, MaterialRevision
    latest = (
        select(func.max(MaterialRevision.revision_no))
        .where(MaterialRevision.material_id == material.id)
        .correlate(material)
        .scalar_subquery()
    )
    revoked = revision.status == "revoked"
    material_query = projection(
        "material",
        material,
        material.title,
        material.status,
        material.kind,
        revision_id=revision.id,
        revision_no=revision.revision_no,
        revision_status=revision.status,
        checksum=revision.content_hash,
        source_kind=revision.source_kind,
        source_url=revision.source_url,
        provider_key=revision.provider_key,
        provider_version=revision.provider_version,
        rights_status=revision.rights_status,
        mime_type=revision.mime_type,
        public_use_allowed=revision.public_use_allowed,
        model_use_allowed=revision.model_use_allowed,
        commercial_use_allowed=revision.commercial_use_allowed,
        public_use=permission(revision.public_use_allowed, revoked),
        model_use=permission(revision.model_use_allowed, revoked),
        commercial_use=permission(revision.commercial_use_allowed, revoked),
        attribution_present=func.length(func.trim(func.coalesce(revision.attribution_text, ""))) > 0,
        created_by=material.created_by,
        # Linked drive files record their folder here; storage paths stay out of library queries.
        drive_source_id=revision.source_metadata_json["material_source_id"].as_integer(),
        width=revision.width,
        height=revision.height,
        duration_ms=revision.duration_ms,
    ).outerjoin(revision, (revision.material_id == material.id) & (revision.revision_no == latest))
    source = SourceDocument
    source_query = projection(
        "source",
        source,
        source.title,
        case((source.is_archived.is_(True), "archived"), else_="active"),
        source.source_type,
        checksum=source.sha256,
        source_url=source.source_url,
        parse_status=source.parse_status,
        trust_level=source.trust_level,
        as_of=source.as_of,
        public_use=literal("not_decided_at_source_level"),
        model_use=literal("not_decided_at_source_level"),
    )
    aggregate = pack_aggregate()
    extras = {key: func.coalesce(aggregate.c[key], 0) for key in EXTRA_COLUMNS if key in aggregate.c}
    count = func.coalesce(aggregate.c.item_count, 0)

    def pack_state(prefix):
        return case(
            (getattr(aggregate.c, f"{prefix}_revoked_count") > 0, "revoked"),
            (getattr(aggregate.c, f"{prefix}_denied_count") > 0, "denied"),
            ((count == 0) | (getattr(aggregate.c, f"{prefix}_unknown_count") > 0), "unknown"),
            else_="allowed",
        )

    pack_query = projection(
        "fact_pack",
        FactPack,
        FactPack.name,
        FactPack.status,
        literal("evidence_pack"),
        revision_no=FactPack.version,
        checksum=FactPack.checksum,
        public_use=pack_state("public"),
        model_use=pack_state("model"),
        created_by=FactPack.created_by,
        **extras,
    ).outerjoin(aggregate, aggregate.c.pack_id == FactPack.id)
    collection_query = projection(
        "knowledge_collection",
        KnowledgeCollection,
        KnowledgeCollection.name,
        KnowledgeCollection.status,
        literal("collection"),
        revision_no=KnowledgeCollection.revision,
        created_by=KnowledgeCollection.created_by,
        public_use=literal("not_applicable"),
        model_use=literal("not_applicable"),
    )
    queries = {
        "material": material_query,
        "source": source_query,
        "fact_pack": pack_query,
        "knowledge_collection": collection_query,
    }
    requested_type = filters.get("type")
    if filters.get("rights") and requested_type not in {"material", "fact_pack"}:
        raise HTTPException(422, "rights requires material or fact_pack type")
    if filters.get("material_kind") and requested_type != "material":
        raise HTTPException(422, "material_kind requires material type")
    material_only = ("material_source_kind", "model_use", "material_source_id", "material_collection_id")
    if any(filters.get(key) for key in material_only) and requested_type != "material":
        raise HTTPException(422, "material filters require material type")
    if filters.get("source_type") and requested_type != "source":
        raise HTTPException(422, "source_type requires source type")
    status = filters.get("status")
    if (
        status
        and requested_type
        and status not in ({"draft", "frozen", "archived"} if requested_type == "fact_pack" else {"active", "archived"})
    ):
        raise HTTPException(422, "Unsupported status for type")
    selected = [queries[requested_type]] if requested_type else list(queries.values())
    rows = union_all(*selected).subquery()
    statement = select(rows)
    if status:
        statement = statement.where(rows.c.status == status)
    if filters.get("q"):
        statement = statement.where(rows.c.title.icontains(filters["q"], autoescape=True))
    for key in ("material_kind", "source_type"):
        if filters.get(key):
            statement = statement.where(rows.c.subtype == filters[key])
    if filters.get("rights"):
        statement = statement.where(rows.c.public_use == filters["rights"])
    if filters.get("model_use"):
        statement = statement.where(rows.c.model_use == filters["model_use"])
    if filters.get("material_source_kind") == "drive":
        statement = statement.where(rows.c.drive_source_id.is_not(None))
    elif filters.get("material_source_kind"):
        statement = statement.where(rows.c.source_kind == filters["material_source_kind"], rows.c.drive_source_id.is_(None))
    if filters.get("material_source_id"):
        statement = statement.where(rows.c.drive_source_id == filters["material_source_id"])
    if filters.get("material_ids") is not None:
        statement = statement.where(rows.c.type == "material", rows.c.id.in_(filters["material_ids"]))
    if filters.get("exclude_material_ids"):
        statement = statement.where(~((rows.c.type == "material") & rows.c.id.in_(filters["exclude_material_ids"])))
    if filters.get("material_collection_id"):
        statement = statement.where(rows.c.id.in_(select(MaterialCollectionItem.material_id).where(
            MaterialCollectionItem.collection_id == filters["material_collection_id"])))
    if filters.get("collection_id"):
        membership = KnowledgeCollectionItem
        statement = statement.where(
            (
                (rows.c.type == "source")
                & rows.c.id.in_(
                    select(membership.source_document_id).where(
                        membership.collection_id == filters["collection_id"], membership.status == "active"
                    )
                )
            )
            | (
                (rows.c.type == "fact_pack")
                & rows.c.id.in_(
                    select(membership.fact_pack_id).where(
                        membership.collection_id == filters["collection_id"], membership.status == "active"
                    )
                )
            )
        )
    return statement, rows


def serialize(row):
    kind = row["type"]
    value = {key: row[key] for key in ("type", "id", "title", "status", "subtype", "created_at")}
    route = {"source": "sources", "material": "materials", "fact_pack": "fact-packs", "knowledge_collection": "assets"}[
        kind
    ]
    value.update(
        scope="system_shared",
        href=f"/{route}/{row['id']}",
        latest_revision=None,
        rights={"public_use": row["public_use"], "model_use": row["model_use"]},
        provenance={},
    )
    if kind == "material":
        if row["revision_id"] is not None:
            value["latest_revision"] = {
                "id": row["revision_id"],
                "revision_no": row["revision_no"],
                "status": row["revision_status"],
                "checksum": row["checksum"],
            }
        value["rights"].update(
            commercial_use=row["commercial_use"],
            rights_status=row["rights_status"],
            attribution_present=bool(row["attribution_present"]),
        )
        value["provenance"] = {
            k: row[k] for k in ("source_kind", "source_url", "provider_key", "provider_version", "created_by")
        }
        value["kind"] = row["subtype"]
        value["drive"] = {"source_id": row["drive_source_id"]} if row["drive_source_id"] else None
        if value["latest_revision"] is not None:
            value["latest_revision"].update(
                {
                    key: row[key]
                    for key in (
                        "mime_type",
                        "public_use_allowed",
                        "model_use_allowed",
                        "commercial_use_allowed",
                        "rights_status",
                        "source_kind",
                        "source_url",
                        "provider_key",
                        "provider_version",
                        "attribution_present",
                        "width",
                        "height",
                        "duration_ms",
                    )
                }
            )
            value["latest_revision"]["content_hash"] = row["checksum"]
            value["latest_revision"]["rights"] = dict(value["rights"])
    elif kind == "source":
        value["source_type"] = row["subtype"]
        value["provenance"] = {k: row[k] for k in ("source_url", "parse_status", "trust_level", "as_of", "checksum")}
    elif kind == "fact_pack":
        value["version"], value["checksum"] = row["revision_no"], row["checksum"]
        value["latest_revision"] = {
            "id": row["id"],
            "revision_no": row["revision_no"],
            "status": row["status"],
            "checksum": row["checksum"],
        }
        value["rights"].update({key: row[key] for key in EXTRA_COLUMNS if key.endswith("_count")})
        value["rights"]["evidence_kind_counts"] = {
            key.removeprefix("evidence_"): row[key] for key in EXTRA_COLUMNS if key.startswith("evidence_")
        }
        value["rights"]["public_ready"] = (
            row["status"] == "frozen"
            and bool(row["checksum"])
            and row["item_count"] > 0
            and row["public_use"] == "allowed"
        )
        value["provenance"] = {"created_by": row["created_by"]}
    else:
        value["revision"] = row["revision_no"]
        value["provenance"] = {"created_by": row["created_by"]}
    return value


def list_library(db, filters, limit, offset):
    statement, rows = library_query(filters)
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    order = ((rows.c.created_at.desc(), rows.c.type, rows.c.id.desc()) if filters.get("order") == "newest"
             else (rows.c.created_at, rows.c.type, rows.c.id))
    items = [serialize(row) for row in db.execute(statement.order_by(*order).limit(limit).offset(offset)).mappings()]
    _drive_status(db, items)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def _drive_status(db, items):
    from ..models import MaterialSource
    from .material_external import source_status

    # One volume check per folder per page keeps listing fast while an unplugged drive stays visible.
    states = {}
    for item in items:
        drive = item.get("drive")
        if drive:
            if drive["source_id"] not in states:
                source = db.get(MaterialSource, drive["source_id"])
                states[drive["source_id"]] = (source_status(source), source.label) if source else ("unavailable", None)
            drive["status"], drive["label"] = states[drive["source_id"]]


def summary(db):
    statement, _ = library_query({})
    rows = statement.subquery()
    counts = dict.fromkeys(RESOURCE_MODELS, 0)
    counts.update(dict(db.execute(select(rows.c.type, func.count()).group_by(rows.c.type)).all()))
    return {"total": sum(counts.values()), "counts": counts}


def resource_detail(db, kind, resource_id):
    statement, rows = library_query({"type": kind})
    row = db.execute(statement.where(rows.c.id == resource_id)).mappings().first()
    if row is None:
        raise HTTPException(404, "Resource not found")
    item = serialize(row)
    _drive_status(db, [item])
    return item


def material_revisions(db, material_id, limit, offset, *, revision_id=None):
    if db.scalar(select(Material.id).where(Material.id == material_id)) is None:
        raise HTTPException(404, "Material not found")
    revision = MaterialRevision
    names = (
        "id",
        "material_id",
        "revision_no",
        "status",
        "content_hash",
        "mime_type",
        "source_kind",
        "source_url",
        "provider_key",
        "provider_version",
        "rights_status",
        "public_use_allowed",
        "model_use_allowed",
        "commercial_use_allowed",
        "created_at",
    )
    statement = select(
        *(getattr(revision, key) for key in names),
        (func.length(func.trim(func.coalesce(revision.attribution_text, ""))) > 0).label("attribution_present"),
        permission(revision.public_use_allowed, revision.status == "revoked").label("public_use"),
        permission(revision.model_use_allowed, revision.status == "revoked").label("model_use"),
        permission(revision.commercial_use_allowed, revision.status == "revoked").label("commercial_use"),
    ).where(revision.material_id == material_id)
    if revision_id is not None:
        statement = statement.where(revision.id == revision_id)
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    items = []
    for row in db.execute(
        statement.order_by(revision.revision_no.desc(), revision.id.desc()).limit(limit).offset(offset)
    ).mappings():
        item = {key: row[key] for key in names}
        item["attribution_present"] = bool(row["attribution_present"])
        item["rights"] = {key: row[key] for key in ("public_use", "model_use", "commercial_use", "rights_status")}
        item["provenance"] = {
            key: row[key] for key in ("source_kind", "source_url", "provider_key", "provider_version")
        }
        items.append(item)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def material_revision(db, material_id, revision_id):
    result = material_revisions(db, material_id, 1, 0, revision_id=revision_id)
    if not result["items"]:
        raise HTTPException(404, "Material revision not found")
    return result["items"][0]
