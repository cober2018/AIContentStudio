"""V1 平台 Profiles golden cases（Phase 7 / capability: v1-platform-artifacts）。

R2 验收修正后每个 target 的最小验收：profile resolves → /generate 启动**真实 WorkflowRun**
（共享 Bundle，节点经 registry 执行）→ 人工节点经引擎 complete → v2 批准（候选冻结
workflow/plugin/SEO 快照）→ copy package builds。小红书零图必须先被 media_requirements
blocker 拦截，补真实 Material 后才可批准。不要求远端自动发布（unverified / copy package）。
"""

import struct
import zlib

import pytest
from sqlalchemy import select

from app.models import Draft
from app.seed import seed_v1_channel_profiles
from app.services import workflow_engine  # noqa: F401  导入即注册 builtin node plugins
from app.services.content_harness import channel_registry
from app.services.content_harness.registry import registry
from app.services.content_harness.renderers import bootstrap_renderers
from app.services.workflow_templates import FAMILY_STEPS, build_catalog_workflow

ADMIN = {"X-Studio-User": "admin@studio.local"}
EDITOR = {"X-Studio-User": "editor@studio.local"}
REVIEWER = {"X-Studio-User": "reviewer@studio.local"}

# (channel, default content_form, 期望 artifact_kind, 目标 family)
GOLDEN_CASES = [
    ("wechat", "article", "text", "workflow.article.editorial"),
    ("toutiao", "article", "text", "workflow.article.feed"),
    ("baijia", "article", "text", "workflow.article.feed"),
    ("zhihu", "article", "text", "workflow.article.editorial"),
    ("zhihu", "answer", "text", "workflow.qa.answer"),
    ("bilibili", "article", "text", "workflow.article.editorial"),
    ("sohu", "article", "text", "workflow.article.feed"),
    ("penguin", "article", "text", "workflow.article.feed"),
    ("netease", "article", "text", "workflow.article.feed"),
    ("xiaohongshu", "image_note", "image", "workflow.image.cards"),
    ("x", "single", "text", "workflow.social.short"),
    ("x", "thread", "text", "workflow.social.thread"),
    ("weibo", "single", "text", "workflow.social.short"),
    ("xueqiu", "quant_research", "text", "workflow.finance.article"),
    ("juejin", "tech_article", "text", "workflow.tech.article"),
    ("douyin", "spoken_script", "script", "workflow.script.spoken"),
]


@pytest.fixture
def seeded(db_session):
    db_session.add(User_row())
    seed_v1_channel_profiles(db_session)
    db_session.commit()
    bootstrap_renderers()
    return db_session


def User_row():
    from app.models import User

    return User(email="admin@studio.local", name="A", role="admin")


def _client(db):
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    return TestClient(app)


def test_profile_resolves_for_all_golden_cases(seeded):
    for channel, form, artifact, _family in GOLDEN_CASES:
        spec = channel_registry.resolve_content_form(seeded, channel, form)
        assert spec.artifact_kind == artifact, channel
        assert spec.source == "profile"
        assert spec.profile_version_id is not None


def test_workflow_families_instantiate_with_resolvable_plugins(seeded):
    for family in FAMILY_STEPS:
        # R2-B1：共享 Bundle 以「无 channel 参数」构建（target 由 run 参数承载）
        definition = build_catalog_workflow(family)
        assert definition["nodes"] and definition["edges"]
        assert not any((n.get("params") or n.get("config") or {}).get("channel") for n in definition["nodes"])
        for node in definition["nodes"]:
            key, version = node["plugin"], node["plugin_version"]
            registry.resolve("node", key, version)  # 不可解析即抛错


def _png_bytes(rgb=(37, 99, 235)) -> bytes:
    """测试用真实 PNG 字节（非 SVG/placeholder）。"""
    w, h = 64, 64
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def _upload_use_media(client, draft_id: int, role: str, editor):
    """上传真实图片并挂载为指定 role 的 use（public_use_allowed=true，走 query 参数）。

    每个 role 用不同字节：DraftMedia 以 content_hash 幂等，同 hash 二次挂载会被去重。
    """
    rgb = (37, 99, 235) if role == "cover" else (220, 38, 38)
    resp = client.post(
        f"/api/v1/drafts/{draft_id}/materials/upload",
        files={"file": (f"{role}.png", _png_bytes(rgb), "image/png")},
        params={"role": role, "rights_status": "cleared", "public_use_allowed": "true"},
        headers=editor,
    )
    assert resp.status_code == 201, resp.json()
    return resp.json()


