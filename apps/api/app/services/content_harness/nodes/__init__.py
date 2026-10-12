"""Built-in Node Plugins（D6）：把 workflow_engine 的既有 handler 薄包装为 registry 插件。

- 业务行为零变化：execute 直接委托旧 handler（同一套校验/审计/闸门）；
- schema v1 节点 `{"type": "generate"}` 经 TYPE_TO_PLUGIN 映射到 `builtin.generate@1`；
- schema v2 节点直接写 `{"plugin": "node.skill", "plugin_version": "1"}`（Phase 7 起使用）。
"""

from __future__ import annotations

from copy import deepcopy
from typing import ClassVar

from ..contracts import NodeResult, WorkflowExecutionContext, node_config_of  # noqa: F401  re-export（R4.1 统一语义）
from ..registry import registry

# schema v1 node type → builtin plugin key（旧定义兼容层，loader 内存映射，不改历史 JSON）
TYPE_TO_PLUGIN: dict[str, str] = {
    "connector_pull": "builtin.connector_pull",
    "extract_facts": "builtin.extract_facts",
    "factpack_freeze": "builtin.factpack_freeze",
    "suggest_topics": "builtin.topic_suggest",
    "generate": "builtin.generate",
    "humanize_polish": "builtin.humanize",
    "content_censor": "builtin.content_censor",
    "generate_cover": "builtin.generate_cover",
    "fact_check": "builtin.fact_check",
    "discoverability_post": "builtin.discoverability_post",
    "export": "builtin.export",
    "publish_wechat": "builtin.publish_wechat",
    "adopt_topic": "builtin.adopt_topic",
    "confirm_facts": "builtin.confirm_facts",
    "approve": "builtin.approve",
}


class LegacyHandlerNodePlugin:
    """以 (db, run, step, user) 签名委托 workflow_engine 旧 handler 的通用插件。"""

    key = ""
    version = "1"
    human_gate = False
    side_effect = False
    label = ""
    handler_name = ""
    complete_handler_name = ""

    @property
    def _handler(self):
        from ....services import workflow_engine as legacy  # 延迟导入避免循环

        return getattr(legacy, self.handler_name)

    def execute(self, db, ctx: WorkflowExecutionContext, config: dict, user) -> NodeResult:
        return NodeResult(output=self._handler(db, ctx.run, ctx.step, user) or {})


class LegacyHumanNodePlugin(LegacyHandlerNodePlugin):
    """人工节点：human_gate=True，complete 委托旧 COMPLETE_HANDLERS 实现。"""

    human_gate = True

    def complete(self, db, ctx: WorkflowExecutionContext, payload: dict, user) -> NodeResult:
        from ....services import workflow_engine as legacy

        handler = getattr(legacy, self.complete_handler_name)
        return NodeResult(output=handler(db, ctx.run, ctx.step, payload or {}, user) or {})


class SkillNodePlugin:
    """node.skill@1（R2-H5）：按节点 config.skill 把执行委托给已注册 SkillRuntime。

    preflight_workflow 会在启动前拒绝「没有任何可执行 runtime」的工作流；
    本插件是真正的执行路径：runtime 返回 unavailable 即节点失败（如实报告，不静默跳过）。
    """

    key = "node.skill"
    version = "1"
    human_gate = False
    side_effect = False

    def _runtime(self):
        # R3-1：相对导入修正（nodes 的上级包才是 content_harness）
        from .. import skill_runtime

        skill_runtime.bootstrap_skill_runtimes()
        return skill_runtime.resolve_executable_runtime()

    def execute(self, db, ctx: WorkflowExecutionContext, config: dict, user) -> NodeResult:
        from ..contracts import SkillExecutionResult

        runtime = self._runtime()
        name = config.get("skill") or "unknown"
        if runtime is None:
            raise ValueError(
                f"技能 {name} 无可执行 SkillRuntime（内置 runtime 不执行外部技能；DSH 契约核实后注册）"
            )
        result: SkillExecutionResult = runtime.execute(
            {"name": name, "version": config.get("skill_version") or "unversioned"},
            {"params": config, "context": {"run_id": ctx.run.id if ctx.run else None}},
            timeout_sec=int(config.get("timeout_sec") or 120),
        )
        if result.status != "succeeded":
            raise ValueError(f"技能 {name} 执行失败（{result.status}）：{result.error or '无详情'}")
        return NodeResult(output={"skill": name, "result": result.output or {}})


