## ADDED Requirements

### Requirement: Completion respects all existing values and protected intent
The system SHALL generate suggestions only for unfilled eligible fields using any substantively filled information and permitted evidence, without requiring all creative intent fields. It MUST preserve filled values, explicit skips, zero and false, and MUST exclude the creative intent block from bulk writes.

#### Scenario: User starts with a scene and benefit
- **WHEN** a user fills the scene and benefit but leaves intent incomplete
- **THEN** AI proposes remaining eligible blank fields using those inputs and leaves every filled field and the intent block unchanged

#### Scenario: Conflicting or empty basis
- **WHEN** the supplied inputs conflict or contain no substantive information
- **THEN** the system explains the specific conflict or asks for a minimal basis rather than silently choosing or fabricating a product

### Requirement: Review is explicit per field
The system SHALL present proposed values, source or missing-data notes, edit, polish, retry and skip controls in a navigable per-field review. Accepted values enter the existing draft and SHALL require the normal Brief or Master save.

#### Scenario: Manual revision of one suggestion
- **WHEN** a user edits a proposed purchase reason then requests polish
- **THEN** the new polish uses the edited value, other fields remain unchanged, and no content revision is saved without the existing save action

### Requirement: Floating assistance preserves target identity
The shared floating assistant SHALL display and lock the focused registered field or selected text by stable identity across pointer focus changes. Bulk protection SHALL NOT prevent an explicitly requested polish of a specific intent field.

#### Scenario: Focus moves into the assistant
- **WHEN** the user focuses a shot prompt then clicks the floating polish control
- **THEN** only that shot's captured prompt is eligible for the proposed change

#### Scenario: Content changes while waiting
- **WHEN** a target, source context, unit, user or text selection changes before adoption
- **THEN** the response cannot overwrite the changed target and the user sees a clear stale-result explanation

### Requirement: Suggestions preserve factual and production boundaries
The system MUST validate structured suggestions against known field types, allowed choices and accessible source references. It SHALL keep unsupported facts unknown, omit private economics from creative generation, and preserve image confirmation, media review and permission actions.

#### Scenario: Only a product photo exists
- **WHEN** AI is asked to fill specifications, price and shot planning without measurements or pricing evidence
- **THEN** it can suggest creative scenes but marks unsupported facts as requiring data and cannot manufacture proof or confirmed imagery

#### Scenario: A video prompt has no approved image
- **WHEN** a shot lacks its exact confirmed reference image
- **THEN** assistance can propose preproduction descriptions but does not create or confirm an executable image-to-video prompt package

### Requirement: Feedback is attributable and supports local revision
The system SHALL retain owner-scoped suggestion attempts, model/prompt versions, explicit feedback and adoption state. Feedback on a field SHALL support regenerating that field without modifying unrelated filled fields. It MUST distinguish user edits, adoption intent and actual saved content from satisfaction ratings.

#### Scenario: User asks for a concrete scene
- **WHEN** the user marks a suggestion too vague and requests a specific use scenario
- **THEN** a new attributable attempt follows that feedback while the earlier output remains available for comparison

#### Scenario: A review session is reopened
- **WHEN** the same authorized user resumes a saved assistance session
- **THEN** pending suggestions and explicit feedback are restored, actual content baselines are checked, and unsaved adopted text is not represented as committed content

### Requirement: Reusable preferences require explicit promotion and use
The system SHALL reuse existing scoped Capability Memory candidates and revision selection for explicitly requested reusable preferences. Feedback alone MUST NOT change Skills, Persona profiles, Workflow defaults or model parameters.

#### Scenario: User wants a rule reused
- **WHEN** a user explicitly chooses to retain a wording rule for later
- **THEN** the rule is reviewed with its project or explicitly selected scope, saved as a candidate, and used only through explicit version selection or separately confirmed configuration

