"""R2 验收修正回归（2026-09-24 评审复核后的 acceptance-fix 批次）。

对应复核结论的阻断/次级问题：
- B1 主生产入口按 target 启动独立 WorkflowRun（多 target 各自冻结 family）；
- B2 Channel Profile media_requirements 在 readiness 直接强制；
- B3 publisher 只发已批准载荷（缺封面 fail、digest 不截断）；
- B4 candidate v2 冻结 plugins / discoverability 快照；
- H5 node.skill 无可执行 runtime 时 create_run 409；
- H6 skills_enabled 禁用集生效；
- H7 rerun 前后新旧 output 均可审计（attempt 历史 API）；
- M8 换图不失效正文 FactCheck、只失效 media/rights check runs；
- M9 renderer 由 profile renderer_key 驱动（x/thread ≠ generic）；
- M10 unverified auto_draft 默认禁止执行、配置显式放行。
"""

import pytest
from sqlalchemy import select

from app.models import ContentJob, Draft, FactPack, TopicBrief, User, utcnow
from app.seed import seed_v1_channel_profiles
from app.services.candidates import build_manifest_v2, readiness_reasons_v2
from app.services.checks import record_check_run
from app.services.content_harness.renderers import render_for

EDITOR = {"X-Studio-User": "editor@studio.local"}
ADMIN = {"X-Studio-User": "admin@studio.local"}
PNG = b"\x89PNG\r\n\x1a\n" + b"r2" * 8


def _client(db):
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    return TestClient(app)


@pytest.fixture
def seeded(db_session):
    for email, role in [
        ("admin@studio.local", "admin"),
        ("editor@studio.local", "editor"),
        ("reviewer@studio.local", "reviewer"),
    ]:
        db_session.add(User(email=email, name=email[0], role=role))
    seed_v1_channel_profiles(db_session)
    db_session.commit()
    return db_session


def _make_topic_with_frozen_pack(client, targets):
    src = client.post(
        "/api/v1/sources/text",
        json={"title": "源", "as_of": "2026-09-24", "content": "沪深300上涨1.2%，成交额1.1万亿。"},
        headers=EDITOR,
    ).json()
    client.post(f"/api/v1/sources/{src['id']}/extract-facts", headers=EDITOR)
    facts = [f["id"] for f in client.get(f"/api/v1/sources/{src['id']}", headers=EDITOR).json()["facts"]]
    for fid in facts:
        client.post(f"/api/v1/facts/{fid}/confirm", headers=EDITOR)
    pack = client.post("/api/v1/fact-packs", json={"name": "r2-pack", "fact_ids": facts}, headers=EDITOR).json()
    client.post(f"/api/v1/fact-packs/{pack['id']}/freeze", headers=EDITOR)
    topic = client.post(
        "/api/v1/topics",
        json={"title": "r2 多目标", "fact_pack_id": pack["id"], "targets": targets},
        headers=EDITOR,
    )
    assert topic.status_code == 201, topic.json()
    return topic.json()["id"]


_PACK_SEQ = [0]


def _xhs_draft(db, *, with_media: bool = False) -> Draft:
    """构造带 profile 的 xiaohongshu/image_note 草稿（不走 LLM）。"""
    _PACK_SEQ[0] += 1
    pack = FactPack(name=f"r2包{_PACK_SEQ[0]}", version=1, status="frozen", checksum="8" * 64)
    db.add(pack)
    db.flush()
    topic = TopicBrief(title="小红书 readiness", fact_pack_id=pack.id, fact_pack_version=1)
    db.add(topic)
    db.flush()
    job = ContentJob(
        topic_brief_id=topic.id, channel="xiaohongshu", content_form="image_note",
        artifact_kind="image", status="succeeded",
    )
    db.add(job)
    db.flush()
    draft = Draft(
        content_job_id=job.id, revision_no=1, title="小红书标题", body="正文",
        artifact_kind="image", content_form="image_note",
        input_hash="9" * 64, fact_check_json={"result": "pass", "input_hash": "9" * 64, "stats": {"blockers": 0, "warnings": 0}},
    )
    db.add(draft)
    db.flush()
    record_check_run(db, draft, check_kind="fact", status="pass", report={"result": "pass"}, input_hash="9" * 64)
    record_check_run(db, draft, check_kind="platform", status="pass", report={}, input_hash="9" * 64)
    if with_media:
        from app.services import materials as materials_service

        material = materials_service.create_material(db, kind="image", title="封面")
        cover = materials_service.create_revision(
            db, material, content=PNG, suffix=".png", declared_mime="image/png",
            public_use_allowed=True, rights_status="cleared",
        )
        materials_service.attach_to_draft(db, draft, cover, role="cover")
        material2 = materials_service.create_material(db, kind="image", title="内嵌")
        inline = materials_service.create_revision(
            db, material2, content=PNG + b"2", suffix=".png", declared_mime="image/png",
            public_use_allowed=True, rights_status="cleared",
        )
        materials_service.attach_to_draft(db, draft, inline, role="inline")
    if with_media:
        from app.services.document_composition import sync_document

        sync_document(db, draft)
    db.commit()
    return draft


# ---------- B1：主生产入口按 target 启动独立 WorkflowRun ----------


def test_generate_creates_independent_run_per_target(seeded):
    """同一 Topic 多 target：每个 channel × content_form 一个独立 WorkflowRun（冻结各自 family）。"""
    from app.models import ContentJob, WorkflowRun

    client = _client(seeded)
    topic_id = _make_topic_with_frozen_pack(
        client,
        [
            {"channel": "wechat", "content_form": "article"},
            {"channel": "x", "content_form": "thread"},
            {"channel": "x", "content_form": "single"},
        ],
    )
    gen = client.post(f"/api/v1/topics/{topic_id}/generate", headers=EDITOR)
    assert gen.status_code == 201, gen.json()
    jobs = gen.json()["jobs"]
    assert len(jobs) == 3
    run_ids = [j["workflow_run_id"] for j in jobs]
    assert len(set(run_ids)) == 3, "三个 target 必须各自独立 WorkflowRun"

    keys = {}
    for job in jobs:
        assert job["status"] == "succeeded", job
        row = seeded.get(ContentJob, job["job_id"])
        assert row.workflow_run_id == job["workflow_run_id"], "ContentJob 必须挂到对应 run"
        run = seeded.get(WorkflowRun, row.workflow_run_id)
        assert run.topic_id == topic_id
        assert (run.channel, run.content_form) == (job["channel"], job["content_form"])
        keys[(run.channel, run.content_form)] = run.workflow_key
    assert keys[("wechat", "article")] == "workflow.article.editorial"
    assert keys[("x", "thread")] == "workflow.social.thread"
    assert keys[("x", "single")] == "workflow.social.short"


