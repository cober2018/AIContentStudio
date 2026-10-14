# content-harness-registry Specification

## Purpose
TBD - created by archiving change align-v1-prd2-content-harness. Update Purpose after archive.
## Requirements
### Requirement: Channel selection uses one registry

系统 SHALL 使用单一 Channel Registry 校验 Topic target、Generation、Workflow、Renderer、Delivery，不得让前后端维护互相独立的合法渠道集合。现代 Recipe/Production/Variant/Review SHALL 使用同一服务端 exact source schema × target form × published profile × adapter descriptor。目录 MUST 区分 planned/configured/executable/packageable/remote_verified 和明确 unavailable reason；标签、旧 fallback 或 profile 存在本身 MUST NOT 证明现代可执行或远端已验证。

#### Scenario: 新增平台配置

- **WHEN** admin 发布一个合法的新 Channel Profile
- **THEN** Topic target selector、Workflow target validation 和 Delivery capability 均从 Registry 读取
- **AND** 不要求修改 `models.Channel` 才能识别新平台

#### Scenario: 现代目标缺少真实适配合同
- **WHEN** UI 展示计划平台但缺 exact published profile、兼容 source schema 或 executable adapter
- **THEN** 目标明确显示不可执行原因，不在前端用标签或旧 fallback 伪造执行资格
- **AND** 历史路径继续按原兼容规则读取

### Requirement: Runtime plugin resolution is version-pinned

系统 MUST 对新 Workflow Node 保存 plugin key/version，并在运行时按该版本解析。

#### Scenario: Skill 后续升级

- **WHEN** `studio-xueqiu-article` 从 1.0 升到 1.1
- **THEN** 历史 WorkflowRun 仍显示并引用 1.0
- **AND** 新 Workflow Version 才使用 1.1

### Requirement: Profile enablement is additive explicit and reviewable

平台 profile 初始化 SHALL 复用 ChannelTemplateVersion，提供零写入 dry-run 和完整差异，缺失配置仅显式新建；已有 published 配置变更 SHALL 以 expected current ID/hash 做 CAS，append-only 新版本并保持历史 hash。重复同一启用请求 MUST 幂等，MUST NOT 覆盖用户配置、绑定旧 Unit/Run、执行全库 seed 或修改模型/用户/默认流程。正式库启用 SHALL 另有明确授权和配套备份，不从代码 apply 推定。

#### Scenario: Existing customized profile
- **WHEN** 初始化发现同渠道已有用户修改的 published profile
- **THEN** 系统展示冲突/完整差异，未经确认不新增替代版本也不改旧配置

#### Scenario: Repeat identical enablement
- **WHEN** 相同的 profile 启用请求重复提交
- **THEN** 返回现有 exact profile，不产生重复版本或重新绑定历史内容

### Requirement: Node descriptors may expose a versioned Stage Contract

The node/plugin registry SHALL support an optional bounded Stage Contract descriptor containing typed config/UI/input/output/tunable-field and execution-preview capabilities. The contract is metadata/validation truth for product controls and MUST NOT make an unavailable executor executable.

Stage activation SHALL use a distinct new registered plugin version pinned with its exact contract schema/version in a newly saved Workflow definition. Existing media/check/human plugin versions and historical definitions/reruns MUST NOT inherit new contract validation or execution/review semantics merely because registry metadata changed.

#### Scenario: Legacy node without Stage Contract
- **WHEN** an old plugin has no Stage Contract
- **THEN** it remains executable through its existing advanced workflow behavior but is not given invented normal-stage tuning controls

#### Scenario: Stage controls are added for a media or check plugin
- **WHEN** a new stage-capable version is registered while old Workflow definitions remain pinned to the original version
- **THEN** only explicitly saved definitions selecting the new version activate that Stage Contract and historical reruns keep the old behavior

### Requirement: Stage executors consume the exact resolved contract

A Stage Contract executor SHALL receive the canonical ResolvedStageExecution/effective config produced by the server resolver. It MUST NOT read a conflicting hidden parameter source for fields declared tunable. Any exposed field that the executor cannot consume MUST fail validation rather than be ignored.

#### Scenario: Prompt exists in config but executor ignores it
- **WHEN** a plugin declares prompt/instruction tunable but its execution adapter cannot bind that value
- **THEN** the definition is rejected as an invalid Stage Contract implementation

### Requirement: Project-native stage plugins do not redefine legacy plugins

New modern Master/Variant/Creative Execution stage plugins SHALL use distinct plugin identities/versioning and existing domain services. Legacy `builtin.generate` and historical workflow behavior remain unchanged.

#### Scenario: Historical Draft workflow
- **WHEN** an old Run uses `builtin.generate`
- **THEN** it continues its frozen Draft-oriented behavior and is not reinterpreted as a Master proposal stage
