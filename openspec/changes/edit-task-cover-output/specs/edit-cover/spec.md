## ADDED Requirements

### Requirement: Edit tasks accept a cover image

Rough-cut and final edit tasks SHALL offer one optional cover output, JPEG or PNG, that must sit in the project's 导出/封面/ folder when submitted. The review page SHALL show the submitted cover beside the cut. When the user approves the final cut, its cover SHALL become the work's cover.

#### Scenario: Submit a cover
- **WHEN** the executor exports 导出/封面/封面.jpg and submits it as cover
- **THEN** the review page shows that image and the file stays in 导出/封面/

#### Scenario: No cover
- **WHEN** a task finishes without a cover
- **THEN** the task completes as before and the work's cover is unchanged

#### Scenario: Final approved
- **WHEN** the user approves a final cut that came with a cover
- **THEN** the work's master records that image as its cover