class SystemConstantNodePlugin:
    """Persist a configured, local value as an ordinary workflow attempt."""

    key = "system.constant"
    version = "1"
    human_gate = False
    side_effect = False

    def execute(self, db, ctx: WorkflowExecutionContext, config: dict, user) -> NodeResult:
        value = config.get("value")
        if not isinstance(value, dict):
            raise ValueError("system.constant 需要对象形式的 value")  # noqa: TRY004 - 保留既有节点配置失败契约。
        return NodeResult(output=value)


class DataSourceNodePlugin:
    key = "data.source"
    version = "1"
    human_gate = False
    side_effect = False

    def execute(self, db, ctx: WorkflowExecutionContext, config: dict, user) -> NodeResult:
        from ...data_source_plugins import snapshot_source

        return NodeResult(output=snapshot_source(db, ctx.run, ctx.step.node_id, config.get("data_source_plugin_key", ""), str(config.get("source_ref", "")), user))


class MediaGenerationNodePlugin:
    key = "media.generate"
    version = "1"
    human_gate = False
    side_effect = True

    def execute(self, db, ctx: WorkflowExecutionContext, config: dict, user) -> NodeResult:
        from ...generation_tasks import workflow_execute

        return NodeResult(output=workflow_execute(db, ctx.run, ctx.step, config, user))

    def complete(self, db, ctx: WorkflowExecutionContext, payload: dict, user) -> NodeResult:
        from ...generation_tasks import workflow_complete

        return NodeResult(output=workflow_complete(db, ctx.run, ctx.step, payload, user))


_METHOD_SCHEMA = {
    "type": "object", "additionalProperties": False, "properties": {
        "source_kind": {"type": "string", "enum": ["studio_builtin", "capability_memory", "installed_agent_skill"], "maxLength": 30},
        "artifact_id": {"type": "integer", "minimum": 1, "maximum": 2147483647},
        "revision_id": {"type": "integer", "minimum": 1, "maximum": 2147483647},
        "arguments_json": {"type": "string", "maxLength": 4000},
        "skill_id": {"type": "string", "maxLength": 150},
        "version": {"type": "string", "maxLength": 100},
        "runtime_key": {"type": "string", "maxLength": 150},
        "runtime_version": {"type": "string", "maxLength": 100},
        "skill_ref": {"type": "string", "maxLength": 150},
    }, "required": ["source_kind"],
}


class StageMasterProposalNodePlugin:
    """Versioned proposal stage; the invocation gate owns real dispatch."""

    key = "stage.master.propose"
    version = "1"
    human_gate = False
    side_effect = False
    stage_consumed_fields = frozenset({"purpose", "instruction", "candidate_count", "length", "temperature", "model_profile_id", "method", "tone", "fact_mode"})
    stage_contract: ClassVar[dict] = {
        "stage_schema": "stage.master.propose.v1",
        "title": "生成 Master 候选",
        "category": "AI",
        "config_schema": {"type": "object", "additionalProperties": False, "properties": {
            "instruction": {"type": "string", "minLength": 1, "maxLength": 4000},
            "purpose": {"type": "string", "minLength": 1, "maxLength": 150},
            "temperature": {"type": "number", "minimum": 0, "maximum": 2},
            "method": _METHOD_SCHEMA,
            "tone": {"type": "string", "maxLength": 200},
            "fact_mode": {"type": "string", "maxLength": 11, "enum": ["grounded", "current", "reflection", "speculation"], "default": "grounded"},
            "candidate_count": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
            "length": {"type": "string", "enum": ["short", "medium", "long"], "minLength": 1, "maxLength": 6, "default": "medium"},
            "model_profile_id": {"type": "string", "minLength": 1, "maxLength": 100},
        }, "required": ["instruction"]},
        "ui_schema": {"instruction": {"control": "textarea", "label": "阶段要求"},
                      "purpose": {"control": "textarea", "label": "创作目的"},
                      "temperature": {"control": "number", "label": "创意程度"},
                      "method": {"control": "method", "label": "使用方法"},
                      "fact_mode": {"control": "select", "label": "事实时效模式"},
                      "tone": {"control": "text", "label": "表达语气"},
                      "candidate_count": {"control": "number", "label": "候选数量"},
                      "length": {"control": "select", "label": "内容长度"},
                      "model_profile_id": {"control": "text", "label": "模型配置"}},
        "tunable_fields": ["purpose", "instruction", "candidate_count", "length", "temperature", "model_profile_id", "method", "tone", "fact_mode"],
        "input_contract": {"required_context": [], "upstream": "accepted"},
        "output_contract": {"schema": "stage.master.proposal.v1", "max_candidates": 5,
                             "supported_modalities": ["text", "graphic", "video"],
                             "candidate_shape": {"payload": "canonical text.master.v2, graphic.master.v2 or video.master.v2 for the Unit modality",
                                                 "asset_refs": "exact supplied MaterialRevision refs only",
                                                 "evidence_refs": "exact supplied FactPackItem refs only"},
                             "response_shape": "object with candidates array; honor requested candidate_count",
                             "accepted_content_required": True},
        "method_sources": ["builtin", "studio_builtin", "capability_memory", "installed_agent_skill"],
        "supports_preview": True, "supports_run_override": True,
        "supports_candidates": True, "requires_human_acceptance": True,
    }

    def execute(self, db, ctx: WorkflowExecutionContext, config: dict, user) -> NodeResult:
        raise ValueError("stage_invocation_required")

    def execute_resolved(self, db, ctx: WorkflowExecutionContext, resolved: dict, user) -> NodeResult:
        from ...stage_master_proposals import execute_text_proposal

        return NodeResult(output=execute_text_proposal(db, ctx, resolved, user))


