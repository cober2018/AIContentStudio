## ADDED Requirements

### Requirement: A work's own older edit task never blocks its new one

When the model claims an edit task, the one-edit-at-a-time check SHALL ignore other edit tasks of the same work, and the waiting count SHALL count only other works' tasks; another work's active edit SHALL still block as before.

#### Scenario: New task after a blocked one
- **WHEN** a work's task 51 is blocked with activity 20 minutes ago and the model claims the same work's new task 52
- **THEN** the claim succeeds

#### Scenario: Other work still blocks
- **WHEN** another work's edit task had activity 5 minutes ago
- **THEN** the claim is refused with `video_edit_queue_busy`
