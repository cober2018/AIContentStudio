## ADDED Requirements

### Requirement: Manual receipts need a link and can be corrected
复制包类目标回填人工回执时 SHALL 要求非空链接；已回填的复制包目标 SHALL 可以修改回执链接，修改原地更新该回执并写修改记录，SHALL NOT 新增回执或发布记录。

#### Scenario: Empty receipt is not accepted
- **WHEN** 输入框为空
- **THEN** 「回填人工回执」不可点，直接调用接口也被拒绝

#### Scenario: Filling an earlier empty receipt
- **WHEN** 百家号目标 #7 的回执没有链接，用户点「修改」填入链接保存
- **THEN** 回执显示新链接，目标仍是人工已确认，发布记录仍只有一条