def _stage_contract(schema, title, category, properties, required, output_schema, *, context=(), ui=None,
                    methods=("builtin",), tunable=None):
    return {
        "stage_schema": schema, "title": title, "category": category,
        "config_schema": {"type": "object", "additionalProperties": False,
                          "properties": properties, "required": required},
        "ui_schema": ui or {}, "tunable_fields": list(properties) if tunable is None else tunable,
        "input_contract": {"required_context": list(context), "upstream": "accepted"},
        "output_contract": {"schema": output_schema, "accepted_content_required": True},
        "method_sources": list(methods), "supports_preview": True, "supports_run_override": True,
        "supports_candidates": False, "requires_human_acceptance": True,
    }


class StageCreativeMethodNodePlugin:
    key = "stage.creative.method"
    version = "1"
    human_gate = False
    side_effect = False
    stage_consumed_fields = frozenset({
        "output_schema", "instruction", "purpose", "candidate_count", "length", "temperature", "method", "model_profile_id",
        "tone", "density", "canvas_count", "aspect_ratio", "pace", "energy", "pause_policy", "shot_count", "fact_mode",
    })
    stage_contract: ClassVar[dict] = _stage_contract(
        "stage.creative.method.v1", "中间创作方法", "AI", {
            "output_schema": {"type": "string", "minLength": 1, "maxLength": 80, "enum": [
                "research.brief.v1", "creative.angles.v1", "content.outline.v1",
                "graphic.visual-direction.v1", "graphic.card-plan.v1",
                "audio.spoken-adaptation.v1", "audio.voice-direction.v1", "video.shot-plan.v1",
            ]},
            "instruction": {"type": "string", "minLength": 1, "maxLength": 4000},
            "purpose": {"type": "string", "minLength": 1, "maxLength": 150, "default": "完成当前中间创作阶段"},
            "candidate_count": {"type": "integer", "minimum": 1, "maximum": 5, "default": 1},
            "length": {"type": "string", "minLength": 1, "maxLength": 6, "enum": ["short", "medium", "long"], "default": "medium"},
            "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.4},
            "method": _METHOD_SCHEMA,
            "model_profile_id": {"type": "string", "minLength": 1, "maxLength": 100},
            "tone": {"type": "string", "maxLength": 200},
            "fact_mode": {"type": "string", "maxLength": 11, "enum": ["grounded", "current", "reflection", "speculation"], "default": "grounded"},
            "density": {"type": "string", "enum": ["low", "medium", "high"], "maxLength": 6},
            "canvas_count": {"type": "integer", "minimum": 1, "maximum": 10},
            "aspect_ratio": {"type": "string", "enum": ["1:1", "4:3", "3:4", "16:9", "9:16"], "maxLength": 5},
            "pace": {"type": "string", "enum": ["slow", "medium", "fast"], "maxLength": 6},
            "energy": {"type": "string", "maxLength": 100},
            "pause_policy": {"type": "string", "maxLength": 200},
            "shot_count": {"type": "integer", "minimum": 1, "maximum": 100},
        }, ["output_schema", "instruction"], "stage.creative.method.result.v1",
        context=("identity",), methods=("builtin", "studio_builtin", "capability_memory", "installed_agent_skill"),
        ui={"output_schema": {"control": "select", "label": "中间产物类型"},
            "fact_mode": {"control": "select", "label": "事实时效模式"},
            "instruction": {"control": "textarea", "label": "阶段要求"},
            "purpose": {"control": "text", "label": "阶段目的"},
            "candidate_count": {"control": "number", "label": "候选数量"},
            "length": {"control": "select", "label": "内容长度"},
            "temperature": {"control": "number", "label": "创意程度"},
            "method": {"control": "method", "label": "使用方法"},
            "model_profile_id": {"control": "text", "label": "模型配置"}},
    )
    stage_contract["output_contract"].update({
        "response_shape": "object {schema: requested output_schema, candidates: [{id: stable identifier, summary: concise text, content: bounded structured artifact, references: exact supplied refs, warnings: bounded strings}]}",
        "reference_shape": "{kind: fact_pack_item or material_revision, id: integer, checksum: exact supplied hash}",
    })

    def execute(self, db, ctx: WorkflowExecutionContext, config: dict, user) -> NodeResult:
        raise ValueError("stage_invocation_required")

    def execute_resolved(self, db, ctx: WorkflowExecutionContext, resolved: dict, user) -> NodeResult:
        from ...creative_method_stage import execute

        return NodeResult(output=execute(db, ctx, resolved, user))


