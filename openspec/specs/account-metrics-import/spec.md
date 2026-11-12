# account-metrics-import Specification

## Purpose
TBD - created by archiving change browser-metrics-review. Update Purpose after archive.
## Requirements
### Requirement: A third-party model imports works data read from the logged-in platform backend
The platform SHALL accept works data that a third-party model read directly from a platform's logged-in backend as source kind `platform_page`, without first waiting for the user's OK, and SHALL report the batch with its undo link. Each row MAY carry the platform's own item id and the id of a published record the model matched. The platform SHALL match a row to a published record by platform item id first, then by the given record id, then by title and publish time, SHALL remember the platform item id on the matched record, and SHALL fill the record's missing publish time, link or account from the row. The platform SHALL list an account's published records for the model to match against. Step-by-step instructions per platform SHALL be a platform skill readable without naming a work.

#### Scenario: Our own work gets its data
- **WHEN** the model imports 抖音 data for work 97, passing the record id it matched and the 抖音 item id
- **THEN** the metrics attach to the studio's 抖音 record of work 97, which gains its publish time and item id, and no new external work is created

#### Scenario: Next import
- **WHEN** the same 抖音 work is imported again with only its item id
- **THEN** it matches the same record

#### Scenario: Data read from screenshots
- **WHEN** the source is a screenshot
- **THEN** the model still shows the table to the user and waits for their OK before importing

### Requirement: The published work's link goes back into its receipt
After publishing, the model SHALL read the work's public link from the platform and record it in the delivery receipt; when the platform has no link yet (in review, scheduled) or none at all, the receipt SHALL keep the screenshot and the model SHALL fill the link later. The platform SHALL list published targets still missing a link, SHALL let the model fill it, and SHALL update the receipt and the published record together. A metrics import that matches a studio record SHALL fill a missing link the same way.

#### Scenario: Link filled later
- **WHEN** the 抖音 work of target 5 was published with only a screenshot and the model later reads its link
- **THEN** the model fills it, and the delivery page and the published record both show the link

