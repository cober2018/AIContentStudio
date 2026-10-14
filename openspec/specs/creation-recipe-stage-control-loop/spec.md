# creation-recipe-stage-control-loop Specification

## Purpose
Keep account-aware Variant Stage adaptation aligned with the existing production contract and authoritative Workflow state.
## Requirements
### Requirement: Exact account-aware stage adaptation without new Workflow truth

The existing Workflow and `stage.variant.adapt@1` SHALL remain the only process and modern channel-adaptation plugin truths, and SHALL accept a resolved target context including exact Account/form/Series binding when applicable.

#### Scenario: One accepted source reaches multiple account targets
- **WHEN** an accepted Master is chosen for several valid Series targets
- **THEN** each needed Variant adaptation is resolved using an exact target account identity and applicable style/rights context
- **AND** each execution records its pinned resolution, method, prompt and output hashes

#### Scenario: No invented variant plugin
- **WHEN** the implementation registers or calls a channel Variant Stage
- **THEN** it reuses `stage.variant.adapt@1`
- **AND** no `stage.variant.propose` or duplicate Recipe/Variant truth is introduced

### Requirement: Creation Recipe is the user-facing Workflow truth

The product SHALL present the selected effective immutable Workflow Definition revision as a Creation Recipe made of understandable stages. It MUST NOT create a second recipe persistence root or duplicate Workflow currentness. Every stage maps to one exact Workflow node/plugin/version and derives execution state from existing Run/Step/Attempt truth.

#### Scenario: Open a normal production unit
- **WHEN** a user opens an active Content Unit
- **THEN** Production shows the effective Creation Recipe, its inherited/default/project source and actionable stages without requiring the raw graph

### Requirement: Stage controls are typed and executor-backed

A stage shown in the normal Creation Recipe UI SHALL have a versioned Stage Contract declaring exactly which fields are tunable, how they are rendered, what inputs/outputs are expected and whether preview/override/candidates/human acceptance are supported. A visible tunable control MUST affect the server-resolved execution contract; unsupported or unconsumed fields MUST be rejected.

Contract activation SHALL use distinct new plugin versions explicitly pinned with the contract identity in newly saved definitions. Registering Stage controls MUST NOT reinterpret any existing pinned plugin version, historical definition or rerun.

#### Scenario: Change a stage prompt
- **WHEN** the user edits a declared stage instruction field
- **THEN** the effective-config/prompt hash changes and the subsequent attempt receipt proves that exact instruction was used

#### Scenario: Cosmetic unsupported field
- **WHEN** a client submits a field not declared or consumed by the Stage Contract
- **THEN** validation fails instead of saving a setting that execution ignores

### Requirement: Effective Stage preview and execution share one resolver

The server SHALL deterministically resolve the saved node, allowed temporary override, exact method/skill/capability revision, model profile/provider/model, pinned Identity/Brief/Creative Intent/Fact Boundary context and declared upstream outputs into one canonical ResolvedStageExecution. Preview MUST make no external call. Actual execution MUST use the same resolution identity or fail stale/conflict.

Explicit user run/rerun SHALL require the preview's `expected_resolution_hash` plus an invocation idempotency key. Automatic successors SHALL use a server-prepared pure resolution after upstream acceptance commits, record/expose that automatic request and pass its exact expected hash to the same invocation gate; it MUST NOT be falsely labeled user-inspected. The identity SHALL bind Workflow/node/plugin/contract, overrides, context/upstream/method and applicable routing-plan/adapter/runtime identities. Re-resolution drift or missing expected identity MUST fail before external invocation. The original Attempt claim, frozen receipt and bounded input snapshot MUST commit before dispatch; identical retries reuse/reconcile that claim, conflicting requests fail and possible-dispatch/unknown outcomes MUST NOT trigger another invocation.

#### Scenario: Model route changes after preview
- **WHEN** the selected model/profile becomes unavailable or resolves differently before run
- **THEN** execution fails visibly instead of silently using another model

#### Scenario: Lost execution response
- **WHEN** the client retries the same invocation key after the original claim may have dispatched
- **THEN** the server returns or reconciles that exact claimed attempt and does not make a second model/Provider/Agent call

### Requirement: Effective prompt is inspectable in layers

