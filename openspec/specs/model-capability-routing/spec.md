# model-capability-routing Specification

## Purpose

Provide deterministic capability-aware model and plugin routing from existing configuration, with durable one-send generation tasks, exact accepted media provenance, explicit human acceptance and truthful unavailable states across Workflow and Production.

Current acceptance scope, explicitly revised by the user on 2026-10-03: MiniMax video generation and original H3 download are excluded for the current account/package, not verified and not a F7 acceptance blocker. No further MiniMax video submission/query or replacement-provider generation is authorized by this scope. Preserve existing generic video contracts, immutable history and offline safety regression. In-scope MiniMax validation focuses on TTS, ASR and validated extraction of an existing video's audio for ASR; it does not imply video generation or visual understanding. This scope record does not mutate saved configuration, remove generic adapters or infer a vendor-wide lack of video capability.
## Requirements
### Requirement: Model capability declarations are explicit and truthful
The system SHALL support admin-edited chat, image_generation, video_generation, tts and asr declarations independently of adapter support, connection configuration and real verification. Understanding media MUST NOT imply generation.

#### Scenario: Declare image generation without an adapter
- **WHEN** an admin marks a model as supporting images but no supported configured binding exists
- **THEN** Settings shows the declaration and an unavailable reason, and execution/verification is not fabricated

### Requirement: Configuration reuses existing truth with concurrency protection
Profiles, capability bindings, plugin bindings and routes SHALL use versioned existing SystemSetting services with atomic expected-revision validation, safe cache refresh and complete unrelated-field preservation. New durable tables require an explicitly reviewed specification amendment.

#### Scenario: Concurrent settings saves
- **WHEN** two admins save from the same configuration revision
- **THEN** only one succeeds and the other receives 409 without partial configuration or secret mutation

### Requirement: Plugins bind real registered executors and models
Each configured plugin SHALL pin Registry key/version and the model/connection parameters needed by its execution capability. Unknown executors, cycles and dangling bindings MUST be rejected. A chat-only selected model MAY use a separately configured image plugin without becoming an image model.

#### Scenario: Chat model uses image plugin
- **WHEN** an image task selects a chat-only model and an authorized image plugin is configured
- **THEN** the plan selects the plugin's actual generation binding and preserves the requested task and selected-model explanation

### Requirement: Unified capability routing is deterministic
Workflow and Production SHALL share a resolver honoring explicit pinned bindings first, then executable selected-model bindings, then preconfigured ordered capability plugin defaults. Explicit pinned node bindings MUST NOT be silently replaced; no unrelated provider scan is permitted.

#### Scenario: Missing default plugin
- **WHEN** the selected model lacks video generation and no authorized video fallback is executable
- **THEN** the task is blocked with a typed safe reason and performs no external request

#### Scenario: Explicit Workflow binding unavailable
- **WHEN** a node pins a disabled binding even though a global default exists
- **THEN** execution blocks rather than changing the frozen Workflow intent

### Requirement: Execution plans freeze exact runtime selection
Dispatch SHALL pin configuration revision, adapter version/runtime identity, model/plugin IDs, normalized parameters, source refs, input hash and authorization limits. Changes before dispatch/acceptance MUST be revalidated; historical attempts MUST retain their original plan.

#### Scenario: Configuration changes after planning
- **WHEN** a connection or route changes before a planned generation dispatch
- **THEN** the stale plan is rejected or explicitly replanned before sending, and historical evidence is unchanged

### Requirement: Automatic plugin routing stays within explicit limits
Automatic fallback SHALL require an enabled policy and bounded per-request quantities/duration/size/tokens. Configured monetary limits MUST use provable versioned cost bounds; unknown price MUST NOT be treated as zero. Monetary aggregate budgets MUST NOT be claimed without transactional persistent reservation.

#### Scenario: Unbounded or unpriceable request
- **WHEN** automatic generation lacks hard input/output limits or cannot prove a configured monetary ceiling
- **THEN** the request blocks before dispatch and explains the missing limit without charging

### Requirement: Unknown generation does not trigger automatic resubmission
Once a billable request may have been sent, uncertainty SHALL preserve Unknown and MUST NOT cause provider switching, plugin retry or new async job creation. Polling SHALL use the original known job ID within bounds.

#### Scenario: Video submission times out
- **WHEN** the provider may have accepted a video job but the response is unknown
- **THEN** execution records Unknown and does not create another job through a fallback

