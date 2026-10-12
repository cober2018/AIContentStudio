# Agent Implementation Prompt — add-persona-creative-studio

你正在 `/Users/mshengran/Project/AIContentStudio` 的 `main` 工作区实施 OpenSpec change：
`openspec/changes/add-persona-creative-studio/`。

## 授权与边界

- 用户已经明确授权本 change 的业务代码 apply。
- 当前基线是 `main@341ead8` 加上已有的 ACO、Creation Recipe、F8 等未提交工作；这些既有改动属于受保护内容，不得 reset、rebase、清理、覆盖或回滚。
- 只实现本 change 已批准的 147 项任务；不开始 `complete-multiplatform-content-handoff`、F6C/F6D 或其他新 change。
- 不新增表或 migration；如果实现证明必须新增持久化真源，立即停下并回到规格层，不要自行扩展。
- 不执行正式 SQLite/素材库写入，不初始化正式 Starter Persona，不调用真实付费 Provider，不公开发布，不 push，不 archive，不 commit，除非用户另行授权。
- 真实 Provider 的 Text/Graphic/Audio 质量验收是独立门禁；实现阶段使用已有 fixture/本地合同测试，不能用 mock 宣称“开箱质量已通过”。

## 不可破坏的真源

1. `Brand → Persona → Account → Series` 只用于身份/品牌约束上下文。
2. Creative Profile 的唯一默认继承链是 `Persona → Account → Series`。Brand 不得提供 Skill、Style、Quality、Recipe、writing/visual/audio style 或 method stack；Brand 写入 `*_creative_profile` 必须拒绝。
3. Workflow/Creation Recipe 是流程真源；Studio Built-in Skill、Capability Memory、Installed Agent Skill 是三套分离 inventory。
4. `ContentMaster` 是内容真源，`MaterialRevision` 是文件真源，`ChannelVariant` 是渠道表达真源，`CreativeExecution` 是外部专业执行真源。
5. Audio 不新增第四种 Master；真实音频仍通过 ProviderGenerationTask → 人工接受 → MaterialRevision。
6. Video 只做到 script/shot/director package 和 professional handoff，不在本 change 内建设专业剪辑器或自动 dispatch。
7. Auto 可以走已授权 capability-routing fallback；Custom 是一个 exact provider/model/profile pin，不可用就 blocked；Custom Composition 只能使用用户事先保存的 exact ordered chain，Preview 和 receipt 必须显示实际选择与 fallback reason，禁止临时发现其他 Provider。
8. 中间 Research/Angle/Outline/Visual/Audio/Video 产物只进入 immutable WorkflowStepAttempt；Stage Handoff 只传 exact attempt/output/hash/summary/ref，不伪造 Master。

## 实施顺序

按 `tasks.md` 分批推进，每批约 20 项，但必须按原任务 ID 精确勾选，不得预勾、跳过或用文件存在冒充完成：

1. 目录、合同、校验器、Studio Skill/Preset/Quality/Blueprint catalog。
2. Persona/Account/Series creative profile validator、whole-object inheritance、snapshot provenance、Brand rejection、starter blueprint preview/apply service（正式初始化仍只做隔离测试）。
3. `CreativeConfigurationResolver`、Auto/Custom/Composition、Effective Preview/receipt、`stage.creative.method@1`、Stage Handoff、两套 Text Recipe 和确定性 Text checks。
4. Graphic visual direction/card plan、deterministic layout composer、现有 renderer 接入、Graphic QC/contact sheet。
5. Audio spoken adaptation/voice direction/TTS task reuse、MaterialRevision acceptance、Audio QC/ASR alignment；Video 只接 Director Package/handoff。
6. Identities/Settings/Recipe/feedback/save-what-worked UI，保持 lazy boundaries；然后补合同回归和浏览器 smoke。
7. 最后只运行代码审查、全量门禁和现有本地 smoke。真实 Persona A/B 的 Text+Graphic+Audio provider 质量样本另列为未授权/待验收，不虚报通过。

## 代码规则

- 优先复用现有 ACO/Creation Recipe、Identity、Stage Contract、Model Routing、Graphic Renderer、ProviderGenerationTask、MaterialRevision、Capability Memory API；不要造第二套 resolver、Skill inventory、事实真源或 Master。
- 每个 UI 可调参数必须被真实 resolver/executor 消费；否则不显示或明确 unavailable。
- 所有 profile/resource/ref 都需要版本、hash、source_kind、provenance 和边界校验；禁止 secrets、绝对路径、任意可执行内容进入 profile/skill/artifact。
- 每完成一批，立即更新本 change 的 `tasks.md`、`progress.md`、`findings.md`，记录真实命令和未完成项。
- 发现与规格矛盾、必须新增 durable object、或影响既有 ACO/F8 行为时暂停并记录 blocker。

## 外部依赖处理

`complete-multiplatform-content-handoff` 的 `stage.variant.propose` 修正和测试策略属于另一个 change。除非用户单独授权，不改它、不把它伪装成已完成；本 change 使用当前真实的 `stage.variant.adapt@1`。

## 交付与验收

实现完成后报告：

- 实际完成任务数与保留的外部依赖/真实质量门禁；
- changed files；
- backend/frontend/build/bundle/OpenSpec/Ruff/diff 结果；
- 两个 Persona 的 resolver/profile/recipe/UI smoke 结果；
- 尚未执行的正式数据初始化、真实 Provider 质量和生命周期动作。

不要在没有新鲜命令输出时声称测试通过，也不要把 `openspec status isComplete` 当成业务完成。
