# v1-platform-artifacts Specification

## Purpose
TBD - created by archiving change align-v1-prd2-content-harness. Update Purpose after archive.
## Requirements
### Requirement: Article and answer are separate content forms

系统 SHALL 将知乎文章与知乎回答作为独立 content forms：同时选择时创建两个独立 WorkflowRun/Draft，Answer MUST 使用 direct-answer 结构规则。

#### Scenario: 同时选择文章与回答

- **WHEN** Topic 同时选择知乎文章和知乎回答
- **THEN** 系统创建两个独立 WorkflowRun/Draft
- **AND** Answer 使用 direct-answer 结构规则

### Requirement: Xueqiu finance rules are mandatory

雪球 quant / market recap 内容 MUST 完成 as_of / scope / risk / no-return-guarantee Rule Set，未完成时 MUST NOT 可批准。

#### Scenario: 财经规则未完成

- **WHEN** content form 是 quant / market recap
- **THEN** as_of / scope / risk / no-return-guarantee Rule Set 必须完成
- **AND** 未完成时不可批准

### Requirement: Juejin technical rules are mandatory

掘金 tech article MUST 按 profile 执行 code/provenance/version/benchmark 条件，无依据代码 MUST NOT 被标记为 verified runnable。

#### Scenario: 技术内容规则检查

- **WHEN** content form 是 tech article
- **THEN** code/provenance/version/benchmark 条件按 profile 执行
- **AND** 无依据代码不得被标记为 verified runnable

### Requirement: Douyin remains script-only in V1

抖音在 V1 SHALL 保持 script-only：approved package 可含 spoken script/scenes/B-roll brief/estimated SRT，UI MUST 明确显示 `script package` 且 MUST NOT 显示「视频成片 Ready」。

#### Scenario: 抖音脚本批准

- **WHEN** 抖音 Script Candidate approved
- **THEN** package 可含 spoken script/scenes/B-roll brief/estimated SRT
- **AND** UI 明确显示 `script package`
- **AND** 不显示「视频成片 Ready」