# ---------- B2：media_requirements 直接强制 ----------


def test_readiness_blocks_zero_media_xhs_and_passes_with_real_media(seeded):
    draft = _xhs_draft(seeded, with_media=False)
    manifest = build_manifest_v2(seeded, draft)
    reasons = readiness_reasons_v2(seeded, draft, manifest)
    assert "missing_required_cover" in reasons
    assert "missing_required_inline_media" in reasons

    draft2 = _xhs_draft(seeded, with_media=True)
    manifest2 = build_manifest_v2(seeded, draft2)
    reasons2 = readiness_reasons_v2(seeded, draft2, manifest2)
    assert "missing_required_cover" not in reasons2
    assert "missing_required_inline_media" not in reasons2


# ---------- B3：publisher 只发已批准载荷 ----------


def _wechat_publisher():
    from app.services.content_harness.publishers.wechat_wewrite import WechatWewritePublisher

    return WechatWewritePublisher()


def _manifest(*, digest=None, cover=b""):
    payload = {"title": "交付标题", "markdown": "# 正文", "digest": digest if digest is not None else "交付标题"}
    return {
        "schema_version": 2,
        "render": {"payload": payload},
        "media": [],
        "_cover_bytes": cover,
    }


def test_publisher_fails_without_approved_cover(seeded):
    result = _wechat_publisher().deliver(_manifest(cover=b""), target=None, attempt=None)
    assert result.status == "failed"
    assert "缺少已批准封面" in (result.error or "")


def test_publisher_never_truncates_digest(seeded):
    long_digest = "摘" * 200
    result = _wechat_publisher().deliver(_manifest(digest=long_digest, cover=PNG), target=None, attempt=None)
    assert result.status == "failed"
    assert "120" in (result.error or ""), "超长 digest 必须 fail 而非截断"


# ---------- B4：candidate 冻结 plugins / discoverability 快照 ----------


def test_manifest_freezes_execution_plugins_from_run(seeded):
    """带 WorkflowRun 的 job：manifest.execution.plugins 来自 step 钉死记录。"""
    client = _client(seeded)
    topic_id = _make_topic_with_frozen_pack(client, [{"channel": "x", "content_form": "thread"}])
    gen = client.post(f"/api/v1/topics/{topic_id}/generate", headers=EDITOR).json()
    job = gen["jobs"][0]
    from sqlalchemy import select

    draft = seeded.execute(
        select(Draft).where(Draft.content_job_id == job["job_id"]).order_by(Draft.revision_no.desc()).limit(1)
    ).scalar_one()
    manifest = build_manifest_v2(seeded, draft)
    execution = manifest["execution"]
    assert execution["workflow_key"] == "workflow.social.thread"
    assert execution["workflow_run_id"] == job["workflow_run_id"]
    keys = {p["key"] for p in execution["plugins"]}
    assert "builtin.generate" in keys and "builtin.fact_check" in keys
    assert all(p.get("version") for p in execution["plugins"]), "plugin 版本必须钉死"


def test_manifest_freezes_discoverability_from_workflow_node(seeded):
    """R3-2 后：post 报告由工作流 disco 节点产出并冻结进 manifest（不再依赖测试手工 POST）。

    无报告时（如手工构造）readiness 仍按 profile 声明报 missing_discoverability_report。
    """
    client = _client(seeded)
    topic_id = _make_topic_with_frozen_pack(client, [{"channel": "wechat", "content_form": "article"}])
    gen = client.post(f"/api/v1/topics/{topic_id}/generate", headers=EDITOR).json()
    job = gen["jobs"][0]
    from sqlalchemy import select

    from app.models import DiscoverabilityReport

    # disco 节点已在 run 内产出 post 报告
    reports = seeded.query(DiscoverabilityReport).filter_by(topic_id=topic_id, stage="post").all()
    assert reports, "disco 节点未产出 post 报告"

    draft = seeded.execute(
        select(Draft).where(Draft.content_job_id == job["job_id"]).order_by(Draft.revision_no.desc()).limit(1)
    ).scalar_one()
    manifest = build_manifest_v2(seeded, draft)
    assert manifest["discoverability_required"] is True
    assert manifest["discoverability"] and manifest["discoverability"]["report_id"] == reports[0].id
    reasons = readiness_reasons_v2(seeded, draft, manifest)
    assert "missing_discoverability_report" not in reasons

    # 无报告的构造稿：readiness 按 profile 声明拦截
    bare = _xhs_draft(seeded)  # xiaohongshu 未声明 SEO → 不触发该 reason
    _ = bare
    draft2 = seeded.execute(
        select(Draft).where(Draft.content_job_id == job["job_id"]).order_by(Draft.revision_no.desc()).limit(1)
    ).scalar_one()
    manifest_bare = dict(manifest)
    manifest_bare["discoverability"] = None
    assert "missing_discoverability_report" in readiness_reasons_v2(seeded, draft2, manifest_bare)


# ---------- H5：node.skill 无可执行 runtime → 启动前拒绝 ----------


