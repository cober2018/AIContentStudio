## ADDED Requirements

### Requirement: Every visual platform version has a cover

Each visual platform version SHALL carry a cover slot sized to that platform's spec, with safe areas recorded, and SHALL be reviewable at real size before approval.

#### Scenario: Douyin version of a video
- **WHEN** a video work has a Douyin platform version
- **THEN** it shows a 9:16 cover slot with its 3:4 feed crop and safe-area overlay

### Requirement: Covers and titles are chosen from candidates

The platform SHALL propose several cover and title candidates (video frame, project image, generated image, composed layout) as rights-bearing material revisions, and the user MUST choose one of each; the choice SHALL be frozen into the approved candidate.

#### Scenario: Changing the cover after approval
- **WHEN** the user picks a different cover after approval
- **THEN** a new candidate is required and the old approval does not cover it
