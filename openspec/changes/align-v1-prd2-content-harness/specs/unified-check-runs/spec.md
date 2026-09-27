## ADDED Requirements

### Requirement: All mandatory checks are input-bound

系统 SHALL 为每个检查记录 input_hash，draft body/material/SEO metadata 改变时 MUST 将受影响 check run 标 stale，Review Center MUST NOT 将旧 pass 显示为当前有效。

#### Scenario: 正文修改后

- **WHEN** draft body/material/SEO metadata 改变
- **THEN** 受影响 check run 标 stale
- **AND** Review Center 不显示旧 pass 为当前有效

### Requirement: Incomplete is not pass

系统 MUST 将执行失败/截断的检查标记为 incomplete/failed，且 mandatory check 未完成时 MUST NOT 允许 Approval。

#### Scenario: 检查执行失败

- **WHEN** semantic checker、SEO checker 或 provider 执行失败/截断
- **THEN** 状态为 incomplete/failed
- **AND** mandatory check 不允许 Approval
