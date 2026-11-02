## ADDED Requirements

### Requirement: Approving a sample or final shows in progress until it is written

When the user approves a 小样 or 成片, the platform SHALL first record and save an in-progress approval, then accept the task's outputs, then record the approval and clear the marker; a failure SHALL clear the marker. While the marker exists the chain state SHALL be 「正在通过…」 on the page and `approving` in `get_video_decision`, with a note to check again later, never 「待你看」. A marker older than 5 minutes SHALL be ignored.

#### Scenario: Model asks right after the user clicks 通过
- **WHEN** the user approves the 小样 and the model calls get_video_decision while outputs are still being accepted
- **THEN** it reads state approving with the note to check again, not 小样待你看

### Requirement: Platform-written cover check is kept with the output

The platform-written `cover_check` result SHALL be an allowed output metadata field, so deliveries with a cover and a final are not refused, while an executor-supplied value is still discarded.

#### Scenario: Cover then final delivered
- **WHEN** a cover and then a final are delivered for one task
- **THEN** both are accepted and the cover check is stored and shown on the review page