For a prompt-bearing stage, preview SHALL expose bounded safe prompt layers for method/base instruction, Identity, stage instruction, Brief, Creative Intent, evidence constraints, upstream output and current-task override, plus an effective prompt hash. Secrets and raw credential-bearing diagnostics MUST be absent.

#### Scenario: User reviews what AI will receive
- **WHEN** a stage is ready for model execution
- **THEN** the user can inspect the effective instruction layers and exact model/method identity before running

### Requirement: Run-only tuning is frozen but non-authoritative

The user MAY apply a temporary stage override only to Stage Contract tunable fields for one run/rerun. The override MUST be frozen in the resulting attempt receipt and MUST NOT mutate the saved Workflow Definition or scoped defaults. Plugin/dependency/gate/rights/approval/side-effect fields are not overridable.

#### Scenario: Try a different tone once
- **WHEN** the user changes only the stage instruction for a rerun
- **THEN** a new attempt freezes the override while later ordinary runs continue using the saved Recipe until the user explicitly promotes it

### Requirement: Stage attempts freeze exact execution receipts

Stage-contract WorkflowStepAttempt rows SHALL freeze bounded input snapshot and execution receipt including Workflow/node/plugin/config/method/model/prompt/upstream/output-contract hashes. Failed attempts SHALL also retain these snapshots. Historical legacy attempts without them remain valid/unknown.

The receipt SHALL also bind the invocation fingerprint, expected preview hash and applicable routing-plan/adapter/runtime identities. Receipt/input are immutable from the pre-dispatch claim; the claimed attempt can seal its outcome/output once, but retries MUST NOT replace a historical receipt or sealed output.

#### Scenario: Compare two iterations
- **WHEN** two attempts used different temporary instructions
- **THEN** each historical attempt can explain its exact effective configuration and output without reading the current mutable step state

### Requirement: Project-native Master stages produce proposals, not Masters

The modern Content Master Creation Recipe SHALL use a project-native stage executor rather than silently changing legacy Draft-oriented generation semantics. A Master proposal stage SHALL return one or more bounded canonical modality-specific proposal candidates and MUST NOT persist ContentMasterRevision automatically.

Successful proposal execution SHALL remain distinct from required human review readiness. An unresolved required acceptance MUST block Run completion and dependencies requiring accepted content. Such dependencies SHALL consume only the exact accepted entity/revision/hash and decision association, never raw proposals merely because an attempt succeeded. Accepted-with-edits input hash changes SHALL propagate downstream stale through existing mechanisms.

After acceptance commits, the existing runtime SHALL automatically execute the next dependency-ready Stage using deterministic visual-order tie-breaking, stopping at the next required human review or failure/stale/unknown/unavailable/safety blocker. Automatic continuation MUST NOT auto-adopt proposals, bind accepted media, dispatch professional tools, freeze/approve Candidates or publish. Acceptance replay/recovery SHALL reuse original Run/Step invocation claims without duplicating calls.

#### Scenario: Generate three article drafts
- **WHEN** the Text stage is configured for three candidates
- **THEN** the attempt contains three hashed proposals and current Master remains unchanged until one is explicitly adopted

#### Scenario: Downstream needs accepted content
- **WHEN** a proposal attempt succeeds but required adoption is unresolved
- **THEN** its accepted-content dependency and overall Run completion remain blocked until the exact acceptance decision exists

#### Scenario: Accept and automatically continue
- **WHEN** an authorized acceptance commits and the next Stage has valid accepted inputs and no blocker
- **THEN** the runtime prepares/records its exact request, executes it once and stops again if its new result requires human review, without implicitly adopting that result

### Requirement: Explicit stage adoption creates authoritative content

An authorized user MAY accept one exact current stage proposal, optionally with bounded edits. Adoption SHALL validate exact Run/Attempt/candidate hashes and current project context, then create the normal authoritative Master/Variant/Material result through the existing domain service. Proposal review MUST NOT freeze Candidate, Approval or Delivery.

