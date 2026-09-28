from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, OperationalError

from ..models import FactPack, KnowledgeCollection, KnowledgeCollectionItem, SourceDocument, utcnow


def collection_dict(row):
    return {
        **{column.name: getattr(row, column.name) for column in KnowledgeCollection.__table__.columns},
        "scope": "system_shared",
    }


def item_dict(row, revision):
    return {
        **{column.name: getattr(row, column.name) for column in KnowledgeCollectionItem.__table__.columns},
        "collection_revision": revision,
    }


def get_collection(db, collection_id):
    row = db.get(KnowledgeCollection, collection_id)
    if row is None:
        raise HTTPException(404, "Collection not found")
    return row


def page(db, statement, limit, offset, serializer):
    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery()))
    return {
        "items": [serializer(row) for row in db.scalars(statement.limit(limit).offset(offset))],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def list_collections(db, status, q, limit, offset):
    statement = select(KnowledgeCollection)
    if status:
        statement = statement.where(KnowledgeCollection.status == status)
    if q:
        statement = statement.where(KnowledgeCollection.name.icontains(q, autoescape=True))
    return page(
        db, statement.order_by(KnowledgeCollection.created_at, KnowledgeCollection.id), limit, offset, collection_dict
    )


def create_collection(db, user, payload):
    row = KnowledgeCollection(**payload, created_by=user.email)
    db.add(row)
    db.commit()
    return collection_dict(row)


def list_items(db, collection_id, status, limit, offset):
    collection = get_collection(db, collection_id)
    statement = select(KnowledgeCollectionItem).where(
        KnowledgeCollectionItem.collection_id == collection_id, KnowledgeCollectionItem.status == status
    )
    result = page(
        db,
        statement.order_by(KnowledgeCollectionItem.sort_order, KnowledgeCollectionItem.id),
        limit,
        offset,
        lambda row: item_dict(row, collection.revision),
    )
    result["collection_revision"] = collection.revision
    return result


def mutate(db, collection_id, expected_revision, action):
    try:
        get_collection(db, collection_id)
        # Conditional UPDATE holds the collection lock until commit, including every item write.
        result = db.execute(
            update(KnowledgeCollection)
            .where(
                KnowledgeCollection.id == collection_id,
                KnowledgeCollection.revision == expected_revision,
                KnowledgeCollection.status == "active",
            )
            .values(revision=KnowledgeCollection.revision + 1, updated_at=utcnow()),
            execution_options={"synchronize_session": False},
        )
        if result.rowcount != 1:
            raise HTTPException(409, "Stale revision or archived collection")
        db.expire_all()
        collection = get_collection(db, collection_id)
        response = action(collection)
        db.commit()
        return response
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Membership conflict") from exc
    except OperationalError as exc:
        db.rollback()
        original = exc.orig
        code = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        sqlite_code = getattr(original, "sqlite_errorcode", 0) or 0
        if code in {"40001", "40P01"} or sqlite_code & 255 in {5, 6}:
            raise HTTPException(409, "Concurrent collection mutation; reload and retry") from exc
        raise


def edit_collection(db, collection_id, payload):
    def action(row):
        for key, value in payload.items():
            if key != "expected_revision":
                setattr(row, key, value)
        return collection_dict(row)

    return mutate(db, collection_id, payload["expected_revision"], action)


def archive_collection(db, collection_id, expected_revision):
    def action(row):
        row.status = "archived"
        db.execute(
            update(KnowledgeCollectionItem)
            .where(KnowledgeCollectionItem.collection_id == collection_id, KnowledgeCollectionItem.status == "active")
            .values(status="detached", detached_at=utcnow())
        )
        return collection_dict(row)

    return mutate(db, collection_id, expected_revision, action)


def add_item(db, user, collection_id, payload):
    def action(collection):
        kind = payload["item_type"]
        source_id, pack_id = payload.get("source_document_id"), payload.get("fact_pack_id")
        resource_model = SourceDocument if kind == "source_document" else FactPack
        resource_id = source_id if kind == "source_document" else pack_id
        archived = resource_model.is_archived if kind == "source_document" else resource_model.status == "archived"
        resource = db.execute(
            select(resource_model.id, archived.label("archived"))
            .where(resource_model.id == resource_id)
            .with_for_update()
        ).first()
        if resource is None:
            raise HTTPException(404, "Resource not found")
        if resource.archived:
            raise HTTPException(409, "Archived resource")
        row = db.scalar(
            select(KnowledgeCollectionItem).where(
                KnowledgeCollectionItem.collection_id == collection_id,
                KnowledgeCollectionItem.item_type == kind,
                KnowledgeCollectionItem.source_document_id == source_id,
                KnowledgeCollectionItem.fact_pack_id == pack_id,
            )
        )
        if row and row.status == "active":
            raise HTTPException(409, "Membership already active")
        if row is None:
            row = KnowledgeCollectionItem(
                collection_id=collection_id, item_type=kind, source_document_id=source_id, fact_pack_id=pack_id
            )
            db.add(row)
        row.status, row.detached_at = "active", None
        row.added_by, row.added_at = user.email, utcnow()
        row.note, row.sort_order = payload.get("note"), payload.get("sort_order", 0)
        db.flush()
        return item_dict(row, collection.revision)

    return mutate(db, collection_id, payload["expected_revision"], action)


def edit_item(db, collection_id, item_id, payload, detach=False):
    def action(collection):
        row = db.scalar(
            select(KnowledgeCollectionItem).where(
                KnowledgeCollectionItem.collection_id == collection_id, KnowledgeCollectionItem.id == item_id
            )
        )
        if row is None:
            raise HTTPException(404, "Item not found")
        if row.status != "active":
            raise HTTPException(409, "Item detached")
        if detach:
            row.status, row.detached_at = "detached", utcnow()
        else:
            for key in ("note", "sort_order"):
                if key in payload:
                    setattr(row, key, payload[key])
        return item_dict(row, collection.revision)

    return mutate(db, collection_id, payload["expected_revision"], action)


def reorder(db, collection_id, payload):
    def action(collection):
        rows = db.scalars(
            select(KnowledgeCollectionItem).where(
                KnowledgeCollectionItem.collection_id == collection_id, KnowledgeCollectionItem.status == "active"
            )
        ).all()
        ids = payload["item_ids"]
        if len(ids) != len(set(ids)) or set(ids) != {row.id for row in rows}:
            raise HTTPException(422, "item_ids must exactly match active membership")
        positions = {identifier: i for i, identifier in enumerate(ids)}
        for row in rows:
            row.sort_order = positions[row.id]
        return collection_dict(collection)

    return mutate(db, collection_id, payload["expected_revision"], action)