class StageGraphicCompositionNodePlugin:
    key = "stage.graphic.compose"
    version = "1"
    human_gate = False
    side_effect = False
    stage_consumed_fields = frozenset({"method", "preset_ref", "template", "density"})
    stage_contract: ClassVar[dict] = _stage_contract(
        "stage.graphic.compose.v1", "确定性图文排版", "Tool", {
            "method": _METHOD_SCHEMA,
            "preset_ref": {"type": "string", "minLength": 1, "maxLength": 150},
            "template": {"type": "string", "maxLength": 9, "enum": ["editorial", "split", "cards"], "default": "editorial"},
            "density": {"type": "string", "maxLength": 6, "enum": ["low", "medium", "high"]},
        }, [], "stage.master.proposal.v1", context=("identity",), methods=("studio_builtin",),
        ui={"preset_ref": {"control": "text", "label": "视觉预设"},
            "template": {"control": "select", "label": "排版模板"},
            "density": {"control": "select", "label": "文字密度"},
            "method": {"control": "method", "label": "排版方法"}},
    )
    stage_contract["output_contract"].update(supported_modalities=["graphic"], max_candidates=1,
        execution_kind="deterministic", final_render=False)

    def execute(self, db, ctx, config, user):
        raise ValueError("stage_invocation_required")

    def execute_resolved(self, db, ctx, resolved, user):
        from ...graphic_composition import build_proposal

        return NodeResult(output=build_proposal(resolved))


class ResolvedDomainStagePlugin:
    human_gate = False
    side_effect = False
    version = "1"

    def execute(self, db, ctx, config, user):
        raise ValueError("stage_invocation_required")

    def execute_resolved(self, db, ctx, resolved, user):
        from ...stage_domain_integrations import execute_domain

        return NodeResult(output=execute_domain(db, ctx, resolved, user))


class StageMediaGenerationNodePlugin(ResolvedDomainStagePlugin):
    key = "media.generate"
    version = "2"
    side_effect = True
    stage_contract: ClassVar[dict] = _stage_contract(
        "media.generate.stage.v2", "生成媒体素材", "Tool", {
            "capability": {"type": "string", "enum": ["image_generation", "video_generation", "tts"], "maxLength": 30},
            "selected_profile": {"type": "string", "minLength": 1, "maxLength": 100},
            "explicit_plugin": {"type": "string", "minLength": 1, "maxLength": 100},
            "prompt": {"type": "string", "minLength": 1, "maxLength": 2000},
            **{name: {"type": "integer", "minimum": 1, "maximum": ceiling}
               for name, ceiling in {"items": 20, "pixels": 16777216, "seconds": 600,
                                     "tokens": 1000000, "timeout_seconds": 600}.items()},
            "source_revision_ids": {"type": "array", "maxItems": 4,
                "items": {"type": "integer", "minimum": 1, "maximum": 2147483647}, "default": []},
            "parameters": {"type": "object", "additionalProperties": False, "default": {}, "properties": {
                name: {"type": "integer", "minimum": 1, "maximum": ceiling}
                for name, ceiling in {"items": 20, "pixels": 16777216, "seconds": 600,
                                      "tokens": 1000000, "timeout_seconds": 600}.items()}},
        }, ["capability", "selected_profile", "prompt"], "stage.media.result.v1",
        ui={"capability": {"control": "select", "label": "生成能力"},
            "selected_profile": {"control": "text", "label": "模型配置"},
            "explicit_plugin": {"control": "text", "label": "指定插件"},
            "prompt": {"control": "textarea", "label": "媒体要求"},
            **{name: {"control": "number", "label": label} for name, label in {
                "items": "生成数量", "pixels": "图像像素上限", "seconds": "时长秒数",
                "tokens": "Token 上限", "timeout_seconds": "请求时限秒数"}.items()}})
    stage_consumed_fields = frozenset(stage_contract["config_schema"]["properties"])


