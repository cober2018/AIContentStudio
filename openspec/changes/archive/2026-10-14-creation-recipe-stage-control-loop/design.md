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

Stage Contract activation is version-pinned, not a registry-wide reinterpretation. A distinct new plugin/version supplies the contract for a newly saved Workflow Definition. Adding stage controls to an existing media/check/human plugin requires a new registered plugin version; already pinned definitions/runs/reruns keep the original version, validation and execution behavior. New definitions pin the exact Stage Contract schema/version with that plugin. Selecting or saving a new Recipe is explicit; opening a historical definition never upgrades it.

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

Every explicit user stage run/rerun request MUST supply the preview's `expected_resolution_hash` and an invocation idempotency key. Resolution identity binds the exact Workflow/node/plugin/Stage Contract, override, selected methods, context and upstream identities, together with the applicable routing-plan hash, adapter version and safe runtime/credential-continuity identity. The server re-resolves before dispatch and returns a conflict without an external call if any bound identity differs; missing preview identity is rejected, not replaced with a fresh hidden preview.

For authorized automatic continuation, the server prepares the successor's pure resolution after the accepted upstream decision commits, then supplies that exact expected hash to the same invocation path. This preparation is recorded/exposed as the automatic request, not falsely described as a user-inspected preview. It uses only the pinned Recipe, allowed saved/run-local tuning and exact accepted inputs; it cannot silently select another method/model or bypass a blocker. Dispatch revalidates that prepared identity and conflicts on drift just as an explicit invocation does.

Before any external invocation, the existing WorkflowStep/Attempt persistence MUST atomically claim that idempotency key and commit the frozen input snapshot/receipt. A serialized current-step claim prevents competing submissions. An identical retry returns or reconciles the original claimed attempt; the same key with another request fingerprint conflicts. Confirmed pre-dispatch failures remain distinct from possible-dispatch/unknown outcomes. A timeout, response loss or abandoned claim after possible dispatch MUST NOT create another invocation; explicit original-attempt reconciliation is required. No separate invocation truth table is introduced.

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

The receipt also freezes the invocation key/request fingerprint, expected preview hash and applicable routing-plan/adapter/runtime identities. It and the input snapshot are immutable from the pre-dispatch claim. That claimed attempt may finalize its outcome/output once, retaining unsuccessful or unresolved dispatch evidence; a later retry/rerun cannot rewrite a sealed historical output or receipt. Legacy terminal-attempt recording semantics remain unchanged.

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

Execution outcome and review readiness are separate: a successful proposal attempt means proposals exist, not that they are accepted content. If the Stage Contract requires human acceptance, the Step/Run remains waiting for the required decision and cannot report overall completion merely because model execution succeeded. A dependent input declared as accepted content resolves only the exact accepted entity/revision/hash and its decision/output association; it MUST NOT read raw proposal data solely because an attempt is `succeeded`. Inputs explicitly declared as proposal data are distinguishable and do not acquire accepted-content authority.

Acceptance-with-edits publishes the accepted canonical payload/entity hash as the downstream input identity. The existing downstream stale mechanism compares those consumed identities, not only the original proposal hash. Changed accepted input invalidates affected checks/results; unresolved/rejected required review never releases a downstream accepted-content dependency.

The user confirmed **automatic execution of the next eligible stage after acceptance** on 2026-10-05. Acceptance commits first; the existing Workflow runtime then continues dependency-ready stages in deterministic visual-order tie-break order until another required human review, failure, stale/unknown/unavailable blocker or prohibited side effect stops it. The continuation may generate proposals or perform allowed checks, but cannot implicitly adopt the next proposal, bind media into Master, dispatch professional tools, freeze/approve a Candidate or publish. An acceptance replay/recovery resumes the same Run/Step invocation claims and must not duplicate external calls or write another accepted revision. Historical non-stage workflows retain their old semantics.

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

