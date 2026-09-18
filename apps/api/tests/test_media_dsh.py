"""配图素材库 / HTML 导出 / 技能目录配置 / dsh 集成 测试。"""


import pytest

from app import runtime_config
from app.models import ContentAsset
from app.services.dsh_integration import apply_default_model, snapshot, studio_view
from app.services.plugin_registry import scan_skills

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}


@pytest.fixture
def seed_users(db_session):
    from app.models import User

    db_session.add(User(email="admin@studio.local", name="Admin", role="admin"))
    db_session.add(User(email="editor@studio.local", name="Editor", role="editor"))
    db_session.commit()


def _asset(db_session, channel="xiaohongshu", structured=None) -> ContentAsset:
    asset = ContentAsset(
        draft_id=0, topic_brief_id=0, channel=channel, title="测试文章标题",
        final_body="正文", structured_json=structured or {},
        fact_pack_id=1, fact_pack_version=1, approved_revision=1, reviewer="r@x",
    )
    db_session.add(asset)
    db_session.commit()
    return asset


# ---------- 配图素材 ----------


def test_media_lazy_generated_from_prompts(client, seed_users, db_session):
    asset = _asset(
        db_session,
        structured={
            "cover_text": "封面主文案",
            "image_prompts": ["城市天际线夜景，冷色调", "油价曲线突破新高的信息图"],
        },
    )
    resp = client.get(f"/api/v1/assets/{asset.id}/media", headers=ADMIN)
    assert resp.status_code == 200
    media = resp.json()
    assert [m["kind"] for m in media] == ["cover", "inline", "inline"]
    assert media[0]["prompt"] == "封面主文案"
    assert "油价曲线" in media[2]["prompt"]
    assert all(m["url"].endswith("/raw") for m in media)
    # 占位本体是 SVG
    raw = client.get(media[1]["url"])
    assert raw.status_code == 200 and raw.text.startswith("<svg")


def test_media_wechat_suggestions(client, seed_users, db_session):
    asset = _asset(
        db_session, channel="wechat",
        structured={"image_suggestions": ["配图建议：宏观指标仪表盘"]},
    )
    media = client.get(f"/api/v1/assets/{asset.id}/media", headers=ADMIN).json()
    assert len(media) == 2
    assert "宏观指标仪表盘" in media[1]["prompt"]


def test_media_upload_and_only_append(client, seed_users, db_session):
    from io import BytesIO

    asset = _asset(db_session, structured={"image_prompts": ["示意图"]})
    media = client.get(f"/api/v1/assets/{asset.id}/media", headers=EDITOR).json()
    slot = media[1]
    files = {"file": ("pic.png", BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 64), "image/png")}
    resp = client.post(
        f"/api/v1/assets/{asset.id}/media/{slot['id']}/upload", headers=EDITOR, files=files
    )
    assert resp.status_code == 200, resp.text
    # 只增不改：同序位出现 upload 记录，原占位保留
    after = client.get(f"/api/v1/assets/{asset.id}/media", headers=ADMIN).json()
    uploads = [m for m in after if m["source"] == "upload"]
    assert len(uploads) == 1 and uploads[0]["sort_order"] == slot["sort_order"]
    raw = client.get(uploads[0]["url"])
    assert raw.status_code == 200 and raw.content.startswith(b"\x89PNG")
    # 非 PNG/JPG 拒绝
    bad = {"file": ("x.txt", BytesIO(b"hello"), "text/plain")}
    assert client.post(f"/api/v1/assets/{asset.id}/media/{slot['id']}/upload", headers=EDITOR, files=bad).status_code == 400


# ---------- HTML 导出 ----------


def test_wechat_html_export(client, seed_users, db_session):
    asset = _asset(db_session, channel="wechat")
    asset.final_body = "# 标题\n\n**加粗**正文段落\n\n- 要点一\n- 要点二\n\n> 风险提示"
    db_session.commit()
    resp = client.post("/api/v1/assets/1/export", headers=ADMIN, json={"fmt": "html"})
    assert resp.status_code == 200, resp.text
    content = resp.json()["content"]
    assert content.startswith("<!DOCTYPE html>")
    assert "<article" in content and "font-family" in content
    assert "要点一" in content
    # 抖音不允许 html
    douyin = _asset(db_session, channel="douyin")
    resp = client.post(f"/api/v1/assets/{douyin.id}/export", headers=ADMIN, json={"fmt": "html"})
    assert resp.status_code == 400


# ---------- 技能扫描目录可配置 ----------


def test_plugins_skill_dirs_custom(client, seed_users, tmp_path, reset_runtime_plugins):
    skill = tmp_path / "custom-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: custom-skill\ndescription: 自定义目录技能\n---\n", encoding="utf-8")
    resp = client.put(
        "/api/v1/settings/plugins", headers=ADMIN,
        json={"skill_dirs": [str(tmp_path)], "skills_enabled": [], "mcp": []},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [s["name"] for s in body["skills"]] == ["custom-skill"]  # 自定义目录替代默认
    assert body["skill_dirs"] == [str(tmp_path)]


def test_plugins_skill_dirs_missing_rejected(client, seed_users, reset_runtime_plugins):
    resp = client.put(
        "/api/v1/settings/plugins", headers=ADMIN,
        json={"skill_dirs": ["/nonexistent-dir-xyz"], "skills_enabled": [], "mcp": []},
    )
    assert resp.status_code == 422


@pytest.fixture
def reset_runtime_plugins():
    yield
    runtime_config.clear_all()


def test_scan_skills_custom_dir(tmp_path):
    (tmp_path / "s1").mkdir()
    (tmp_path / "s1" / "SKILL.md").write_text("---\nname: s1\ndescription: d\n---\n", encoding="utf-8")
    assert [s["name"] for s in scan_skills([tmp_path])] == ["s1"]


# ---------- dsh 集成 ----------


def test_dsh_snapshot_reads_user_settings():
    snap = snapshot()
    assert snap["configured"] in (True, False)  # 本机有 ~/.dsh 则 True
    assert "providers" in snap and "env_keys" in snap
    view = studio_view(None)
    assert view["config"]["default_provider"] == "minimax"


def test_dsh_apply_default_model(tmp_path):
    home = tmp_path / ".dsh"
    home.mkdir()
    (home / "settings.yaml").write_text(
        "# 注释保留测试\nllm-pi-ai:\n  providers: {}\nagent-default-model:\n"
        "  provider: minimax\n  model: MiniMax-M3\n",
        encoding="utf-8",
    )
    result = apply_default_model("deepseek", "deepseek-chat", dsh_home=home)
    assert result["ok"] is True
    text = (home / "settings.yaml").read_text(encoding="utf-8")
    assert "provider: deepseek" in text and "model: deepseek-chat" in text
    assert "# 注释保留测试" in text  # 注释未被 yaml 重写破坏
    assert list(home.glob("settings.yaml.bak-*"))  # 有备份


def test_dsh_apply_rejects_unexpected_structure(tmp_path):
    home = tmp_path / ".dsh"
    home.mkdir()
    (home / "settings.yaml").write_text("other: config\n", encoding="utf-8")
    result = apply_default_model("deepseek", "deepseek-chat", dsh_home=home)
    assert result["ok"] is False


def test_dsh_put_requires_admin(client, seed_users):
    resp = client.put("/api/v1/settings/dsh", headers={"X-Studio-User": "editor@studio.local"}, json={})
    assert resp.status_code == 403
