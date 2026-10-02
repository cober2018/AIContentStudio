## ADDED Requirements

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

#### Scenario: Refresh or archive is not submission authority
- **WHEN** a user refreshes task details or opens an archived project
- **THEN** reads do not submit generation, and the archived project cannot submit, mutate recovery or accept new results

### Requirement: Workflow generation preserves immutable pre-send and terminal history
Explicit new media.generate nodes SHALL append a real immutable started Attempt before submitting their durable generation task, then wait on that original task without generic rerun/retry or executing dependent nodes. Resume SHALL use server-derived run/step/Attempt/task association and owner/archive checks. Media acceptance SHALL remain a separate explicit operation; only accepted exact MaterialRevision results SHALL complete the node and enter ProjectWorkflowOutput. Terminal history SHALL be appended, never overwrite started or legacy Attempts. Legacy nodes SHALL remain unchanged.

#### Scenario: Workflow waits for original media and human acceptance
- **WHEN** a new media node submits a task and receives running, unknown or result_ready
- **THEN** the node remains waiting, retains its original task and started Attempt, and does not run dependent nodes or silently accept media

#### Scenario: Explicit acceptance resumes the workflow
- **WHEN** the original task is explicitly accepted and the user resumes the waiting node
- **THEN** a terminal Attempt and exact project output are appended once without resubmission or mutation of the started Attempt

#### Scenario: Archive or foreign ownership blocks task mutation
- **WHEN** a task bound to an archived or foreign ContentUnit is executed, recovered or accepted
- **THEN** mutation fails closed through standalone and Workflow APIs while authorized historical reads remain possible

### Requirement: Legacy configurations remain non-destructively compatible
Existing text purpose routes, legacy image configuration, historical executions and Candidate v1-v5 semantics SHALL remain compatible. Upgrading configuration SHALL be explicit and MUST NOT enable paid generation by default or rewrite old history.

#### Scenario: Read a legacy profile
- **WHEN** a Profile without capability fields is loaded
- **THEN** its existing chat routing remains available and no image/video/TTS ability is inferred