def _media_v3_contract() -> dict:
    contract = deepcopy(StageMediaGenerationNodePlugin.stage_contract)
    contract["stage_schema"] = "media.generate.stage.v3"
    aspect = {"type": "string", "minLength": 3, "maxLength": 5,
              "enum": ["1:1", "4:3", "3:4", "16:9", "9:16"]}
    contract["config_schema"]["properties"]["aspect_ratio"] = aspect
    contract["config_schema"]["properties"]["parameters"]["properties"]["aspect_ratio"] = aspect
    contract["tunable_fields"] = list(contract["config_schema"]["properties"])
    contract["ui_schema"]["aspect_ratio"] = {"control": "select", "label": "画面比例"}
    return contract


class StageMediaGenerationV3NodePlugin(StageMediaGenerationNodePlugin):
    """Geometry-aware media stage; v2 remains byte-for-byte compatible."""

    version = "3"
    stage_contract: ClassVar[dict] = _media_v3_contract()
    stage_consumed_fields: ClassVar[frozenset[str]] = frozenset(stage_contract["config_schema"]["properties"])


class StageMediaGenerationV4NodePlugin(StageMediaGenerationNodePlugin):
    version = "4"
    stage_contract: ClassVar[dict] = _stage_contract(
        "media.generate.stage.v4", "生成已确认口语稿音频", "Tool", {
            "capability": {"type": "string", "enum": ["tts"], "default": "tts", "maxLength": 3},
            "tts_source": {"type": "string", "enum": ["accepted_spoken"], "default": "accepted_spoken", "maxLength": 15},
            "method": _METHOD_SCHEMA,
            "selected_profile": {"type": "string", "minLength": 1, "maxLength": 100},
            "explicit_plugin": {"type": "string", "minLength": 1, "maxLength": 100},
            "voice": {"type": "string", "minLength": 1, "maxLength": 150},
            "rate": {"type": "number", "minimum": 0.5, "maximum": 2},
            "items": {"type": "integer", "enum": [1], "minimum": 1, "maximum": 1, "default": 1},
            "seconds": {"type": "integer", "minimum": 1, "maximum": 600, "default": 120},
            "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 300, "default": 25},
        }, [], "stage.media.result.v1", context=("identity", "master"), methods=("studio_builtin",),
        ui={"voice": {"control": "text", "label": "供应商声音ID（必须真实配置）"},
            "rate": {"control": "number", "label": "语速（未覆盖时采用已接受声音方案）"},
            "selected_profile": {"control": "text", "label": "明确指定TTS模型配置"},
            "seconds": {"control": "number", "label": "音频时长上限秒"},
            "timeout_seconds": {"control": "number", "label": "请求时限秒"}})
    stage_consumed_fields: ClassVar[frozenset[str]] = frozenset(stage_contract["config_schema"]["properties"])


class StageAudioASRNodePlugin(ResolvedDomainStagePlugin):
    key = "stage.audio.asr"
    stage_contract: ClassVar[dict] = _stage_contract(
        "stage.audio.asr.v1", "本机识别已接受音频（须明确执行）", "Tool", {
            "provider_key": {"type": "string", "enum": ["local.mlx_whisper"], "default": "local.mlx_whisper", "maxLength": 100},
            "provider_version": {"type": "string", "enum": ["1"], "default": "1", "maxLength": 20},
            "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 120, "default": 120},
        }, [], "stage.audio_asr.result.v1", context=("identity",),
        ui={"timeout_seconds": {"control": "number", "label": "本机识别时限（秒）"}})
    stage_consumed_fields: ClassVar[frozenset[str]] = frozenset(stage_contract["config_schema"]["properties"])


