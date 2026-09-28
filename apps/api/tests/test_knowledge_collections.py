import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import models


@pytest.fixture
def library_client(client):
    return client


def create(client):
    response = client.post(
        "/api/v1/knowledge-collections", json={"name": "Knowledge", "description": "References only"}
    )
    assert response.status_code == 201, response.text
    return response.json()


def source(db):
    row = models.SourceDocument(title="Source", source_type="text", raw_text="original")
    db.add(row)
    db.commit()
    return row


def add(client, collection, resource, revision):
    return client.post(
        f"/api/v1/knowledge-collections/{collection}/items",
        json={"item_type": "source_document", "source_document_id": resource, "expected_revision": revision},
    )


def test_collection_lifecycle_cas_reactivate_and_archive(library_client, db_session):
    c = create(library_client)
    s = source(db_session)
    assert c["revision"] == 1 and c["scope"] == "system_shared"
    r = add(library_client, c["id"], s.id, 1)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["collection_revision"] == 2
    assert add(library_client, c["id"], s.id, 1).status_code == 409
    assert add(library_client, c["id"], s.id, 2).status_code == 409
    url = f"/api/v1/knowledge-collections/{c['id']}"
    assert library_client.delete(f"{url}/items/{item['id']}?expected_revision=2").status_code == 200
    reactivated = add(library_client, c["id"], s.id, 3)
    assert reactivated.status_code == 201 and reactivated.json()["id"] == item["id"]
    assert library_client.patch(url, json={"expected_revision": 3, "name": "stale"}).status_code == 409
    assert library_client.delete(f"{url}?expected_revision=4").status_code == 200
    assert library_client.get(url).json()["status"] == "archived"
    assert library_client.get(f"{url}/items?status=detached").json()["total"] == 1
    assert add(library_client, c["id"], s.id, 5).status_code == 409
    assert (
        library_client.patch(f"{url}/items/{item['id']}", json={"expected_revision": 5, "note": "bad"}).status_code
        == 409
    )
    assert (
        db_session.scalar(select(models.SourceDocument.raw_text).where(models.SourceDocument.id == s.id)) == "original"
    )
    assert len(db_session.scalars(select(models.KnowledgeCollectionItem)).all()) == 1


def test_collection_reorder_exact_ids_and_item_edit(library_client, db_session):
    c = create(library_client)
    first, second = source(db_session), source(db_session)
    a = add(library_client, c["id"], first.id, 1).json()
    b = add(library_client, c["id"], second.id, 2).json()
    url = f"/api/v1/knowledge-collections/{c['id']}"
    assert (
        library_client.post(f"{url}/reorder", json={"expected_revision": 3, "item_ids": [b["id"]]}).status_code == 422
    )
    assert library_client.get(url).json()["revision"] == 3
    assert (
        library_client.post(f"{url}/reorder", json={"expected_revision": 3, "item_ids": [b["id"], a["id"]]}).status_code
        == 200
    )
    assert (
        library_client.patch(
            f"{url}/items/{a['id']}", json={"expected_revision": 4, "note": "annotation", "sort_order": 8}
        ).status_code
        == 200
    )
    items = library_client.get(f"{url}/items?limit=1").json()
    assert items["total"] == 2 and len(items["items"]) == 1 and items["items"][0]["id"] == b["id"]


def test_items_page_revision_includes_empty_and_matches_members(library_client, db_session):
    collection = create(library_client)
    url = f"/api/v1/knowledge-collections/{collection['id']}/items"
    empty = library_client.get(url).json()
    assert empty["collection_revision"] == 1 and empty["items"] == []
    resource = source(db_session)
    item = add(library_client, collection["id"], resource.id, 1).json()
    page = library_client.get(url).json()
    assert page["collection_revision"] == 2
    assert all(row["collection_revision"] == page["collection_revision"] for row in page["items"])
    assert library_client.delete(f"{url}/{item['id']}?expected_revision=2").status_code == 200
    empty = library_client.get(url).json()
    assert empty["collection_revision"] == 3 and empty["items"] == []
    assert library_client.get(f"{url}?status=detached").json()["collection_revision"] == 3


def test_shared_read_and_editor_write(library_client, db_session):
    db_session.add(models.User(email="viewer@studio.local", name="viewer", role="viewer"))
    db_session.commit()
    c = create(library_client)
    headers = {"X-Studio-User": "viewer@studio.local"}
    assert library_client.get(f"/api/v1/knowledge-collections/{c['id']}", headers=headers).status_code == 200
    assert (
        library_client.post("/api/v1/knowledge-collections", json={"name": "Denied"}, headers=headers).status_code
        == 403
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"item_type": "source_document", "source_document_id": True},
        {"item_type": "source_document", "source_document_id": 0},
        {"item_type": "source_document", "fact_pack_id": 1},
        {"item_type": "fact_pack", "source_document_id": 1, "fact_pack_id": 1},
        {"item_type": "material", "source_document_id": 1},
    ],
)
def test_collection_typed_membership(library_client, payload):
    c = create(library_client)
    payload["expected_revision"] = 1
    assert library_client.post(f"/api/v1/knowledge-collections/{c['id']}/items", json=payload).status_code == 422


