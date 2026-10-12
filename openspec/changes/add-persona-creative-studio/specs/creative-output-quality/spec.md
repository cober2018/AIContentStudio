## ADDED Requirements

### Requirement: Image and Audio generation use one normalized multimedia contract

Image and Audio generation SHALL be presented as one user-facing multimedia generation surface with modality-specific adapters. Both SHALL support server-derived Effective Preview, exact provider/model/profile binding, adapter-declared controls, immutable attempt provenance, candidate output validation and explicit acceptance before durable MaterialRevision/Master/Variant use. Adapter-specific fields that are unsupported or unavailable MUST be hidden or reported unavailable; they MUST NOT be silently ignored.

Image adapters SHALL declare output MIME/dimensions, aspect/size controls, optional exact reference-asset inputs and candidate-count behavior. The normalized Image request SHALL support a bounded count from 1 through 4. Native multi-output is preferred; bounded fan-out is permitted only by Auto policy or a previously declared Custom Composition. Custom single-binding mode MUST NOT switch provider/model to obtain additional candidates. Every candidate SHALL have an exact index, binding receipt, bytes/hash/MIME and explicit acceptance state before it becomes an accepted MaterialRevision.

Audio adapters SHALL declare voice binding, rate and supported advanced controls. The normalized Audio request MAY return one or more candidates only when the adapter explicitly supports that behavior; the default remains one. Exact voice/provider/model/profile and supported parameter values SHALL be recorded in the same receipt contract. Audio remains MaterialRevision truth and does not create a fourth Master modality.

#### Scenario: Generate and choose from image candidates
- **WHEN** a user requests four image candidates through an adapter that supports native multi-output
- **THEN** the UI shows four normalized candidates with exact hashes and binding provenance, and only the explicitly chosen candidate(s) can proceed to MaterialRevision acceptance

#### Scenario: Image adapter cannot return a batch
- **WHEN** an Auto route supports only one image per request
- **THEN** the system may use a bounded declared fan-out, records each request/candidate separately, and does not present the result as one native batch

#### Scenario: Advanced audio control is unsupported
- **WHEN** a selected TTS adapter does not declare a requested voice parameter
- **THEN** Advanced Settings marks it unavailable and execution rejects or omits it according to the adapter contract, never silently pretending it was consumed

#### Scenario: Configuration changes after preview
- **WHEN** the effective multimedia configuration or exact provider binding changes before execution
- **THEN** execution blocks on hash drift and does not call a substitute provider/model

### Requirement: Quality Profiles are versioned and media-specific

The product SHALL ship versioned Quality Profiles for technical/lifestyle Text, editorial/lifestyle Graphic and explainer/conversational Audio. A Quality Profile SHALL declare required deterministic checks, optional model-critic dimensions, blocking/warning thresholds and human-review requirements. Deterministic blockers MUST NOT be overridden by a model critic.

#### Scenario: Model critic likes content with invalid rights
- **WHEN** a critic rates a Graphic highly but a referenced MaterialRevision lacks required rights
- **THEN** the Graphic remains blocked and critic output cannot make it ready

#### Scenario: Quality reference belongs to a different modality
- **WHEN** a Text, Graphic or Audio creative profile selects an existing Quality reference for another modality
- **THEN** profile validation SHALL reject the configuration before an identity revision is saved, and readiness SHALL report the invalid profile rather than claim ready
- **AND** historical profile/snapshot data SHALL NOT be silently repaired; existing Video planning script-quality references remain compatible without claiming final-video quality

### Requirement: Text quality is grounded and persona-aware

Text quality SHALL evaluate exact content/input hashes and include deterministic checks for required evidence/citation coverage, unsupported bounded factual elements where existing evidence mapping can prove them, structure/empty-content bounds, excessive repetition and persona-configured hype/marketing/clickbait restrictions. Optional model critique MAY score role fit, clarity, specificity and naturalness but is advisory unless the profile explicitly defines a bounded non-safety threshold.

#### Scenario: Technical article becomes stale
- **WHEN** a Text Master changes after a technical quality result
- **THEN** the prior quality result is stale and cannot be reused for the changed content

### Requirement: Graphic quality validates real rendered outputs

Graphic quality SHALL validate semantic/canvas contract, element bounds, minimum margins, supported overlap rules, text overflow/density, supported contrast/readability thresholds, required visual refs, live rights, exact rendered dimensions/MIME/hash and required cover/first-card roles. Passing plan/schema validation alone MUST NOT be described as a finished Graphic.

#### Scenario: Lifestyle cover image with text-only body cards
- **WHEN** warm-magazine composition contains an exact image reference on its cover and text-only body cards
- **THEN** planning, composition and Graphic structure QC SHALL permit that mixed layout, while exact references, live rights, render bytes, dimensions and human quality gates remain required
- **AND** a missing cover image remains blocked; documentary-photo continues to require an image on every card and undeclared diagram fallback remains forbidden
- **AND** new composition provenance and current check input hashes bind the role-aware visual policy; existing requests, accepted plans, Masters and frozen check requirements SHALL NOT be rewritten

#### Scenario: Graphic plan exists but renderer failed
- **WHEN** a Graphic Master/plan is structurally valid but no valid render MaterialRevision exists
- **THEN** Graphic output quality remains incomplete and the product does not present the plan as finished images

#### Scenario: Accepted image has the wrong canvas dimensions
- **WHEN** a Persona Graphic quality flow binds a Graphic v2 render with valid bytes/hash/MIME but its decoded width or height differs from its exact canvas
- **THEN** render readiness and subsequent Candidate/Review/package gates SHALL fail closed; a manual attestation MUST NOT waive the dimension mismatch
- **AND** this new Persona quality contract SHALL NOT retrospectively reinterpret legacy Graphic v2 manual attestations that have no Persona creative profile

