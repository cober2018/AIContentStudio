## ADDED Requirements

### Requirement: Generate only after the draft is approved and materials are mapped

For product video works, the 导演稿 step SHALL show only the draft content, with no shot generation controls or material status. Shot first-frame generation, automatic image-to-video and manual/auto switching SHALL be refused before the 导演稿 is approved. The materials step SHALL summarise how many shots use the user's materials and how many lack a picture, and SHALL offer generation controls only on shots without a material.

#### Scenario: Reviewing the draft
- **WHEN** the user opens a product work's 导演稿 for review
- **THEN** no 手动 / 自动 or prompt controls appear and no generation can start

#### Scenario: After mapping
- **WHEN** the draft is approved and 7 of 12 shots have the user's materials
- **THEN** the materials step says 7 use the user's materials and 5 lack a picture, and only those 5 show 手动 / 自动

#### Scenario: Generation before approval
- **WHEN** the executor calls generate_shot_video before the draft is approved
- **THEN** it is refused with a message to approve the draft and map materials first
