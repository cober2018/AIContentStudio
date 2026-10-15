# web-video-production-handoff Specification

## Purpose
TBD - created by archiving change verify-grok-gemini-media-capabilities. Update Purpose after archive.
## Requirements
### Requirement: Normal video production pages expose the complete workflow
The system SHALL extend the existing project video production route and Director workspace with shot-material preparation, website generation handoff, returned-material review, explicit shot binding, professional edit handoff, rough-cut feedback and final-result adoption. The existing creation queue SHALL project these execution phases and link to the exact project, unit, execution and shot. Reading a page or preparing a package MUST NOT start external generation, create a Codex chat or publish content.

#### Scenario: Prepare a website video from a shot
- **WHEN** an editor opens a saved video unit and chooses the new image-first website workflow for a shot
- **THEN** the page first presents image creation/selection and explicit shot-image confirmation, then image-grounded video prompt editing, and only after both are saved offers the frozen image, prompt, parameters and manual Grok/Gemini handoff

#### Scenario: Unsubmitted edits remain local
- **WHEN** a shot has unsaved changes
- **THEN** preparing its execution requires saving or explicitly using the known saved version, without discarding the local draft or silently dispatching it

### Requirement: Shot production preserves stable identities and source revisions
Shot production SHALL use the existing stable shot ID and exact saved Video Master revision, with a bounded optional versioned production configuration for source mode, prompt, reference image, generation duration and audio intent. Requested source duration and edited use duration SHALL remain distinct. Selected accepted MaterialRevision references SHALL remain the sole adopted-media truth. Old Video v2 documents without the extension SHALL remain valid.

#### Scenario: Several shots are produced from one saved storyboard
- **WHEN** clips return for multiple tasks based on the same Master revision
- **THEN** accepting individual materials does not advance Master, and an explicit batch binding/save can adopt the selected exact clips without invalidating other tasks by an implicit save

#### Scenario: Storyboard changes during generation
- **WHEN** a user saves a changed storyboard after packages were prepared
- **THEN** original packages and outputs remain inspectable, stale packages cannot perform further side effects, and reuse or a new task requires an explicit current-version action without automatic regeneration

### Requirement: Video prompts follow explicit shot image selection
The new normal website workflow SHALL create or select an image, explicitly confirm and save its exact accepted MaterialRevision and content hash for the shot, then author and confirm the video prompt based on that image. Image creation descriptions and video motion prompts SHALL remain distinct. Image library acceptance alone MUST NOT count as shot image confirmation. Existing image generation, upload, selection, editing and CLI/MCP operations SHALL be reused without a new prompt-generation service. Multiple shots MAY explicitly reuse one image.

#### Scenario: The image has not been selected
- **WHEN** a new image-first shot has no saved, authorized reference image
- **THEN** image creation and selection remain available but neither the dedicated nor generic preparation path can produce a ready website execution

#### Scenario: The chosen image changes after a prompt was authored
- **WHEN** a shot reference is replaced with another image revision
- **THEN** the previous prompt remains visible for review but is not ready for handoff until explicitly reviewed and confirmed against the new revision; preparation rejects mismatched prompt-image provenance and never rewrites old packages

#### Scenario: A confirmed image and prompt are handed to the user
- **WHEN** the saved shot contains a usable authorized image and a video prompt confirmed against that exact image hash
- **THEN** the handoff freezes image-to-video mode, the downloadable image, motion prompt and settings; manual return records which image was used, while the platform does not claim to independently observe website actions

### Requirement: API images and website videos have truthful execution identities
Native API images SHALL continue to use ProviderGenerationTask and confirmed registered Grok/Gemini image protocols. Website video tasks SHALL use the existing CreativeExecution domain with a frozen web_video extension and one-shot output contract. They MUST NOT claim native provider task IDs, verified hidden model identities, API billing or unavailable video API support. Current MiniMax paths and defaults SHALL remain intact.

#### Scenario: Website hides the exact video model
- **WHEN** a returned Grok or Gemini clip has a known website but no visible exact model identifier
- **THEN** provenance records the website and available settings while marking the model unspecified, without inventing an API execution receipt

### Requirement: Website production uses a manual prompt-and-return handoff
The system SHALL present shot copy, a copyable frozen prompt, provider website, requested source duration, aspect ratio, audio intent and the confirmed authorized reference image for the new image-first workflow (historical tasks retain their original contracts). The user SHALL upload that image and paste the video prompt/settings into Grok or Gemini, generate and download the source clip manually, then upload it to the exact shot task. The platform and project Skill MUST NOT automatically operate the generation website, submit prompts, poll the website or download its results. Website credentials SHALL remain outside the platform. Historical browser executions and outputs SHALL remain inspectable; a possibly submitted historical operation MUST be reconciled before any replacement submission. Professional editing SHALL continue through Codex and the existing local MCP after the user returns accepted media.