class StageAudioQCNodePlugin(ResolvedDomainStagePlugin):
    key = "stage.audio.qc"
    stage_contract: ClassVar[dict] = _stage_contract(
        "stage.audio.qc.v1", "检查已接受音频", "Rule", {
            "method": _METHOD_SCHEMA,
            "quality_profile_ref": {"type": "string", "enum": ["studio.quality.audio.explainer@1", "studio.quality.audio.conversational@1"], "maxLength": 100},
            "alignment_enabled": {"type": "boolean", "default": False},
            "asr_master_revision_id": {"type": "integer", "minimum": 1, "maximum": 2147483647},
            "asr_receipt_id": {"type": "string", "minLength": 32, "maxLength": 32},
            "asr_output_hash": {"type": "string", "minLength": 64, "maxLength": 64},
            "srt_mode": {"type": "string", "enum": ["none", "asr", "estimated"], "default": "none", "maxLength": 9},
        }, [], "stage.checks.result.v1", context=("identity",), methods=("studio_builtin",),
        ui={"quality_profile_ref": {"control": "select", "label": "音频质量标准"},
            "alignment_enabled": {"control": "toggle", "label": "对照已接受的 ASR 回执（不调用识别）"},
            "asr_master_revision_id": {"control": "number", "label": "已保存 ASR 字幕的 Video Master 版本 ID"},
            "asr_receipt_id": {"control": "text", "label": "该版本的精确 ASR 回执 ID"},
            "asr_output_hash": {"control": "text", "label": "该 ASR 回执的输出 SHA-256"},
            "srt_mode": {"control": "select", "label": "字幕导出（none 无 / asr 真实分段 / estimated 估计）"}})
    stage_consumed_fields: ClassVar[frozenset[str]] = frozenset(stage_contract["config_schema"]["properties"])


class StageVariantAdaptNodePlugin(ResolvedDomainStagePlugin):
    key = "stage.variant.adapt"
    stage_contract: ClassVar[dict] = _stage_contract(
        "stage.variant.adapt.v1", "适配渠道版本", "AI", {
            "variant_key": {"type": "string", "minLength": 1, "maxLength": 120},
            "channel_id": {"type": "string", "minLength": 1, "maxLength": 100},
            "content_form": {"type": "string", "minLength": 1, "maxLength": 100},
            "mode": {"type": "string", "enum": ["deterministic", "model_assisted"], "maxLength": 20, "default": "deterministic"},
            "instruction": {"type": "string", "minLength": 1, "maxLength": 4000},
            "model_profile_id": {"type": "string", "minLength": 1, "maxLength": 100},
            "method": deepcopy(_METHOD_SCHEMA),
        }, ["variant_key", "channel_id", "content_form"], "stage.variant.result.v1", context=("master",),
        methods=("builtin", "capability_memory"),
        ui={"variant_key": {"control": "text", "label": "版本标识"},
            "channel_id": {"control": "text", "label": "目标渠道"},
            "content_form": {"control": "text", "label": "内容形态"},
            "mode": {"control": "select", "label": "适配方式"},
            "instruction": {"control": "textarea", "label": "适配要求"},
            "model_profile_id": {"control": "text", "label": "模型配置"},
            "method": {"control": "method", "label": "使用方法"}})
    stage_consumed_fields = frozenset(stage_contract["config_schema"]["properties"])


