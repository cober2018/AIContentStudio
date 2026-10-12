## Context

The current product has the right durable objects but an incomplete control loop.

At the code level:

- Workflow Definition already stores node kind/plugin/version/config, input/output mapping, condition, failure policy, dependency graph and visual order.
- Production currently hides `WorkflowMiniCanvas` + `NodeInspector` under “Advanced Automation.”
- NodeInspector can edit raw config, mappings, conditions, model profile, media prompt and skill references.
- Project Workflow Override and Persona × Modality default workflow versions already exist.
- WorkflowRun freezes definition checksum; WorkflowStepAttempt freezes status/output/input/output hashes, but not the exact resolved configuration/prompt receipt needed for meaningful iterative tuning.
- `builtin.generate` still routes through the legacy Topic/Draft generation path and does not make every current NodeInspector prompt/config field authoritative.
- Content Master is a separate modern truth and only the legacy Draft→Master seed path bridges Workflow output into Master.
- ProviderGenerationTask, ChannelVariant, CreativeExecution and Capability Memory each have their own correct truth but are not presented as stages in one creation journey.

The missing product concept is not a second workflow engine. It is a usable control surface over the existing one.

## Goals / Non-Goals

**Goals**

- Make one Content Unit usable from “idea/context → controlled stages → accepted Master/Material/Variant/Execution → Review.”
- Make every visible stage tuning field actually affect execution or be rejected.
- Let users inspect the effective prompt/method/model/input contract before a model/Agent call.
- Let users run and review one stage at a time.
- Make stage outputs proposals until explicit acceptance.
- Preserve exact attempt/config/output provenance.
- Support one-run tuning without immediately changing the saved recipe.
- Let users promote successful tuning to current Project, scoped default Workflow, or Capability Memory.
- Let explicit feedback create improvement candidates without hidden self-modification.
- Keep the raw graph/JSON tools for advanced users.
- Preserve all historical Workflow, Draft, Master, Candidate and delivery records.

**Non-Goals**

- Creating a second Recipe table or replacing Workflow Definition.
- Allowing an Agent to rewrite the workflow graph autonomously.
- Making Capability Memory an executable workflow engine.
- Auto-applying feedback or performance learning to a workflow.
- Letting stage tuning bypass Fact Boundary, rights, Candidate, Approval or Delivery gates.
- Replacing professional editors.
- Removing legacy `builtin.generate` or historical Draft workflows.
- Making every legacy node tunable in the first implementation.

## Decisions

### 1. Creation Recipe is a product projection of Workflow Definition

The term **Creation Recipe** is the user-facing representation of one exact effective Workflow Definition revision.

There is no new Recipe persistence root.

A recipe stage maps to one Workflow node plus its dependencies. Stage order shown to normal users is derived from `visual_order` and dependency data. Advanced mode exposes the same graph/mapping/JSON definition.

A Content Unit continues to pin the existing effective Workflow version. Historical Runs remain pinned to exact Workflow ID/version/checksum.

### 2. Daily UX is Stage-first; graph-first becomes Advanced

Production SHALL show a compact Creation Recipe strip/list before the raw canvas.

Each stage shows:

- purpose/label;
- executor/method summary;
- readiness;
- current/last attempt state;
- whether review is required;
- accepted output/target when any;
- blocker/stale reason;
- whether this Project differs from its scoped default.

Opening a stage shows a **Stage Control Drawer**. Normal controls are typed fields. Raw JSON/mappings/dependencies stay under Advanced.

### 3. A Stage Contract defines what can actually be tuned

Extend node/plugin descriptors with an optional versioned `stage_contract`.

First fields:

- `stage_schema`;
- display category/title;
- `config_schema`;
- `ui_schema`;
- `tunable_fields`;
- `input_contract`;
- `output_contract`;
- supported method sources (`builtin`, Capability Memory, Installed Skill, model route, Creative Execution);
- `supports_preview`;
- `supports_run_override`;
- `supports_candidates`;
- `requires_human_acceptance`.

The backend remains authoritative. A field may appear in the normal Stage Drawer only if it is declared tunable and the executor consumes it.

Unknown or unsupported config SHALL fail validation. “UI-only prompt controls” are forbidden.

Legacy node plugins without a Stage Contract remain available in Advanced/compatibility view and continue current semantics.

### 4. Effective Stage Resolver is the one configuration truth at execution time

For a stage-contract node, server resolution produces a canonical `ResolvedStageExecution` from:

