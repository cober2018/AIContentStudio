## MODIFIED Requirements

### Requirement: Text, Graphic and Video use versioned modality payloads

The production core SHALL register schema-versioned payload adapters for `text`, `graphic`, and `video`. Adapter dispatch SHALL use the exact persisted payload schema. Historical `text.master.v1` remains supported; after F6B the default new Text schema SHALL be `text.master.v2`, whose authoritative content is a Studio structured document and whose Markdown is a deterministic render. Graphic/Video F6A schemas remain unchanged.

#### Scenario: Historical Text v1
- **WHEN** a v1 Master or Candidate is read after F6B
- **THEN** the v1 adapter preserves its original validation/render/history behavior without rewriting it

#### Scenario: New professional Text revision
- **WHEN** a new user-authored Text Master is created through Text Studio after F6B
- **THEN** the server uses `text.master.v2` by default and stores the structured document rather than a second editable Markdown truth

### Requirement: Master checks are append-only and input-bound

ContentMasterCheckRun SHALL remain append-only, bound to one Master revision and exact input/profile/adapter version. Required check kinds SHALL be resolved by the exact schema adapter and current registered profile context rather than a modality-wide fixed tuple. An old check MUST NOT be current for another revision/schema/input.

For `text.master.v2`, required current checks SHALL include common Production Core gates plus text structure, fact, identity and platform checks. Discoverability SHALL be required only when an exact published profile resolves.

#### Scenario: Schema-specific checks
- **WHEN** a `text.master.v1` and `text.master.v2` revision exist in the same unit history
- **THEN** each revision uses its own adapter/version/check requirement set and neither reuses the other's incompatible checks

### Requirement: Workflow Draft output can seed Text Master safely

The production core SHALL keep the explicit verified Draft ProjectWorkflowOutput compatibility action. After F6B, new Text seeds SHALL deterministically create `text.master.v2` while preserving exact Draft/Run/node/attempt lineage, provable exact MaterialRevision/Evidence refs and conversion warnings. Historical v1 seed revisions SHALL remain unchanged.

#### Scenario: Seed after F6B
- **WHEN** a valid current Draft workflow output is seeded after F6B
- **THEN** a new v2 structured Text Master is created with truthful workflow provenance and no historical v1 rewrite

### Requirement: Candidate manifest v4 freezes ContentMasterRevision

Manifest v4 SHALL continue to freeze the exact ContentMasterRevision, context, refs, checks, render and provenance. For `text.master.v2`, `content` SHALL freeze the structured v2 payload and `render` SHALL freeze deterministic human-readable Markdown/hash. Candidate/Review/package MUST NOT require editable Markdown to be stored in the v2 payload.

#### Scenario: Freeze v2 Text Candidate
- **WHEN** a current v2 Text Master satisfies exact dynamic checks and render gates
- **THEN** Candidate v4 freezes the structured document plus deterministic render while retaining normal exact-hash Approval/Delivery behavior