#### Scenario: Recipe guides the existing renderer without replacing Master edits
- **WHEN** a Graphic recipe reaches quality confirmation after explicit Master adoption
- **THEN** normal mode SHALL expose the current saved canvas/render status and direct the user to the existing render/accept/bind/explicit-save controls without raw Workflow authoring
- **AND** opening or refreshing that projection SHALL NOT invoke a model/renderer, accept a material, or discard an unsaved Master draft

### Requirement: Audio quality validates real media and voice contract

Audio quality SHALL bind to an exact accepted audio MaterialRevision and validate bytes/hash/MIME/nonzero bounded duration plus available local checks for gross clipping, excessive silence and configured loudness. It SHALL verify the exact TTS task/provider/model/voice/rate contract from provenance. Optional ASR alignment MAY compare speech with the accepted spoken script only when an executable ASR capability is explicitly invoked.

#### Scenario: Local QC of restricted accepted audio
- **WHEN** the exact same-run TTS MaterialRevision is explicitly accepted for local-only use with public/model/commercial permissions remaining false
- **THEN** the deterministic local Audio QC Stage SHALL inspect its live bytes and signed task/script/voice provenance without requiring or granting public/model-use permission
- **AND** revoked/unavailable material, tampered bytes/provenance and derived-rights violations remain blocked; ASR inference, AI consumption, publication and other upstream consumers retain their existing permission gates

#### Scenario: Approved six-minute Audio Recipe ceiling
- **WHEN** a user explicitly selects the built-in Persona Audio Recipe under the approved local 360-second TTS output policy
- **THEN** the new Recipe template SHALL request a 360-second maximum output duration, not silently request the former 600-second template value
- **AND** the duration ceiling is not a target duration or interface timeout; actual duration depends on the accepted script and rate, while the registered timeout and all live media checks remain independent
- **AND** existing saved workflows, Runs, Attempts, MaterialRevisions and their frozen limits SHALL NOT be rewritten; an explicit request exceeding the current policy remains blocked

#### Scenario: TTS returns corrupt or silent output
- **WHEN** accepted provider bytes fail media/duration/silence checks
- **THEN** Audio QC blocks readiness without rewriting or deleting the historical MaterialRevision

#### Scenario: Explicitly reuse accepted ASR segment timing
- **WHEN** the user enables alignment and selects an exact previously accepted ASR receipt for the same audio MaterialRevision/hash
- **THEN** QC SHALL verify its saved provenance and segment timing, compare the transcript with the signed accepted spoken script, and freeze the exact comparison and optional SRT hashes in the Attempt report
- **AND** Preview/read SHALL NOT run ASR; missing, changed or foreign proof SHALL fail closed rather than substitute estimated timing

#### Scenario: Estimated subtitle export is not alignment evidence
- **WHEN** the user explicitly requests estimated SRT without a proven ASR timing receipt
- **THEN** the report and filename SHALL label it estimated and SHALL NOT claim speech alignment; export SHALL preserve its exact content hash and SHALL NOT write Master or accept a new MaterialRevision

#### Scenario: Explicit Audio Recipe ASR without a Video Master
- **WHEN** the user selects the optional local-ASR Audio Recipe and explicitly executes `stage.audio.asr@1` over its direct, same-run accepted TTS MaterialRevision
- **THEN** the Stage SHALL use only the existing executable local MLX ASR capability, revalidate exact accepted task/script/material bytes and model-use rights, and freeze real transcript/segment timing and runtime/input/output hashes in an immutable WorkflowStepAttempt
- **AND** read, Preview and automatic continuation SHALL NOT perform inference; automatic continuation stops with the ASR step pending for explicit execution, with no cloud fallback, Audio Master, new media entity or fabricated Video Master
- **AND** source bytes SHALL be at most 30 MiB, audio duration at most 600 seconds, execution timeout at most 120 seconds and the accepted output at most 256 segments; invalid or over-limit results are rejected without truncation, and a possible-dispatch unknown outcome is not automatically retried
- **AND** the user SHALL explicitly accept that exact ASR Attempt before Audio QC may compare its transcript with the signed spoken script or export verified-timing SRT; replaced/revoked inputs, runtime drift or forged/foreign/unaccepted ASR proofs fail closed

### Requirement: Creative quality readiness is truthful

For each Persona/modality the product SHALL expose `ready`, `partial` or `blocked` with exact reasons derived from creative resources, provider/model/tool/renderer readiness and quality requirements. Mock providers or fixture outputs MUST NOT satisfy real creative-quality acceptance.

#### Scenario: Chat ready but TTS missing
- **WHEN** the Persona has a valid Text recipe and executable chat model but no TTS route
- **THEN** Text may be ready while Audio is blocked with a TTS reason

### Requirement: Real-provider acceptance is required to claim out-of-box quality

Before this change is marked fully accepted, explicitly authorized real configured providers SHALL be used for bounded representative Text, Graphic and Audio journeys for both starter Personas. The acceptance record SHALL freeze provider/model/profile/runtime identities, prompt/config hashes, output artifact hashes, deterministic quality results and a fixed human rubric.

Contract/mock tests SHALL be labeled as contract evidence only. A passing real sample proves usability under the tested configuration, not universal objective quality.

#### Scenario: Only mocks were exercised
- **WHEN** all schema and workflow tests pass but no authorized real provider outputs were reviewed
- **THEN** implementation may be contract-complete but MUST NOT claim the shipped defaults produce proven good creative results