1. exact Workflow definition/node/plugin version;
2. saved node config;
3. optional one-run/one-attempt override restricted to declared tunable fields;
4. exact selected Capability Memory revision or Installed Skill descriptor when explicitly selected;
5. exact model profile/provider/model route;
6. current Run-pinned IdentitySnapshot;
7. current/frozen Brief and Fact Boundary context required by the stage;
8. current Creative Intent;
9. declared upstream stage outputs;
10. explicit current-task instruction.

It returns:

- effective config;
- source layers and exact IDs/hashes;
- model/executor identity;
- method/skill identity;
- prompt sections and bounded preview;
- effective prompt hash;
- effective config hash;
- exact upstream input hashes;
- output contract;
- safety/readiness blockers;
- `resolution_hash`.

The preview endpoint is pure: no LLM, Provider, Agent, Connector, professional-tool or publication call.

Actual execution MUST resolve the same contract and either use exactly the same hashes or fail with a stale/config conflict.

### 5. Prompt composition is visible and layered

AI stages SHALL expose the effective instruction in understandable layers rather than one hidden prompt blob:

- method/base instruction;
- Identity/Persona guidance;
- stage instruction;
- Project Brief;
- Creative Intent;
- evidence/fact constraints;
- selected upstream output;
- current task override.

The preview can show bounded business content required to understand the request, but SHALL NOT expose secrets or raw provider credentials.

The execution receipt records exact layer hashes and the effective prompt hash. Where an LLMRun exists, its input hash/model/prompt version SHALL bind to the same resolution.

### 6. Run-only overrides are explicit and non-authoritative

A user MAY temporarily tune declared fields for one stage run/rerun without changing the saved Workflow Definition.

Examples:

- stage instruction;
- model profile;
- candidate count;
- length/temperature when supported;
- selected saved method revision;
- generation dimensions/duration;
- optional stage-specific style controls.

Overrides MUST NOT change:

- plugin identity/version;
- dependency graph;
- input/output mappings outside declared tuning;
- Fact Boundary;
- rights;
- approval/publication gates;
- side-effect classification.

A run-only override is frozen into the exact attempt receipt. It disappears from future Runs unless explicitly promoted.

### 7. WorkflowStepAttempt becomes the exact historical execution unit

Add nullable bounded `input_snapshot_json` and `execution_receipt_json` to WorkflowStepAttempt.

For stage-contract attempts the receipt freezes:

- Workflow ID/version/checksum;
- node ID/plugin/version;
- base config hash;
- run/attempt override;
- effective config hash;
- method/capability/skill identity;
- model/provider/profile identity;
- prompt hash/layer hashes;
- upstream input IDs/hashes;
- output contract;
- resolution hash.

`input_snapshot_json` stores the bounded resolved input projection required to reproduce/explain the attempt without depending on the mutable current WorkflowStep row.

Legacy attempts keep both fields null and remain readable.

### 8. New project-native generation does not reuse legacy Draft generation semantics

Do not make `builtin.generate` silently change meaning.

Add project-native stage executor(s) for the modern Master flow. The first required AI content stage is `stage.master.propose@1`.

It SHALL:

- operate on the current Content Unit and optional current Master;
- consume the exact ResolvedStageExecution contract;
- call an explicitly resolved model route;
- record LLMRun;
- produce 1–5 bounded `stage.master.proposal.v1` candidates;
- validate each candidate against the current modality's canonical Master schema;
- inherit/validate exact existing evidence/asset references instead of inventing IDs;
- never save ContentMasterRevision by itself.

Text, Graphic and Video use the same proposal envelope with modality-specific payload validation.

Legacy `builtin.generate` remains Draft-oriented compatibility behavior.

### 9. Stage results are proposals until explicit adoption

A stage-contract attempt MAY return candidate outputs.

Each candidate freezes:

- local candidate ID within the attempt;
- target kind;
- payload/schema;
- canonical candidate hash;
- exact source/current Master revision when applicable;
- exact refs/context used;
- execution receipt reference.

User decisions:

- accept;
- accept with bounded edits;
- reject with reason;
- rerun unchanged;
- rerun with temporary override.

No candidate may directly become a Candidate/Approval/PublishedContent record.

### 10. Master adoption is an explicit trusted bridge

For a `stage.master.proposal.v1` candidate, an authorized user may explicitly adopt one exact current attempt candidate.

The service SHALL:

- require exact Run/StepAttempt/output/candidate hash;
- require the Workflow definition and source context to still be valid or require an explicit rebase/re-run;
- validate the final payload with the same modality adapters used by normal Master save;
- support bounded user edits before adoption;
- create one new ContentMasterRevision through a trusted `workflow_stage` service path;
- freeze run ID, attempt ID/no, node ID, Workflow checksum, resolution/config/prompt hashes, proposal hash, user edit summary and model/method provenance;
- create a ProjectWorkflowOutput `content_master_revision` association after the Master exists;
- never overwrite an older Master.

Acceptance with edits records both proposal hash and accepted Master hash so future tuning can distinguish model output from human correction.

### 11. Native media, Channel Variant and Creative Execution are stage integrations, not duplicate engines

**Native media**

`media.generate` remains ProviderGenerationTask truth. Stage control exposes its declared capability/model/prompt/dimensions/duration inputs. Provider acceptance creates MaterialRevision exactly as today. Stage feedback may record which exact MaterialRevision was selected; binding it into a Master remains an explicit Master save.

**Channel Variant**

A channel-adaptation stage SHALL call existing F6E preview/model-assist/save services. Its result is not a second Variant object. Explicit acceptance creates the normal new ChannelVariantRevision using existing deterministic/model provenance.

**Professional execution**

A professional-execution stage prepares the existing CreativeExecutionPackage / CreativeExecution using current Master/Variant. It does not auto-dispatch a professional tool. Existing MCP/result acceptance remains authoritative. An accepted external MaterialRevision must still be explicitly incorporated into Master/Variant before Candidate freeze.

### 12. Checks and human gates remain stages

Existing FactCheck, content-censor, discoverability and human-confirmation behaviors MAY expose Stage Contracts so their relevant parameters and results are understandable in the same flow.

They do not become generative proposals when their existing business truth is a CheckRun/Review/Fact decision.

A gate stage cannot be disabled through a run-only override when the target Candidate/profile requires it.

### 13. Stage feedback uses ProjectEvent, not a new truth table

Every explicit stage result decision writes an append-only `creation_recipe.stage_feedback.v1` ProjectEvent with:

- project/unit;
- Workflow ID/version/checksum;
- Run;
- node;
- attempt ID/no;
- base/effective config hashes;
- prompt/resolution hash when applicable;
- output/candidate hash;
- decision (`accepted`, `accepted_with_edits`, `rejected`, `rerun_requested`, `skipped_when_allowed`);
- bounded reason tags/note;
- resulting entity type/id/hash when applicable;
- actor/time.

Feedback never changes the Workflow by itself.

### 14. “Save what worked” promotes an exact known change

When a run-only override or accepted-with-edits stage succeeds, the product SHALL offer explicit promotion.

**Save to this Project**

Apply an allowlisted patch to the exact node in the current Workflow draft and save a new Project Workflow Override revision under existing CAS/version rules.

**Save as scoped default**

Apply the same patch to a draft and run the existing portability gate, then save a new Series/Account/Persona × modality default Workflow version. Existing units do not silently rebind.

**Save method**

Capture a Capability Memory `recipe` or `prompt_skill` candidate with exact source feedback/attempt/workflow hashes. Promotion to saved/pinned remains separate.

The system MUST show the patch/diff before any promotion.

### 15. Workflow Improvement Candidates reuse Capability Memory

A Workflow improvement is not a new mutable workflow state.

Use Capability Memory `recipe` content schema `workflow.stage.recipe.v1` for reusable stage patches.

It includes:

- exact source/base Workflow checksum;
- node ID;
- plugin key/version;
- allowlisted config patch;
- optional prompt/method patch;
- applicable stage schema;
- source feedback event IDs/hashes;
- source attempt/config/output/result hashes;
- scope.

A recipe candidate cannot modify graph/dependencies/plugin identity/gates.

Applying it to a Project/default Workflow requires explicit user review and creates a new Workflow revision. It does not mutate the Capability artifact or historical run.

### 16. Deterministic feedback promotion comes before AI tuning

First implementation MUST support deterministic promotion of the exact user override/edit that produced an accepted result.

Only after that is stable MAY the product offer model-assisted tuning suggestions.

A model-assisted tuning preview:

- takes explicitly selected feedback events/attempts;
- operates only on fields declared tunable by the Stage Contract;
- returns a proposed config patch and explanation;
- records a successful exact-input LLMRun;
- creates no Workflow/Capability change until explicit acceptance;
- cannot alter dependencies, plugin identity, evidence/rights, human gates, Candidate/Delivery rules or side-effect policy.