def test_node_skill_workflow_rejected_at_start_without_runtime(seeded, db_session):
    from app.models import Workflow
    from app.services.content_harness import registry as plugin_registry
    from app.services.content_harness.skill_runtime import resolve_executable_runtime
    from app.services.workflow_engine import definition_checksum, start_run

    assert resolve_executable_runtime() is None, "内置 runtime 不可执行（如实）"
    definition = {
        "nodes": [
            {"id": "s1", "plugin": "node.skill", "plugin_version": "1", "config": {"skill": "任意"}, "layout": {}},
        ],
        "edges": [],
    }
    wf = Workflow(
        name="skill-flow", workflow_key="workflow.skill.test", version=1, schema_version=2,
        status="published", checksum=definition_checksum(definition), definition_json=definition,
    )
    db_session.add(wf)
    db_session.commit()
    user = db_session.query(User).filter_by(email="editor@studio.local").first()
    with pytest.raises(ValueError, match="无可执行 SkillRuntime"):
        start_run(db_session, wf, {}, user)

    # node.skill 插件本体已注册（有真实 runtime 时可执行）
    plugin = plugin_registry.resolve("node", "node.skill", "1")
    assert plugin is not None


# ---------- H6：skills_enabled 禁用集生效 ----------


def test_preflight_respects_skills_enabled(tmp_path, monkeypatch):
    """R3-4 三态语义：未配置=默认政策放行；[]=全禁用；白名单=只允许列表内。"""
    from app import runtime_config
    from app.services.content_harness import skill_runtime
    from app.services.plugin_registry import scan_skills

    installed = tmp_path / "s1"
    installed.mkdir()
    (installed / "SKILL.md").write_text("---\nname: skill-x\nversion: 1.0.0\n---\n正文", encoding="utf-8")
    import app.services.plugin_registry as pr

    monkeypatch.setattr(pr, "scan_skills", lambda dirs=None: scan_skills((tmp_path,)))
    definition = {"nodes": [{"id": "n1", "config": {"skill": "skill-x"}}], "edges": []}

    # 未配置（无 plugins / 无 skills_enabled 键）→ 系统默认政策：不启用 enable gate
    monkeypatch.setattr(runtime_config, "get_runtime", lambda key: None)
    assert skill_runtime.preflight_workflow(None, definition) == []

    # skills_enabled=[] → 明确全部禁用
    monkeypatch.setattr(runtime_config, "get_runtime", lambda key: {"skills_enabled": []})
    problems = skill_runtime.preflight_workflow(None, definition)
    assert any("not enabled" in p and "skill-x" in p for p in problems), problems

    # 白名单不含 → 禁用；含 → 放行
    monkeypatch.setattr(runtime_config, "get_runtime", lambda key: {"skills_enabled": ["other-skill"]})
    problems = skill_runtime.preflight_workflow(None, definition)
    assert any("not enabled" in p and "skill-x" in p for p in problems)
    monkeypatch.setattr(runtime_config, "get_runtime", lambda key: {"skills_enabled": ["skill-x"]})
    assert skill_runtime.preflight_workflow(None, definition) == []


# ---------- H7：rerun 新旧 output 均可审计 ----------


class BumpPlugin:
    key = "r2.bump"
    version = "1"
    human_gate = False
    side_effect = False
    calls = 0

    def execute(self, db, ctx, config, user):
        BumpPlugin.calls += 1
        from app.services.content_harness.contracts import NodeResult

        return NodeResult(output={"n": BumpPlugin.calls, "marker": f"attempt-{BumpPlugin.calls}"})


def test_rerun_attempt_history_preserves_old_output(db_session):
    from app.models import Workflow
    from app.services.content_harness import registry as plugin_registry
    from app.services.content_harness.registry import RegistryError
    from app.services.workflow_engine import _steps, definition_checksum, rerun_node, start_run

    try:
        plugin_registry.register("node", BumpPlugin.key, "1", BumpPlugin())
    except RegistryError:
        pass
    BumpPlugin.calls = 0
    definition = {
        "nodes": [{"id": "a", "plugin": "r2.bump", "plugin_version": "1", "config": {}, "layout": {}}],
        "edges": [],
    }
    wf = Workflow(
        name="r2-audit", workflow_key="workflow.r2.audit", version=1, schema_version=2,
        status="published", checksum=definition_checksum(definition), definition_json=definition,
    )
    db_session.add(wf)
    user = User(email="editor@studio.local", name="E", role="editor")
    db_session.add(user)
    db_session.commit()

    run = start_run(db_session, wf, {}, user)
    assert run.status == "succeeded"
    rerun_node(db_session, run, "a", user)
    db_session.expire_all()

    step = _steps(db_session, run)[0]
    assert step.attempt_no == 2
    assert step.output_json["marker"] == "attempt-2"  # 当前 = 新 output

    client = _client(db_session)
    history = client.get(f"/api/v1/workflow-runs/{run.id}/nodes/a/attempts", headers=EDITOR).json()
    assert len(history) == 2
    assert history[0]["attempt_no"] == 1 and history[0]["output_json"]["marker"] == "attempt-1"
    assert history[0]["output_hash"] and history[1]["output_hash"]
    assert history[0]["output_hash"] != history[1]["output_hash"], "新旧 output 均可审计且可区分"


# ---------- M8：换图不失效正文 FactCheck ----------


def test_media_change_keeps_fact_check_and_stales_only_media_kinds(seeded):
    draft = _xhs_draft(seeded, with_media=False)
    from app.services import checks as checks_service
    from app.services import materials as materials_service
    from app.services.content_harness import staleness

    record_check_run(seeded, draft, check_kind="media", status="pass", report={}, input_hash=draft.input_hash)
    record_check_run(seeded, draft, check_kind="rights", status="pass", report={}, input_hash=draft.input_hash)
    seeded.commit()

    material = materials_service.create_material(seeded, kind="image", title="后补封面")
    revision = materials_service.create_revision(
        seeded, material, content=PNG + b"m8", suffix=".png", declared_mime="image/png",
        public_use_allowed=True, rights_status="cleared",
    )
    materials_service.attach_to_draft(seeded, draft, revision, role="cover")  # 内部走 mark_media_changed
    seeded.commit()
    seeded.refresh(draft)

    assert draft.fact_check_json is not None, "换图不得清空正文 FactCheck"
    assert draft.candidate_readiness == "stale"
    by_kind = {row.check_kind: row.status for row in checks_service.current_checks(seeded, draft)}
    assert by_kind["media"] == "stale" and by_kind["rights"] == "stale"
    assert by_kind["fact"] == "pass" and by_kind["platform"] == "pass", "正文 fact/platform 检查保持有效"
    _ = staleness


