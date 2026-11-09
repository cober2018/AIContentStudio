## ADDED Requirements

### Requirement: Draft push is offered again after explicit not-delivered reconciliation
用户对结果未确认的草稿推送明确核对为「未交付」后，交付页 SHALL 重新提供「推到草稿箱」；结果仍需核对时 SHALL NOT 提供。是否允许新尝试仍以后端判断为准。

#### Scenario: Re-push after not delivered
- **WHEN** 目标已核对为未交付并回到「已授权」
- **THEN** 页面显示「推到草稿箱」，点击后产生新编号的尝试

#### Scenario: Unreconciled result hides push
- **WHEN** 目标处于「需核对」
- **THEN** 页面只显示核对操作，不显示推送
