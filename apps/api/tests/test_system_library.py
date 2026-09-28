import re

import pytest
from sqlalchemy import event
from test_knowledge_collections import create

from app import models

pytest_plugins = ["test_knowledge_collections"]


def seed(db):
    s = models.SourceDocument(title="Source", source_type="text", raw_text="heavy", parsed_json={"heavy": True})
    m = models.Material(title="Material", kind="image")
    p = models.FactPack(name="Empty", status="frozen", checksum="a" * 64)
    db.add_all([s, m, p])
    db.flush()
    r = models.MaterialRevision(
        material_id=m.id, content_hash="b" * 64, public_use_allowed=None, model_use_allowed=False
    )
    db.add(r)
    db.commit()
    return s, m, p, r


def test_library_union_pagination_light_queries(library_client, db_session):
    seed(db_session)
    create(library_client)
    sql = []
    listener = lambda conn, cursor, statement, parameters, context, many: sql.append(statement)
    event.listen(db_session.bind, "before_cursor_execute", listener)
    try:
        page = library_client.get("/api/v1/system-library?limit=2&offset=1").json()
    finally:
        event.remove(db_session.bind, "before_cursor_execute", listener)
    assert page["total"] == 4 and len(page["items"]) == 2
    assert any("UNION ALL" in q and "LIMIT" in q for q in sql)
    assert not any("raw_text" in q or "parsed_json" in q or "file_path" in q for q in sql)
    assert not any(re.search(r"(?:SELECT|,)\s+fact_pack_item\.snapshot_json\s*(?:AS|,|\nFROM)", q) for q in sql)
    all_items = library_client.get("/api/v1/system-library").json()["items"]
    pages = [library_client.get(f"/api/v1/system-library?limit=1&offset={i}").json()["items"][0] for i in range(4)]
    assert [(i["type"], i["id"]) for i in all_items] == [(i["type"], i["id"]) for i in pages]
    assert all(i["scope"] == "system_shared" for i in all_items)
    assert library_client.get("/api/v1/system-library/summary").json()["total"] == 4


def test_material_rights_false_unknown_revoked(library_client, db_session):
    _s, _m, _p, r = seed(db_session)

    def rights():
        return library_client.get("/api/v1/system-library?type=material").json()["items"][0]["rights"]

    assert rights()["public_use"] == "unknown" and rights()["model_use"] == "denied"
    latest = library_client.get("/api/v1/system-library?type=material").json()["items"][0]["latest_revision"]
    assert latest["public_use_allowed"] is None and latest["model_use_allowed"] is False
    r.public_use_allowed = True
    r.status = "revoked"
    db_session.commit()
    assert rights()["public_use"] == "revoked"
    assert library_client.get("/api/v1/system-library?type=material&rights=allowed").json()["total"] == 0
    assert library_client.get("/api/v1/system-library?type=material&rights=revoked").json()["total"] == 1
    assert (
        library_client.get("/api/v1/system-library?type=source").json()["items"][0]["rights"]["public_use"]
        == "not_decided_at_source_level"
    )


def test_pack_empty_unknown_denied_and_frozen_grants(library_client, db_session):
    _s, _m, p, _r = seed(db_session)

    def rights():
        return library_client.get("/api/v1/system-library?type=fact_pack").json()["items"][0]["rights"]

    assert rights()["public_ready"] is False
    item = models.FactPackItem(
        fact_pack_id=p.id,
        evidence_kind="author_opinion",
        public_use_allowed=True,
        model_use_allowed=True,
        snapshot_json={"public_use_allowed": True, "model_use_allowed": True, "statement": "heavy"},
    )
    db_session.add(item)
    db_session.commit()
    assert rights()["public_ready"] is True
    from app.models import utcnow

    item.public_use_revoked_at = utcnow()
    db_session.commit()
    value = rights()
    assert value["public_use"] == "revoked" and value["public_ready"] is False
    assert value["snapshot_public_allowed_count"] == 1 and value["public_revoked_count"] == 1
    db_session.add(models.FactPackItem(fact_pack_id=p.id, evidence_kind="author_opinion"))
    db_session.commit()
    assert rights()["public_unknown_count"] == 1


