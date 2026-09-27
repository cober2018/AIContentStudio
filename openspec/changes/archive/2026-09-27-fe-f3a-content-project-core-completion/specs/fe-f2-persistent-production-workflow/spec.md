## MODIFIED Requirements

### Requirement: Project-shared workflow outputs

The system SHALL persist references to supported workflow-produced Draft, MaterialRevision, and Candidate outputs with owning project, unit, run, node, attempt, and applicable source/rights provenance. Generated image, chart, screenshot, and video-clip revisions SHALL appear in the owning project's Shared Assets. FE-F3A MAY add explicit project MaterialRevision references for project upload/system-library use, but those references SHALL remain a separate persistence source from ProjectWorkflowOutput. The project Shared Assets API SHALL unify both sources at read time and MUST NOT create a synthetic material, duplicate bytes, or infer an asset merely because a node reports success.

#### Scenario: Workflow material and explicit material coexist
- **WHEN** a project has both explicit MaterialRevision references and a verified workflow-generated MaterialRevision
- **THEN** the Shared Assets response includes both with distinct source types and preserves the workflow item's run/node/attempt provenance

#### Scenario: Explicit detach does not erase workflow history
- **WHEN** an editor detaches an explicit project material reference
- **THEN** any separate ProjectWorkflowOutput association to the same MaterialRevision remains intact and historical runs are not modified
