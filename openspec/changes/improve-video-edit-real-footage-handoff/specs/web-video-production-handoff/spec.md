## MODIFIED Requirements

### Requirement: Resolve owns the master edit and After Effects supplies scoped compositions
DaVinci Resolve SHALL own the main timeline, edit, sound assembly, grading and final export for this workflow. After Effects SHALL produce only explicitly requested compositions with declared duration, dimensions, frame rate and alpha requirements, which Resolve consumes as media. No-AE projects SHALL skip that branch. The edit manifest SHALL identify actual source use ranges and narration timing, and generated-clip audio SHALL follow the frozen keep/mute intent. A shot MAY map to several exact source cuts: each manifest timeline item SHALL name the shot, a MaterialRevision that is either the shot source or a Master timeline media placement inside that shot's time span, source in/out within that placement, and the composition role when the shot has one. Every shot SHALL still have at least one item, and existing single-source manifests SHALL remain valid. The workflow MUST NOT force every source clip to ten seconds or modify unrelated application projects/global settings.

#### Scenario: A shot requires an animated explanatory overlay
- **WHEN** the frozen director instructions request one AE composition
- **THEN** Codex produces that composition and its required intermediate media, incorporates it into the Resolve main timeline, and records the exact source and composition lineage

#### Scenario: The video needs only straightforward cuts
- **WHEN** no AE work is requested
- **THEN** Resolve completes the edit without an artificial AE dependency

#### Scenario: One shot is cut from several real clips
- **WHEN** a Master shot spans three placed footage cuts from two MaterialRevisions
- **THEN** the manifest records three items for that shot with their exact revisions and in/out ranges and validation accepts them

#### Scenario: A manifest cites material not placed in the shot
- **WHEN** a manifest item for a shot names a MaterialRevision that has no placement inside that shot's span
- **THEN** validation rejects the manifest

## ADDED Requirements

### Requirement: Execution inputs are linked store files, not copies
Input materialization SHALL expose each authorized MaterialRevision in the execution `inputs/` folder as a read-only copy-on-write clone of its content-addressed stored file (sharing the stored blocks without duplicating bytes, while writes to the input can never change the library file), named `{revision}-{hash}.{ext}` with the extension of its verified media type, and SHALL verify the hash after linking. When cloning is impossible (for example a filesystem without clone support) it SHALL fall back to the existing bounded copy and record that fallback and its reason in the execution. Executors SHALL reference these inputs directly from professional projects instead of making working copies. Manifests SHALL accept both the extension path and the legacy `.bin` path. Existing transfer bounds and rights checks SHALL be unchanged.

#### Scenario: Footage is materialized on the same volume
- **WHEN** an execution materializes a 27 MiB video revision stored locally
- **THEN** `inputs/` contains a read-only clone with the real extension whose hash matches, and no second copy of the bytes is written

#### Scenario: Cloning is not possible
- **WHEN** the store filesystem does not support clones
- **THEN** the input is copied within the existing bounds and the execution records `copy` with the reason

### Requirement: Edit outputs report loudness and true peak
Validation of rough-cut and final MP4 outputs SHALL measure integrated loudness (EBU R128) and true peak and store them with the output. A true peak above −1 dBTP or loudness outside the configured window SHALL be shown as a warning at human review; it SHALL NOT automatically reject or alter the output.

#### Scenario: A mix clips after gain
- **WHEN** a submitted rough cut measures +2.2 dBTP
- **THEN** the output is staged with the measurement and a clipping warning visible to the reviewer