def test_all_golden_targets_end_to_end(seeded):
    """全链路（R2 修正版）：Profile → 真实 WorkflowRun → 节点 → Candidate → copy package。

    - /generate 不再绕开工作流：每个 target 断言返回 workflow_run_id 且冻结期望 family；
    - 批准走引擎 approve 节点 complete（内部调用同一 Review Gate）；
    - 小红书：零图先被 blocker 拦截，补 cover+inline 真实素材后才通过；
    - 公众号：补已批准封面 + 运行 post SEO 报告（冻结进 candidate hash）。
    """
    from app.models import ContentAsset

    db = seeded
    client = _client(db)
    channels = {c["channel"]: c for c in client.get("/api/v1/channels", headers=EDITOR).json()}

    for channel, form, artifact, family in GOLDEN_CASES:
        assert channel in channels, channel

        # topic（targets 真源）
        packs = client.get("/api/v1/fact-packs?status=frozen", headers=EDITOR).json()
        if not packs:
            # 建最小 frozen pack
            src = client.post("/api/v1/sources/text", json={"title": "源", "as_of": "2026-09-24", "content": "沪深300上涨1.2%，成交额1.1万亿。"}, headers=EDITOR).json()
            client.post(f"/api/v1/sources/{src['id']}/extract-facts", headers=EDITOR)
            facts = [f["id"] for f in client.get(f"/api/v1/sources/{src['id']}", headers=EDITOR).json()["facts"]]
            for fid in facts:
                client.post(f"/api/v1/facts/{fid}/confirm", headers=EDITOR)
            pack = client.post("/api/v1/fact-packs", json={"name": f"golden-{channel}-{form}", "fact_ids": facts}, headers=EDITOR).json()
            client.post(f"/api/v1/fact-packs/{pack['id']}/freeze", headers=EDITOR)
            packs = [pack]
        topic = client.post(
            "/api/v1/topics",
            json={"title": f"golden {channel}/{form}", "fact_pack_id": packs[0]["id"], "targets": [{"channel": channel, "content_form": form}]},
            headers=EDITOR,
        )
        assert topic.status_code == 201, f"{channel}/{form}: {topic.json()}"
        topic_id = topic.json()["id"]

        # R2-B1：主生产入口必须启动真实 WorkflowRun（不再先建 workflow 再绕开）
        gen = client.post(f"/api/v1/topics/{topic_id}/generate", headers=EDITOR)
        assert gen.status_code == 201, f"{channel}/{form}: {gen.json()}"
        job = gen.json()["jobs"][0]
        run_id = job.get("workflow_run_id")
        assert run_id, f"{channel}/{form}: generate 未创建 WorkflowRun：{job}"
        assert job["status"] == "succeeded", f"{channel}/{form}: {job}"
        detail = client.get(f"/api/v1/drafts/{job['draft_id']}", headers=EDITOR).json()
        assert detail["title"], f"{channel}/{form} 缺标题"
        # censor/humanize 可能产出新 revision：批准节点作用于「最新」稿，素材/SEO 也挂最新稿。
        # （TestClient 共享 db 会话且 expire_on_commit=False，job.drafts 关系可能是旧快照——直接查库）
        db.expire_all()
        draft_id = db.execute(
            select(Draft.id)
            .where(Draft.content_job_id == job["job_id"])
            .order_by(Draft.revision_no.desc())
            .limit(1)
        ).scalar_one()

        run = client.get(f"/api/v1/workflow-runs/{run_id}", headers=EDITOR).json()
        assert run["workflow_key"] == family, f"{channel}/{form}: {run.get('workflow_key')}"
        assert run["channel"] == channel and run["content_form"] == form
        approve_steps = [s for s in run["steps"] if s["node_id"].startswith("approve")]
        assert approve_steps and approve_steps[0]["status"] == "waiting_input", f"{channel}/{form}: 批准节点未挂起：{approve_steps}"
        gen_steps = [s for s in run["steps"] if s["node_id"].startswith("gen")]
        assert gen_steps and gen_steps[0]["status"] == "succeeded"
        assert gen_steps[0]["plugin_key"], "生成节点未钉死 plugin"
        # R3-2：SEO 审查是 Workflow Timeline 的独立 Stage（disco 节点在 approve 之前已执行）
        disco_steps = [s for s in run["steps"] if s["node_id"].startswith("disco")]
        assert disco_steps and disco_steps[0]["status"] == "succeeded", f"{channel}/{form}: {disco_steps}"
        # R4-B2：family 含 fact_check 节点的（全部 family），工作流自身完成 FactCheck——
        # 不存在「测试/用户手工补调用才能过批准闸」的外部依赖
        check_steps = [s for s in run["steps"] if s["node_id"].startswith("check")]
        assert check_steps and check_steps[0]["status"] == "succeeded", f"{channel}/{form}: {check_steps}"

        # R4-B2：FactCheck 由工作流 check 节点完成（上方断言），不再手工补调用
        _ = draft_id
        approve_node_id = approve_steps[0]["node_id"]

        if (channel, form) == ("xiaohongshu", "image_note"):
            # R2-B2：零图必须 blocker（Prompt 不算成品）
            blocked = client.post(
                f"/api/v1/workflow-runs/{run_id}/nodes/{approve_node_id}/complete",
                json={"payload": {}}, headers=REVIEWER,
            )
            assert blocked.status_code == 409, f"小红书零图未被拦截：{blocked.json()}"
            reasons = str(blocked.json())
            assert "missing_required_cover" in reasons and "missing_required_inline_media" in reasons, reasons
            # 补真实素材（cover + inline）后重试
            _upload_use_material = _upload_use_media(client, draft_id, "cover", EDITOR)
            _upload_use_media(client, draft_id, "inline", EDITOR)
            assert _upload_use_material["role"] == "cover"

        # R3-2：profile 声明了 discoverability_profile 的形态由 disco 节点产出 post 报告
        # （不再是测试手工 POST——节点属于 Workflow Timeline）；未声明形态节点空转 ran=False
        spec = channel_registry.resolve_content_form(db, channel, form)
        if channel == "wechat":
            # 公众号封面必需（publisher 不再造 placeholder），批准闸前补真实素材
            _upload_use_media(client, draft_id, "cover", EDITOR)

        # 批准经真实工作流节点（_h_approve → 同一 Review Gate → ContentAsset）
        approve = client.post(
            f"/api/v1/workflow-runs/{run_id}/nodes/{approve_node_id}/complete",
            json={"payload": {}}, headers=REVIEWER,
        )
        assert approve.status_code == 200, f"{channel}/{form}: {approve.json()}"
        run_after = approve.json()
        asset_id = (run_after["context"].get("assets") or {}).get(channel)
        assert asset_id, f"{channel}/{form}: 批准节点未产出 asset：{run_after['context']}"
        disco_out = disco_steps[0].get("output") or {}
        assert disco_out.get("ran") is bool(spec.discoverability_profile), (
            f"{channel}/{form}: disco 节点空转语义不符：{disco_out}（profile 声明={spec.discoverability_profile}）"
        )

        # R2-B4：candidate 冻结 workflow/plugin/SEO 快照
        asset = db.get(ContentAsset, asset_id)
        manifest = asset.candidate_manifest_json or {}
        assert manifest["schema_version"] == 2
        execution = manifest["execution"]
        assert execution["workflow_key"] == family
        assert execution["workflow_run_id"] == run_id
        assert execution["plugins"], f"{channel}/{form}: candidate 未冻结 plugin 版本"
        plugin_keys = {p["key"] for p in execution["plugins"]}
        assert "builtin.generate" in plugin_keys
        if spec.discoverability_profile:
            assert manifest["discoverability"] and manifest["discoverability"]["report_id"]
            assert manifest["discoverability_required"] is True
        if (channel, form) == ("x", "thread"):
            # R2-M9：renderer 由 profile renderer_key 驱动（x/thread ≠ generic）
            assert manifest["render"]["renderer_key"] == "renderer.x.thread", manifest["render"]

        # R2-H7：节点执行有可审计 attempt 历史
        attempts = client.get(f"/api/v1/workflow-runs/{run_id}/nodes/{gen_steps[0]['node_id']}/attempts", headers=EDITOR).json()
        assert attempts and attempts[0]["status"] == "succeeded" and attempts[0]["output_hash"]

        # copy package builds（universal fallback）
        target = client.post(
            f"/api/v1/assets/{asset_id}/delivery-targets",
            json={"channel": channel, "content_form": form, "account_ref": "golden", "authorization_version": "v1", "action": "copy_package"},
            headers=EDITOR,
        )
        assert target.status_code == 201, f"{channel}/{form}: {target.json()}"
        package = client.post(f"/api/v1/delivery-targets/{target.json()['id']}/package", headers=EDITOR)
        assert package.status_code == 200, f"{channel}/{form}: {package.json()}"
        assert package.json()["manifest"]["schema_version"] == 2