The trusted adoption transaction SHALL revalidate relevant revision/context heads at commit and atomically persist the authoritative result/refs, required accepted-output association and acceptance feedback. Any failure MUST leave no partial adoption. Its idempotency fingerprint SHALL bind the exact proposal/receipt and final canonical payload/refs/decision/expected heads; an identical committed retry returns the original result/association/feedback without repeating writes or failing merely because that original save advanced currentness. A conflicting key fails. Output association MUST verify the original proposal receipt against the accepted provenance and decision without inserting a later entity ID into immutable proposal output.

#### Scenario: Accept with edits
- **WHEN** the user edits an AI proposal before acceptance
- **THEN** the resulting Master revision records both the original proposal hash and final accepted hash plus exact stage provenance

#### Scenario: Association or feedback fails
- **WHEN** result validation succeeds but its required output association or feedback cannot be persisted
- **THEN** the entire adoption rolls back and no authoritative revision or accepted decision is partially committed

#### Scenario: Retry an already committed adoption
- **WHEN** an authorized identical request is retried after the original adoption advanced the Master head
- **THEN** it returns the original revision, association and feedback once while a changed final payload under the same key conflicts

### Requirement: Stage feedback is append-only evidence

Every explicit stage accept/accept-with-edits/reject/rerun decision SHALL record a bounded append-only ProjectEvent bound to exact Workflow/Run/Attempt/config/prompt/output hashes. Feedback MUST NOT change Workflow, Capability Memory, Identity, facts or defaults by itself.

#### Scenario: Reject a result
- **WHEN** the user rejects a proposal and records a short reason
- **THEN** the feedback remains tied to that exact attempt while the saved Recipe remains unchanged

### Requirement: Successful tuning can be promoted explicitly

The product SHALL offer a diff-based “Save what worked” action for accepted attempts that used temporary tuning. The user MAY explicitly create a new Project Workflow Override revision, a portable scoped default Workflow version, or a Capability Memory candidate. No promotion silently rebinds existing Units/Runs.

Deterministic Workflow promotion SHALL use an actual explicit Stage tunable-field diff. Content edits alone SHALL remain feedback evidence; without a config diff the user must explicitly author/select an allowed instruction/method change. The system MUST NOT infer or silently fabricate a config patch from edits to accepted content.

#### Scenario: Keep the improved Project prompt
- **WHEN** a run-only instruction produces an accepted result and the user chooses Save to Project
- **THEN** the server shows/applies the allowlisted node patch and creates a new immutable Project Workflow revision through existing CAS rules

#### Scenario: Edit content without changing configuration
- **WHEN** the user only corrects proposal text and accepts it with no tunable-field override
- **THEN** the correction is recorded as content feedback and no deterministic Recipe patch is inferred; Workflow promotion requires an explicit instruction/method diff

### Requirement: Workflow improvement uses Capability Memory, not hidden workflow mutation

Reusable stage improvements SHALL be represented as non-authoritative Capability Memory `recipe`/`prompt_skill` candidates with frozen workflow/node/config/feedback provenance. Applying one requires explicit selection and creates a new Workflow revision. Usage/popularity cannot auto-apply it.

#### Scenario: Reuse a successful video-director method
- **WHEN** a saved recipe is applicable to another Video Unit
- **THEN** it is offered with exact scope/revision and only affects that Unit after the user explicitly applies or uses it

### Requirement: Text, Graphic and Video share the same control loop

Text, Graphic and Video Creation Recipes SHALL use the same stage-control/preview/run/review/feedback/promotion model while delegating authoritative outputs to their existing Master/Material/Variant/CreativeExecution domains.

#### Scenario: Professional video stage
- **WHEN** a Video recipe reaches professional execution
- **THEN** the stage prepares/projects existing CreativeExecution state and does not create a second external-execution truth or auto-dispatch a professional tool

### Requirement: Master proposal receipts retain the normalized validated candidates

The modern `stage.master.propose@1` successful LLMRun SHALL retain only the service-normalized, validated candidate projection and safe server provenance. Provider envelope/candidate diagnostics or extra local-path fields ignored by candidate validation MUST NOT enter that receipt. Original response evidence SHALL be hash-only; a rejected response SHALL retain only the existing bounded failure projection. Historical receipts and legacy generation recorder behavior SHALL remain unchanged.

