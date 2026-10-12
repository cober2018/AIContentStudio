## ADDED Requirements

### Requirement: Post-enable local schema truth and regressions remain durable

After separately authorized formal enablement, the approved single-machine schema/readiness default SHALL be `aco000000001`. The `f8a000000001` nullable identity columns in its ancestry SHALL NOT imply JWT activation or identity acceptance; existing local Header identity remains unchanged, and current formal issuer/subject values remain null/inert. Previous `f7d000000001` acceptance SHALL remain identifiable as historical evidence. Documentation correction MUST NOT downgrade or roll back the formal database. Repository regression tests SHALL protect execution stale/Unknown/replacement/derived-rights, MCP authorization/tool restrictions, Capability lifecycle/scope/secret/installed-inventory separation and ACO migration/downgrade/inert-identity invariants using isolated test storage only.

#### Scenario: Formal enablement has already advanced the schema
- **WHEN** the operator has separately enabled the local database at `aco000000001` through `f8a000000001`
- **THEN** code readiness defaults and recovery/current-state documentation identify `aco000000001`, preserve earlier acceptance as historical, and do not enable JWT or roll back live data

#### Scenario: Future ordinary test run protects the new domains
- **WHEN** the repository backend regression suite runs after closeout
- **THEN** persistent isolated tests exercise the execution, MCP, Capability Memory and ACO safety contracts without provider calls or formal database writes

### Requirement: Creative intent is versioned with content truth

ContentMasterRevision and ChannelVariantRevision SHALL support an optional bounded versioned creative-intent projection with a server-derived hash. Creative intent SHALL describe objective, audience, must-keep/must-avoid boundaries, creative freedom and stable-ID rationale without copying FactPack truth, Identity profiles, full source bodies, secrets or raw provider output. Changing intent MUST create a new normal Master/Variant revision; historical rows without intent remain valid and MUST NOT be backfilled with invented rationale.

#### Scenario: Explain why a scene must remain
- **WHEN** an editor saves a current Video Master with a must-keep rationale for a stable shot/scene ID
- **THEN** the new Master revision freezes the canonical creative-intent hash and prior revisions remain unchanged

#### Scenario: Historical content has no recorded intent
- **WHEN** an old Master/Variant predates creative intent
- **THEN** it remains readable with intent reported absent/unknown rather than inferred from content

### Requirement: Creative Execution Package is immutable and exact-source-bound

The system SHALL create immutable `CreativeExecutionPackage` rows from exactly one authorized current ContentMasterRevision or ChannelVariantRevision. A package SHALL freeze source identity/hash/context/creative-intent hash, exact eligible asset/evidence refs, target medium/channel/form when applicable, requirements, output contract, acceptance criteria, package schema/version and server-derived package hash. Each output-contract role SHALL define `role_id`, `kind`, `required`, allowed MIME types, minimum/maximum count and maximum bytes. `required=true` SHALL have `min_count >= 1`; `required=false` SHALL have `min_count=0`; and `max_count >= min_count`. Creating a package MUST NOT call an executor, approve content, authorize delivery or mutate the source.

#### Scenario: Build package from a channel variant
- **WHEN** an editor prepares professional execution for one current Xiaohongshu Variant
- **THEN** the package freezes that exact Variant/Master/evidence/assets and no sibling Variant or Master revision changes

#### Scenario: Source advances after package creation
- **WHEN** the Master or Variant advances later
- **THEN** the old package remains readable for inspection/comparison but cannot be claimed or started for side-effecting execution; a new package is required

### Requirement: Director Package is the first specialized execution schema

`director.video.v1` SHALL describe script/scenes/shots, voice/narration intent, subtitle/overlay intent, B-roll requirements, selected exact assets, pacing/transition intention, target duration/aspect ratio, creative constraints and output acceptance criteria. Existing Video v2 timeline/render data MAY be included as advanced guidance but SHALL NOT require AIContentStudio to implement professional NLE semantics.

A Director Package MAY be prepared from a current internally valid Video Master before a final render is bound. Existing F6D render/Candidate gates remain authoritative for later Candidate freeze.

#### Scenario: Prepare a director package before final edit
- **WHEN** a current Video Master has valid script/shot/context/assets but no final MP4 render
- **THEN** the system may create a Director Package that truthfully requires a final render result and does not claim Candidate readiness

### Requirement: Native generation and professional execution remain distinct

Existing ProviderGenerationTask SHALL remain the source of truth for native model image/video/TTS generation. CreativeExecution SHALL represent package-driven external/professional work and MUST NOT replace, backfill or reinterpret ProviderGenerationTask history. UI MAY show both in a shared creation/execution projection. Both paths may produce accepted MaterialRevision only through their own explicit acceptance contracts.

