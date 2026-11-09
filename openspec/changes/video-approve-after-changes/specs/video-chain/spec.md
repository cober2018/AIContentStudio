## ADDED Requirements

### Requirement: Approve the current cut after sending changes
When the user sends a 小样 or 成片 back with changes, the platform SHALL keep the approve action available on that cut until the user approves it or it is superseded. Approving accepts the cut as it stands, and the page SHALL say that the user's changes are dropped.

#### Scenario: Approve after changes before a new task starts
- **WHEN** the user has sent a 成片 back with changes and no new task has started
- **THEN** 「成片通过」 is available and approving it accepts the current 成片 and moves the piece to 审阅与交付

#### Scenario: Approve after a new task has started
- **WHEN** the user approves the current 成片 after the third-party model has started a new task (per the chosen option)
- **THEN** the new task is marked 已作废 and cannot be approved, and its files are kept, not deleted

#### Scenario: Same for 小样
- **WHEN** the user sends a 小样 back with changes
- **THEN** 「小样通过」 is available by the same rule