Adoption has one trusted transaction owner. It performs current Unit/Run/Attempt and relevant context-head/current Master CAS revalidation at the commit boundary, then commits the new Master plus refs, mandatory accepted-output association and acceptance feedback together. No internal domain save may commit those pieces independently on this path; existing standalone save endpoints keep their behavior. Any validation, race or association/feedback failure rolls the whole adoption back. The same atomic decision rule applies when a Stage owns acceptance of a Variant or Material through its existing service; merely projecting a previously accepted result does not accept it again.

An adoption idempotency key binds the exact proposal/receipt/output identities, canonical final edited payload/refs, decision and expected revision/context. After authorization, an identical committed retry returns the original revision, output association and feedback before attempting fresh currentness checks, even though that first adoption advanced the Master head. A reused key with a different fingerprint conflicts; an uncommitted adoption must still satisfy all currentness/CAS/live gates. Concurrent duplicate requests create only one accepted revision/decision.

The association uses a dedicated trusted adoption path: validate the original immutable proposal attempt/receipt against the accepted Master provenance and exact acceptance decision, then attach that accepted entity. The legacy `associate_step_output()` path expects an entity ID already present in the produced output and is not the adoption proof. Neither Step proposal output nor Attempt output/hash/receipt may be rewritten to insert the later Master ID. Raw proposals and unrelated entities never qualify.

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

When an accepted result has an actual explicit run-only tunable-field change, the product SHALL offer promotion of that exact base-to-effective config diff. Content edits are not config edits: accepting an edited sentence/document by itself supplies feedback evidence but no deterministic Workflow patch. With no explicit tunable-field diff, the user must first author/select an allowed instruction or method change and review its diff; the system MUST NOT infer a prompt/config patch from content corrections or promote a fabricated/empty change.

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

First implementation MUST support deterministic promotion of the exact explicit tunable-field override that produced an accepted result. Accepted-with-edits content retains proposal/final hashes as evidence but cannot by itself become an inferred Stage config patch. An explicitly user-authored instruction/method change is a separate allowlisted diff, not an automatic translation of those content edits.

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

The current workspace has already completed the prior R1/R2 corrections. Phase 0 inherits and verifies that evidence rather than repeating the implementation:

- approved schema/readiness/runbooks already use the enabled `aco000000001`;
- `f8a` identity columns are documented as inert nullable ancestry, not JWT/production identity activation;
- four permanent CreativeExecution/MCP/Capability Memory/ACO regression files retain 108 cases; the previously recorded full backend result is inherited evidence, not a fresh run of this change;
- the prior align change's separate task 15.7 final closeout review remains open until actually reviewed; this change does not silently close, archive or commit it.

Before new business implementation, confirm these corrections remain present and run the planned fresh baseline gates. Do not roll back or re-migrate the live database, re-enable authentication or add duplicate ACO regression files to mark Phase 0 complete.

## Migration Plan

### Phase 0 — close current lifecycle inconsistency

Verify/inherit the completed schema/readiness/runbook and 108 permanent regression corrections; preserve the independent prior 15.7 closeout gate. Run fresh baseline checks without repeating business changes or touching formal SQLite/runtime.

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

## 2026-10-14 独立生命周期与持久覆盖

用户明确补齐19.4持久测试并独立收尾Recipe/Persona，不顺带关闭align15.7。核心ACO/Recipe代码已在main，当前Recipe九delta全ADDED且与Persona新增requirement名无重叠，故可只同步本change增量并保全align原文/任务；不把新增capability-memory中Recipe职责当align整体完成。19.4复用已存核心Contract/Resolver/claim/Master覆盖，补反馈/保存调整/方法/调优及领域wrapper/stale保全。新增持久测试发现非法feedbackID先set导致500；只交换类型校验与去重顺序。本批无新产品状态表、依赖、生产数据迁移或公开发布。

### 合法版本合同的有界冻结深度

已提交多平台Descriptor的nested字段，在Recipe冻结envelope内合法达到深度13，旧12误拒正常Variant。收尾兼容修复把Stage JSON深度上限保留为有界16，17层拒绝；128KiB与集合数/类型/秘密字段限制不变。仅纳入必要depth常量hunk，未更改已确认Text/Graphic/Video模型响应形状或复制相邻验证诊断工具。