### Requirement: Supplier adapters expose actual supported protocols
For the user-configured third-party CPA gateway, the platform SHALL reuse a configurable versioned OpenAI-compatible adapter for Gemini and `grok-4.7` instead of requiring Google/xAI official native adapters. The exact gateway URL, credential reference, model ID and supported operation SHALL be explicit. Compatible chat alone SHALL NOT imply image/video/TTS/ASR support: each non-chat operation requires a verified exact protocol contract, otherwise an authorized configured capability plugin MAY be selected before dispatch or the operation SHALL remain unavailable. The platform SHALL preserve the bounded MiniMax CLI adapter separately. Each supported operation SHALL have a documented request/response/auth/output contract; unsupported configured model-operation pairs SHALL be unavailable rather than chat-output substitutes. Previously added Google/xAI descriptor-only registrations MUST NOT become executable or verified merely because they are present.

#### Scenario: Chat endpoint selected for video
- **WHEN** a binding points a video operation at an adapter that supports only chat
- **THEN** validation rejects it and never treats chat text or an invented URL as a generated video

### Requirement: Generated artifacts are validated and accepted through existing media truth
Image/video/audio results SHALL undergo existing bounded transport, MIME/decode, bytes/hash, provenance and rights gates. Media previews SHALL remain temporary until explicit acceptance under the existing contract writes exact MaterialRevision and project refs. ASR suggestions SHALL use the existing explicit text acceptance path.

#### Scenario: Provider returns a URL only
- **WHEN** a generator responds with a media URL
- **THEN** the system safely downloads and validates actual bytes before presenting a valid preview or writing a revision

### Requirement: Local CLI providers are bounded and explicit
The system MAY register an installed local MiniMax CLI as a versioned provider for its confirmed `text`, `image`, `video`, `speech synthesize` and `speech transcribe` command families. It MUST invoke only fixed allowlisted subcommands through an argument array with bounded timeout/output/temp-file handling; it MUST NOT accept arbitrary executable paths, shell command strings, arbitrary passthrough flags, or arbitrary credential paths. With explicit user authorization, it MAY read only the official CLI's fixed local credential configuration through a controlled process using the current OS user's fixed home path and no-follow file-descriptor reads to establish credential continuity. The known projection MUST cover API-key and OAuth/token credential changes when present. Raw credentials, tokens, full config, and CLI diagnostics MUST remain in process memory only and MUST NOT enter task/database/log/UI/asset projections; only an irreversible HMAC-derived credential epoch may be persisted. CLI help/installation proves only that the adapter is loaded, not that a model, account, quota or generated result is verified.

#### Scenario: MiniMax CLI media generation
- **WHEN** a configured local MiniMax route requests an image, video, speech or transcription operation
- **THEN** the route uses the matching fixed CLI adapter, validates actual returned bytes or bounded transcript output, and continues through the existing preview/explicit acceptance or ASR acceptance flow

#### Scenario: MiniMax CLI unavailable or uncertain
- **WHEN** `mmx` is missing, a command times out, or a video task outcome is uncertain
- **THEN** the capability is shown unavailable/unknown when the fixed credential configuration is missing, unsafe, incomplete, changed, or cannot be safely fingerprinted, without exposing secrets, automatic resubmission, provider switching after dispatch, or fabricated media

### Requirement: Generation cannot replace authentic evidence
Generated media SHALL retain generated provenance and MUST NOT be represented as actual product screenshots, news photography or independent factual evidence. Generation routing MUST NOT silently mutate Identity, Brief, Fact Boundary, frozen Candidate or approved package.

#### Scenario: News photo request
- **WHEN** a task requires authentic event photography or factual evidence
- **THEN** generation is not selected as an equivalent source and missing authentic material remains explicit

### Requirement: Local generation operations have durable task identity
The system SHALL persist a ProviderGenerationTask before any external generation submission, with owner, optional authorized project and real Workflow attempt, idempotency key, canonical request hash, immutable bounded plan/input/source/runtime/credential-epoch projections, state/revision and safe original provider job identity. The amendment SHALL add only one task table and reuse existing asset/configuration/Workflow truth. Secrets, raw provider responses/errors and signed download URLs MUST NOT enter task projections.

#### Scenario: Concurrent duplicate submission
- **WHEN** two callers submit the same owner/idempotency key and request
- **THEN** they resolve to one task with at most one send claim, while the same key with different canonical input returns 409 without sending

