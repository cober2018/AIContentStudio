## ADDED Requirements

### Requirement: Films default to 60 fps

When the edit is prepared for a work whose 导演稿 has no recorded frame rate, the platform SHALL set the 小样, the 成片 and every AE intermediate composition to 60 frames per second. A work whose 导演稿 already records a frame rate SHALL keep it, so videos already made are not redone. The Resolve timeline and delivery SHALL use the 导演稿's recorded frame rate.

#### Scenario: New work
- **WHEN** the model prepares the edit of a work that has never been prepared
- **THEN** the 导演稿 records 60 fps for the 小样, the 成片 and its AE compositions, and a 30 fps upload is rejected

#### Scenario: Work already at 30 fps
- **WHEN** the model prepares the 成片 of a work whose 小样 was made at 30 fps
- **THEN** the 导演稿 keeps 30 fps