class StageProfessionalPrepareNodePlugin(ResolvedDomainStagePlugin):
    key = "stage.professional.prepare"
    stage_contract: ClassVar[dict] = _stage_contract(
        "stage.professional.prepare.v1", "准备专业执行", "Tool", {
            "source_variant_revision_id": {"type": "integer", "minimum": 1, "maximum": 2147483647},
            "package_schema": {"type": "string", "enum": ["creative.execution.v1", "director.video.v1"], "maxLength": 30, "default": "creative.execution.v1"},
            "objective": {"type": "string", "minLength": 1, "maxLength": 2000},
            "output_kind": {"type": "string", "enum": ["image", "video", "audio", "other"], "maxLength": 10, "default": "video"},
            "output_mime": {"type": "string", "minLength": 1, "maxLength": 100, "default": "video/mp4"},
            "output_role": {"type": "string", "minLength": 1, "maxLength": 100, "default": "final-render"},
            "output_count": {"type": "integer", "minimum": 1, "maximum": 20, "default": 1},
            "output_max_bytes": {"type": "integer", "minimum": 1, "maximum": 31457280, "default": 31457280},
            "constraints": {"type": "array", "maxItems": 50, "items": {"type": "string", "maxLength": 2000}, "default": []},
            "acceptance_criteria": {"type": "array", "maxItems": 50, "items": {"type": "string", "maxLength": 2000}, "default": []},
            "output_contract": {"type": "object", "additionalProperties": False, "required": ["roles"], "properties": {
                "roles": {"type": "array", "minItems": 1, "maxItems": 20, "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["role_id", "kind", "required", "allowed_mime", "min_count", "max_count", "max_bytes"],
                    "properties": {
                        "role_id": {"type": "string", "minLength": 1, "maxLength": 100},
                        "kind": {"type": "string", "enum": ["image", "video", "audio", "other"], "maxLength": 10},
                        "required": {"type": "boolean"},
                        "allowed_mime": {"type": "array", "minItems": 1, "maxItems": 10, "items": {"type": "string", "minLength": 1, "maxLength": 100}},
                        "min_count": {"type": "integer", "minimum": 0, "maximum": 20},
                        "max_count": {"type": "integer", "minimum": 1, "maximum": 20},
                        "max_bytes": {"type": "integer", "minimum": 1, "maximum": 31457280},
                    }}}}},
            "prepare_execution": {"type": "boolean", "default": False},
            "executor_kind": {"type": "string", "minLength": 1, "maxLength": 30},
            "executor_key": {"type": "string", "minLength": 1, "maxLength": 150},
            "executor_version": {"type": "string", "minLength": 1, "maxLength": 50},
        }, ["objective"], "stage.professional.result.v1", context=("master",),
        ui={"objective": {"control": "textarea", "label": "执行目标"},
            "package_schema": {"control": "select", "label": "交接包类型"},
            "prepare_execution": {"control": "toggle", "label": "同时准备执行记录"},
            "executor_kind": {"control": "text", "label": "执行器类型"},
            "executor_key": {"control": "text", "label": "执行器标识"},
            "executor_version": {"control": "text", "label": "执行器版本"},
            "output_kind": {"control": "select", "label": "输出类型"},
            "output_mime": {"control": "text", "label": "输出格式 MIME"},
            "output_role": {"control": "text", "label": "输出角色"},
            "output_count": {"control": "number", "label": "输出数量"},
            "output_max_bytes": {"control": "number", "label": "文件字节上限"}})
    stage_consumed_fields = frozenset(stage_contract["config_schema"]["properties"])


def _professional_v2_contract() -> dict:
    contract = deepcopy(StageProfessionalPrepareNodePlugin.stage_contract)
    contract["stage_schema"] = "stage.professional.prepare.v2"
    contract["config_schema"]["properties"].update({
        "method": _METHOD_SCHEMA,
        "instruction": {"type": "string", "maxLength": 2000, "default": ""},
        "aspect_ratio": {"type": "string", "enum": ["1:1", "4:3", "3:4", "16:9", "9:16"], "maxLength": 5},
    })
    contract["tunable_fields"] = list(contract["config_schema"]["properties"])
    contract["method_sources"] = ["studio_builtin"]
    contract["ui_schema"].update({"method": {"control": "method", "label": "导演交接方法"},
        "instruction": {"control": "textarea", "label": "额外交接要求"},
        "aspect_ratio": {"control": "select", "label": "验证已保存导演稿的比例"}})
    return contract


class StageProfessionalPrepareV2NodePlugin(StageProfessionalPrepareNodePlugin):
    version = "2"
    stage_contract: ClassVar[dict] = _professional_v2_contract()
    stage_consumed_fields: ClassVar[frozenset[str]] = frozenset(stage_contract["config_schema"]["properties"])


class StageChecksNodePlugin(ResolvedDomainStagePlugin):
    key = "stage.checks"
    stage_contract: ClassVar[dict] = _stage_contract(
        "stage.checks.v1", "检查 Master", "Rule", {}, [], "stage.checks.result.v1", context=("master",))
    stage_consumed_fields = frozenset()


class StageHumanReviewNodePlugin(ResolvedDomainStagePlugin):
    key = "stage.human.review"
    human_gate = True
    stage_contract: ClassVar[dict] = _stage_contract(
        "stage.human.review.v1", "人工确认阶段", "Human",
        {"instruction": {"type": "string", "minLength": 1, "maxLength": 4000}}, ["instruction"],
        "stage.human.result.v1", ui={"instruction": {"control": "textarea", "label": "人工确认事项"}})
    stage_consumed_fields = frozenset({"instruction"})

    def complete(self, db, ctx, payload, user):
        raise ValueError("stage_adoption_required")


def _plugin(key: str, handler: str, label: str, *, complete: str | None = None, side_effect: bool = False):
    attrs = {"key": key, "handler_name": handler, "label": label, "side_effect": side_effect}
    if complete:
        attrs["complete_handler_name"] = complete
        base: type = LegacyHumanNodePlugin
    else:
        base = LegacyHandlerNodePlugin
    return type(f"_Plugin_{key.replace('.', '_')}", (base,), attrs)


