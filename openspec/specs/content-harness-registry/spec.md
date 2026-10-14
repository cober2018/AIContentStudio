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

