## ADDED Requirements

### Requirement: Dialogue level checks skip shots nobody speaks in

The dialogue loudness check SHALL treat a shot as spoken only when it has a script line and its board speaker is not none; unspoken shots SHALL NOT be measured for dialogue or included in the median, while their brightness checks still run.

#### Scenario: Closing shot with on-screen text only
- **WHEN** task 40 of work 93 is checked and its last shot has speaker none with a caption line
- **THEN** no dialogue_level_uneven warning is given for it and the other shots read the same as before