#### Scenario: Standalone local generation
- **WHEN** generation is requested without a Workflow run
- **THEN** its task remains durable without creating a fake WorkflowRun or storing job state in SystemSetting

### Requirement: Restart recovery never resubmits uncertain generation
The system SHALL commit an atomic send claim before calling the provider, persist the original job as soon as known and use bounded original-job queries after restart. Expired claims after a possible send SHALL become unknown, not new submissions. Protocol/model/owner/runtime/credential scope SHALL be revalidated; CAS and lease tokens SHALL prevent late worker overwrites.

#### Scenario: Crash before original job persistence
- **WHEN** a claimed request may have reached the provider but no original job is durably known
- **THEN** restart exposes unknown and requires reconciliation without retries, provider switching or new jobs

#### Scenario: Known MiniMax video survives restart
- **WHEN** an authorized caller resumes a task with its persisted original MiniMax job and unchanged scope
- **THEN** the system queries that same job using its pinned model and V1/V2 protocol within limits, validates returned bytes and does not submit generation again

#### Scenario: Runtime or ownership drift
- **WHEN** a foreign caller, changed credential epoch or stale worker attempts recovery
- **THEN** the operation fails closed without exposing private results, changing the frozen plan or creating another job

#### Scenario: Rotating the active receipt key preserves historical credential identity
- **WHEN** MiniMax credentials are unchanged and the active receipt key rotates while the task's original key remains configured
- **THEN** recovery and acceptance derive the credential epoch with the task's original key ID, verify the original receipt and do not mistake key rotation for credential change; removing that original key or changing real credentials still blocks

#### Scenario: Terminal output belongs to a foreign job or file
- **WHEN** recovery of a known job returns successful bytes or a confirmed terminal status with missing or different required original job/file identity
- **THEN** the task rejects the output without accepting bytes, replacing the original job/file or signing a successful result; running and uncertain outputs also reject any explicitly returned foreign identity

#### Scenario: Revocation and a send claim race
- **WHEN** a source revocation races the transaction that validates rights and commits a send claim
- **THEN** a revocation committed first prevents the claim; an already committed claim retains its one frozen dispatch authorization without holding database locks during network IO, while later acceptance and reuse fail live-rights validation

#### Scenario: A known job query adapter becomes unavailable
- **WHEN** querying an already known provider job returns an unavailable adapter result without confirmed remote failure
- **THEN** the task remains unknown with its original job rather than becoming failed or permitting a replacement submission

#### Scenario: Persistent trust key unavailable
- **WHEN** a task receipt cannot be verified with its explicitly configured stable key after restart
- **THEN** execution and acceptance block without replanning or resubmitting the original job; safe historical state remains readable

#### Scenario: CLI authentication continuity cannot be proven
- **WHEN** the CLI lacks a safe official identity/credential-version contract or an external login change invalidates that proof
- **THEN** remote recovery and acceptance block with credential_continuity_unverified, retaining the original job rather than trusting a local epoch or masked key suffix

### Requirement: Recovered results require atomic explicit acceptance
Validated results SHALL persist in private controlled storage with exact MIME/bytes/hash and safe provenance/rights, independently of process-local preview tokens. Missing/tampered results MUST NOT be accepted or automatically regenerated. Explicit authorized acceptance SHALL atomically write existing MaterialRevision/project refs and its task linkage with idempotent readback and live source/rights checks. ASR SHALL retain its existing explicit text-save contract.

#### Scenario: Repeated acceptance after restart
- **WHEN** an authorized caller accepts the same validated task result twice across a restart
- **THEN** both successful readbacks identify the same exact MaterialRevision, with no duplicate revision or partial project reference

#### Scenario: Source rights revoked before acceptance
- **WHEN** a source is revoked or result bytes change after generation
- **THEN** acceptance blocks and writes neither a MaterialRevision nor a project reference

#### Scenario: Empty audio is not a generated result
- **WHEN** a provider returns a structurally readable WAV with zero audio frames
- **THEN** decoding rejects it before result storage or acceptance, retains the original send claim and does not resubmit

#### Scenario: MiniMax ASR credentials change before suggestion save
- **WHEN** the CLI credential epoch changes or cannot be proven after an ASR proposal was created
- **THEN** its execution fingerprint no longer validates, and explicit Master save rejects the old proposal rather than recording trusted provenance; static Settings inventory still reads no credential file