#### Scenario: Generate a simple image inside Studio
- **WHEN** a user uses the existing native image generation path
- **THEN** ProviderGenerationTask continues to own the send/result/acceptance lifecycle and no CreativeExecution is fabricated

#### Scenario: Request professional image refinement
- **WHEN** a user prepares an exact package for an external Agent
- **THEN** CreativeExecution owns that task and the system does not pretend it was a ProviderGenerationTask

### Requirement: Creative Execution is idempotent and side-effect-aware

CreativeExecution SHALL use an owner-scoped idempotency key/request fingerprint and explicit states `prepared`, `claimed`, `in_progress`, `failed_before_dispatch`, `blocked`, `unknown`, `result_ready`, `accepted`, `rejected`, `cancelled`, `superseded`. Identical retries return the same execution; changed intent under the same key returns 409. Archived Project/Unit rejects new execution.

A failure that proves no external dispatch occurred MUST become terminal `failed_before_dispatch`; retry creates a new execution with a new idempotency key and an explicit link to the failed execution, which remains immutable. A possible-dispatch failure MUST become `unknown` rather than auto-retry. Unknown execution requires explicit observation/reconciliation before another side-effecting attempt.

Only a current package built from the current Master/Variant may be claimed or started for side-effecting execution. Stale or historical packages remain readable for inspection and comparison only; re-execution requires a new current package.

#### Scenario: Transport fails after Agent may have edited a project
- **WHEN** dispatch certainty is lost after execution was claimed
- **THEN** the execution becomes unknown and no automatic resend/restart occurs

#### Scenario: Failure is proven before dispatch
- **WHEN** validation or local preparation fails before any external dispatch can occur
- **THEN** the execution becomes terminal `failed_before_dispatch`, and a retry creates a new linked execution instead of rewriting the failed record

#### Scenario: Stale package is inspected
- **WHEN** a user opens a package whose source Master/Variant has advanced
- **THEN** the package remains readable for comparison but cannot be claimed or started for side-effecting execution

### Requirement: Execution workspaces expose only exact package files

Each execution SHALL use a private local work root. The system SHALL materialize only package-authorized exact MaterialRevision inputs after live scope/hash/rights/model-use checks. Output submission SHALL accept only bounded regular files rooted inside that execution workspace and SHALL reject traversal, symlink escape, devices, unlisted inputs or unexpected size/MIME.

The work root is transport state, not business truth.

#### Scenario: Agent requests another local file
- **WHEN** an MCP client attempts to read or submit a path outside the execution work root
- **THEN** the request is rejected without disclosing filesystem metadata or importing bytes

### Requirement: External outputs remain staged until explicit acceptance

CreativeExecutionOutput SHALL freeze output role/kind, positive `output_index`, monotonic `attempt_no`, staged byte hash/MIME/size and safe executor provenance before acceptance. A role MAY have multiple immutable output rows. A replacement for a rejected output reuses its `output_index` with a higher `attempt_no`; the old row is never overwritten. A staged output SHALL satisfy its matching frozen output-contract role. `result_ready` means every required role has valid staged output for at least `min_count` distinct indexes and no role exceeds `max_count`; all outputs are inspectable. Missing required roles keep the execution in progress or blocked.

An authorized human SHALL explicitly accept each eligible output with a rights/license decision. Acceptance rehashes bytes and creates one immutable MaterialRevision linked to the execution/package/output. The accepted output MUST NOT claim public/model/commercial rights broader than every exact MaterialRevision input materialized for the execution, and inherited attribution/license obligations MUST remain present. Revoked or unprovable input rights block escalation; the result may remain restricted/unknown only when the stored rights say so. `CreativeExecution.accepted` SHALL be set only after every required role has accepted output for at least `min_count` distinct indexes; optional outputs do not block acceptance. A required rejection moves the execution to `blocked` with reason `needs_output_replacement` and permits a higher-attempt replacement in the same execution; it does not enter terminal `rejected` unless the user explicitly rejects the whole execution. A missing required role prevents `accepted`. Terminal `accepted/rejected/cancelled/superseded` executions accept no new outputs. It MAY explicitly create ProjectMaterialReference. It MUST NOT mutate Master/Variant, freeze/approve Candidate, authorize DeliveryTarget or create PublishedContentRecord.

#### Scenario: Agent returns a final MP4
- **WHEN** the file passes staging validation
- **THEN** execution becomes result_ready but the current Video Master and Candidate state do not change

#### Scenario: Human accepts the MP4
- **WHEN** the user accepts exact staged bytes and records the permitted rights decision
- **THEN** a MaterialRevision is created; binding it as the current final render still requires a separate Video Master save

#### Scenario: Required output is missing
- **WHEN** a package requires both a final MP4 and subtitles but only the MP4 is staged
- **THEN** the execution does not become `result_ready` or `accepted`, and the missing subtitle role remains visible

