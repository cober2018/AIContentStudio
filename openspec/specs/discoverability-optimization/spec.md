# discoverability-optimization Specification

## Purpose
TBD - created by archiving change align-v1-prd2-content-harness. Update Purpose after archive.
## Requirements
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

### Requirement: Search promotion discoverability check

对 search 域文字作品，系统 SHALL 以检索规则版本 `seo.search_promotion` 执行检索检查（摘要位置即开头一段）：
- 平台机械检查：标题前段（前 15 字内）含主词；开头一段非空且含主词或品牌词；有问答段；关键词没有堆砌。数据能否对上出处由现有事实检查按项目事实边界执行。
- 语义判断：「是否正面回答了对应问题、开头是否给出结论、品牌说法是否一致」交给写作模型，经现有提醒判断流程给出结论。

检查结果 MUST 显示在现有检查流程中；采纳修改建议 MUST 生成新版本，MUST NOT 修改已通过内容。规则 MUST 按作品锁定的搜索规划版本执行。

#### Scenario: 标题没含主词
- **WHEN** search 域文章标题前 15 字不含主词
- **THEN** 检索检查给出提醒「标题前段没有主词」

#### Scenario: 数据对不上出处
- **WHEN** 正文写了一个数字，推广对象带出处的事实里找不到
- **THEN** 事实检查标出这一句

#### Scenario: 是否回答了问题
- **WHEN** 机械检查通过
- **THEN** 「是否正面回答对应问题」由写作模型判断，结果作为提醒处理记录