#### Scenario: Refresh or archive is not submission authority
- **WHEN** a user refreshes task details or opens an archived project
- **THEN** reads do not submit generation, and the archived project cannot submit, mutate recovery or accept new results

#### Scenario: Switching previews invalidates previous acceptance consent
- **WHEN** a user opens a different task and its raw-result read fails or a previous read returns late
- **THEN** previous media, confirmation and rights choices cannot authorize acceptance of the new task; only the latest matching task/result preview can be accepted

### Requirement: Workflow generation preserves immutable pre-send and terminal history
Explicit new media.generate nodes SHALL append a real immutable started Attempt before submitting their durable generation task, then wait on that original task without generic rerun/retry or executing dependent nodes. Resume SHALL use server-derived run/step/Attempt/task association and owner/archive checks. Media acceptance SHALL remain a separate explicit operation; only accepted exact MaterialRevision results SHALL complete the node and enter ProjectWorkflowOutput. Terminal history SHALL be appended, never overwrite started or legacy Attempts. Legacy nodes SHALL remain unchanged.

#### Scenario: Workflow waits for original media and human acceptance
- **WHEN** a new media node submits a task and receives running, unknown or result_ready
- **THEN** the node remains waiting, retains its original task and started Attempt, and does not run dependent nodes or silently accept media

#### Scenario: Explicit acceptance resumes the workflow
- **WHEN** the original task is explicitly accepted and the user resumes the waiting node
- **THEN** a terminal Attempt and exact project output are appended once without resubmission or mutation of the started Attempt

#### Scenario: Accepted media keeps configured output mappings
- **WHEN** a media node maps an accepted MaterialRevision field to a downstream alias
- **THEN** the pending phase defers that unavailable field and the accepted terminal output includes the mapping before downstream execution, without another provider submission; invalid mappings still fail closed

#### Scenario: Output aliases cannot overwrite generation identity or state
- **WHEN** a media node maps a different field into a reserved generation output name such as generation_state, generation_task_id or material_revision_id
- **THEN** definition validation and execution/resume reject the mapping before a provider call or recovery, preserving server-derived task identity, accepted state, exact asset identity and terminal history; same-field identity mappings remain compatible

#### Scenario: Archive or foreign ownership blocks task mutation
- **WHEN** a task bound to an archived or foreign ContentUnit is executed, recovered or accepted
- **THEN** mutation fails closed through standalone and Workflow APIs while authorized historical reads remain possible

### Requirement: Legacy configurations remain non-destructively compatible
Existing text purpose routes, legacy image configuration, historical executions and Candidate v1-v5 semantics SHALL remain compatible. Upgrading configuration SHALL be explicit and MUST NOT enable paid generation by default or rewrite old history.

#### Scenario: Read a legacy profile
- **WHEN** a Profile without capability fields is loaded
- **THEN** its existing chat routing remains available and no image/video/TTS ability is inferred

### Requirement: Stage model selection is exact and previewable

A prompt-bearing Stage Contract SHALL resolve an exact executable model profile/provider/model using the existing model capability registry/routing. Preview SHALL return that exact identity and availability without making a model call. Execution MUST fail on route drift instead of silently falling back.

The expected resolution hash SHALL also bind applicable routing-plan, adapter/version and safe runtime/credential-continuity identities, not only display model names. They SHALL be frozen into the durable invocation receipt before dispatch and revalidated through the existing routing gate; no silent replacement plan/model/runtime is allowed.

#### Scenario: Stage pins a model profile
- **WHEN** the stage explicitly selects a registered profile
- **THEN** preview and execution bind the same provider/model/profile identity or execution is blocked

#### Scenario: Adapter or runtime changes under the same model name
- **WHEN** the applicable routing-plan/adapter/runtime identity changes after preview despite unchanged provider/model labels
- **THEN** the expected resolution conflicts before dispatch and the user must inspect a new preview

### Requirement: Stage prompt receipt binds model execution

For model-backed stage execution, the successful LLMRun/input hash SHALL correspond to the effective Stage resolution and prompt hash recorded in the WorkflowStepAttempt receipt. Raw provider output/errors remain governed by existing redaction/retention policy.

#### Scenario: Review model provenance
- **WHEN** a proposal is later adopted into a Master
- **THEN** its provenance can trace to the exact attempt receipt and verified LLMRun/model identity used to produce the proposal

### Requirement: Persona auto configuration reuses executable capability routing

