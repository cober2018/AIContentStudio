# 依赖梳理（2026-10-29，只读核查）

## 可删
- `stage_audio.py`、`stage_audio_asr.py`（只服务 `stage.audio.asr` 节点）、`audio_quality.py`（除 `master_loudness` / `_loudnorm`）。
- `content_harness/nodes/__init__.py`：`StageMediaGenerationV4NodePlugin`（TTS）、`StageAudioASRNodePlugin`、`StageAudioQCNodePlugin` 及注册、`bootstrap_audio_quality()`、`stage.creative.method` 输出枚举里的 `audio.spoken-adaptation.v1` / `audio.voice-direction.v1`（口语稿保留时 spoken-adaptation 留下）。
- `stage_domain_integrations.py` DOMAIN_PLUGINS 的 `("media.generate","4")`、`("stage.audio.asr","1")`、`("stage.audio.qc","1")` 与 audio_context 分支；`stage_domain_adoptions.py` audio_asr / audio_quality / TTS 漂移分支；`stage_invocations.py:499`、`stage_continuation.py:112` ASR 特判；`routers/stage_integrations.py` 的 `"audio_asr"`。
- `creative_configuration.py`：native_tts / audio_qc / audio_planning / product_voice_required；`production_stage_key` 的 `audio.` 与 `stage.audio.qc` 分支；`MODALITY_FIELDS["audio"]`。
- `starter_personas.py` audio_definition 与 audio readiness；`creation_recipe_learning.py:559–587` 音频配方选项、`_creative_method_scope` 的 audio。
- `studio_creative_catalog.py`：OUTPUT_SCHEMAS 两个 audio 键、`studio.audio.{voice-director,tts,qc}` 资源、两个 audio 质量标准、BLUEPRINTS 的 audio_creative_profile、PERSONA_METHOD_TRIAL_KEYS 的 audio、validate_creative_profile 的 audio 分支。
- `content_identity.CreativeProfile.schema_` 的 audio、`IdentityProfile.audio_creative_profile`、`validate_creative_modalities`。
- 技能包 `studio.audio.{tts,qc,voice-director}`；`craft_skills._NOT_WRITING`、`_WRITING_FAMILIES` 的 audio。
- 前端：`PersonaCreativeConfig.tsx` 音频页签、`StageDomainResultPanel.tsx`（audio_asr / audio qc / audio subtitles）、`CreationRecipePanel.tsx:212,451`、`IdentityProfileView.tsx:18`。
- 测试：`test_persona_audio_quality.py` 整个；`test_persona_creative_studio.py` audio 参数化。

## 必须保留 / 挪
- `audio_quality.master_loudness` + `_loudnorm`：`routers/materials.py:596` `POST …/loudness-master`，craft-resolve `finishing.md` 让第三方模型剪前调用，库里已有 2 条母带。
- `asr_suggestions`、`local_mlx_asr_provider`：视频字幕 ASR。
- `tts_parameters`、generation_tasks 的 tts、minimax provider、素材手动 TTS（`materials.py:69-83`）、voiceover。
- `media.generate` v2/v3；`PRODUCTION_STAGES` 阶段 id（只去掉 modalities 里的 "audio"）。
- `PersonaVoicePreset.tsx` 只挂在音频页签（`PersonaCreativeConfig.tsx:307`），删页签前挪出。
- `studio.audio.spoken-adapt`：在 SHARED_SKILLS，经 `_WRITING_FAMILIES["video"]` 暴露给视频作品（人设与商品）——保留为视频 / 文字写作 skill。

## 数据
- `content_persona_revision.profile_json` 14 条带 audio_creative_profile（IdentityProfile `extra="forbid"`，删字段前先迁移）。
- `identity_snapshot` 52 条：冻结只读，确认读取不重新校验。
- `workflow.definition_json` 11 条（文字作品 unit 8,44,46,55,56,57,58,61,64,71,73）含 TTS/ASR/QC 节点；`project_workflow_binding` 11 条；12 个 run、33 个相关 attempt、32 条已接受输出、12 条 TTS 生成任务——只读保留。
- `production_profile_revision.settings_json` 101 条 audio_creative_profile 全为 null；`product_sku_work` 25 条全为 null。
- 音频素材 25 条保留。
