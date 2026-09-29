"""Unverified Video/TTS/ASR providers never create project content."""

from app.models import ContentMasterRevision, MaterialRevision, ProjectMaterialReference


def test_project_video_capabilities_are_scoped_and_unverified_calls_write_nothing(client, db_session):
    headers = {"X-Studio-User": "video-capability@studio.local"}
    project = client.post("/api/v1/content-projects", json={"title": "视频能力边界"}, headers=headers).json()["id"]
    prefix = f"/api/v1/content-projects/{project}"
    response = client.get(f"{prefix}/video-capabilities", headers=headers)
    assert response.status_code == 200, response.text
    assert set(response.json()) == {"video_generation", "tts", "asr"}
    for capability in response.json().values():
        assert capability == {"configured": False, "executable": False, "verified": False, "reason": "project_provider_not_verified"}
    before = (
        db_session.query(MaterialRevision).count(),
        db_session.query(ContentMasterRevision).count(),
        db_session.query(ProjectMaterialReference).count(),
    )
    for action in ("video-generation", "video-tts", "video-asr"):
        attempted = client.post(f"{prefix}/{action}", json={"prompt": "测试生成", "secret": "never-echo-this"}, headers=headers)
        assert attempted.status_code == 422, attempted.text
        assert attempted.json()["detail"] == {"code": "capability_unavailable", "reason": "project_provider_not_verified"}
        assert "never-echo-this" not in attempted.text
    assert (
        db_session.query(MaterialRevision).count(),
        db_session.query(ContentMasterRevision).count(),
        db_session.query(ProjectMaterialReference).count(),
    ) == before
    foreign = {"X-Studio-User": "foreign-video@studio.local"}
    assert client.get(f"{prefix}/video-capabilities", headers=foreign).status_code == 404
    assert client.post(f"{prefix}/video-tts", json={}, headers=foreign).status_code == 404