### 17. Recipe version comparison is visible

Production SHALL show:

- current pinned Workflow;
- source scope (Series/Account/Persona/project override);
- Project changes relative to the inherited default;
- per-stage changed fields;
- last accepted attempt and feedback;
- current unsaved tuning.

Users may inspect historical Workflow versions and explicitly restore by creating/rebinding to a new current revision; history is never overwritten.

### 18. End-to-end daily flow

The normal product journey becomes:

`Idea/Source/Opportunity → Project → Brief/Identity/Evidence → choose effective Creation Recipe → configure/preview stage → run → review result → accept/adopt → next stage → Channel Variant / professional execution when needed → Candidate → Review → Delivery → Publication/Learning`

A user does not need to open the raw graph to complete the supported path.

Advanced graph mode remains available for changing dependencies/plugin topology.

### 19. Product truth boundaries remain unchanged

- Workflow Definition = recipe/process truth.
- WorkflowRun/StepAttempt = execution truth.
- ContentMasterRevision = source-content truth.
- MaterialRevision = accepted file truth.
- ChannelVariantRevision = channel-expression truth.
- CreativeExecution = external/professional execution truth.
- CapabilityArtifact = reusable method truth.
- Candidate/Review/Delivery = final decision/delivery truth.
- Performance/Learning = post-publication evidence truth.

No layer silently replaces another.

### 20. Previous align closeout must be made internally consistent first

Before a new migration is applied:

- update the single-machine approved schema/readiness default to the already-enabled `aco000000001`;
- document that `f8a` identity columns exist only as inert nullable Alembic ancestry and do not mean JWT/production identity activation;
- update recovery/parity documents that still say formal DB remains at `f7d`;
- add persistent repository tests for CreativeExecution, MCP, Capability Memory and ACO migration so the previous core does not rely only on temporary acceptance scripts.

Do not rollback the live database to solve the documentation conflict.

## Migration Plan

### Phase 0 — close current lifecycle inconsistency

Correct approved schema/readiness/runbooks and add persistent ACO/core regression tests. No product behavior change.

### Phase 1 — Stage Contract and recipe projection

Extend descriptors, server validation and Production read model. Add stage strip/control drawer using existing Workflow Definition only.

### Phase 2 — effective-stage preview and exact receipts

Implement resolver, pure preview, prompt layers and additive attempt receipt migration on isolated SQLite. No live migration yet.

### Phase 3 — run-only overrides

Allow only Stage Contract tunable fields. Freeze overrides into attempts. Add stage-specific rerun with exact CAS/currentness.

### Phase 4 — project-native Master proposal/adoption

Implement `stage.master.propose@1`, candidate review and explicit Master adoption. Text first, then Graphic/Video canonical payloads before the phase closes.

### Phase 5 — media/check/variant/external stage integrations

Project existing ProviderGenerationTask, checks, ChannelVariant and CreativeExecution into the same stage experience without duplicating truth.

### Phase 6 — feedback and promotion loop

Record ProjectEvent feedback, “Save what worked,” Project/default workflow promotion and Capability Memory recipe/prompt candidate capture.

### Phase 7 — optional tuning suggestions

Only after deterministic promotion is accepted, add bounded model-assisted config-patch preview.

### Phase 8 — complete daily E2E and closeout

Browser-prove Text, Graphic and Video journeys without raw graph use; separately prove Advanced graph still works. Run full backend/frontend/FE-P1/OpenSpec/migration/backup/security review before formal SQLite upgrade, sync/archive or commit.

## Risks / Trade-offs

- **Workflow becomes complex again** → keep Stage-first UI; raw graph stays Advanced.
- **Visible controls that do nothing** → Stage Contract + effective receipt makes that invalid by design.
- **Feedback silently changes defaults** → all promotion is explicit diff + new immutable Workflow revision.
- **Recipe vs Capability Memory duplication** → Workflow owns process; Capability Memory owns reusable method/patch only.
- **Legacy workflow breakage** → legacy plugins without Stage Contract keep current behavior.
- **Prompt leakage** → bounded safe preview; secrets remain excluded; execution receipts store hashes/allowlisted projections.
- **Too many stage-specific executors** → common Stage Contract and proposal/adoption envelope; modality validation remains in existing adapters.
- **Migration lifecycle confusion** → Phase 0 aligns `aco` before any new migration and persistent tests become mandatory.