# ---------- M9：renderer 由 profile renderer_key 驱动 ----------


def test_renderer_resolves_from_profile(seeded):
    draft = _xhs_draft(seeded)  # xiaohongshu/image_note → renderer.xhs.cards
    result = render_for(seeded, draft)
    assert result.renderer_key == "renderer.xhs.cards"

    # x/thread：profile 声明 renderer.x.thread（静态渠道映射会错落到 generic）
    pack = FactPack(name="r2包x-thread", version=1, status="frozen", checksum="7" * 64)
    seeded.add(pack)
    seeded.flush()
    topic = TopicBrief(title="x thread", fact_pack_id=pack.id, fact_pack_version=1)
    seeded.add(topic)
    seeded.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="x", content_form="thread", status="succeeded")
    seeded.add(job)
    seeded.flush()
    xdraft = Draft(
        content_job_id=job.id, revision_no=1, title="thread", body="b",
        content_form="thread", thread_posts_json=[{"index": 1, "text": "t1"}],
    )
    seeded.add(xdraft)
    seeded.commit()
    xresult = render_for(seeded, xdraft)
    assert xresult.renderer_key == "renderer.x.thread", "x/thread 必须由 profile renderer_key 驱动"


# ---------- M10：unverified auto_draft 默认禁止 ----------


def test_unverified_auto_draft_denied_by_default(seeded):
    from fastapi import HTTPException

    from app.models import ContentAsset, DeliveryTarget
    from app.services import delivery as delivery_service

    pack = FactPack(name="r2交付包", version=1, status="frozen", checksum="6" * 64)
    seeded.add(pack)
    seeded.flush()
    topic = TopicBrief(title="r2 交付", fact_pack_id=pack.id, fact_pack_version=1)
    seeded.add(topic)
    seeded.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="wechat", content_form="article", status="succeeded")
    seeded.add(job)
    seeded.flush()
    draft = Draft(content_job_id=job.id, revision_no=1, title="t", body="b")
    seeded.add(draft)
    seeded.flush()
    asset = ContentAsset(
        draft_id=draft.id, topic_brief_id=topic.id, channel="wechat", title="t", final_body="b",
        fact_pack_id=pack.id, fact_pack_version=1, fact_pack_checksum="6" * 64,
        reviewer="reviewer@studio.local", approved_revision=1,
        status="approved", approved_candidate_hash="a" * 64,
        candidate_manifest_json={"schema_version": 2, "render": {"payload": {"title": "t", "markdown": "b"}}, "media": []},
    )
    seeded.add(asset)
    seeded.flush()

    class _Payload:
        channel = "wechat"
        content_form = "article"
        account_ref = "acct"
        action = "auto_draft"
        authorization_version = "v1"

    user = seeded.query(User).filter_by(email="editor@studio.local").first()
    target = delivery_service.authorize_target(seeded, asset, _Payload(), user)
    assert target.capability_snapshot_json["verified"] is False

    with pytest.raises(HTTPException) as exc:
        delivery_service.execute_attempt(seeded, target.id, user)
    assert exc.value.status_code == 409
    assert "unverified" in str(exc.value.detail)
    # 未发起任何远端尝试
    assert seeded.query(DeliveryTarget).filter_by(id=target.id).first().status == "target_authorized"


# ==================== R3 批次（二次复核后 archive blocker 收口） ====================


# ---------- R3-1：node.skill 真实执行链（fake runtime 注册 → 执行 → attempt 审计） ----------


def test_node_skill_executes_via_registered_runtime(db_session, monkeypatch):
    """完整执行链：注册可执行 runtime → skill 已安装 → start_run 真正执行 node.skill 节点。

    此前只测了注册与 preflight 拒绝；相对导入 bug（. → ..）曾让执行路径 ImportError。
    """
    from app.models import Workflow
    from app.services.content_harness import registry as plugin_registry
    from app.services.content_harness.contracts import SkillExecutionResult
    from app.services.content_harness.registry import RegistryError
    from app.services.workflow_engine import definition_checksum

    calls = []

    class FakeRuntime:
        key = "skill_runtime.r2fake"
        version = "1"

        def execute(self, skill, input_payload, timeout_sec):
            calls.append({"skill": skill, "payload": input_payload, "timeout": timeout_sec})
            return SkillExecutionResult(status="succeeded", output={"echo": skill["name"], "ok": True})

    try:
        plugin_registry.register("skill_runtime", "skill_runtime.r2fake", "1", FakeRuntime())
    except RegistryError:
        pass

    tmp_skills(monkeypatch, {"skill-x": "1.0.0"})
    # R4-B1：使用正式 schema v2 的 config 字段（此前曾因 start_run 只读 params 而丢失）
    definition = {
        "nodes": [
            {"id": "s1", "plugin": "node.skill", "plugin_version": "1", "config": {"skill": "skill-x", "skill_version": "1.0.0"}, "layout": {"x": 0, "y": 0}},
        ],
        "edges": [],
    }
    wf = Workflow(
        name="skill-exe", workflow_key="workflow.skill.exe", version=1, schema_version=2,
        status="published", checksum=definition_checksum(definition), definition_json=definition,
    )
    db_session.add(wf)
    user = db_session.query(User).filter_by(email="editor@studio.local").first()
    db_session.commit()

    try:
        _run_skill_execution_assertions(db_session, wf, user, calls)
    finally:
        # 全局 registry 是进程级单例：必须摘除 fake runtime，避免污染后续测试的 preflight 语义
        plugin_registry.registry._items.pop(("skill_runtime", "skill_runtime.r2fake", "1"), None)
        plugin_registry.registry._descriptors.pop(("skill_runtime", "skill_runtime.r2fake", "1"), None)


