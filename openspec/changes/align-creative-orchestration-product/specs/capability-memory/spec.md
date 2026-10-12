## ADDED Requirements

### Requirement: Capability Memory is a separate reusable-method truth

The system SHALL persist versioned CapabilityArtifact roots and append-only revisions for reusable creative/execution methods. Supported first-version kinds SHALL be `prompt_skill`, `recipe`, `creative_pattern`, `preference`, `execution_template`, and `tool`. Capability Memory MUST NOT replace FactPack, Identity, Workflow definition, Channel Registry, ContentMemory or source content.

Installed Agent Skills discovered from configured local skill directories are a separate external inventory, not Capability Memory truth. Version 1 SHALL NOT automatically import, export, install, enable, overwrite or promote installed skills. If both inventories are displayed, each item SHALL expose a distinct `source_kind` and stable identity; equal names SHALL NOT imply equivalence or replacement, and Capability promotion MUST NOT change `skills_enabled`.

#### Scenario: Save a reusable title method
- **WHEN** a user explicitly promotes a successful Persona-scoped title prompt
- **THEN** a CapabilityArtifact revision is created without modifying the Persona or any historical content

#### Scenario: Installed skill is shown beside Capability Memory
- **WHEN** the product lists a locally installed Agent Skill and a CapabilityArtifact with the same display name
- **THEN** both remain separately identified and neither is silently imported, enabled, overwritten or promoted by the other

### Requirement: Candidates are non-authoritative and promotion is explicit

Capability status SHALL be `candidate`, `saved`, `pinned`, `archived`, or `deprecated`. The system MAY capture/deduplicate a candidate from bounded successful/accepted work that supplies reusable content, but a candidate MUST NOT become saved/pinned, broaden scope or influence mandatory execution without explicit authorized human action. When the source is CreativeExecution, capture requires the top-level execution to be fully `accepted` under its frozen required-output contract; acceptance of one output is insufficient.

#### Scenario: One successful external edit
- **WHEN** an Agent supplies a reusable Recipe after a result the user accepts
- **THEN** the system may create a hidden candidate but MUST NOT silently make it a default workflow

#### Scenario: User keeps the method
- **WHEN** the user explicitly promotes the candidate
- **THEN** it becomes saved under the confirmed scope and its captured content hash remains identifiable

### Requirement: Capability revisions are immutable and hash-bound

A CapabilityArtifactRevision SHALL freeze kind, normalized bounded content, argument schema when applicable, content hash, source provenance, actor/time and safe metadata. Editing content or argument schema creates revision N+1; revision N remains readable. Promotion metadata changes MUST NOT silently substitute different captured content.

#### Scenario: Improve a saved prompt
- **WHEN** the user edits a saved prompt skill
- **THEN** a new revision/hash is appended and executions that used the prior revision retain that exact identity

### Requirement: Capability scope prevents preference pollution

Capability scope SHALL be explicit and authorized: `owner`, `persona`, `account`, `series`, `project`, `channel`, or `executor`. Auto-captured candidates default to the narrowest provable source scope. Broadening scope requires explicit confirmation and hierarchy ownership validation. Discovery SHALL return every applicable saved/pinned revision with its exact scope; the system MUST NOT silently merge, override or choose a winner when scopes or artifacts conflict. The caller must explicitly select a revision, and stable ordering is presentation only.

Facts/evidence SHALL never be inferred from capability scope.

#### Scenario: Project-specific editing preference
- **WHEN** a preference is learned from Project A
- **THEN** it is not automatically applied to another Project/Persona until explicitly promoted to a broader applicable scope

### Requirement: Capability content is secret-safe and bounded

Artifact save/import/capture SHALL reject secrets, signed/credential URLs, raw private source dumps, unbounded/non-finite JSON and unsupported executable payloads. First-version `tool` artifacts are definitions rendered to an external Agent; AIContentStudio SHALL NOT execute arbitrary CapabilityArtifact code inside its backend.

The system MUST reject the entire artifact capture/save when artifact content or argument schema contains a secret-like value. Only allowlisted provenance or diagnostic metadata outside the artifact content may be omitted before persistence; capture rejection MUST NOT alter the successful source execution result.

#### Scenario: Candidate contains an API key
- **WHEN** captured reusable content includes a secret-like credential
- **THEN** capability capture/save is rejected without changing the successful source execution result

### Requirement: Discovery and use are exact and observable

Capability search SHALL return applicable saved/pinned revisions with kind, scope, exact revision/hash, provenance and truthful usage metadata. Archived/deprecated/candidate artifacts are excluded from ordinary discovery unless explicitly requested.

`use` SHALL render/return exact stored content with validated bounded arguments and record a CapabilityUse referencing the exact revision. It MUST NOT mutate the artifact.

#### Scenario: Reuse a pinned Director recipe
- **WHEN** Codex requests applicable video execution methods for a Project
- **THEN** the exact pinned/saved recipe revision is returned and its use is recorded without changing the recipe

### Requirement: Usage is evidence, not automatic quality truth

CapabilityUse SHALL record exact artifact revision, actor/project/execution context, rendered-argument hash, use time and optional bounded outcome `used`, `accepted`, `rejected`, or `unknown`. Usage counts or acceptance frequency MAY support ranking/suggestions but MUST NOT auto-promote, rewrite content, change scope or claim objective quality.

#### Scenario: Frequently used method
- **WHEN** a prompt has high use count
- **THEN** the UI may rank it higher but its scope/content/status remain unchanged until explicit edit/promotion

### Requirement: Preference memory is visible and overridable

Saved preference/creative-pattern capabilities MAY be suggested in creation UI with their source scope and rationale. They MUST be visible, removable/archivable and overridable for the current task. Hidden mandatory prompt injection from Capability Memory is forbidden.

#### Scenario: User does not want a usual tone
- **WHEN** a Persona has a saved preference but the current Project explicitly overrides it
- **THEN** the current task uses the explicit Project decision and the stored preference remains historical guidance only

### Requirement: Learning and Capability Memory require a separate bridge

An accepted evidence-backed LearningCandidate MAY be explicitly converted into a new Capability Memory candidate with frozen source candidate/evidence provenance. Learning acceptance alone SHALL NOT create/update a CapabilityArtifact. Capability usage/outcomes SHALL NOT be treated as publication performance without existing PublishedContent/Performance evidence.

#### Scenario: Performance suggests a better hook
- **WHEN** a validated LearningCandidate says a Persona's question-hook pattern appears useful
- **THEN** an authorized user may create a Creative Pattern candidate, then separately promote it after review

### Requirement: Capability history is recoverable and does not rewrite business history

Archiving/deprecating a capability SHALL remove it from ordinary discovery while preserving revisions and references from prior executions/content. Deleting retained referenced revisions is forbidden. Backup/restore includes saved capability history and use evidence.

#### Scenario: Deprecate an old recipe
- **WHEN** the user replaces a recipe with a new revision/artifact
- **THEN** old executions can still identify the exact recipe they used, while new discovery omits the deprecated method
