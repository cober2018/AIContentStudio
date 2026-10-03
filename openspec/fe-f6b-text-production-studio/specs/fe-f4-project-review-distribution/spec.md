## MODIFIED Requirements

### Requirement: Unit review workspace

A selected unit SHALL expose Preview, Changes, Checks and Publish tabs and clearly separate Freeze Candidate, Content Approval, Delivery Authorization and delivery execution. Preview/Changes/Checks SHALL render v4 Text/Graphic/Video according to modality and exact frozen schema.

For `text.master.v2`, Preview SHALL derive the readable body from the Candidate's frozen deterministic render while exposing bounded structured-document metadata. Changes SHOULD use structured block-aware comparison when both candidates are v2; rendered Markdown similarity MAY remain a secondary text metric. Review MUST NOT read mutable current Master state or assume v2 payload contains editable Markdown.

#### Scenario: Review Text v2 Candidate
- **WHEN** a reviewer opens a frozen v2 Text Candidate
- **THEN** Preview shows the exact frozen rendered body and schema metadata, and Changes reports frozen structured/render differences without reading current editor state

#### Scenario: Compare v1 and v2 Text Candidates
- **WHEN** Candidate history crosses the explicit v1→v2 fork
- **THEN** Review remains bounded/read-only and presents a truthful comparable text projection without rewriting either Candidate