#### Scenario: Valid Master proposal carries unaccepted diagnostic fields
- **WHEN** a provider returns valid Master candidates plus unrelated envelope or candidate diagnostics containing local file paths
- **THEN** candidate validation and sealing SHALL use the normalized Master payload, exact refs and service-built candidate hashes, and the successful LLMRun SHALL store that validated projection without the unrelated fields
- **AND** the original response hash remains traceable, no Master is accepted automatically, and existing citation resolution and modality contracts remain intact

### Requirement: Modern Variant Stage receipts retain only validated outputs

The model-assisted `stage.variant.adapt@1` path SHALL validate its canonical Variant payload before recording a successful LLMRun. It SHALL reuse the validated Stage recorder: successful receipts retain canonical accepted output and server-built provenance with allowlisted numeric usage; rejected responses retain a bounded failure code and response hash, not raw output, parsed rejected data or arbitrary provider diagnostics. This SHALL NOT change legacy recorder semantics or automatically accept the Variant.

#### Scenario: Provider returns valid payload with unaccepted diagnostics
- **WHEN** a model-assisted Variant Stage returns a valid payload but includes unrelated raw reasoning or diagnostic usage
- **THEN** the LLMRun SHALL retain only the validated canonical payload, safe server provenance and numeric usage, and the Variant SHALL still require explicit acceptance

#### Scenario: Provider response fails Variant validation
- **WHEN** a received response fails canonical Variant validation
- **THEN** the attempt SHALL be a confirmed validation failure with hash-only response evidence and no rejected output retained as successful history

### Requirement: Normal-mode configuration and Audio guidance match actual authority

Creative configuration controls and save handlers SHALL honor the current user role and archived ancestors, not only the selected identity's own status. Readonly projection and Preview MAY remain available without implying mutation authority. Audio created from an accepted Text Master SHALL guide the user to explicit MaterialRevision acceptance and Audio QC; it SHALL NOT require an audio binding or save operation unsupported by Text Master.

#### Scenario: Viewer or archived ancestor opens creative configuration
- **WHEN** a viewer opens an owned identity, or an active identity belongs to an archived Brand, Persona or Account
- **THEN** creative edit and save controls SHALL be readonly and their handlers SHALL not submit an identity mutation; existing local drafts SHALL not be silently discarded

#### Scenario: Text Recipe accepts TTS audio
- **WHEN** the user explicitly accepts the Audio Recipe's TTS result as a MaterialRevision
- **THEN** normal mode SHALL guide the user to the Audio quality stage and the accepted audio material rather than instruct them to bind audio in the Text editor or save a Text Master
- **AND** the accepted Text Master SHALL remain unchanged; later use in a Video Master remains a separate explicit reference/save action

#### Scenario: Native TTS profile exists without a chat profile
- **WHEN** an authorized native TTS profile is present in the existing capability-routing inventory but has no registered chat profile
- **THEN** the normal Stage controls SHALL expose its exact profile ID and capability-specific configured/executable state, provider and model from that inventory without copying credentials or connection URLs
- **AND** a fallback chat row without native-capability metadata SHALL not crash the page or become a selectable media route; selection does not prove verification and execution still requires the exact backend Preview/currentness gates

### Requirement: Creation Recipe resolves Persona creative defaults

Effective Stage resolution SHALL consume the Unit's frozen IdentitySnapshot creative profile and derive exact Studio Skill, Style Preset, Quality Profile and model policy before applying saved Project Stage config and run-only overrides according to the documented precedence. Preview and attempt receipt SHALL freeze those exact identities/hashes.

#### Scenario: Same recipe topology under two Personas
- **WHEN** two Units use the same stage topology but different Persona creative profiles
- **THEN** preview/execution use each Persona's exact methods/styles while preserving the same Workflow process truth

#### Scenario: Explicit Chat Stage binding takes precedence without automatic substitution
- **WHEN** a saved Project Stage or run-only adjustment explicitly selects one registered chat model profile
- **THEN** the higher-scope selection SHALL override the Persona model default as one exact provider/model/profile binding, and Preview and Attempt SHALL preserve the original Persona binding/chain plus the selected binding and source scope
- **AND** an unavailable, mismatched or changed selected binding SHALL block execution without falling back to the Persona chain or discovering another Provider; without a Stage selection, Custom and Custom Composition retain their declared pin/chain rules

