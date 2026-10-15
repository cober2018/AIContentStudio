# obsidian-knowledge-context Specification

## Purpose
TBD - created by archiving change add-obsidian-knowledge-context. Update Purpose after archive.
## Requirements
### Requirement: A configured Obsidian vault is accessible through bounded read-only search
The system SHALL expose configured local Obsidian Markdown search and preview in the existing project Sources and Evidence page. A connection SHALL restrict access to an explicitly configured vault and folder scope, resolve real paths inside that scope, and exclude configuration, hidden and non-Markdown files. It MUST NOT write, delete or rename vault files or execute note content.

#### Scenario: Search saved knowledge notes
- **WHEN** an authorized project operator searches within a configured vault scope
- **THEN** the page shows bounded matching note titles, relative paths and snippets and allows explicit preview of saved Markdown

#### Scenario: A requested note is unavailable or outside scope
- **WHEN** a note cannot be read from disk or its resolved path is outside the configured scope
- **THEN** the system returns an explicit unavailable or denied result without substituting empty content or reading another file

### Requirement: Selected notes have explicit content or style purpose
The user SHALL explicitly select notes or excerpts for professional content reference, personal writing-style reference, or both, with a project and intended Persona or unit scope. Unselected notes MUST NOT be automatically imported or sent to a generation model. Model-use permission SHALL be explicit and default to false.

#### Scenario: A user selects previous personal writing as a style sample
- **WHEN** a user selects an earlier article as a style sample and allows model use
- **THEN** the project records the exact note version and purpose and can use it as reference prose without adding its assertions to the Fact Boundary

### Requirement: Vault selections are versioned and preserve source provenance
Explicitly accepted selections SHALL reuse SourceDocument as the content truth and persist exact source IDs, content checksums, note locators, selected excerpts, use purposes and authorizations in a versioned project knowledge context. Vault edits SHALL require explicit refresh and a new context revision and MUST NOT silently mutate previous source snapshots, accepted manuscripts or run inputs.

#### Scenario: A selected note changes after manuscript generation
- **WHEN** the original Vault file is edited after a run has fixed its knowledge context
- **THEN** that run retains its earlier input version and the user can explicitly select the updated version for a later run

### Requirement: Knowledge and writing style remain distinct from verified facts
Knowledge references SHALL provide background or writing examples without granting factual confirmation, public rights or publication authority. Facts used as evidence SHALL retain existing confirmation, model-use and public-use permissions and frozen FactPack/Project Fact Boundary requirements. Existing no-knowledge projects SHALL retain their prior behavior.

#### Scenario: An old opinion note contains an unverified numeric assertion
- **WHEN** that note is selected for professional context or writing style
- **THEN** the assertion is not automatically treated as a verified fact or a permitted evidence citation

### Requirement: Normal manuscript stages use inspectable selected knowledge
The actual-request preview and relevant manuscript generation, refinement and finalization stages SHALL include the selected professional references and style samples with exact version provenance and visible excerpt limits. Knowledge content SHALL be treated as reference data rather than privileged instructions. The run SHALL freeze its selected input and MUST NOT fetch unrelated Vault notes during later stages without a new explicit selection.

#### Scenario: Produce a manuscript in the selected personal style
- **WHEN** a user prepares a topic with authorized professional references and personal writing samples
- **THEN** the normal stage preview shows those exact selections and the generated manuscript can be reviewed for professional grounding and style correspondence before explicit adoption

### Requirement: Acceptance proves the product workflow rather than tool installation
Completion SHALL include normal-page connection, search, preview, explicit purpose and model-use selection, saved context reload, actual input inspection and delegated creative-quality review for both existing Personas. Installing an MCP server, discovering a vault, or passing structural checks alone MUST NOT be reported as successful manuscript integration.

#### Scenario: A connector is available but no notes reach the model
- **WHEN** connectivity succeeds while the normal creation request lacks the chosen knowledge context
- **THEN** the feature remains incomplete and cannot be accepted as working Obsidian-assisted creation
