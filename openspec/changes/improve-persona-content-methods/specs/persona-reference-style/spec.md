## MODIFIED Requirements

### Requirement: Reference style observations preserve modality and evidence
The system SHALL support separate text, image, audio and video reference observations linked to existing material/source revisions. Each observation SHALL distinguish directly observed expression, inferred creative intent and unknown details, and carry a text passage, image region or audio/video time reference as applicable. It SHALL identify whether a quality is to be followed or avoided and why, without treating an example to avoid as a positive style instruction. Reference identity, personal experiences and historical claims MUST NOT become Persona facts by style extraction. Existing observations SHALL remain readable with their original revisions/hashes; audio or example-polarity extensions SHALL use compatible reads and explicit new revisions rather than rewriting history.

#### Scenario: A reference video informs the technology Persona
- **WHEN** an Agent analyzes the user's video reference
- **THEN** the resulting draft preserves evidence for narrative, screen demonstrations, graphical treatment, pacing and inspected sound, while unsupported or uninspected sound characteristics remain unknown

#### Scenario: Audio has only machine transcription evidence
- **WHEN** an audio reference was transcribed or measured but not actually listened to by the declared reviewer
- **THEN** the observation records that inspection method, and listening-only judgments remain unknown rather than being reported as directly heard

### Requirement: Style transfer validation uses a new subject
Before promoting a trial production Skill combination as the technology or lifestyle Persona default, the workflow SHALL compare baseline and selected method outputs and evaluate work on a subject not used to derive that Persona's reference style. Technical validation, AI creative review and user style acceptance SHALL be recorded separately per Persona and modality. The tested modality scope and any video-plan-only scope SHALL be explicit; results MUST NOT be generalized to untested modalities or represented as proof of commercial performance.

#### Scenario: Engineering passes but style is not accepted
- **WHEN** an output renders correctly but has no user style acceptance
- **THEN** it remains a trial and is not reported as the finalized Persona standard

#### Scenario: Lifestyle transfer fails on a new subject
- **WHEN** a lifestyle method matches its reference example but introduces generic or invented experiences on a new topic
- **THEN** transfer is not accepted and the method is not promoted merely because the reference-topic output succeeded

## ADDED Requirements

### Requirement: Persona references are selected through inspectable existing resources
The normal Persona reference flow SHALL let users select and preview authorized existing sources/materials or enter the existing import flow, identify the relevant passage/region/time and record why it is preferred or avoided. The application SHALL resolve exact resource identities and hashes without requiring manual ID/hash entry in the normal path. Model-use and public-use permissions SHALL remain independent, and missing accepted references SHALL be shown as a provisional style rather than fabricated user approval.

#### Scenario: Select a previously accepted card as a reference
- **WHEN** a user selects an existing card revision and marks its information hierarchy as preferred
- **THEN** the saved reference identifies that exact artifact and region, preserves its permissions, and does not automatically authorize generation or publication
