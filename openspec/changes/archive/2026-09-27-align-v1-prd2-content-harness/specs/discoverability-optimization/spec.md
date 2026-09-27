## ADDED Requirements

### Requirement: Discoverability is a distinct stage

系统 SHALL 为启用 SEO profile 的平台 Workflow 生成结构化 DiscoverabilityReport，MUST NOT 把 SEO 指令隐藏在普通 Writer Prompt 中作为唯一实现。

#### Scenario: 启用 SEO profile 的工作流

- **WHEN** 平台 Workflow 启用 SEO profile
- **THEN** 系统生成结构化 DiscoverabilityReport
- **AND** 不把 SEO 指令隐藏在普通 Writer Prompt 中作为唯一实现

### Requirement: SEO suggestion cannot mutate approved content

系统 MUST 通过新 Draft Revision 应用 SEO 建议，且使 downstream checks/render/candidate stale，MUST NOT 原地修改已批准内容。

#### Scenario: 应用 SEO 标题建议

- **WHEN** 用户将 SEO 标题建议应用到 Draft
- **THEN** 创建新 Draft Revision
- **AND** downstream checks/render/candidate stale