def _run_skill_execution_assertions(db_session, wf, user, calls):
    from app.models import WorkflowStepAttempt
    from app.services.workflow_engine import _steps, start_run

    run = start_run(db_session, wf, {}, user)
    assert run.status == "succeeded", run.error
    assert calls and calls[0]["skill"]["name"] == "skill-x", "runtime 未被真正调用"
    step = _steps(db_session, run)[0]
    assert step.status == "succeeded"
    assert step.output_json["result"]["echo"] == "skill-x"
    # R2-H7 联动：node.skill 执行同样落 attempt 审计行
    attempts = db_session.scalars(
        select(WorkflowStepAttempt).where(WorkflowStepAttempt.step_id == step.id)
    ).all()
    assert len(attempts) == 1 and attempts[0].output_hash


def tmp_skills(monkeypatch, skills: dict[str, str]):
    """构造已安装 skill 目录并 monkeypatch scan_skills。"""
    import tempfile
    from pathlib import Path

    from app.services.plugin_registry import scan_skills

    root = Path(tempfile.mkdtemp())
    for name, version in skills.items():
        d = root / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"---\nname: {name}\nversion: {version}\n---\n正文", encoding="utf-8")
    import app.services.plugin_registry as pr

    monkeypatch.setattr(pr, "scan_skills", lambda dirs=None: scan_skills((root,)))
    return root


# ---------- R3-3：auto_draft 统一实时校验（字节算改 / 撤权 → 409 且不产生 attempt） ----------


def _wechat_asset_with_cover(db) -> tuple:
    """批准态 asset + manifest 内真实 cover（hash 一致）。"""
    import hashlib

    from app.models import ContentAsset, ContentJob, FactPack, TopicBrief
    from app.services import materials as materials_service
    from app.services.candidates import candidate_hash

    pack = FactPack(name="r3交付包", version=1, status="frozen", checksum="5" * 64)
    db.add(pack)
    db.flush()
    topic = TopicBrief(title="r3 交付", fact_pack_id=pack.id, fact_pack_version=1)
    db.add(topic)
    db.flush()
    job = ContentJob(topic_brief_id=topic.id, channel="wechat", content_form="article", status="succeeded")
    db.add(job)
    db.flush()
    draft = Draft(content_job_id=job.id, revision_no=1, title="t", body="b")
    db.add(draft)
    db.flush()
    material = materials_service.create_material(db, kind="image", title="r3封面")
    revision = materials_service.create_revision(
        db, material, content=PNG, suffix=".png", declared_mime="image/png",
        public_use_allowed=True, rights_status="cleared",
    )
    manifest = {
        "schema_version": 2,
        "channel": "wechat",
        "content_form": "article",
        "content": {"title": "t", "body_markdown": "b"},
        "media": [
            {
                "draft_media_id": None, "material_revision_id": revision.id, "hash": revision.content_hash,
                "role": "cover", "sort_order": 0, "placement": {}, "alt_text": None, "caption": None,
                "rights": {"rights_status": "cleared", "public_use_allowed": True, "revoked": False},
            }
        ],
        "checks": [],
        "discoverability": None,
        "render": {
            "renderer_key": "renderer.wechat.article", "renderer_version": "1", "content_hash": "r" * 64,
            "payload": {"title": "t", "markdown": "b", "digest": "t"}, "warnings": [],
        },
        "execution": {},
        "declarations": [],
        "citations": [],
    }
    asset = ContentAsset(
        draft_id=draft.id, topic_brief_id=topic.id, channel="wechat", title="t", final_body="b",
        fact_pack_id=pack.id, fact_pack_version=1, fact_pack_checksum="5" * 64,
        reviewer="reviewer@studio.local", approved_revision=1,
        status="approved", approved_candidate_hash=candidate_hash(manifest),
        candidate_manifest_json=manifest,
    )
    db.add(asset)
    db.commit()
    _ = hashlib
    return asset, revision


def _authorize_auto_draft(db, asset, monkeypatch):
    from app import runtime_config
    from app.models import User
    from app.services import delivery as delivery_service

    monkeypatch.setattr(runtime_config, "get_runtime", lambda key: {"allow_unverified_auto_draft": True})
    user = db.query(User).filter_by(email="editor@studio.local").first()

    class _Payload:
        channel = "wechat"
        content_form = "article"
        account_ref = "acct-r3"
        action = "auto_draft"
        authorization_version = "v1"

    return delivery_service.authorize_target(db, asset, _Payload(), user), user


def test_auto_draft_rejects_tampered_media_bytes(seeded, monkeypatch):
    """批准后磁盘字节被替换 → execute 409、不产生 DeliveryAttempt、不调用 publisher。"""
    from fastapi import HTTPException

    from app.models import DeliveryAttempt
    from app.services import delivery as delivery_service
    from app.services.asset_media import MEDIA_ROOT

    asset, revision = _wechat_asset_with_cover(seeded)
    target, user = _authorize_auto_draft(seeded, asset, monkeypatch)

    # 篡改磁盘字节（内容寻址文件被覆盖/替换的模拟）
    path = MEDIA_ROOT / revision.file_path
    original = path.read_bytes()
    path.write_bytes(original + b"tampered")

    def _must_not_run(*a, **k):  # publisher 子进程绝不能被调用
        raise AssertionError("publisher 不应在完整性校验失败后被调用")

    import app.services.content_harness.publishers.wechat_wewrite as ww

    monkeypatch.setattr(ww.subprocess, "run", _must_not_run)

    with pytest.raises(HTTPException) as exc:
        delivery_service.execute_attempt(seeded, target.id, user)
    assert exc.value.status_code == 409
    assert "字节与批准哈希不一致" in str(exc.value.detail)
    assert seeded.query(DeliveryAttempt).filter_by(target_id=target.id).count() == 0
    path.write_bytes(original)  # 还原，避免污染共享 MEDIA_ROOT


