## ADDED Requirements

### Requirement: Actions in the review detail keep the scroll position
审阅与交付详情页里，操作成功后的刷新 SHALL 保留已显示内容并原地更新，页面 SHALL NOT 跳回顶端；切换作品或版本时才清空重读。

#### Scenario: Backfilling a receipt
- **WHEN** 用户在交付与回填里点「回填人工回执」并成功
- **THEN** 页面停在原位置，该目标显示新的回执和状态
