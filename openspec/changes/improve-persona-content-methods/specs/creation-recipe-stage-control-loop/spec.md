## ADDED Requirements

### Requirement: Persona modalities plan from shared confirmed content with distinct outputs
Persona planning SHALL expose the intended audience/question, core angle, selected factual and professional/style context, target form/platform and unresolved gaps through the existing Brief and accepted intermediate outputs. Each requested modality SHALL have an appropriate plan: text structure, graphic page purposes and visual structures, audio spoken adaptation, or video shot purposes/continuity/sound. Exact accepted input references SHALL remain inspectable. Audio SHALL continue to derive from an accepted source into MaterialRevision rather than a new Audio Master. Unrequested modalities SHALL NOT be generated merely to complete a bundle.

#### Scenario: Derive graphic and audio versions from an accepted article
- **WHEN** a user requests those two forms using the same accepted source
- **THEN** graphic planning specifies visual explanations and page purposes, audio planning specifies suitable spoken expression, both preserve the selected evidence, and neither is automatically accepted or publicly delivered

#### Scenario: A style example contains an unverified numerical assertion
- **WHEN** that example is included as selected style context
- **THEN** its assertion does not enter the verified factual boundary and the stage preserves its style-only purpose and exact authorized excerpt

### Requirement: Located creative feedback preserves exact targets and bounded rework
Stage feedback SHALL support exact target revision/hash and a bounded text passage, graphic page/element or audio/video time locator. Feedback on a stale or invalid target SHALL not be silently applied to a new revision. Rework SHALL preserve unaffected content and independent branches where supported; where a tool requires a larger regeneration it SHALL show the actual scope before execution. New results SHALL retain the original history and invalidate affected downstream checks/outputs through existing dependency rules.

#### Scenario: Revise the second card only
- **WHEN** a user targets an accepted second-card revision with a density complaint
- **THEN** the system locates that card, records the intended change, explains any necessary larger render scope and creates a new reviewed result without automatically regenerating independent audio or changing the accepted old version

#### Scenario: Feedback targets an old audio segment
- **WHEN** the current audio hash differs from the feedback target
- **THEN** the feedback remains attached to its old segment and the user is asked to relocate or explicitly reuse it rather than editing an unrelated time range

### Requirement: Creative improvements remain work-scoped until explicitly promoted
The normal feedback action SHALL default to the current work. A reusable suggestion SHALL expose its supporting exact feedback/output references, proposed instruction or tunable-field difference and existing Persona/Series plus modality scope. Applying it SHALL use the existing explicit promotion and revision mechanisms. Content edits alone MUST NOT be interpreted as an executable configuration patch, factual confirmation or model-setting change.

#### Scenario: A user prefers less introductory text in one image
- **WHEN** the user accepts the local revision without selecting a reusable rule
- **THEN** the revision and feedback are saved for that work and other works, roles and defaults remain unchanged

### Requirement: Shot plans surface material needs through the platform
A persona video shot plan SHALL list, per shot, each missing material as a structured requirement with slot, purpose, acceptable sources (user upload, platform image generation, website video handoff, real shooting) and a platform-authored description, instead of only free-text unknowns. Descriptions, any generated prompt, generation information, rights and content hash MUST be retained with the resulting MaterialRevision, and an unfilled slot MUST stop the affected shot visibly without inventing material identifiers or silently changing the layout. Resolve remains the master edit and After Effects is requested only for explicitly declared compositions.

#### Scenario: A shot has no usable material
- **WHEN** an accepted shot plan contains a shot whose subject has no authorized material
- **THEN** the plan exposes a structured requirement for that shot and the user can fill it through an existing platform material path, with each supplied item keeping its origin, prompt, rights and hash

#### Scenario: A graphic cover slot has no authorized photograph
- **WHEN** an accepted visual plan requires a cover photograph and none is registered
- **THEN** the flow stops at that slot with the requirement stated and does not replace it with a different cover type
