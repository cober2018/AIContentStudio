## ADDED Requirements

### Requirement: Text candidate preserves image placement

系统 SHALL 在 Draft document/placement 中保存图文 composition，placement 变化 MUST 产生新 Draft 版本并使 Render/Candidate 失效，且不得改动 prior Candidate。

#### Scenario: 移动图片位置

- **WHEN** 用户把某张图片移动到另一段之后
- **THEN** Draft document/placement 产生新版本
- **AND** prior Candidate 不变化
- **AND** Render/Candidate 标 stale

### Requirement: Placeholder is not final media

系统 MUST 保证 image prompt / generated placeholder SVG 不满足 required actual-media 规则，不得批准为最终图文成品。

#### Scenario: 只有占位图

- **WHEN** draft 只有 image prompt / generated placeholder SVG
- **THEN** required actual-media rule 返回 blocker/incomplete
- **AND** 不得批准为最终图文成品
