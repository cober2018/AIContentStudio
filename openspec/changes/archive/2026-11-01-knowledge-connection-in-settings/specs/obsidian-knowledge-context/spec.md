## ADDED Requirements

### Requirement: The vault connection is set once in Settings

The Obsidian connection (vault root, allowed folders, enabled) SHALL be managed by an admin in Settings → 知识库, not inside a project page. The project Sources and Evidence page SHALL keep search, preview and selection, and SHALL point to Settings when the connection is missing or needs changing.

#### Scenario: Admin sets the vault location
- **WHEN** an admin opens Settings → 知识库
- **THEN** they can view and save the vault root, allowed folders and enabled state with the existing revision check

#### Scenario: Project page without connection controls
- **WHEN** an operator opens a project's Sources and Evidence page
- **THEN** no connection form is shown there, and the page links to Settings → 知识库

### Requirement: The allowed folders limit project knowledge only

The allowed-folder list SHALL limit only project knowledge search, preview and selection. A persona's speech-sample folder MAY be any folder inside the vault root; saving and reading it SHALL still reject paths outside the vault, hidden entries, symlinks and non-Markdown files.

#### Scenario: Persona folder outside the allowed list
- **WHEN** the allowed folders are `knowledge/permanent` and `自媒体/文章` and a persona saves `自媒体/逐字稿/懒羊羊小王`, which exists in the vault
- **THEN** the folder is saved and its notes are read as speech samples

#### Scenario: Persona folder outside the vault
- **WHEN** a persona saves a folder path that escapes the vault root or does not exist
- **THEN** the save is rejected with a plain-language reason
