## ADDED Requirements

### Requirement: Verified publication separates model and human confirmation
Each Studio PublishedContentRecord SHALL report who confirmed its receipt and whether it counts as a verified publication. A receipt recorded by a third-party model publishing in the user's browser (verification method `third_party_model_browser`) SHALL be reported as model-confirmed; every other confirmed receipt SHALL be reported as human-confirmed. A Studio record SHALL count as a verified publication only when its receipt is human-confirmed or the record has a platform URL; a model-confirmed record without a URL SHALL be reported as pending a link and MUST NOT be counted as verified. External imports SHALL report no verification verdict. The published-content list SHALL return the verified count and the pending-link count over all records matching its filters.

#### Scenario: Model publish with a link
- **WHEN** a third-party model publishes in the browser and records the work's platform URL
- **THEN** the record reports confirmed_by model, publication_verified true, and counts toward verified_total

#### Scenario: Model publish with only a screenshot
- **WHEN** a third-party model publishes and records only a screenshot path
- **THEN** the record reports publication_verified false and pending_link true, counts toward pending_link_total, and not toward verified_total

#### Scenario: Link added later
- **WHEN** the platform URL is added later for a pending record
- **THEN** the record reports publication_verified true and pending_link false

#### Scenario: Human receipt
- **WHEN** the user records a receipt on the delivery page
- **THEN** the record reports confirmed_by human and counts as verified

#### Scenario: External import
- **WHEN** a record was imported from platform history
- **THEN** confirmed_by and publication_verified are null and it counts toward neither total

#### Scenario: Learning page shows the two counts
- **WHEN** the user opens 效果复盘 → 已发布作品
- **THEN** the list header shows the verified count and the pending-link count next to the total, and each pending-link row is marked 待补链接