#### Scenario: A user generates a clip manually
- **WHEN** the user prepares a saved shot
- **THEN** the page provides the prompt and settings to copy, an optional website link and the exact task upload entry, without starting any external operation

#### Scenario: A previously started browser task is uncertain
- **WHEN** the old website task may already have been submitted
- **THEN** its history and result remain preserved, and switching the normal workflow to manual does not automatically resubmit it

### Requirement: Returned clips are inspected and accepted before shot binding
Both private-workspace submission and manual upload SHALL stage actual bounded video bytes under the exact execution, shot and output role. The system SHALL validate hash, MIME, decodability, actual duration, dimensions, frame rate and audio presence against the frozen contract and live input rights. URLs, filenames and success text alone MUST NOT count as clips. Explicit acceptance SHALL create immutable MaterialRevision and project references; binding to a shot SHALL require a separate visible Master save. Replacement candidates SHALL preserve prior attempts.

#### Scenario: A clip is uploaded to the wrong task or violates the shot contract
- **WHEN** an upload has mismatched scope, insufficient duration, wrong aspect or invalid video bytes
- **THEN** the system identifies the specific mismatch and does not silently bind, crop, overwrite or accept it as satisfying the shot

#### Scenario: A reference image loses authorization
- **WHEN** model-use rights are revoked before reference download or derived-output adoption
- **THEN** the corresponding external send or adoption is blocked without upgrading rights or rewriting historical evidence

### Requirement: Video transport remains bounded across the entire file lifecycle
Explicitly versioned new video/professional execution contracts SHALL support a per-file upper bound of 512 MiB and a total authorized-input plus staged-output bound of 4 GiB per execution, with lower frozen limits permitted and one active transfer per execution. Legacy contracts and unrelated upload limits SHALL retain their existing bounds. Upload, input materialization, local-file submission, hash/media validation, persistent storage and authorized playback SHALL enforce the same effective limits using bounded streaming rather than full-file JSON/base64 or unbounded memory. MCP payloads SHALL contain only small metadata and scoped relative references. Preflight and stream-time checks SHALL reject excess before acceptance without silently reducing quality.

#### Scenario: A real video exceeds the old 30 MiB limit
- **WHEN** a 40 MiB valid clip is handled under a new contract whose explicit bounds permit it
- **THEN** upload or local submission, validation, authorized playback and adoption all succeed within bounded memory while old contracts retain the old refusal behavior

#### Scenario: A file or accumulated output exceeds the frozen budget
- **WHEN** an incoming stream exceeds a per-file or execution aggregate bound
- **THEN** the transfer is rejected, incomplete bytes cannot be accepted, and no automatic quota increase or transcoding occurs

### Requirement: Codex receives an exact professional editing package
The system SHALL reuse director.video.v1 and the existing MCP claim/materialize/progress/submit tools to hand off the saved script, narration, subtitles, selected exact clip revisions, use ranges, frame/aspect requirements, editing intent and acceptance criteria. A bounded optional versioned postproduction extension SHALL identify rough-cut, refinement or final phase and exact parent-result feedback when applicable. A project Skill SHALL explain how Codex executes these tools, manual material handoff and local professional actions without creating a second task or content truth. Preparing a task SHALL expose a copyable execution instruction and SHALL remain distinct from Codex actually claiming it.

#### Scenario: An editor prepares an edit before all required media are ready
- **WHEN** required shot clips, narration or exact asset references are missing or stale
- **THEN** the normal page lists those gaps and does not claim a complete ready-to-edit package

### Requirement: Resolve owns the master edit and After Effects supplies scoped compositions
DaVinci Resolve SHALL own the main timeline, edit, sound assembly, grading and final export for this workflow. After Effects SHALL produce only explicitly requested compositions with declared duration, dimensions, frame rate and alpha requirements, which Resolve consumes as media. No-AE projects SHALL skip that branch. The edit manifest SHALL identify actual source use ranges and narration timing, and generated-clip audio SHALL follow the frozen keep/mute intent. The workflow MUST NOT force every source clip to ten seconds or modify unrelated application projects/global settings.

#### Scenario: A shot requires an animated explanatory overlay
- **WHEN** the frozen director instructions request one AE composition
- **THEN** Codex produces that composition and its required intermediate media, incorporates it into the Resolve main timeline, and records the exact source and composition lineage

#### Scenario: The video needs only straightforward cuts
- **WHEN** no AE work is requested
- **THEN** Resolve completes the edit without an artificial AE dependency