def test_auto_draft_rejects_revoked_media_rights(seeded, monkeypatch):
    """批准后素材撤权 → execute 409（live rights 复核），不产生 attempt。"""
    from fastapi import HTTPException

    from app.models import DeliveryAttempt
    from app.services import delivery as delivery_service
    from app.services import materials as materials_service

    asset, revision = _wechat_asset_with_cover(seeded)
    target, user = _authorize_auto_draft(seeded, asset, monkeypatch)

    materials_service.revoke_public_use(seeded, revision, "版权存疑")

    import app.services.content_harness.publishers.wechat_wewrite as ww

    def _must_not_run(*a, **k):
        raise AssertionError("publisher 不应在权利复核失败后被调用")

    monkeypatch.setattr(ww.subprocess, "run", _must_not_run)

    with pytest.raises(HTTPException) as exc:
        delivery_service.execute_attempt(seeded, target.id, user)
    assert exc.value.status_code == 409
    assert "权限已撤销" in str(exc.value.detail)
    assert seeded.query(DeliveryAttempt).filter_by(target_id=target.id).count() == 0


# ---------- R3-5：fork_draft_revision 统一入口（media use 继承 + document 重建） ----------


def test_fork_draft_revision_clones_media_and_rebuilds_document(seeded):
    from app.services.draft_fork import fork_draft_revision

    draft = _xhs_draft(seeded, with_media=True)
    old_media = {m.id: m for m in draft.media}
    old_document_ids = {
        b.get("draft_media_id") for b in (draft.document_json or {}).get("blocks", []) if b.get("type") == "image"
    }
    assert old_document_ids and old_document_ids <= set(old_media), "前置：document 引用旧稿 use"

    forked = fork_draft_revision(seeded, draft, title="改题", created_by="editor@studio.local", reason="seo_apply:1")
    seeded.commit()
    seeded.expire_all()
    draft = seeded.get(Draft, draft.id)
    forked = seeded.get(Draft, forked.id)

    assert forked.revision_no == draft.revision_no + 1
    assert forked.title == "改题" and forked.body == draft.body
    assert forked.fact_check_json is None and forked.candidate_readiness == "stale"
    # media use 克隆：新 id、同 material_revision、同 role/sort
    assert {m.id for m in forked.media}.isdisjoint(set(old_media)), "fork 不得复用旧 use 行"
    assert {(m.role, m.material_revision_id) for m in forked.media} == {
        (m.role, m.material_revision_id) for m in draft.media
    }
    # document 重建：image 块全部指向 fork 后的新 use id
    new_document_ids = {
        b.get("draft_media_id") for b in (forked.document_json or {}).get("blocks", []) if b.get("type") == "image"
    }
    forked_use_ids = {m.id for m in forked.media}
    assert new_document_ids and new_document_ids <= forked_use_ids, "document 引用了不属于自己的素材"
    assert new_document_ids.isdisjoint(set(old_media))
    # 旧 revision 原样保留
    assert {m.id for m in draft.media} == set(old_media)
    assert draft.title != "改题"


def test_seo_apply_and_manual_edit_share_fork(seeded):
    """SEO apply 的新 revision 继承 media use（图文一致性）；与人工编辑同一实现。"""
    from app.models import DiscoverabilityReport, DiscoverabilityStage, DiscoverabilityStatus
    from app.services import materials as materials_service
    from app.services.discoverability import apply_suggestion

    draft = _xhs_draft(seeded, with_media=True)
    material = materials_service.create_material(seeded, kind="image", title="再补一张")
    revision = materials_service.create_revision(
        seeded, material, content=PNG + b"x9", suffix=".png", declared_mime="image/png",
        public_use_allowed=True, rights_status="cleared",
    )
    materials_service.attach_to_draft(seeded, draft, revision, role="inline")
    report = DiscoverabilityReport(
        topic_id=draft.content_job.topic_brief_id, draft_id=draft.id, stage=DiscoverabilityStage.post.value,
        channel="xiaohongshu", content_form="image_note", status=DiscoverabilityStatus.ready.value,
        report_json={"title_suggestions": ["SEO 新标题"]},
    )
    seeded.add(report)
    seeded.commit()

    user = seeded.query(User).filter_by(email="editor@studio.local").first()
    result = apply_suggestion(seeded, draft, report, {"title_index": 0}, user)
    seeded.expire_all()
    forked = seeded.get(Draft, result["new_draft_id"])
    assert forked.title == "SEO 新标题"
    assert {m.material_revision_id for m in forked.media} >= {revision.id}, "SEO apply 后新 revision 必须继承 media use"
    document_ids = {
        b.get("draft_media_id") for b in (forked.document_json or {}).get("blocks", []) if b.get("type") == "image"
    }
    assert document_ids <= {m.id for m in forked.media}, "document 不得引用旧稿素材"


# ==================== R4 批次（三次复核：Contract & Rights Integrity） ====================


# ---------- R4-B3：全局撤权进入 Approval Gate（rule + readiness 统一判定） ----------


def test_global_revocation_blocks_rule_and_readiness(seeded):
    """素材库全局撤权（revision revoked）后：rule.media.public_rights = blocker，
    readiness 报 media_rights_incomplete:…:revision_revoked——Rights 在 Candidate Ready 前拦截。"""
    from app.services import materials as materials_service
    from app.services.content_harness.rules import MediaPublicRightsRule, effective_media_rights

    draft = _xhs_draft(seeded, with_media=True)
    cover_use = next(m for m in draft.media if m.role == "cover")
    revision = seeded.get(type(cover_use.material_revision), cover_use.material_revision_id)

    # use 行缓存「可用」，但素材库全局撤权
    materials_service.revoke_public_use(seeded, revision, "版权存疑")
    seeded.commit()
    seeded.expire_all()
    draft = seeded.get(Draft, draft.id)

    assert effective_media_rights(cover_use) == "revision_revoked"

    from app.services.candidates import build_manifest_v2, readiness_reasons_v2

    manifest = build_manifest_v2(seeded, draft)
    reasons = readiness_reasons_v2(seeded, draft, manifest)
    assert any("revision_revoked" in r for r in reasons), reasons

    result = MediaPublicRightsRule().evaluate(seeded, {"draft": draft})
    assert result.status == "blocker"