### Requirement: Deterministic Stages consume only their declared parameters

Deterministic layout, rendering and QC Stages SHALL consume only typed values declared in and validated by their exact Stage Contract. An ordered Capability Memory method may contribute to such a Stage only through a matching, validated `workflow.stage.recipe.v1` `config_patch`; the patch order and exact source hashes SHALL be frozen into the Effective Preview and Attempt receipt, with a run override applied last. Free-form method text, unsupported fields and hidden provider calls SHALL never alter deterministic output. Model-assisted transformation SHALL use a visible explicit AI Stage instead.

#### Scenario: Graphic composition uses an exact parameter recipe
- **WHEN** a Graphic composition Stage selects a built-in layout Tool and a saved Capability Memory recipe for the same plugin/version/stage schema
- **THEN** the recipe's validated `config_patch` is applied only to declared tunable parameters, never method/output/package/model/provider selectors; its exact hashes are visible and saved Project fields then Run overrides take precedence before the final deterministic composer consumes the resulting effective config

#### Scenario: Foreign or free-form method cannot alter deterministic layout
- **WHEN** a selected Capability Memory revision is free-form, targets another plugin/stage schema or contains an unsupported config field
- **THEN** the deterministic Stage blocks before composition and does not discover a provider, interpret the method as layout instructions or silently ignore the mismatch

### Requirement: Intermediate creative stages use accepted attempt outputs

Creation Recipe SHALL support `stage.creative.method@1` for bounded intermediate artifacts such as research brief, angles, outline, visual direction, card plan, spoken adaptation, voice direction and video shot plan. Intermediate acceptance remains WorkflowStepAttempt truth and MUST NOT create a synthetic Master/Material/Variant entity.

#### Scenario: Accept an outline
- **WHEN** the user accepts one exact outline candidate
- **THEN** downstream draft generation may consume its exact attempt/candidate hash while no ContentMasterRevision is created merely for the outline

#### Scenario: Concrete intermediate output schema
- **WHEN** the effective stage requests `research.brief.v1` or another supported intermediate schema
- **THEN** Preview and execution MUST use that exact schema as the provider response envelope, with the exact candidate count and reference shape
- **AND** the provider-visible response schema MUST explicitly close the envelope to `schema` and `candidates`; count controls are not extra response fields, and undeclared fields are rejected rather than silently removed
- **AND** a received response rejected by output validation is a confirmed failed attempt, not an unknown transport outcome; it creates no accepted result or Master

### Requirement: Stage Handoff is thin exact lineage

Downstream Stage input SHALL identify accepted upstream run/attempt/node/output schema/hash plus concise summary and exact business refs needed by the Stage Contract. It MUST NOT implicitly re-derive or copy complete unrelated run histories into every prompt.

#### Scenario: Draft consumes accepted outline
- **WHEN** the draft stage follows research/angle/outline stages
- **THEN** its receipt identifies the exact accepted upstream outputs and hashes rather than treating the current mutable WorkflowStep output as unversioned context

#### Scenario: Accepted intermediate result references material that is no longer available
- **WHEN** an accepted intermediate candidate references an exact MaterialRevision whose parent Material is archived, revision is unavailable, bytes/hash have changed or materialized derived ancestry no longer supports its live model-use rights
- **THEN** downstream Preview and execution SHALL block before exposing selected content or dispatching a provider, using the existing shared ancestry-rights and byte-integrity checks
- **AND** the prior accepted Attempt and its hashes SHALL remain unchanged; acceptance is not a permanent grant of model-use rights

### Requirement: Persona starter recipes are complete normal-mode journeys

The two starter Personas SHALL provide normal-mode default recipes for Text and Graphic plus one-click Audio output flow, and Video planning/handoff. A supported user SHALL be able to complete those journeys without opening raw Workflow JSON/canvas or writing a Prompt from scratch.

#### Scenario: New AI technology Persona project
- **WHEN** a user chooses the starter AI technology Persona and creates a Text Unit
- **THEN** its default recipe offers research → angle → outline → draft → quality/refine → final acceptance using shipped built-in methods

