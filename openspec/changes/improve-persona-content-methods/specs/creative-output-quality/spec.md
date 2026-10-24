## ADDED Requirements

### Requirement: Persona creative review reports located artifact issues and separate outcomes
Review SHALL distinguish technical validity, content/creative quality and user acceptance of Persona style for exact artifact versions. Issues SHALL name a concrete artifact location, reason and suggested correction; uninspected dimensions SHALL remain uninspected. Graphic checks SHALL inspect actual rendered images, audio checks SHALL retain exact media/voice/ASR evidence, and video-plan checks SHALL not stand in for actual movie inspection. Layout-density measurements and model self-scores SHALL be advisory diagnostics rather than universal style acceptance.

#### Scenario: A sparse image passes technical checks
- **WHEN** an image has valid dimensions/rights but a reviewer finds its hierarchy ineffective
- **THEN** technical validity remains recorded separately, the creative issue identifies that image/location, and the work is not described as fully accepted by citing only the technical result

#### Scenario: Transcription passes without listening
- **WHEN** full-length ASR and acoustic checks pass but no listening review was performed
- **THEN** the report states the completed checks and preserves the unperformed listening boundary and any existing human-review field

### Requirement: Technology and lifestyle method acceptance uses bounded controlled comparisons
Both Personas SHALL be evaluated independently using frozen source/knowledge versions, task/platform constraints, permitted materials and actual model/voice/generation configuration. A baseline and candidate SHALL differ only in declared method/style/quality or necessary tool changes, which SHALL be recorded. Reusing an old baseline requires proof of comparability; otherwise a bounded current baseline is required. Acceptance SHALL record previously defined defects, regressions and concrete artifact evidence, followed by a new-topic transfer check. A successful sample SHALL NOT be represented as statistical or sales-performance proof.

#### Scenario: An old baseline used a different model
- **WHEN** that baseline is proposed as proof of a method's quality improvement
- **THEN** it is labeled non-equivalent and a controlled baseline is required before attributing improvement to the method

#### Scenario: The candidate only passes its own self-score
- **WHEN** no artifact-level evidence shows resolution of the defined defect
- **THEN** improvement remains unproven even if the generator rates its output highly

### Requirement: Acceptance matrix distinguishes completed outputs from external dependencies
For this improvement, each Persona SHALL have a controlled text/graphic/audio comparison, candidate actual outputs and new-topic text/graphic/audio transfer outputs; video SHALL include a baseline/candidate director-plan comparison, one complete candidate real-video sample and a new-topic director-plan check. Full new-topic video production is outside this required matrix. Missing source footage or manual web returns SHALL leave the real-video sample pending while independent engineering work proceeds. Closure SHALL require all required rows and explicit scoped style acceptance; partial completion MUST NOT trigger archive or silent default promotion.

#### Scenario: Video plans pass while a clip is missing
- **WHEN** the director plan and handoff are complete but the candidate final video lacks required footage
- **THEN** planning can pass, real-video acceptance stays pending, and no placeholder video or plan is reported as a complete sample

#### Scenario: Both roles complete controlled local delivery
- **WHEN** all required actual outputs, transfer checks, quality reviews and user style decisions are recorded
- **THEN** the change can proceed to final scoped acceptance while public publication remains outside the evidence and model/voice/product preservation is verified
