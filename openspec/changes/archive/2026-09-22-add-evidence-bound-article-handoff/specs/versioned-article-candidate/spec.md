## ADDED Requirements

### Requirement: Existing satisfactory articles enter as immutable mother revisions
The system SHALL allow an existing satisfactory article to be imported as a MotherRevision without mandatory regeneration, and SHALL create a new revision instead of overwriting an existing mother revision when the article changes.

#### Scenario: Import preserves the original article
- **WHEN** a user imports and confirms an existing article with a valid frozen evidence pack
- **THEN** the system creates a MotherRevision whose canonical Markdown matches the confirmed article
- **AND** no model rewrite is required to proceed

#### Scenario: Mother edit creates lineage
- **WHEN** a user edits a confirmed MotherRevision
- **THEN** the system creates a child revision with a new body hash
- **AND** the prior revision remains readable and unchanged

### Requirement: Platform drafts bind to an explicit mother revision
Each M1 WeChat or X Thread Draft SHALL reference the exact MotherRevision and evidence snapshot from which it was adapted.

#### Scenario: New mother revision does not silently replace a draft
- **WHEN** a newer MotherRevision is created after a platform Draft was adapted
- **THEN** the Draft remains bound to its original revision
- **AND** the user must explicitly create or rebase a new platform revision to use the newer mother content

#### Scenario: X Thread stores ordered post boundaries
- **WHEN** an X Thread Draft is created or edited
- **THEN** the system persists its ordered post boundaries as a derived artifact tied to the Draft input hash

### Requirement: Derived artifacts become stale when inputs change
Structured content, thread boundaries, citation maps, checks, renders, and export manifests SHALL record their input hash and SHALL be marked stale when any material input changes.

#### Scenario: Body edit invalidates old derived content
- **WHEN** the title, canonical body, thread order, citation, declaration, or media order changes
- **THEN** dependent artifacts no longer qualify as current
- **AND** the candidate cannot be approved until required artifacts are rebuilt and reviewed

### Requirement: Review includes final media before approval
The system SHALL support draft-stage media and SHALL present the actual ordered media with the final text before creating content approval.

#### Scenario: Approval candidate includes final cover and image order
- **WHEN** a user opens an M1 candidate for approval
- **THEN** the candidate manifest includes the final title, body, ordered media content hashes, citations, declarations, and current check records
- **AND** missing or placeholder required media prevents ready status

#### Scenario: Approved media cannot be overwritten or deleted
- **WHEN** media bytes are referenced by an approved candidate
- **THEN** those bytes remain addressable by the approved content hash
- **AND** upload or deletion operations cannot alter the historical candidate

### Requirement: Content approval binds a complete immutable candidate hash
Content approval SHALL bind the complete candidate manifest hash and SHALL not mean that any platform account or delivery action is authorized.

#### Scenario: Candidate edit invalidates its approval
- **WHEN** any item represented by an approved candidate hash is changed
- **THEN** the changed candidate has a new hash and requires new content approval
- **AND** the previous immutable approved candidate remains historical unless explicitly revoked

#### Scenario: Incomplete semantic review is not a pass
- **WHEN** a required model or manual review is missing, failed, truncated, or stale
- **THEN** the candidate review status is incomplete rather than passed
- **AND** approval remains blocked until coverage is completed or an allowed evidence-backed disposition is recorded

### Requirement: Evidence and rights revocation affects pending candidates
The system SHALL identify uncompleted candidates and targets affected by evidence correction, public-rights revocation, or approval revocation.

#### Scenario: Rights revocation pauses an uncompleted target
- **WHEN** media or evidence rights used by an approved but undelivered target are revoked
- **THEN** the target is paused and requires a new valid candidate and authorization before handoff
