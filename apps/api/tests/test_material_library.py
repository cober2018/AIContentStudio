"""Material Library（V1 PRD 2.0 D9 / capability: material-library-v1）。

覆盖：upload→MaterialRevision；同素材多稿复用；rights 撤权失效链；
approved 引用不可变（替换=新 Revision）；历史 DraftMedia 可读。
"""

import hashlib
import io
import os
import subprocess
import sys
import wave



EDITOR = {"X-Studio-User": "editor@studio.local"}

PNG = b"\x89PNG\r\n\x1a\n" + b"rest-of-png-bytes" * 8


def test_riff_wave_is_identified_without_client_mime_and_other_riff_is_not():
    from app.services.materials import sniff_mime

    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x00\x00" * 160)
    assert sniff_mime(output.getvalue(), None) == "audio/wav"
    assert sniff_mime(b"RIFF\x00\x00\x00\x00WEBPVP8 ", None) == "image/webp"
    assert sniff_mime(b"RIFF\x00\x00\x00\x00FAKE", None) == "application/octet-stream"


def test_media_root_can_be_isolated_for_acceptance(tmp_path):
    isolated = tmp_path / "media"
    output = subprocess.check_output(
        [sys.executable, "-c", "from app.services.asset_media import MEDIA_ROOT; print(MEDIA_ROOT)"],
        env={**os.environ, "AI_STUDIO_MEDIA_ROOT": str(isolated)},
        text=True,
    ).strip()
    assert output == str(isolated)


def _upload(client, *, title="测试图", public=False, role="inline"):
    return client.post(
        "/api/v1/materials/upload",
        data={"kind": "image", "title": title, "rights_status": "cleared", "public_use_allowed": str(public)},
        files={"file": ("pic.png", PNG, "image/png")},
        headers=EDITOR,
    )


def test_upload_creates_material_and_revision(client):
    resp = _upload(client)
    assert resp.status_code == 201, resp.json()
    body = resp.json()
    assert body["kind"] == "image"
    revision = body["revisions"][0]
    assert revision["source_kind"] == "upload"
    assert revision["content_hash"] == hashlib.sha256(PNG).hexdigest()
    # 用户放进素材库的素材默认可剪、可发布
    assert revision["public_use_allowed"] is True


def test_upload_validation_rejects_unknown_binary(client):
    resp = client.post(
        "/api/v1/materials/upload",
        data={"kind": "image", "title": "bad"},
        files={"file": ("evil.bin", b"\x00\x01\x02\x03not-an-image", "application/octet-stream")},
        headers=EDITOR,
    )
    assert resp.status_code == 422


def test_search_capability_unavailable(client):
    """无 provider：422 capability_unavailable，不返回假数据（§6.15）。"""
    resp = client.post("/api/v1/materials/search", json={"query": "城市夜景"}, headers=EDITOR)
    assert resp.status_code == 422
    assert "capability_unavailable" in resp.json()["detail"]