def test_install_missing_profiles_keeps_existing_published_profile_and_promotes_legacy(db_session):
    from types import SimpleNamespace

    from app.models import ChannelTemplateVersion
    from app.seed import install_missing_channel_profiles
    from app.services.channel_variants import _profile_check

    db_session.add(ChannelTemplateVersion(channel="douyin", name="旧口播模板", version=2, status="published", structure=[]))
    db_session.commit()
    created = install_missing_channel_profiles(db_session)
    db_session.commit()
    assert "wechat" in created and "xiaohongshu" in created and "douyin" in created
    assert "xueqiu" in created and "juejin" in created
    legacy = db_session.query(ChannelTemplateVersion).filter_by(channel="douyin", version=2).one()
    assert legacy.status == "archived"
    current = db_session.query(ChannelTemplateVersion).filter_by(channel="douyin", status="published").one()
    assert current.profile_json["content_forms"]["spoken_script"]["artifact_kind"] == "script"
    wechat = db_session.query(ChannelTemplateVersion).filter_by(channel="wechat", status="published").one()
    wechat.profile_json = {"content_forms": {"article": {
        "artifact_kind": "text", "renderer_key": "wechat.official.html",
        "publisher_candidates": ["publisher.wechat.official"], "media_requirements": {"cover": "required"},
    }}}
    db_session.commit()
    assert install_missing_channel_profiles(db_session) == []
    db_session.refresh(wechat)
    assert wechat.profile_json["content_forms"]["article"]["publisher_candidates"] == ["publisher.wechat.official"]

    xueqiu = db_session.query(ChannelTemplateVersion).filter_by(channel="xueqiu", status="published").one()
    blocked = SimpleNamespace(profile_template_version_id=xueqiu.id, content_form="quant_research", payload_schema="xueqiu.quant_research.v1",
                              payload_json={"title": "研究", "blocks": [{"text": "这是保证收益"}]})
    status, report = _profile_check(db_session, blocked, [])
    assert status == "blocker"
    assert "finance_as_of_missing" in report["reasons"] and "finance_return_guarantee" in report["reasons"]
    dated = SimpleNamespace(profile_template_version_id=xueqiu.id, content_form="market_recap", payload_schema="xueqiu.market_recap.v1",
                            payload_json={"title": "复盘", "blocks": [{"text": "截至2026-09，指数上涨1.2%。"}]})
    assert _profile_check(db_session, dated, [])[0] == "pass"
    juejin = db_session.query(ChannelTemplateVersion).filter_by(channel="juejin", status="published").one()
    coded = SimpleNamespace(profile_template_version_id=juejin.id, content_form="tech_article", payload_schema="juejin.tech_article.v1",
                            payload_json={"title": "实现", "blocks": [{"text": "```\nprint(1)\n```"}]})
    warned, warning = _profile_check(db_session, coded, [])
    assert warned == "warning" and warning["reasons"] == ["tech_code_provenance_missing"]