@pytest.mark.parametrize(
    "query",
    [
        "type=source&rights=allowed",
        "rights=allowed",
        "type=material&source_type=text",
        "material_kind=image",
        "type=unknown",
        "limit=201",
        "offset=-1",
        "status=garbage",
    ],
)
def test_library_rejects_invalid_filters(library_client, query):
    assert library_client.get(f"/api/v1/system-library?{query}").status_code == 422


def test_usage_no_foreign_projects_or_opportunities(library_client, db_session):
    s, m, p, r = seed(db_session)
    users = [models.User(email=f"{name}@studio.local", name=name, role="editor") for name in ["mine", "foreign"]]
    db_session.add_all(users)
    db_session.flush()
    for u in users:
        project = models.ContentProject(owner_user_id=u.id, title=u.name)
        opportunity = models.ContentOpportunity(owner_user_id=u.id, title=u.name)
        db_session.add_all([project, opportunity])
        db_session.flush()
        db_session.add_all(
            [
                models.ProjectSourceBinding(project_id=project.id, source_document_id=s.id),
                models.ProjectMaterialReference(project_id=project.id, material_revision_id=r.id, origin="system"),
                models.ProjectFactBoundaryRevision(
                    project_id=project.id,
                    revision_no=1,
                    fact_pack_id=p.id,
                    fact_pack_version=1,
                    fact_pack_checksum=p.checksum,
                ),
                models.ContentOpportunitySignal(
                    opportunity_id=opportunity.id, signal_type="source_document", source_entity_id=s.id, label=u.name
                ),
            ]
        )
    db_session.commit()
    for kind, identifier in [("source", s.id), ("material", m.id), ("fact_pack", p.id)]:
        response = library_client.get(
            f"/api/v1/system-library/{kind}/{identifier}/usage", headers={"X-Studio-User": users[0].email}
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["counts"]["project_references"] == 1
        assert "foreign" not in response.text
        assert body["coverage"]["candidate_manifests"] == "unsupported"
    body = library_client.get(
        f"/api/v1/system-library/source/{s.id}/usage", headers={"X-Studio-User": users[0].email}
    ).json()
    assert body["counts"]["opportunity_signals"] == 1
    assert library_client.get("/api/v1/system-library/source/99999/usage").status_code == 404


def test_collection_filter_references_only(library_client, db_session):
    _s, _m, p, _r = seed(db_session)
    c = create(library_client)
    response = library_client.post(
        f"/api/v1/knowledge-collections/{c['id']}/items",
        json={"expected_revision": 1, "item_type": "fact_pack", "fact_pack_id": p.id},
    )
    assert response.status_code == 201
    page = library_client.get(f"/api/v1/system-library?collection_id={c['id']}").json()
    assert page["total"] == 1 and page["items"][0]["type"] == "fact_pack"


def test_union_null_placeholders_have_postgres_types():
    from sqlalchemy.sql.sqltypes import NullType

    from app.services.system_library import library_query

    _statement, rows = library_query({})
    branches = rows.element.selects
    assert not any(isinstance(column.type, NullType) for branch in branches for column in branch.selected_columns)


def test_archived_pack_keeps_frozen_grants_distinct(library_client, db_session):
    _s, _m, pack, _r = seed(db_session)
    pack.status = "archived"
    db_session.add(
        models.FactPackItem(
            fact_pack_id=pack.id,
            evidence_kind="author_opinion",
            public_use_allowed=False,
            model_use_allowed=False,
            snapshot_json={"public_use_allowed": True, "model_use_allowed": True},
        )
    )
    db_session.commit()
    rights = library_client.get("/api/v1/system-library?type=fact_pack").json()["items"][0]["rights"]
    assert rights["snapshot_public_allowed_count"] == 1
    assert rights["public_use"] == "allowed" and rights["public_ready"] is False


def test_light_resource_detail_and_material_revisions(library_client, db_session):
    s, m, _p, revision = seed(db_session)
    db_session.add(
        models.MaterialRevision(
            material_id=m.id,
            revision_no=2,
            content_hash="c" * 64,
            status="usable",
            public_use_allowed=True,
            model_use_allowed=True,
        )
    )
    db_session.commit()
    response = library_client.get(f"/api/v1/system-library/source/{s.id}")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "active" and "raw_text" not in response.text
    response = library_client.get(f"/api/v1/system-library/material/{m.id}/revisions?limit=1&offset=1")
    assert response.status_code == 200, response.text
    page = response.json()
    assert page["total"] == 2 and page["items"][0]["id"] == revision.id
    assert page["items"][0]["rights"]["public_use"] == "unknown"
    assert "file_path" not in response.text and "source_metadata_json" not in response.text
    assert library_client.get("/api/v1/system-library/source/999999").status_code == 404
    assert library_client.get("/api/v1/system-library/material/999999/revisions").status_code == 404


def test_exact_revision_refresh_keeps_id_and_current_revocation(library_client, db_session):
    _s, material, _p, revision = seed(db_session)
    revision.public_use_allowed = True
    db_session.add(
        models.MaterialRevision(material_id=material.id, revision_no=2, content_hash="d" * 64, public_use_allowed=True)
    )
    db_session.commit()
    url = f"/api/v1/system-library/material/{material.id}/revisions/{revision.id}"
    response = library_client.get(url)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == revision.id and response.json()["rights"]["public_use"] == "allowed"
    revision.status = "revoked"
    db_session.commit()
    refreshed = library_client.get(url).json()
    assert refreshed["id"] == revision.id and refreshed["revision_no"] == 1
    assert refreshed["rights"]["public_use"] == "revoked"
    assert "file_path" not in refreshed and "metadata_json" not in refreshed
    other = models.Material(title="Other")
    db_session.add(other)
    db_session.commit()
    assert library_client.get(f"/api/v1/system-library/material/{other.id}/revisions/{revision.id}").status_code == 404
    assert library_client.get(f"/api/v1/system-library/material/{material.id}/revisions/999999").status_code == 404


@pytest.mark.parametrize("blocked_status", ["revoked", "archived"])
def test_project_reference_blocks_inactive_revision_preserves_history(library_client, db_session, blocked_status):
    from sqlalchemy import func, select

    _source, material, _pack, revision = seed(db_session)
    owner = models.User(email="library-owner@studio.local", name="owner", role="editor")
    db_session.add(owner)
    db_session.flush()
    project = models.ContentProject(owner_user_id=owner.id, title="Project")
    db_session.add(project)
    db_session.commit()
    headers = {"X-Studio-User": owner.email}
    url = f"/api/v1/content-projects/{project.id}/materials/references"
    payload = {"material_revision_id": revision.id}
    assert library_client.post(url, json=payload, headers=headers).status_code == 201
    revision.status = blocked_status
    newer = models.MaterialRevision(
        material_id=material.id, revision_no=2, content_hash="e" * 64, status=blocked_status
    )
    db_session.add(newer)
    db_session.commit()
    before = db_session.scalar(select(func.count()).select_from(models.ProjectMaterialReference))
    assert library_client.post(url, json={"material_revision_id": newer.id}, headers=headers).status_code == 409
    assert library_client.post(url, json=payload, headers=headers).status_code == 409
    assert db_session.scalar(select(func.count()).select_from(models.ProjectMaterialReference)) == before == 1
    shared = library_client.get(f"/api/v1/content-projects/{project.id}/shared-assets", headers=headers)
    assert shared.status_code == 200 and shared.json()[0]['material_revision_id'] == revision.id
    assert len(shared.json()) == 1
    historical = library_client.get(
        f"/api/v1/system-library/material/{material.id}/revisions/{revision.id}", headers=headers
    )
    assert historical.status_code == 200 and historical.json()["status"] == blocked_status