#### Scenario: Derived output cannot escalate rights
- **WHEN** an external Agent receives an input MaterialRevision without public-use permission and returns a derived PNG
- **THEN** accepting the PNG cannot set public-use permission to true or remove inherited attribution/license obligations; revoked or unprovable input rights block the escalation

#### Scenario: All required outputs are accepted
- **WHEN** every required output role in the frozen contract has an individually accepted output and optional roles are absent
- **THEN** the execution may become `accepted` without requiring optional outputs

#### Scenario: One role requires multiple outputs
- **WHEN** a required `broll_images` role has `min_count=3` and `max_count=5`
- **THEN** at least three distinct valid output indexes are staged before `result_ready`, and at least three distinct accepted indexes are required for `accepted`

#### Scenario: Required output is replaced after rejection
- **WHEN** a required subtitle output at `output_index=1` is rejected
- **THEN** the execution becomes `blocked` with reason `needs_output_replacement`, the rejected row remains immutable, and a later `attempt_no` for the same index may restore the role before the execution returns to `result_ready`

#### Scenario: Whole execution is explicitly rejected
- **WHEN** the user rejects the entire execution rather than one output
- **THEN** the execution becomes terminal `rejected` and no further output submissions are accepted

### Requirement: Professional project files are not unsafe path truth

First-version execution MAY accept a professional project file as an ordinary bounded file output and MaterialRevision (typically non-public `other`/project-file media kind) when bytes can be materialized. If only an external project reference can be recorded, it SHALL remain bounded execution metadata and MUST NOT be treated as immutable media, publication evidence or a general filesystem pointer.

#### Scenario: Premiere project is returned
- **WHEN** an Agent can provide the project file bytes
- **THEN** the file may be accepted into the local material library with external-execution provenance and public-use disabled by default

### Requirement: Checkpoint and recovery are declared executor capabilities

Executor descriptors SHALL declare checkpoint/revert/recover support. An execution MAY store a bounded checkpoint reference and recovery metadata bound to exact package/executor state. AIContentStudio MUST NOT claim an external checkpoint or revert succeeded without executor/Agent readback evidence.

`failed_before_dispatch`, `blocked` and `unknown` SHALL remain distinct. `failed_before_dispatch` is terminal and proves no external dispatch occurred; retry creates a new linked execution instead of rewriting history. Unknown recovery/revert/continue requires an explicit observation and reconciliation action.

#### Scenario: Revert after failed After Effects edit
- **WHEN** an external Agent reports a checkpoint, a possible edit failure and a later verified revert/readback
- **THEN** AIContentStudio records those facts without claiming it directly controlled AE or automatically re-running the edit

### Requirement: AIContentStudio exposes a loopback MCP handoff

The current same-machine API SHALL expose a loopback-only MCP interface authenticated by a dedicated ignored-runtime bearer secret bound to one explicit existing local owner user. The MCP server SHALL reuse existing project authorization/domain services and MUST NOT use the Settings external-MCP registry as a second source of truth.

MCP reads SHALL be bounded and side-effect free. MCP write tools SHALL be limited to CreativeExecution lifecycle/input materialization/output submission/reconciliation/human-review requests. They MUST NOT directly save Master/Variant payloads, approve Candidate, authorize/publish Delivery, read arbitrary filesystem paths or execute SQL.

#### Scenario: Codex reads an execution package
- **WHEN** the local authenticated MCP client requests one owned prepared execution
- **THEN** it receives the bounded exact package/context and no unrelated project, secret or arbitrary local file data

#### Scenario: MCP client attempts approval
- **WHEN** a client attempts to turn result_ready directly into approved/published content
- **THEN** no such MCP tool exists and the normal human Review/Delivery gates remain required

### Requirement: MCP correlation and redaction match local production safety

MCP calls SHALL carry trace correlation, stable safe errors, bounded response sizes and allowlisted metadata. Tokens, provider secrets, raw errors and credential URLs MUST NOT appear in MCP responses, AuditLog or ProjectEvent. Listing resources/tools MUST NOT probe providers or dispatch professional tools.

#### Scenario: External tool reports a token-bearing error
- **WHEN** an Agent includes sensitive diagnostic text
- **THEN** only a bounded safe category/summary is persisted or returned

### Requirement: Creative Execution is not publication

Prepared, claimed, result_ready or accepted external execution SHALL NOT create or imply DeliveryReceipt, PublishedContentRecord, PerformanceObservation or LearningCandidate. Publication semantics remain governed by existing Delivery/Receipt contracts.

#### Scenario: Local professional edit completed
- **WHEN** a final video is accepted into MaterialRevision
- **THEN** the product may proceed to a new Master/Candidate/Review but publication/performance remain absent until their existing gates occur