Persona creative auto mode SHALL use the existing deterministic executable model/capability route truth and its limits. It MUST NOT scan unrelated providers or infer capability from model branding. Preview SHALL show the exact selected route and why it is usable.

#### Scenario: Persona Graphic needs image generation
- **WHEN** the selected Graphic style requires generated imagery and no executable image route exists
- **THEN** readiness reports partial/blocked according to the declared typography-only fallback rather than pretending the chat model can generate images

### Requirement: Multimedia adapters declare image and audio execution capabilities

Registered Image and Audio adapters SHALL declare modality, provider/model/profile scope, supported request fields, output MIME/size constraints, candidate-count behavior and executable/readiness state. Image adapters SHALL declare whether multi-output is native and support normalized counts only within the bounded 1–4 range. Audio adapters SHALL declare exact voice-catalog/verification support, `voice_id`, rate and additional supported controls. Catalog/list operations are read-only and MUST NOT synthesize media.

Auto may use the existing authorized capability-routing policy, including bounded fan-out when an adapter explicitly permits it. Custom single-binding mode MUST block when the exact binding or requested capability is unavailable. Custom Composition MAY use only its predeclared exact chain. No route may discover an undeclared image/audio provider or silently ignore a requested field.

#### Scenario: Native multi-output image adapter
- **WHEN** the selected image model declares native four-candidate output
- **THEN** the resolver passes the bounded candidate count, preview shows it, and the receipt records the native batch capability and candidate indexes

#### Scenario: Voice catalog refresh is not media execution
- **WHEN** the user refreshes a registered TTS adapter's voice catalog
- **THEN** the adapter updates local metadata/readiness only and creates no generation task or audio bytes

#### Scenario: Requested image batch is unavailable on an exact Custom binding
- **WHEN** a Custom profile pins an image model that supports only one output while the Stage requests four
- **THEN** the Stage blocks rather than switching models or silently reducing the request

### Requirement: Explicit Persona model preference distinguishes pins from compositions

Custom creative profiles SHALL pin one exact registered provider/model/profile binding for a purpose. If that binding is unavailable or changes before execution, execution SHALL block and MUST NOT substitute another binding. A Composed/Custom Composition profile MAY instead declare an ordered chain of exact registered provider/model/profile bindings; execution SHALL use only that chain, disclose it in preview and record the selected binding and bounded fallback reason. Historical receipts SHALL retain the original route identity.

#### Scenario: Pinned TTS profile disabled
- **WHEN** the Persona audio profile pins a TTS profile that becomes disabled
- **THEN** Audio readiness blocks and never silently changes voice/provider without disclosure

#### Scenario: Custom Composition selects an explicit model fallback
- **WHEN** the primary model binding is unavailable and the next exact binding in the saved Custom Composition chain is executable
- **THEN** the route selects that declared binding, exposes the fallback reason and preserves the selected binding in the attempt receipt

### Requirement: Registered CPA image execution uses an exact image protocol

Gemini/Grok image execution through CPA SHALL reuse existing registered provider/model/profile credentials and explicitly trusted endpoint configuration. It MUST NOT require unrelated official-provider credentials, infer image capability from a chat model name, probe alternate endpoints or create a second provider configuration truth. The media adapter SHALL declare and freeze its versioned request/response protocol, exact model, supported parameters, MIME/byte constraints and native-count or explicitly authorized fan-out behavior. Effective Preview SHALL expose the server-built safe prompt and exact binding without provider I/O.

Execution SHALL consume that frozen contract and normalize actual image bytes into the same ProviderGenerationTask candidate and explicit MaterialRevision acceptance contracts used by MiniMax. Only bounded validated PNG/JPEG/WebP bytes count as success; returned prose, URLs or an available chat route do not. Unknown execution MUST NOT automatically retry or switch provider/model/protocol. Provider errors and credentials MUST NOT leak into previews, receipts or materials. No new business table or migration SHALL be introduced for this adapter.

#### Scenario: Registered Gemini chat is not an image binding
- **WHEN** an enabled registered Gemini model can chat but has no implemented exact image protocol
- **THEN** image preview reports unavailable with a safe reason and execution neither calls chat as an assumed image endpoint nor silently chooses another model

#### Scenario: CPA image candidates use the existing acceptance truth
- **WHEN** an explicitly selected executable CPA image binding returns the exact declared candidate count as valid image bytes
- **THEN** the candidates retain exact configuration/runtime/output hashes and explicit selection accepts only the chosen image into MaterialRevision without modifying Master or Variant

