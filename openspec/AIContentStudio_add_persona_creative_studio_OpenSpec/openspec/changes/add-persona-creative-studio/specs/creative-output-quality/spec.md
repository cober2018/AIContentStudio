## ADDED Requirements

### Requirement: Quality Profiles are versioned and media-specific

The product SHALL ship versioned Quality Profiles for technical/lifestyle Text, editorial/lifestyle Graphic and explainer/conversational Audio. A Quality Profile SHALL declare required deterministic checks, optional model-critic dimensions, blocking/warning thresholds and human-review requirements. Deterministic blockers MUST NOT be overridden by a model critic.

#### Scenario: Model critic likes content with invalid rights
- **WHEN** a critic rates a Graphic highly but a referenced MaterialRevision lacks required rights
- **THEN** the Graphic remains blocked and critic output cannot make it ready

### Requirement: Text quality is grounded and persona-aware

Text quality SHALL evaluate exact content/input hashes and include deterministic checks for required evidence/citation coverage, unsupported bounded factual elements where existing evidence mapping can prove them, structure/empty-content bounds, excessive repetition and persona-configured hype/marketing/clickbait restrictions. Optional model critique MAY score role fit, clarity, specificity and naturalness but is advisory unless the profile explicitly defines a bounded non-safety threshold.

#### Scenario: Technical article becomes stale
- **WHEN** a Text Master changes after a technical quality result
- **THEN** the prior quality result is stale and cannot be reused for the changed content

### Requirement: Graphic quality validates real rendered outputs

Graphic quality SHALL validate semantic/canvas contract, element bounds, minimum margins, supported overlap rules, text overflow/density, supported contrast/readability thresholds, required visual refs, live rights, exact rendered dimensions/MIME/hash and required cover/first-card roles. Passing plan/schema validation alone MUST NOT be described as a finished Graphic.

#### Scenario: Graphic plan exists but renderer failed
- **WHEN** a Graphic Master/plan is structurally valid but no valid render MaterialRevision exists
- **THEN** Graphic output quality remains incomplete and the product does not present the plan as finished images

### Requirement: Audio quality validates real media and voice contract

Audio quality SHALL bind to an exact accepted audio MaterialRevision and validate bytes/hash/MIME/nonzero bounded duration plus available local checks for gross clipping, excessive silence and configured loudness. It SHALL verify the exact TTS task/provider/model/voice/rate contract from provenance. Optional ASR alignment MAY compare speech with the accepted spoken script only when an executable ASR capability is explicitly invoked.

#### Scenario: TTS returns corrupt or silent output
- **WHEN** accepted provider bytes fail media/duration/silence checks
- **THEN** Audio QC blocks readiness without rewriting or deleting the historical MaterialRevision

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
