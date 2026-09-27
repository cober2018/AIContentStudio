# content-harness-registry Specification

## Purpose
TBD - created by archiving change align-v1-prd2-content-harness. Update Purpose after archive.
## Requirements
### Requirement: Channel selection uses one registry

系统 SHALL 使用单一 Channel Registry 校验 Topic target、Generation、Workflow、Renderer、Delivery，不得让前后端维护互相独立的合法渠道集合。

#### Scenario: 新增平台配置

- **WHEN** admin 发布一个合法的新 Channel Profile
- **THEN** Topic target selector、Workflow target validation 和 Delivery capability 均从 Registry 读取
- **AND** 不要求修改 `models.Channel` 才能识别新平台

### Requirement: Runtime plugin resolution is version-pinned

系统 MUST 对新 Workflow Node 保存 plugin key/version，并在运行时按该版本解析。

#### Scenario: Skill 后续升级

- **WHEN** `studio-xueqiu-article` 从 1.0 升到 1.1
- **THEN** 历史 WorkflowRun 仍显示并引用 1.0
- **AND** 新 Workflow Version 才使用 1.1