def test_archived_resource_and_wrong_collection_item(library_client, db_session):
    c, other = create(library_client), create(library_client)
    s = source(db_session)
    item = add(library_client, other["id"], s.id, 1).json()
    assert (
        library_client.patch(
            f"/api/v1/knowledge-collections/{c['id']}/items/{item['id']}",
            json={"expected_revision": 1, "note": "wrong"},
        ).status_code
        == 404
    )
    s.is_archived = True
    db_session.commit()
    assert add(library_client, c["id"], s.id, 1).status_code == 409
    assert library_client.get(f"/api/v1/knowledge-collections/{c['id']}").json()["revision"] == 1


@pytest.mark.parametrize(
    "values",
    [
        {"item_type": "source_document"},
        {"item_type": "source_document", "fact_pack_id": 1},
        {"item_type": "fact_pack", "source_document_id": 1},
        {"item_type": "source_document", "source_document_id": 1, "fact_pack_id": 1},
    ],
)
def test_database_membership_constraints(library_client, db_session, values):
    c = create(library_client)
    db_session.add(models.KnowledgeCollectionItem(collection_id=c["id"], **values))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_known_database_lock_conflict_rolls_back(library_client, db_session):
    import sqlite3

    from sqlalchemy import event
    from sqlalchemy.exc import OperationalError

    c = create(library_client)

    def fail_gate(conn, cursor, statement, parameters, context, many):
        if statement.startswith("UPDATE knowledge_collection "):
            original = sqlite3.OperationalError("database is locked")
            original.sqlite_errorcode = sqlite3.SQLITE_BUSY
            raise OperationalError(statement, parameters, original)

    event.listen(db_session.bind, "before_cursor_execute", fail_gate)
    try:
        response = library_client.patch(
            f"/api/v1/knowledge-collections/{c['id']}", json={"expected_revision": 1, "name": "Conflict"}
        )
        assert response.status_code == 409
    finally:
        event.remove(db_session.bind, "before_cursor_execute", fail_gate)
    assert library_client.get(f"/api/v1/knowledge-collections/{c['id']}").json()["revision"] == 1


def test_database_unique_membership(library_client, db_session):
    c = create(library_client)
    s = source(db_session)
    assert add(library_client, c["id"], s.id, 1).status_code == 201
    db_session.add(
        models.KnowledgeCollectionItem(collection_id=c["id"], item_type="source_document", source_document_id=s.id)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_concurrent_archive_and_reorder_single_winner(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from fastapi import HTTPException
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.db import Base
    from app.services import knowledge_collections as service

    engine = create_engine(f"sqlite:///{tmp_path / 'race.db'}", connect_args={"check_same_thread": False, "timeout": 5})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = models.User(email="race@studio.local", name="race", role="editor")
        db.add(user)
        db.commit()
        c = service.create_collection(db, user, {"name": "Race"})
        s = source(db)
        item = service.add_item(
            db, user, c["id"], {"expected_revision": 1, "item_type": "source_document", "source_document_id": s.id}
        )
    barrier = Barrier(2)

    def run(archive):
        with Session(engine) as db:
            barrier.wait(timeout=5)
            try:
                if archive:
                    service.archive_collection(db, c["id"], 2)
                else:
                    service.reorder(db, c["id"], {"expected_revision": 2, "item_ids": [item["id"]]})
                return 200
            except HTTPException as error:
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run, [True, False])) == [200, 409]
    with Session(engine) as db:
        collection = db.get(models.KnowledgeCollection, c["id"])
        assert collection.revision == 3
        if collection.status == "archived":
            assert db.get(models.KnowledgeCollectionItem, item["id"]).status == "detached"
    engine.dispose()


def test_migration_isolated_upgrade_downgrade_upgrade_and_pg_ddl(tmp_path, monkeypatch):
    from pathlib import Path

    from alembic.config import Config
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateIndex, CreateTable

    from alembic import command
    from app.config import get_settings
    from app.db import Base

    database = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv("DATABASE_URL", database)
    get_settings.cache_clear()
    engine = create_engine(database)
    tables = [table for table in Base.metadata.sorted_tables if not table.name.startswith("knowledge_collection")]
    Base.metadata.create_all(engine, tables=tables)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    config.attributes["configure_logger"] = False
    try:
        command.stamp(config, "f5b000000001")
        command.upgrade(config, "f5c000000001")
        inspector = inspect(engine)
        assert "knowledge_collection_item" in inspector.get_table_names()
        assert {row["referred_table"] for row in inspector.get_foreign_keys("knowledge_collection_item")} == {
            "source_document",
            "fact_pack",
            "knowledge_collection",
        }
        assert {row["name"] for row in inspector.get_unique_constraints("knowledge_collection_item")} == {
            "uq_knowledge_item_source",
            "uq_knowledge_item_pack",
        }
        command.downgrade(config, "f5b000000001")
        assert "knowledge_collection" not in inspect(engine).get_table_names()
        assert "source_document" in inspect(engine).get_table_names()
        command.upgrade(config, "f5c000000001")
        assert "knowledge_collection" in inspect(engine).get_table_names()
        for model in (models.KnowledgeCollection, models.KnowledgeCollectionItem):
            ddl = str(CreateTable(model.__table__).compile(dialect=postgresql.dialect()))
            assert "CREATE TABLE" in ddl
            for index in model.__table__.indexes:
                assert "CREATE INDEX" in str(CreateIndex(index).compile(dialect=postgresql.dialect()))
    finally:
        engine.dispose()
        get_settings.cache_clear()