#### Scenario: Graphic Recipe prepares missing exact visual materials
- **WHEN** a Graphic visual/card-plan stage requires a photo or illustration not yet present in Project Shared Assets
- **THEN** normal Recipe mode SHALL expose the existing project material upload/reference and explicit generation/acceptance controls without requiring Workflow JSON authoring
- **AND** preparation SHALL NOT automatically call a provider, grant rights or mutate a Master/accepted plan; after assets change, the user SHALL re-preview and explicitly generate/accept a new exact plan rather than silently replacing historical references

#### Scenario: Graphic planning sees the selected preset's executable visual constraints
- **WHEN** a new Visual Direction or Card Plan Preview resolves an exact Graphic Style Preset
- **THEN** its provider-visible output contract SHALL expose that preset's exact reference/hash, role-aware cover/per-card image requirements and declared diagram fallback, using the same rules as the deterministic composer
- **AND** warm-magazine SHALL require an exact supplied image reference on the cover and permit text-only body cards; documentary-photo SHALL require an image on every card; missing required images remain incomplete rather than being replaced by invented assets or another preset and described as composition-ready
- **AND** this projection SHALL be bound to the Prompt/resolution hashes and passed unchanged to the planning request; it SHALL NOT call a provider, mutate historical requests/plans, waive the final composition gate or constrain unrelated Text/Audio/Video schemas

#### Scenario: Default Text proposal needs no handwritten document grammar
- **WHEN** a new Text Master proposal Attempt is resolved, including one from an already saved default Recipe
- **THEN** Preview and the exact execution request SHALL include the bounded `text.master.v2` payload and `studio.text.document.v1` block/inline/citation/reference shapes and the requested candidate count
- **AND** the server-owned contract preserves every currently supported Text block kind and exact reference validation; the user need not write JSON grammar in the Stage instruction
- **AND** historical resolved requests, Attempts and receipts remain immutable, and Graphic/Video output contracts are unchanged

#### Scenario: Service resolves proposed citation selections without trusting model hashes
- **WHEN** a Text proposal supplies bounded citation selections with stable citation/block/list-item IDs, exact selected quote and a supplied FactPackItem ID
- **THEN** the service SHALL require that quote to occur exactly once in the designated eligible text target, derive Unicode-code-point offsets and its UTF-8 SHA256, and copy the snapshot checksum from the frozen supplied evidence catalog
- **AND** only the resulting canonical citations and matching EvidenceRefs may be sealed after all existing validation; the selector hash and deterministic resolution version remain bound to the proposal hash
- **AND** absent, ambiguous, foreign, mixed or invalid selections fail closed; the service MUST NOT repair an invalid canonical citation hash, waive semantic checks or accept the Master automatically

### Requirement: Audio output reuses existing media truth

Creation Recipe MAY add spoken-adaptation/voice-direction/TTS/QC stages to an accepted Text/Video source. TTS dispatch/acceptance remains ProviderGenerationTask/MaterialRevision truth and SHALL NOT introduce an Audio Master or duplicate media result table.

#### Scenario: Generate an audio version of an article
- **WHEN** the user runs the Persona's Audio output flow from an accepted Text Master
- **THEN** the final authoritative file is an accepted MaterialRevision with exact TTS/QC provenance

#### Scenario: Native TTS consumes explicit voice and rate without reading instructions aloud
- **WHEN** `media.generate@4` resolves the exact accepted spoken adaptation and voice-direction attempts
- **THEN** it SHALL freeze their hashes and the selected Persona Audio profile, preserve the accepted spoken script, and map explicit `voice`/`rate` to native `voice_id`/`rate` parameters
- **AND** the current MiniMax CLI adapter SHALL consume those parameters as `--voice`/`--speed`; a voice-style description is not a provider voice ID, and missing IDs or unsupported executors block rather than guess
- **AND** this additive Stage MAY synthesize at most 9999 characters from that accepted script with one bounded TTS result; legacy raw-prompt stages retain their 2000-character limit
- **AND** `studio.audio.stage.tts.v1` SHALL bind workflow/run/node, exact accepted spoken and direction Attempts/output hashes, config hash, script hash, voice/rate, rate origin/difference and input hash; client-supplied raw text SHALL NOT replace the accepted source

