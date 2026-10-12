# Findings — Twelve-platform local content handoff

## 需求与实际范围

- 原范围见根PRD §3.1、docs/AI_CONTENT_STUDIO_V1_ALIGNMENT_PLAN.md渠道表：十二平台，不能用首选三渠道或F6E首批五形态替代。
- 用户2026-10-06确认本阶段先做平台稿件/素材包；公众号既有草稿箱保留，其他人工发布。该回答没有授予新的发文、正式profile写入或business apply权限。
- B站专栏/图文、知乎文章/回答、X single/thread/long_post/articles独立验收；因此十二个平台对应十七形态。抖音当前适配目标是脚本，不是视频成片；通用Video Master生产能力不被删除。

## 代码事实

- ChannelRegistry读取published ChannelTemplateVersion.profile_json并提供legacy fallback；不是缺少平台字符串枚举。
- seed_v1_channel_profiles有十四平台定义，但X仅single/thread、B站仅article；没有现代长帖/Articles/B站图文合同。seed还包含管理员/BrandVoice/Prompt等其它初始化，不能在正式库整体运行来补渠道。
- channel_adapters.FIRST_BATCH/可执行注册、channel_variant_documents与前端ChannelVariantsPanel.TARGETS当前五种形态硬编码；只更新目录会让新平台没有可执行adapter/编辑合同。
- production_packages已有v5受控本地包，但只生成generic guide/有限text/image/script投影；需要安全sources/declarations、平台HTML和形态结构文件，不能从live正文或Draft补内容。
- v5可复用append-only Variant、safe LLMRun、exact refs/checks/profile/currentness和单一source pointer；无需新增表、迁移或Candidate版本。
- 当前未暴露codebase-memory-mcp graph工具，仅对相关代码/字符串使用限定rg/read回退，不全仓扫描。

## 保留边界

既有五schema/hash、所有legacy/v1-v5历史、归档只读、project权限、live material/evidence、derived rights、safe provenance、profile CAS、Unknown不重发及公众号原文件名/字节/MIME契约不能削弱。Registry/profile≠executable adapter≠local package≠verified publisher≠published。

严格校验验证结构，不代表十七平台已实施；受控fixture不代表真实模型质量或平台发布效果。profile正式启用需单独明确授权及配套备份。
# 2026-10-08 Persona前置规格边界

当前真实适配Stage为`stage.variant.adapt@1`（stage_domain_integrations映射）；不存在`stage.variant.propose`可执行插件。计划已统一真实名称，持久参数化覆盖与集中十七形态冒烟均明确为后续义务，临时冒烟不能冒充持久覆盖；目前没有写入许可或新测试文件，不把Persona自动续行扩大成十二平台apply。