#### Scenario: Possible image dispatch cannot trigger protocol discovery
- **WHEN** a CPA image request times out or its external outcome is unknown
- **THEN** the original task remains uncertain and no alternate protocol, model or provider is tried automatically

### Requirement: ChatGPT manual image generation provides prompt handoff and image upload

The normal image-generation UI SHALL expose an explicit `ChatGPT（手动生图）` option. It SHALL display a complete safe effective prompt, one-click copy, and a multi-image drag/drop and file-picker entry instead of an automatic provider Generate action. The prompt SHALL deterministically consume the accepted visual brief/card plan, Persona style, usage, aspect/size, bounded requested count (1–4), reference obligations and output constraints. Preview/copy SHALL make no model request. Manual ChatGPT MUST NOT be advertised as a native executable image binding or enter Auto routing/provider fallback.

This branch SHALL reuse CreativeExecution Package/staging/acceptance truths with explicit human external execution, not ProviderGenerationTask or a new durable table. The existing package SHALL freeze the exact eligible current Master/Variant source, safe prompt snapshot/hash and bounded output contract. Changes to frozen source/prompt/configuration require a new current package. Existing source currentness, archive-read-only, required-role/min-max-count and live derived-rights rules MUST remain authoritative.

Dropping or choosing local image files SHALL immediately enqueue visible candidate rows and upload to temporary staging only. Each row SHALL show upload/validation progress, thumbnail, MIME/dimensions, error or ready state, and selection/removal controls. The server SHALL validate actual bounded PNG/JPEG/WebP bytes, MIME, dimensions, file size, count and hash against the frozen contract. Invalid/failed files MUST NOT be accepted or create partial MaterialRevision writes; other valid candidate rows remain intact. Removing a temporary row MUST NOT delete/revoke an already accepted material.

Explicit `接受入库` SHALL accept only exact selected valid staged outputs through the existing idempotent MaterialRevision acceptance service with `source_kind=external_execution`. Upload alone MUST NOT create an accepted material. Provenance SHALL distinguish user-declared ChatGPT origin from verified native provider execution and preserve prompt/package/output hashes and human decisions without fabricated LLMRun/model/runtime receipts. Accepted material MUST NOT automatically bind/save Master or modify Variant, Candidate, Approval or publication.

AIContentStudio SHALL neither require a browser/session binding nor submit prompts/download images on the user's behalf for this branch. It MUST NOT read/export Cookies, browser-profile files or site credentials, create a fake API/browser endpoint, silently choose another provider, or replay old browser-smoke requests. The user operates the external website themselves. Prompt copy or external image generation alone MUST NOT mark product execution result-ready, accepted or quality-approved.

#### Scenario: Manual ChatGPT is selected without browser automation
- **WHEN** the user selects `ChatGPT（手动生图）` without an application browser/session binding
- **THEN** the frontend exposes the full prompt/copy and upload entry, makes no provider or browser request and does not switch to CPA or MiniMax

#### Scenario: Dragged images remain temporary candidates
- **WHEN** the user drops multiple downloaded images into the manual upload area
- **THEN** each file immediately appears in the candidate list with independent upload/validation state and no accepted material or Master mutation occurs

#### Scenario: Invalid upload does not affect valid candidates
- **WHEN** one returned file violates the frozen image output contract while another is valid
- **THEN** the invalid row shows a bounded error and cannot be accepted, the valid candidate stays selectable and there is no partial material write

#### Scenario: Exact uploaded image is explicitly accepted
- **WHEN** the user selects a valid exact staged output and clicks `接受入库`
- **THEN** the existing service revalidates live derived rights and creates the exact MaterialRevision idempotently with user-declared ChatGPT provenance; Master reference/save remains separate

#### Scenario: Source changes while the user generates externally
- **WHEN** the frozen package source becomes stale before returned image acceptance
- **THEN** the existing stale/currentness gate blocks acceptance and the UI requires a new current package without overwriting the old contract or automatically regenerating

#### Scenario: Copying or uploading is not accepted production output
- **WHEN** the prompt is copied or an image is merely uploaded without explicit acceptance
- **THEN** no provider-success receipt or accepted MaterialRevision is fabricated and the existing result/acceptance states reflect only actual validated staged outputs and explicit decisions