# ---------- R4-H4a：fork 继承撤权字段（不洗白） ----------


def test_fork_preserves_use_revocation(seeded):
    from app.services.draft_fork import fork_draft_revision

    draft = _xhs_draft(seeded, with_media=True)
    inline_use = next(m for m in draft.media if m.role == "inline")
    inline_use.public_use_allowed = False
    inline_use.public_use_revoked_at = utcnow()
    inline_use.public_use_revocation_note = "本稿不合适"
    seeded.commit()

    forked = fork_draft_revision(seeded, draft, title="fork", created_by="editor@studio.local")
    seeded.expire_all()
    forked_inline = next(m for m in forked.media if m.role == "inline")
    assert forked_inline.public_use_allowed is False
    assert forked_inline.public_use_revoked_at is not None
    assert forked_inline.public_use_revocation_note == "本稿不合适"


# ---------- R4-H4b：title-only fork 保留手工编排（映射克隆，不重排） ----------


def test_fork_preserves_manual_composition_on_title_change(seeded):
    from app.services.document_composition import build_document_from_body, set_document
    from app.services.draft_fork import fork_draft_revision

    draft = _xhs_draft(seeded, with_media=True)
    seeded.commit()
    # 用户手工编排：把 image 块移到末尾（非默认位置）
    base = build_document_from_body(draft.body, list(draft.media))
    images = [b for b in base["blocks"] if b["type"] == "image"]
    paragraphs = [b for b in base["blocks"] if b["type"] != "image"]
    set_document(seeded, draft, {"schema_version": 1, "blocks": paragraphs + images})
    seeded.commit()

    forked = fork_draft_revision(seeded, draft, title="只改标题", created_by="editor@studio.local")
    seeded.expire_all()
    forked = seeded.get(Draft, forked.id)

    old_blocks = draft.document_json["blocks"]
    new_blocks = forked.document_json["blocks"]
    assert [b["type"] for b in new_blocks] == [b["type"] for b in old_blocks], "title-only fork 不得重排 composition"
    old_image_ids = [b["draft_media_id"] for b in old_blocks if b["type"] == "image"]
    new_image_ids = [b["draft_media_id"] for b in new_blocks if b["type"] == "image"]
    assert set(new_image_ids).isdisjoint(set(old_image_ids)), "document 必须映射为 fork 后的新 use id"
    assert set(new_image_ids) == {m.id for m in forked.media}
    # title-only：结构化派生数据继承
    assert forked.structured_json == draft.structured_json


def test_body_changing_fork_clears_derived_data_and_rebuilds_document(seeded):
    from app.services.draft_fork import fork_draft_revision

    draft = _xhs_draft(seeded, with_media=True)
    draft.thread_posts_json = [{"index": 1, "text": "旧推串"}]
    seeded.commit()

    forked = fork_draft_revision(
        seeded, draft, body="全新正文", created_by="editor@studio.local", reason="manual_edit"
    )
    seeded.expire_all()
    forked = seeded.get(Draft, forked.id)
    assert forked.body == "全新正文"
    assert forked.structured_json is None, "body 变更必须清空旧正文派生的 structured"
    assert forked.thread_posts_json is None, "body 变更必须清空旧正文派生的 thread（防止旧推串被发送）"
    # document 按新正文重建，image 块仍指向 fork 后 use
    new_ids = {b.get("draft_media_id") for b in forked.document_json["blocks"] if b["type"] == "image"}
    assert new_ids and new_ids <= {m.id for m in forked.media}


# ---------- R4-N1：copy package 媒体扩展名按 mime 推导 ----------


def test_copy_package_media_extension_by_mime(seeded, monkeypatch):
    from app.services import delivery as delivery_service
    from app.services import materials as materials_service

    asset, _revision = _wechat_asset_with_cover(seeded)
    # 换成 JPEG 素材
    material = materials_service.create_material(seeded, kind="image", title="jpeg 封面")
    jpeg = b"\xff\xd8\xff\xe0" + b"j" * 64 + b"\xff\xd9"
    revision = materials_service.create_revision(
        seeded, material, content=jpeg, suffix=".jpg", declared_mime="image/jpeg",
        public_use_allowed=True, rights_status="cleared",
    )
    manifest = asset.candidate_manifest_json
    manifest["media"][0]["material_revision_id"] = revision.id
    manifest["media"][0]["hash"] = revision.content_hash
    asset.candidate_manifest_json = manifest
    from app.services.candidates import candidate_hash

    asset.approved_candidate_hash = candidate_hash(manifest)
    seeded.commit()

    class _Payload:
        channel = "wechat"
        content_form = "article"
        account_ref = "acct-jpg"
        action = "copy_package"
        authorization_version = "v1"

    from app.models import User

    user = seeded.query(User).filter_by(email="editor@studio.local").first()
    target = delivery_service.authorize_target(seeded, asset, _Payload(), user)
    zip_bytes, _filename = delivery_service.package_zip_bytes(seeded, target)
    import io
    import zipfile

    names = zipfile.ZipFile(io.BytesIO(zip_bytes)).namelist()
    media_names = [n for n in names if n.startswith("media/")]
    assert media_names and media_names[0].endswith(".jpg"), media_names


# ---------- R4-N2：Review Center media readiness 结合 media_requirements ----------


