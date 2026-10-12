## ADDED Requirements

### Requirement: Creation Recipe is the normal Production control surface

A user continuing a Project SHALL be able to understand and control the next creation stage without opening raw workflow JSON/canvas. Production SHALL expose the effective recipe, next actionable stage, current content/result and blockers, while Advanced mode preserves full graph editing.

#### Scenario: Continue active Project
- **WHEN** Home/Project opens a unit with an incomplete recipe
- **THEN** the user can jump to the exact next actionable stage and inspect/tune it

### Requirement: Stage tuning has explicit save scopes

The UI SHALL distinguish:
- this run only;
- save to this Project recipe;
- save as scoped default;
- save as reusable method.

It MUST explain which future work will be affected before the user confirms.

#### Scenario: Temporary experiment
- **WHEN** the user selects “仅本次”
- **THEN** no Workflow/Capability/default revision is created even if the result is later accepted