#### Scenario: Audio planning and native speech have distinct visible bindings
- **WHEN** spoken adaptation or voice direction uses a chat Stage before native TTS
- **THEN** Preview and its Attempt SHALL expose the planning chat binding separately from the frozen Persona Audio TTS policy; a TTS pin SHALL NOT be treated as a chat model
- **AND** the native TTS Stage SHALL enforce the Persona single exact pin or declared ordered chain, and the planning chat receipt SHALL NOT prove TTS voice/model/quality
- **AND** the signed successful result and accepted Material provenance SHALL include `studio.audio.tts-applied.v1`; historical parameterless tasks and `media.generate@2/@3` contracts remain unchanged

#### Scenario: Native Audio Stage consumes the frozen bounded wait
- **WHEN** the user sets `timeout_seconds` for `media.generate@4` within the existing routing range of 1–300 seconds and the selected route's configured limit
- **THEN** the Stage controls and server validation SHALL accept and freeze that exact value, and the native generation request SHALL consume it without a separate 25-second hard cap
- **AND** omitting the control retains the existing 25-second default; a smaller provider/profile policy still blocks an excessive request before dispatch rather than raising the policy or reducing the value silently
- **AND** changing the value after Preview invalidates the frozen input/config hashes; historical receipts and `media.generate@2/@3` contracts remain unchanged, and Unknown results never trigger replay

#### Scenario: Audio QC uses an accepted exact file, not an invented Master
- **WHEN** `stage.audio.qc@1` follows an explicitly accepted TTS result
- **THEN** its existing WorkflowStepAttempt SHALL record the exact MaterialRevision/task/script/profile and deterministic QC report hashes, without creating a ContentMasterCheckRun for a fictitious Audio Master
- **AND** accepting or reusing that QC SHALL revalidate the signed task and live media/hash/rights; ASR remains separately explicit and never runs on Preview

#### Scenario: Optional manual local ASR is a distinct accepted Stage handoff
- **WHEN** the user chooses the separately named Audio Recipe with local ASR alignment
- **THEN** the existing spoken-adaptation/voice-direction/TTS flow SHALL remain unchanged, while an optional `stage.audio.asr@1` consumes its direct accepted audio and stops automatic continuation before inference
- **AND** an explicitly executed and accepted ASR output SHALL use the existing generic Attempt adoption truth and exact same-run/material/task/script/runtime hashes; QC consumes that accepted handoff without requesting client-authored transcript or running ASR again
- **AND** existing default Audio recipes, historical Video ASR receipts and their explicit QC controls remain compatible and are not silently rewritten

#### Scenario: Explicit native TTS Stage binding is not automatic fallback
- **WHEN** a saved Project Stage or run-only adjustment explicitly selects one registered native TTS profile under the existing resolution precedence
- **THEN** Preview and the Attempt SHALL freeze its exact provider/model/profile plus the source scope and before/after Persona binding difference
- **AND** that explicit selection SHALL use exact-pin validation with no undeclared provider substitution; disabled or changed bindings block, and absent an explicit selection the Persona Custom pin or declared chain remains authoritative

#### Scenario: Director method prepares the existing professional package
- **WHEN** `stage.professional.prepare@2` selects `studio.video.director-package@1`
- **THEN** the exact method instructions and user constraints SHALL enter the frozen `director.video.v1` package, and an explicit aspect ratio SHALL match the saved Video Master rather than silently transforming it
- **AND** it SHALL not call a chat model or dispatch the executor; the old `stage.professional.prepare@1` contract remains unchanged
- **AND** the Director Skill's user-configurable instruction bound SHALL match the Stage's 2000-character bound; longer built-in method documentation may be transferred only through separately bounded package constraints without silent truncation

#### Scenario: Explicit Director aspect matches the canonical saved ratio
- **WHEN** a Director Stage selects a supported UI ratio such as `9:16` and the saved Video Master declares canonical `[9, 16]`
- **THEN** the server SHALL compare the exact numeric ratio values and allow the matching selection without rewriting the Master, package content or historic Stage receipts
- **AND** a different supported ratio such as `16:9` SHALL remain blocked before package creation or execution dispatch; string UI representation SHALL NOT cause a matching ratio to be reported as different