# (key, execute handler, label, complete handler, side_effect)
_BUILTIN_SPECS: list[tuple[str, str, str, str | None, bool]] = [
    ("builtin.connector_pull", "_h_connector_pull", "拉取监测数据", None, False),
    ("builtin.extract_facts", "_h_extract_facts", "抽取候选事实", None, False),
    ("builtin.factpack_freeze", "_h_factpack_freeze", "打包冻结 FactPack", None, False),
    ("builtin.topic_suggest", "_h_suggest_topics", "AI 荐题", None, False),
    ("builtin.generate", "_h_generate", "生成稿件", None, False),
    ("builtin.humanize", "_h_humanize_polish", "去 AI 味精炼", None, False),
    ("builtin.content_censor", "_h_content_censor", "合规审查", None, False),
    ("builtin.generate_cover", "_h_generate_cover", "AI 封面", None, False),
    ("builtin.fact_check", "_h_fact_check", "事实校验", None, False),
    ("builtin.discoverability_post", "_h_discoverability_post", "SEO 审查（post）", None, False),
    ("builtin.export", "_h_export", "本地导出", None, False),
    ("builtin.publish_wechat", "_h_publish_wechat", "公众号草稿箱（遗留，显式启用）", None, True),
    ("builtin.adopt_topic", "_h_adopt_topic_complete", "人工采纳选题", "_h_adopt_topic_complete", False),
    ("builtin.confirm_facts", "_h_confirm_facts_complete", "人工确认事实", "_h_confirm_facts_complete", False),
    ("builtin.approve", "_h_approve", "人工批准", "_h_approve", False),
]

# 直接注册的非 handler 插件（R2-H5：node.skill 可执行节点）
_DIRECT_PLUGINS = [SkillNodePlugin, SystemConstantNodePlugin, DataSourceNodePlugin, MediaGenerationNodePlugin,
                   StageMasterProposalNodePlugin, StageMediaGenerationNodePlugin, StageMediaGenerationV3NodePlugin,
                   StageMediaGenerationV4NodePlugin, StageAudioASRNodePlugin, StageAudioQCNodePlugin,
                   StageCreativeMethodNodePlugin, StageGraphicCompositionNodePlugin, StageVariantAdaptNodePlugin,
                   StageProfessionalPrepareNodePlugin, StageProfessionalPrepareV2NodePlugin,
                   StageChecksNodePlugin, StageHumanReviewNodePlugin]

_bootstrapped = False


def bootstrap_builtin_nodes() -> None:
    """注册 built-in 节点插件（幂等）。engine 模块导入时调用。"""
    global _bootstrapped
    if _bootstrapped:
        return
    for key, handler, label, complete, side_effect in _BUILTIN_SPECS:
        if key in {d.key for d in registry.list("node")}:
            continue
        plugin_cls = _plugin(key, handler, label, complete=complete, side_effect=side_effect)
        registry.register(
            "node",
            key,
            "1",
            plugin_cls(),  # 注册实例：execute/complete 以绑定方法被引擎调用
            label=label,
            human_gate=complete is not None,
            side_effect=side_effect,
        )
    for plugin_cls in _DIRECT_PLUGINS:
        if (plugin_cls.key, plugin_cls.version) not in {(d.key, d.version) for d in registry.list("node")}:
            registry.register("node", plugin_cls.key, plugin_cls.version, plugin_cls(), label=plugin_cls.key,
                human_gate=getattr(plugin_cls, "human_gate", False),
                side_effect=getattr(plugin_cls, "side_effect", False),
                stage_contract=getattr(plugin_cls, "stage_contract", None))
    from ...graphic_composition import bootstrap

    bootstrap()
    from ...audio_quality import bootstrap as bootstrap_audio_quality

    bootstrap_audio_quality()
    _bootstrapped = True


def resolve_node_key(node: dict) -> tuple[str, str]:
    """从节点定义解析 plugin key/version：schema v2 读 plugin 字段，schema v1 按 type 映射。"""
    plugin = node.get("plugin")
    if plugin:
        return str(plugin), str(node.get("plugin_version") or "1")
    node_type = node.get("type") or ""
    key = TYPE_TO_PLUGIN.get(str(node_type))
    if not key:
        raise ValueError(f"未知节点类型: {node_type or node}")
    return key, "1"
