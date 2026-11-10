## ADDED Requirements

### Requirement: The video delivery step points to 审阅与交付 without channel variants
The 交付 step of a persona video SHALL show covers, publish copy and the link to 审阅与交付, and SHALL NOT show the channel variant panel, because approving the 成片 already sends the work to 审阅与交付.

#### Scenario: Approved finished video
- **WHEN** the user opens the 交付 step of a persona video whose 成片 was approved
- **THEN** the step shows covers, publish copy and 「下一步：审阅与交付当前作品 →」, with no 生成确定性预览 button
