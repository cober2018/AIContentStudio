## ADDED Requirements

### Requirement: Local ASR reuses one registered adapter and existing runtime
The system SHALL expose an explicitly enabled versioned `local.mlx_whisper` ASR adapter through the existing Registry, reuse the operator-approved local Python/MLX worker and cached model, and conform to the existing ASRProvider result contract. It MUST NOT copy Radar's business databases, collectors or workflow engine, install dependencies, download models or add persistent business objects for this change.

#### Scenario: Existing local bridge is configured
- **WHEN** the operator enables the approved local runtime and its existing model snapshot is available
- **THEN** the Registry exposes the local ASR option with truthful installation/configuration state, without executing transcription or marking real verification complete

#### Scenario: Runtime is missing
- **WHEN** Python, worker, model or required offline execution support is missing
- **THEN** local ASR is unavailable with a safe reason and no installation, model download, placeholder transcript or cloud invocation occurs

### Requirement: Local transcription never sends content to cloud
The local adapter SHALL consume validated exact source bytes and a pinned existing local model snapshot, run with network access denied and a credential-free controlled environment, and extract an MP4's real audio through fixed local ffmpeg commands. Client inputs MUST NOT select an executable, file-system path, arbitrary flags, shell command or remote model repository. No-audio or unsupported input MUST fail honestly.

#### Scenario: Local video is selected
- **WHEN** a user explicitly requests local ASR for an allowed exact MP4 revision
- **THEN** audio extraction and model inference occur on the local computer with network access denied, and the output cites that exact source hash rather than a remote upload or unrelated transcript

#### Scenario: Local inference fails
- **WHEN** local preprocessing, inference or offline prerequisites fail
- **THEN** the result is unavailable or unknown as appropriate and the platform does not automatically send the source to MiniMax or another remote provider

### Requirement: Local runtime and process limits are verifiable
The local ASR runtime fingerprint SHALL bind the actual adapter, interpreter/worker and relevant compatible runtime components plus model snapshot/configuration/weights checksums. Changed files MUST invalidate cached identity. A request SHALL have a server-controlled total deadline of at most 120 seconds, one local inference at a time, bounded private temporary files and diagnostics, process-group termination/reaping and cleanup. Other Provider calls SHALL retain their existing 30-second wait and capacity contract; the client MUST NOT control these deadlines. A timed-out operation MUST retain its capacity until it terminates.

#### Scenario: Request exceeds its deadline
- **WHEN** preprocessing or inference exceeds the local deadline
- **THEN** the controlled processes terminate and are reaped before capacity is released, safe errors are returned, no automatic retry or cloud fallback occurs, and legacy provider deadlines remain unchanged

#### Scenario: Model changes before explicit save
- **WHEN** an ASR suggestion was received but its worker/runtime/model identity changes before Master save
- **THEN** the old receipt is rejected rather than recording the new runtime as the origin of old cues

### Requirement: Exact source and existing authorization gates are preserved
Local ASR SHALL operate only on an authorized current `video.master.v2` and an exact visible MaterialRevision already saved in that Master. Existing project ownership, archived/history read-only, current context, actual bytes/hash, active resource and live model-use permission gates SHALL apply at dispatch and explicit save. Local execution MUST NOT auto-grant model, public or commercial rights. The initial scope SHALL preserve current WAV/MP4, 600-second and 30MiB ASR-source limits and leave existing upload-entry limits unchanged, with explicit unavailable states rather than an arbitrary path bypass. SourceDocument upload configuration MUST NOT be treated as a new limit on already saved MaterialRevision transcription.

#### Scenario: Source permission is unavailable
- **WHEN** source model-use permission is absent, revoked or the source bytes/hash have changed
- **THEN** the local request or save is blocked without changing source rights, copying new evidence or producing a trusted receipt

#### Scenario: Source or user scope is invalid
- **WHEN** the source is absent from the saved Master, foreign, historical, archived, unsupported or over the applicable size/duration limit
- **THEN** the action fails before inference and does not bypass the formal library/reference contract

