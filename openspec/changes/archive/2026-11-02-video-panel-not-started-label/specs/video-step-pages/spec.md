## ADDED Requirements

### Requirement: A video that has not started shows 待开始 on the 导演稿 step

When a video work's chain has not started, the 导演稿 step's chain panel SHALL show 「待开始」 with how to start, and SHALL NOT claim the 导演稿 was approved.

#### Scenario: Freshly created product video
- **WHEN** the user opens the 导演稿 step of a product video created a moment ago
- **THEN** the panel shows 「待开始」, not 「导演稿 已采用」