#### Scenario: A revision is adopted without a reusable rule
- **WHEN** the user adopts or manually edits a suggestion without requesting persistent preference capture
- **THEN** only that assistance session and draft are affected and no global style change is inferred

### Requirement: Shared endpoints enforce ownership and safe recovery
Generation, retrieval, feedback and adoption receipts SHALL validate owner and applicable project/unit access independently of client field metadata. Retry SHALL preserve a request identity and attempts, validate output before use, and never turn an unknown timeout into a duplicate hidden generation.

#### Scenario: A different user requests a session
- **WHEN** a caller requests another user's form assistance session or references an inaccessible project
- **THEN** no session content is disclosed or modified

### Requirement: Product category and presentation style are independent selections
The system SHALL distinguish general commercial methods, category-specific methods, versioned presentation style profiles, current product facts and current-task instructions. It SHALL allow multiple styles per category and explicitly applicable cross-category styles, reusing Capability artifacts and existing stage controls rather than duplicating Persona identity.

#### Scenario: Two styles for the same sofa category
- **WHEN** a user selects an outdoor-relaxed or home-warm presentation for an inflatable-sofa project
- **THEN** the confirmed style changes the selected expressive methods while product facts, source evidence and Persona identity remain unchanged

#### Scenario: A stage method is disabled
- **WHEN** a user disables a method from the chosen style configuration
- **THEN** neither category defaults nor general-method discovery silently reactivate it, and generation records the exact remaining selected versions

### Requirement: Feedback distinguishes correction type from reuse applicability
Feedback SHALL identify both the correction target and explicitly selected reuse applicability. Category/style applicability MUST remain separate from ownership scope. The default SHALL remain current-task feedback; broader category, style or general-method reuse SHALL require explicit candidate creation and later selection. Product facts MUST NOT become reusable style assertions.

#### Scenario: A product dimension is corrected
- **WHEN** a user reports that a dimension is incorrect
- **THEN** the system routes it to the current product information and evidence review without propagating that dimension to the category or style profile

#### Scenario: A style-specific shot preference is retained
- **WHEN** a user explicitly saves a relaxed-opening preference for inflatable-sofa outdoor presentation
- **THEN** the candidate records the category, style and relevant stage as applicability, preserves owner scope, and does not affect other categories or styles without explicit selection

#### Scenario: Batch feedback after partial confirmation
- **WHEN** a user supplies feedback for a batch with some values already adopted or filled
- **THEN** regeneration only targets pending suggestions whose fields remain empty, preserving adopted values and requiring explicit single-field editing to change them

### Requirement: Product clip direction owns both keyframes and image-conditioned motion prompts
A selected product video material director Skill SHALL coordinate grounded keyframes, image-conditioned action and camera design, manual web-generation handoff and returned-clip review through existing production contracts. It SHALL reuse explicitly selected methods and preserve human confirmation of the exact reference image. Still-image prompts MUST NOT be silently treated as confirmed motion prompts.

#### Scenario: A confirmed keyframe is used to draft motion
- **WHEN** the user requests a video prompt for an approved exact image
- **THEN** the assistant inspects the actual image through a supported image-capable route, relates preserved product details to feasible action/camera/timing, and returns a separate prompt bound to that image revision and hash for review

#### Scenario: Image inspection is unavailable
- **WHEN** the selected model cannot receive images and no supported image observation is available
- **THEN** the system explains the missing capability rather than claiming an image-conditioned prompt was verified from a filename or text description

#### Scenario: Generated product deforms in a returned clip
- **WHEN** the actual returned clip changes the product shape or fails the requested action
- **THEN** review identifies observable defects and usable ranges, preserves the image/prompt/video lineage, and proposes a targeted new attempt without overwriting accepted history or claiming the prompt alone guarantees quality

#### Scenario: The reference image changes after prompt review
- **WHEN** another keyframe is selected
- **THEN** previous motion prompts and reviews remain historical, and a fresh image-based review is required before a new confirmed web-generation package
