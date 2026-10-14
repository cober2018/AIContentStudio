# creation-recipe-stage-control-loop Specification

## Purpose
Keep account-aware Variant Stage adaptation aligned with the existing production contract and authoritative Workflow state.
## Requirements
### Requirement: Exact account-aware stage adaptation without new Workflow truth

The existing Workflow and `stage.variant.adapt@1` SHALL remain the only process and modern channel-adaptation plugin truths, and SHALL accept a resolved target context including exact Account/form/Series binding when applicable.

#### Scenario: One accepted source reaches multiple account targets
- **WHEN** an accepted Master is chosen for several valid Series targets
- **THEN** each needed Variant adaptation is resolved using an exact target account identity and applicable style/rights context
- **AND** each execution records its pinned resolution, method, prompt and output hashes

#### Scenario: No invented variant plugin
- **WHEN** the implementation registers or calls a channel Variant Stage
- **THEN** it reuses `stage.variant.adapt@1`
- **AND** no `stage.variant.propose` or duplicate Recipe/Variant truth is introduced
