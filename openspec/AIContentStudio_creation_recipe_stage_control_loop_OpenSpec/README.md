# AIContentStudio Creation Recipe Stage Control Loop — OpenSpec package

This follow-up change addresses the newly identified usability gap: the product has many correct capabilities but lacks a controllable creation loop.

The package makes existing Workflow Definition the user-facing Creation Recipe truth. It does not add a second recipe database.

Core loop:

`Recipe Stage → tune exact details → preview effective AI/Agent request → run → review exact result → adopt into Master/Material/Variant/Execution → record feedback → explicitly save what worked into Project/default Workflow or Capability Memory`

The change is designed against the current local working tree where `align-creative-orchestration-product` has been implemented but not yet canonical-synced/archived/committed.

Before new feature apply, the prior closeout blockers must be fixed:
- current formal DB is already `aco000000001`, so readiness/runbooks must stop claiming `f7d` is current;
- `f8a` identity columns may be documented as inert nullable migration ancestry, not auth activation;
- persistent regression tests must protect CreativeExecution/MCP/CapabilityMemory/ACO.

No live DB rollback is intended.