def test_review_center_media_readiness_uses_profile_requirements(seeded):
    """小红书零图：汇总卡 media=blocked（profile 要求 cover+inline）；公众号补封面后 ready。"""
    client = _client(seeded)
    topic_id = _make_topic_with_frozen_pack(
        client,
        [
            {"channel": "xiaohongshu", "content_form": "image_note"},
            {"channel": "wechat", "content_form": "article"},
        ],
    )
    client.post(f"/api/v1/topics/{topic_id}/generate", headers=EDITOR)
    projection = client.get(f"/api/v1/review-center/topics/{topic_id}", headers=EDITOR).json()
    by_channel = {t["channel"]: t for t in projection["targets"]}
    assert by_channel["xiaohongshu"]["readiness"]["media"] == "blocked", "零图小红书汇总卡必须 blocked"
    # 公众号同样缺封面（media_requirements cover=required）
    assert by_channel["wechat"]["readiness"]["media"] == "blocked"

    # 补真实素材后转 ready
    for channel, role in [("xiaohongshu", "cover"), ("xiaohongshu", "inline"), ("wechat", "cover")]:
        from sqlalchemy import select

        seeded.expire_all()
        job = seeded.scalars(
            select(ContentJob).where(ContentJob.topic_brief_id == topic_id, ContentJob.channel == channel)
        ).first()
        draft = seeded.scalars(
            select(Draft).where(Draft.content_job_id == job.id).order_by(Draft.revision_no.desc()).limit(1)
        ).first()
        resp = client.post(
            f"/api/v1/drafts/{draft.id}/materials/upload",
            files={"file": (f"{role}.png", PNG + role.encode(), "image/png")},
            params={"role": role, "rights_status": "cleared", "public_use_allowed": "true"},
            headers=EDITOR,
        )
        assert resp.status_code == 201, resp.json()
    projection2 = client.get(f"/api/v1/review-center/topics/{topic_id}", headers=EDITOR).json()
    by_channel2 = {t["channel"]: t for t in projection2["targets"]}
    assert by_channel2["xiaohongshu"]["readiness"]["media"] == "ready"
    assert by_channel2["wechat"]["readiness"]["media"] == "ready"


# ==================== R4.1 Contract Consistency Fix ====================


# ---------- R4.1-1：preflight 与执行配置契约完全一致（混合 params+config 不再有盲区） ----------


def test_preflight_uses_merged_node_config(monkeypatch):
    """params 声明 skill、config 只写 timeout 的兼容定义：preflight 必须看到 skill-x（此前漏检）。"""
    import app.services.plugin_registry as pr
    from app.services.content_harness import skill_runtime

    monkeypatch.setattr(pr, "scan_skills", lambda dirs=None: [])  # 什么技能都没安装
    definition = {
        "nodes": [
            {
                "id": "n1",
                "plugin": "node.skill",
                "params": {"skill": "skill-x"},
                "config": {"timeout_sec": 60},
            },
        ],
        "edges": [],
    }
    problems = skill_runtime.preflight_workflow(None, definition)
    assert any("not installed" in p and "skill-x" in p for p in problems), problems


def test_is_target_agnostic_uses_merged_config(db_session):
    """ensure_bundle_workflow 复用判据同语义：params 里藏 channel 的定义不算 target 无关。"""
    from app.services.workflow_templates import _is_target_agnostic

    assert _is_target_agnostic({"nodes": [{"params": {"channel": "wechat"}, "config": {}}], "edges": []}) is False
    assert _is_target_agnostic({"nodes": [{"params": {}, "config": {"channel": "wechat"}}], "edges": []}) is False
    assert _is_target_agnostic({"nodes": [{"params": {"skill": "x"}, "config": {"timeout_sec": 5}}], "edges": []}) is True


# ---------- R4.1-2：Delivery use 级撤权旁路关闭 ----------


def test_delivery_blocks_use_level_revocation_after_target_creation(seeded, monkeypatch):
    """批准 → 仅对本稿撤权 use（revision 仍公开）→ 撤权后才创建 target：
    copy package 409、auto_draft 409、零 DeliveryAttempt、publisher 零调用。"""
    from fastapi import HTTPException

    from app import runtime_config
    from app.models import DeliveryAttempt, User
    from app.services import delivery as delivery_service
    from app.services import materials as materials_service
    from app.services.candidates import candidate_hash

    asset, revision = _wechat_asset_with_cover(seeded)
    draft = seeded.get(Draft, asset.draft_id)

    # 给 manifest 补上真实 use 引用（v2 candidate 同时带 draft_media_id + material_revision_id）
    use = materials_service.attach_to_draft(seeded, draft, revision, role="cover")
    manifest = asset.candidate_manifest_json
    manifest["media"][0]["draft_media_id"] = use.id
    asset.candidate_manifest_json = manifest
    asset.approved_candidate_hash = candidate_hash(manifest)
    seeded.commit()

    user = seeded.query(User).filter_by(email="editor@studio.local").first()

    class _Payload:
        channel = "wechat"
        content_form = "article"
        account_ref = "acct-r41"
        action = "copy_package"
        authorization_version = "v1"

    class _PayloadAuto(_Payload):
        action = "auto_draft"

    # 撤权发生在 target 创建之前：仅撤本稿 use（revision 保持公开）
    use.public_use_allowed = False
    use.public_use_revoked_at = utcnow()
    use.public_use_revocation_note = "仅本稿撤权"
    seeded.commit()

    # 撤权后创建 copy_package target → 成品包 409
    copy_target = delivery_service.authorize_target(seeded, asset, _Payload(), user)
    with pytest.raises(HTTPException) as exc:
        delivery_service.build_copy_package(seeded, copy_target)
    assert exc.value.status_code == 409

    # 撤权后创建 auto_draft target → execute 409、零 attempt、publisher 零调用
    monkeypatch.setattr(runtime_config, "get_runtime", lambda key: {"allow_unverified_auto_draft": True})
    auto_target = delivery_service.authorize_target(seeded, asset, _PayloadAuto(), user)

    import app.services.content_harness.publishers.wechat_wewrite as ww

    def _must_not_run(*a, **k):
        raise AssertionError("publisher 不应在 use 级撤权后被调用")

    monkeypatch.setattr(ww.subprocess, "run", _must_not_run)
    with pytest.raises(HTTPException) as exc2:
        delivery_service.execute_attempt(seeded, auto_target.id, user)
    assert exc2.value.status_code == 409
    assert seeded.query(DeliveryAttempt).filter_by(target_id=auto_target.id).count() == 0
