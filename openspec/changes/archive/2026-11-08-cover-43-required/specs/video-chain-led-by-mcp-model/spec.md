## ADDED Requirements

### Requirement: A landscape 成片 cannot be approved without its 4:3 cover

When a 成片 task lists the output role `cover_43`, approving that 成片 SHALL be refused while no `cover_43` output has been handed in on the task, with a message saying the 抖音 4:3 cover must be handed in first. A `cover_43` of the wrong size SHALL still only be warned about. The rules given to the model SHALL say the 4:3 cover is required. Tasks without `cover_43` SHALL be approved as before.

#### Scenario: 4:3 cover missing
- **WHEN** the user approves a landscape 成片 whose task lists cover_43 and no cover_43 was handed in
- **THEN** the approval is refused saying the 抖音 4:3 横封面 must be handed in first

#### Scenario: Older task
- **WHEN** the user approves a 成片 whose task lists only cover and cover_vertical
- **THEN** it is approved as before