### Requirement: Rough-cut feedback is tied to exact output versions
The page SHALL collect timecoded feedback against the exact rough-cut output ID and hash. An unaccepted execution SHALL use the existing rejection/replacement-attempt mechanism. An accepted execution SHALL remain terminal; further edits SHALL prepare a new current-source execution with explicit parent result and feedback inputs, preserving all earlier files and decisions. Feedback or page refresh MUST NOT silently re-edit or regenerate media.

#### Scenario: An accepted rough cut needs a shorter scene
- **WHEN** an editor requests a trim against the accepted rough-cut version
- **THEN** a new refinement task freezes that feedback and exact available source references while the accepted rough-cut execution remains unchanged

### Requirement: Final delivery includes usable media and reopenable project evidence
Rough-cut and final contracts SHALL require their respective MP4, a Resolve project and an edit manifest; subtitles SHALL be required when the content has dialogue. When AE is used, its project and necessary intermediate-media dependencies SHALL also be returned. The manifest SHALL map scoped relative files and accepted media IDs/hashes, phases and tool information without arbitrary filesystem access. The executor SHALL actually reopen the project and check for missing media; project filenames alone MUST NOT prove editability. Required project dependencies SHALL remain available and MUST NOT be deleted by routine staging cleanup while referenced. Project files SHALL default to non-public. Final-media acceptance and explicit current-Master final-render binding SHALL remain distinct. An accepted final MP4 with current local/model-use authorization MAY be explicitly bound and privately previewed in the current Video Master even when public-use permission is false. Binding SHALL preserve exact rights flags and MUST NOT grant publication permission; Candidate and publishing SHALL continue to require public-use permission.

#### Scenario: A render exists but the editing project cannot reopen
- **WHEN** the final MP4 is valid but its required project has missing dependencies
- **THEN** the missing project requirement remains incomplete and the workflow does not claim fully editable delivery

#### Scenario: A final video is accepted
- **WHEN** the user accepts the exact validated final MP4 and accompanying required outputs
- **THEN** the result becomes accepted media and only an explicit final-render binding/save changes Video Master, without automatic approval or publication

#### Scenario: A local-only accepted final video is bound
- **WHEN** an accepted final MP4 is authorized for local/model use but lacks public-use permission
- **THEN** explicit binding/save and private owner-scoped preview succeed without changing rights, while Candidate/public delivery remains blocked by the existing public-use checks

### Requirement: Existing records and adjacent change ownership remain preserved
The implementation SHALL reuse existing model registration, Video Master, CreativeExecutionPackage/Execution/Output and MaterialRevision stores, adding only necessary versioned JSON/transport behavior within this scope. Existing API image protocols, saved video documents, execution histories, account configuration and adjacent changes SHALL remain intact. Professional MCP availability SHALL use the user's confirmed local setup; unrelated installation/configuration repair SHALL NOT become this feature's prerequisite. An unforeseen schema migration or new runtime dependency SHALL require an explicit design amendment before implementation.

#### Scenario: A historical task is opened after the new flow is enabled
- **WHEN** a task lacks the new web-video or postproduction extension
- **THEN** the original contract and limits remain readable and executable under their prior supported rules, without backfill or reinterpretation

### Requirement: Acceptance proves the normal-page end-to-end production flow
Acceptance SHALL distinguish earlier API diagnostics, isolated checks, browser generation, manual return, real AE/Resolve work, actual media quality and explicit product adoption. It SHALL demonstrate Grok and Gemini API image generation, one real image-to-video clip from each website, each with confirmed reference-image and prompt provenance, a 60–90-second sample with at least six shots and one AE composition, Resolve rough cut plus a timecoded revision, final export, required subtitles, project reopen and normal-page acceptance/reload. The sample length SHALL be an acceptance fixture rather than a product duration limit. The user-confirmed sample SHALL include narration using the configured technology Persona voice and existing copy. Muting website source clips MUST NOT silence the final narration; the final MP4 SHALL include a real audible narration track with reviewed transcript and synchronized subtitles. The earlier silent sample SHALL remain historical evidence only. The manual prompt/settings copy and exact-task upload path SHALL be demonstrated; automated website operation is excluded from acceptance. User-returned genuine clips from both websites satisfy the website branch when provenance and actual bytes are checked; no replacement generation is authorized merely to repeat old automation evidence. No new persistent test code SHALL be added under this request.

#### Scenario: Complete the agreed sample within the generation budget
- **WHEN** the authorized acceptance run uses the confirmed revision-4 cumulative budget of at most four API image submissions (two already used plus at most two new keyframes) and four cumulative website video submissions (the earlier Grok result and submitted Gemini task count as two used, leaving at most two image-to-video submissions) with serial single-attempt dispatch
- **THEN** evidence records actual outputs and all normal-page/tool handoffs, preserves unknown operations without resending, and does not substitute diagnostic media or local fixtures for genuine provider and editing results
