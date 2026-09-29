## MODIFIED Requirements

### Requirement: Unit review workspace
A selected unit SHALL expose Preview, Changes, Checks and Publish tabs and clearly separate Freeze Candidate, Content Approval, Delivery Authorization and delivery execution.

#### Scenario: Inspect a unit before approval
- **WHEN** an authorized reviewer opens a unit with a frozen but unapproved Candidate
- **THEN** Preview, Changes, and Checks show frozen facts, Publish shows authorization unavailable, and approval is a separate explicit action

#### Scenario: Candidate diff
- **WHEN** a unit has two immutable Candidates
- **THEN** Changes returns a bounded read-only comparison of content, media, evidence, identity, workflow, checks, and render provenance without creating a diff table

Preview/Changes/Checks SHALL render v4 Text/Graphic/Video according to modality. Text similarity is optional for text and MUST NOT be fabricated for Graphic/Video.

#### Scenario: V4 modality review
- **WHEN** a reviewer opens a v4 Candidate
- **THEN** Review shows modality-appropriate preview/diff/check information from the frozen manifest

A selected unit SHALL expose Preview, Changes, Checks and Publish tabs and clearly separate Freeze Candidate, Content Approval, Delivery Authorization and delivery execution. Preview/Changes/Checks SHALL render v4 Text/Graphic/Video according to modality and exact frozen schema.

For `text.master.v2`, Preview SHALL derive the readable body from the Candidate's frozen deterministic render while exposing bounded structured-document metadata. Changes SHOULD use structured block-aware comparison when both candidates are v2; rendered Markdown similarity MAY remain a secondary text metric. Review MUST NOT read mutable current Master state or assume v2 payload contains editable Markdown.

#### Scenario: Review Text v2 Candidate
- **WHEN** a reviewer opens a frozen v2 Text Candidate
- **THEN** Preview shows the exact frozen rendered body and schema metadata, and Changes reports frozen structured/render differences without reading current editor state

#### Scenario: Compare v1 and v2 Text Candidates
- **WHEN** Candidate history crosses the explicit v1→v2 fork
- **THEN** Review remains bounded/read-only and presents a truthful comparable text projection without rewriting either Candidate
