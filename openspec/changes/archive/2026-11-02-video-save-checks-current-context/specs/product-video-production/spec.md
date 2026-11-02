## ADDED Requirements

### Requirement: Video saves check against the current settings

When a 导演稿 or shot material choice is saved for a video work that already has a 导演稿, the save SHALL be checked against the context computed from the work's current settings, not against the context stored with the previous 导演稿 version. A settings change made by someone else while the save is in progress SHALL still be refused.

#### Scenario: Main image changed after approval
- **WHEN** work 90's product main image or footage mode changed after its 导演稿 was approved and the MCP saves a new 导演稿
- **THEN** the save succeeds and the new version records the current context