### Requirement: Segment subtitles are honest bounded model outputs
The adapter SHALL emit real transcript text and segment cues with validated finite non-negative millisecond times and stable order/IDs. Output SHALL obey existing text/cue/count/timeline bounds and bounded JSON; invalid, overlapping or out-of-range cues MUST fail rather than be fabricated, silently truncated or promoted to verified success. The first release MUST NOT claim word-level alignment, speaker identity or visual understanding.

#### Scenario: Worker emits valid segment times
- **WHEN** valid real segments are returned for the exact source within the saved timeline
- **THEN** the server converts their real second times into validated millisecond subtitle cues and records the actual local runtime/source lineage

#### Scenario: Worker emits malformed or unbounded output
- **WHEN** the worker returns invalid JSON, non-finite times, overlapping/out-of-range cues, excessive text or oversized output
- **THEN** the request is rejected with a safe reason and no fake cues or Master revision is created

### Requirement: ASR remains an explicit suggestion and immutable save
Local and existing remote ASR SHALL reuse the existing actor/project/unit/current-Master scoped expiring receipt, local subtitle editing and append-only Master save. Accept MUST modify only local draft cues and invalidate incompatible final render bindings. Only an explicit authorized save SHALL persist a new Master revision after receipt, source, context/runtime and optimistic concurrency revalidation. Edited cues SHALL record subsequently_modified rather than exact-output provenance. Expired or restart-lost unsaved receipts MUST fail closed; saved history SHALL remain readable.

#### Scenario: User accepts and saves subtitles
- **WHEN** the user previews a real local suggestion, explicitly accepts it, optionally corrects the local cues and explicitly saves
- **THEN** no revision is created by Accept alone, the save atomically writes an immutable child with exact local ASR lineage, and refresh returns that saved child without changing Workflow or Identity

#### Scenario: Concurrent or expired suggestion cannot save
- **WHEN** the current Master/context advanced, source/runtime changed or the actor-bound receipt expired before save
- **THEN** the action fails without partial writes or trusted forged/foreign provenance, and the user's local edits are not silently overwritten

### Requirement: UI prefers local ASR without silently selecting cloud
The ASR options and Production panel SHALL present safe human-readable local/cloud labels and truthful available/reason state. A configured available local adapter SHALL be the panel's initial choice; when it is unavailable the selection SHALL remain unset with a reason instead of defaulting to cloud. MiniMax SHALL remain explicitly selectable with a content-transmission notice, without altering CPA text routes/defaults or globally rewriting capability configuration. Inventory MUST NOT execute inference, probe remote credentials or imply verified capability.

#### Scenario: Local adapter is available
- **WHEN** a user opens the ASR panel with the local runtime configured
- **THEN** the local engine is selected, the exact source and limits are shown, and only an explicit request invokes it

#### Scenario: User chooses remote ASR
- **WHEN** a user explicitly selects MiniMax instead
- **THEN** the panel identifies it as a cloud action and only the user's explicit request follows the existing remote flow; local failure alone never initiates that flow

### Requirement: Real acceptance and scoped regression evidence remain separate
Completion SHALL require a real permitted local audio and video-audio run through Production suggestion, acceptance, optional editing, explicit Master save, refresh and persisted-history readback, plus existing compatibility/build/performance/spec/security checks. Static paths, configuration and mocks MUST NOT substitute for inference or saved subtitles. This change MUST NOT claim completion of new media generation acceptance, all F7, long-media support or cloud-provider verification.

#### Scenario: Local subtitle chain is accepted
- **WHEN** real local WAV and MP4-audio inputs have been transcribed and explicitly saved through the product UI
- **THEN** the report distinguishes real runtime/source/output and saved Master evidence from offline negative probes, records any uncovered boundary, and makes no paid-provider or whole-F7 completion claim
