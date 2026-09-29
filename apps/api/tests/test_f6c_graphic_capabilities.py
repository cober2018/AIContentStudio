"""Project Graphic capability boundaries never fabricate provider outputs."""

from app.models import MaterialRevision, ProjectMaterialReference


def test_project_graphic_external_capabilities_are_unavailable_without_verification(client, db_session):
    headers = {"X-Studio-User": "graphic-capability@studio.local"}
    project = client.post("/api/v1/content-projects", json={"title": "能力边界"}, headers=headers).json()["id"]
    prefix = f"/api/v1/content-projects/{project}"
    response = client.get(f"{prefix}/graphic-capabilities", headers=headers)
    assert response.status_code == 200, response.text
    for key in ("material_search", "image_generation", "image_variation", "graphic_renderer"):
        capability = response.json()[key]
        assert capability["configured"] is False
        assert capability["executable"] is False
        assert capability["verified"] is False
        assert capability["reason"] == "project_provider_not_verified"
    before = (db_session.query(MaterialRevision).count(), db_session.query(ProjectMaterialReference).count())
    for key in ("material-search", "image-generation", "image-variation"):
        attempted = client.post(f"{prefix}/graphic-{key}", json={"query": "风景", "prompt": "风景"}, headers=headers)
        assert attempted.status_code == 422, attempted.text
        assert attempted.json()["detail"]["code"] == "capability_unavailable"
    assert (db_session.query(MaterialRevision).count(), db_session.query(ProjectMaterialReference).count()) == before
    assert client.get(f"{prefix}/graphic-capabilities", headers={"X-Studio-User": "foreign@studio.local"}).status_code == 404
