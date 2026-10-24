## ADDED Requirements

### Requirement: Real capture plans derive from a confirmed sales script
A product work SHALL support real capture, AI-generated and mixed material routes independently of Persona. A real-capture shooting assignment SHALL reference the confirmed script revision, relevant purchase reasons, product evidence and saved shooting conditions. Draft planning MAY start earlier, but an assignment SHALL NOT be labelled ready to shoot until its script basis and assignment version have been explicitly confirmed. Complete voiceover wording and generated audio SHALL be optional for a capture route without required live dialogue. Scenes MAY contain multiple shots; scene length and shot count SHALL NOT be fixed globally.

#### Scenario: Voiceover will be added in editing
- **WHEN** a user confirms a sales script expressed as ordered messages and visual actions with no voiceover text
- **THEN** a real-capture assignment can be confirmed and used for filming without TTS, AI keyframes or website execution

#### Scenario: A work mixes real demonstration and generated atmosphere
- **WHEN** a confirmed script uses both material routes
- **THEN** each shot retains its route, and only generated shots require image selection and manual website preparation; generated scenes do not become performance evidence

### Requirement: Shooting assignments provide actionable shot-level direction
Each shooting assignment SHALL retain stable shot IDs, scene membership, edit order, purpose, subject/action, camera position/angle, framing, key visible details, suggested raw duration and planned use duration. Filming order SHALL be independent from edit order. Optional narration, subtitles and sound notes SHALL remain optional. The assignment SHALL distinguish verified product facts, seller-proposed claims and missing evidence; a close-up alone SHALL NOT verify a performance claim. Saved and downloaded assignments SHALL identify the same version.

#### Scenario: A nonprofessional user follows a task
- **WHEN** the user opens a shot on a phone
- **THEN** the task states what to show, how to place the phone, what action to perform and what must remain visible, while professional parameters and optional narration do not obscure the task

#### Scenario: Filming is grouped by camera setup
- **WHEN** the filming order is changed to reduce setup work
- **THEN** stable shot IDs, edit order and source-media associations remain unchanged

### Requirement: Real capture review retains original media and usable ranges
The system SHALL link each uploaded original to its work, shot and shooting-assignment version, retaining exact material revision/hash. Multiple takes MAY be linked to a shot. Review SHALL record inspected time ranges, usable ranges or specific reshoot reasons. Upload, review acceptance and adoption into an edit SHALL be distinct. Replacement takes SHALL preserve prior files and decisions.

#### Scenario: A shot needs another take
- **WHEN** review finds the required product detail obscured
- **THEN** the user receives a targeted reshoot instruction, other usable shots remain available and a new take does not overwrite the rejected original

#### Scenario: A confirmed upstream requirement changes
- **WHEN** the script or shooting conditions change the required visual content
- **THEN** the current dependent assignment or edit usage is marked for review while historical confirmations and media remain intact; no filming or paid generation starts automatically

#### Scenario: Only optional voiceover wording changes
- **WHEN** the visual requirements remain unchanged
- **THEN** capture confirmation is not automatically invalidated, and subsequent edit planning checks actual audio duration separately

### Requirement: Stage methods and decisions remain inspectable and versioned
The system SHALL retain input artifact references, effective optional methods and switches, exact method versions/hashes, actual model or executor provenance, outputs and explicit edit/acceptance/feedback records. Inspectable reasoning SHALL consist of concise decision summaries and supporting evidence, not private model reasoning. Real-capture method instructions SHALL have explicit inputs, decision criteria, outputs, deficiency handling and review criteria. Disabling a method SHALL remove its optional instructions from execution without disabling ownership, factual or version protections.

#### Scenario: A user completes a stage manually
- **WHEN** optional methods are disabled and the user enters the required content
- **THEN** the same product workflow can proceed with manual provenance and no model execution is fabricated

#### Scenario: Feedback is considered for reuse
- **WHEN** a user selects a correction for a defined SKU, category, style or stage scope
- **THEN** the system records a reusable candidate and validation evidence before explicit activation of a new version; current-only feedback and SKU facts do not silently update unrelated methods or frozen work


### Requirement: Selected product methods plan sales coverage before editing
Selected product preproduction methods SHALL connect the intended audience, use situation and grounded purchase reasons to shot purposes, visible information and available or missing assets. Shot count SHALL follow the work's information needs rather than a universal preset. An executor MUST NOT silently substitute repeated crops of one photograph for missing demonstration material while claiming a complete sales expression. A deliberately chosen single-image concept remains valid when its limited objective is explicit.

#### Scenario: One group photo cannot support a requested product advertisement
- **WHEN** the available photo does not cover the planned purchase questions or demonstration views
- **THEN** the executor presents the creative direction, per-shot asset gaps and acquisition or illustration route before editing, preserving unsupported claims as unknown

### Requirement: Product keyframes precede user-confirmed video prompts
For a user-requested image-first product workflow, the executor SHALL present inspectable per-shot candidate keyframes with original-image provenance, shot purpose, known fidelity limitations and review status. Image-generation requests SHALL supply the original reference through a supported image input. User selection SHALL identify the exact image version or hash before downstream motion prompts and video generation proceed. Candidate creation, technical inspection and user creative approval MUST remain distinct.

#### Scenario: A generated product image is ready but has not been selected
- **WHEN** the executor finishes the storyboard and keyframe candidates
- **THEN** the user can inspect those candidates while image selection remains pending and no video generation or image-confirmation receipt is fabricated

#### Scenario: A previously accepted local sample is creatively rejected
- **WHEN** the user rejects its product expression and authorizes a new direction
- **THEN** the new work records that feedback and its own review status without rewriting the historical execution or treating technical acceptance as creative approval

### Requirement: Product sales preparation distinguishes evidence from illustrative assets
Selected sales methods SHALL check a concrete buyer situation, one primary purchase reason and its evidence, a major objection and applicable limits, grounded seller differentiation, one purchase action and internal economic assumptions. These concerns SHALL guide the work without requiring every concern in every video. AI illustration MUST NOT substitute for measured performance, authentic comparisons or authorized real feedback. Missing commercial facts and costs MUST remain unknown.

#### Scenario: A scene video lacks verified dimensions
- **WHEN** the chosen objection is product fit but only an illustrative group photo is available
- **THEN** the storyboard identifies the missing dimensions or real measurement shot, allows grounded scene exploration and does not fabricate measurements or claim the objection has been answered

### Requirement: Product setup reuses versioned project inputs
The product workspace SHALL reuse the existing product entry and versioned brief to configure the buyer situation, main reason, objection, evidence-linked claims, seller information, purchase destination and classified material references. Asset categories SHALL be editable without granting verification or reuse rights. Internal cost estimates SHALL remain outside public generation/export projections. Existing brief fields and legacy tasks MUST remain compatible.

#### Scenario: Incomplete business inputs are saved
- **WHEN** a user saves a product brief with some unknown costs and no verified seller advantage
- **THEN** known fields are retained without invented zero costs, profitability or seller claims, and supported creative preparation remains available

### Requirement: Manual website clips use a per-shot three-column workspace
The video material workspace SHALL present each shot in one row with its storyboard and exact keyframe on the left, editable website prompt and parameters in the middle, and manual original-video upload, preview and review state on the right. It SHALL reuse existing image selection, prompt-image binding, frozen execution and upload contracts. The user SHALL generate clips manually in Grok or Gemini. Upload success MUST NOT imply adoption or bind a different shot by guessing its filename.

#### Scenario: A user returns a clip for one shot
- **WHEN** the user uploads an original MP4 from that shot's row
- **THEN** it is attached to that exact manual task, remains previewable and pending explicit review/adoption, and other rows retain their current state

#### Scenario: A keyframe changes after prompt confirmation
- **WHEN** the user replaces the selected image
- **THEN** the old prompt is marked mismatched until reconfirmed against the new image, while frozen historical tasks and accepted media are preserved without automatic redispatch

#### Scenario: A narrow screen is used
- **WHEN** the three columns cannot be displayed legibly
- **THEN** each shot retains the same ordered image, prompt and upload controls vertically, with accessible labels and non-color-only status

#### Scenario: A shot requires real measurement evidence
- **WHEN** the shot uses actual capture or existing evidence rather than website generation
- **THEN** the middle column shows capture or verification instructions, and the user directly references existing evidence or uploads actual media without an AI keyframe or motion-prompt prerequisite

### Requirement: Product production exposes a coherent next action
The existing product production workspace SHALL expose the current saved stage, relevant missing inputs, unsaved draft state and the next applicable action across planning, images, manual clips, sound/editing and final return. Status SHALL derive from existing versioned records and accepted outputs, not navigation or checklist counts. Whole-plan drafting SHALL reuse the existing recipe proposal and acceptance path; field autofill SHALL preserve its blank-only contract and MUST NOT pretend to create nonexistent shot rows.

#### Scenario: Product inputs exist but no script or shot rows exist
- **WHEN** the user needs an initial product storyboard
- **THEN** the workspace provides a clear entry to the existing whole-plan generation and review path, and accepted results are read back into the current draft without requiring manual creation of every empty row

#### Scenario: A suggestion is adopted but not saved
- **WHEN** the user adopts field changes and proceeds toward external execution
- **THEN** the workspace identifies the unsaved changes and uses only explicitly saved revisions for execution without silently dropping or submitting the draft

### Requirement: Product samples are grounded in current workspace artifacts
Product sample preparation SHALL persist its storyboard and candidate references through existing platform contracts so the normal page can display the exact artifacts under review. Candidate import SHALL NOT imply image approval. New work SHALL preserve old Master revisions and execution receipts; missing dimensions, effects evidence or purchase destinations MUST remain explicit.

#### Scenario: A new storyboard exists only in handoff documents
- **WHEN** the authorized executor integrates it into the product task
- **THEN** the platform displays a new saved draft and pending candidate images while the previously rendered sample remains historical and unmodified

### Requirement: Product completion includes real output quality and scoped reuse
Completion of a product production acceptance run SHALL distinguish engineering checks, image approval, returned clip inspection, final sample quality and commercial readiness. The actual agreed path SHALL include saved planning, user-selected images, image-conditioned prompts, manual returned clips, the selected speech mode (synchronized presenter dialogue, narration or no speech), optional music, Resolve editing, optional AE packaging and returned native projects/final media. Confirmed reusable feedback SHALL identify its general, category, style, product or task scope and be evaluated in a subsequent independent generation with the relevant method version.

#### Scenario: Clips have not been returned
- **WHEN** keyframes or prompts pass inspection but the required manual website clips are absent
- **THEN** clip and final-quality acceptance remain pending and independent preparation can continue without claiming a completed sample

#### Scenario: The result is a scene concept with no verified purchase destination
- **WHEN** the final media is reviewed
- **THEN** the receipt states its limited scene-demonstration scope and does not claim a complete purchasable advertisement, measured performance or unperformed human listening

#### Scenario: Feedback becomes a category method
- **WHEN** a confirmed improvement is saved for a selected product category
- **THEN** the next independent generation records the chosen version and demonstrates whether that improvement is present without altering historical attempts or unrelated categories


### Requirement: Product video has an independent guided journey
The product video workspace SHALL organize product and work goals, director planning, visual and sound setup, per-shot materials, professional editing/packaging and final review/feedback as six distinct user steps. Coarse shot/action planning SHALL precede shared setup; exact keyframe selection and executable motion prompts SHALL follow the relevant setup. Sound repair remains part of professional editing rather than delaying all speech planning until after clip generation. It SHALL retain the existing per-shot three-column contract inside the materials step while progressively revealing long prompts and prior attempts. Real footage SHALL bypass AI-image prerequisites. Optional music or AE packaging SHALL have explicit not-used paths rather than forced completion of unnecessary work.

#### Scenario: A product video is created from partial information
- **WHEN** the user starts through the product workspace
- **THEN** existing product creation contracts are used and the user enters product evidence with known information retained, missing facts visible and no automatic model invocation

#### Scenario: A real demonstration is supplied
- **WHEN** a shot uses real media
- **THEN** the user can reference or upload and review it directly without first confirming an AI keyframe or a video-generation prompt

### Requirement: Selected references yield scoped observations and methods
When reference-video analysis is selected, the executor SHALL retain reference provenance and timecoded observations of purchase reasoning, interaction, camera, action continuity and sound/editing. Observations, creative inferences and unexamined modalities SHALL be distinguished. Missing reference media SHALL remain pending or optional, never fabricated. Reusable findings SHALL be saved as explicitly scoped method candidates using existing mechanisms; visual appeal MUST NOT be reported as proven sales conversion without data.

#### Scenario: A preferred sales video is provided
- **WHEN** the executor analyzes the actual reference
- **THEN** the result cites observable moments and proposes transferable techniques without importing unsupported brand claims, author experience or sales results

### Requirement: Interaction shots are planned for continuity before generation
When the selected style calls for a continuous use scene, the storyboard SHALL specify stable product/subject/scene attributes, one understandable action per shot, start/end states and intended transitions. Keyframes SHALL be reviewed against these relationships before image-conditioned motion prompts. Complicated actions can be split at appropriate edit points. Generated interaction MUST NOT establish actual material, comfort or performance claims.

#### Scenario: A static showcase is revised to a continuous use scene
- **WHEN** new action-ready keyframes are proposed
- **THEN** the user reviews their exact versions before generation; prior image approvals and frozen packages remain historical and are not silently reused as approval of new images

### Requirement: Product methods map to stages and real execution
The workspace SHALL map existing product truth, sales, consistency, shot routing, narration, editing, packaging and review methods to applicable stages. The product material director SHALL own image-to-clip creative decisions, while the handoff skill retains execution/return contracts. The platform SHALL retain selected versions and scope; the external Harness SHALL consume the applicable frozen configuration. Verification MUST inspect actual request/package selection and output behavior rather than treating a displayed method label as integration proof.

#### Scenario: A category style is selected for new work
- **WHEN** the user prepares an applicable stage
- **THEN** its preview identifies the selected methods and versions without changing unrelated Persona defaults, product facts or historical attempts


### Requirement: One product supports independent configurable works
The workspace SHALL offer product showcase/detail, brand/scene advertising and presenter/UGC work types including synchronized on-camera speech. Original creation and reference-based reinterpretation SHALL be selectable across work types. One product SHALL support multiple independently versioned works sharing product facts without overwriting another work's script, selected methods, voice mode, media or acceptance. Configuration SHALL be progressively revealed and SHALL NOT trigger generation merely by being selected.

#### Scenario: Two works use the same sofa
- **WHEN** the user creates a presenter demonstration and a music-led scene advertisement
- **THEN** each retains its own creative configuration and outputs while referring to shared saved product facts, and accepting one does not accept the other

#### Scenario: A previous work is used as a starting point
- **WHEN** the user creates another work with selected inherited settings
- **THEN** its source revision is retained, its production and acceptance states remain independent, and later source changes do not rewrite either frozen history

### Requirement: Presenter speech is an explicit production branch
The workspace SHALL support planning, manual generation handoff, returned media and review for synchronized presenter speech as well as narration, no speech and shot-specific combinations. Dialogue language, exact lines, person reference and action/timing SHALL be resolved before generation. Execution SHALL check actual supported input combinations. Missing capability SHALL be visible without silently changing the requested voice mode. Returned presenter audio SHALL NOT be muted or overwritten by default narration.

#### Scenario: A speaking clip is returned
- **WHEN** the user submits the original generated video to the presenter shot
- **THEN** dialogue, audio presence, lip synchronization and person continuity are reviewed, and accepted original dialogue is retained in the sound/editing handoff unless explicitly replaced

#### Scenario: The requested voice input is unsupported
- **WHEN** the selected website/model cannot consume the requested audio or reference combination
- **THEN** preparation explains the specific limitation and preserves the planned work while requiring an explicit alternative before executing a different mode

### Requirement: Demonstration techniques preserve their evidential meaning
Selected methods SHALL support usage demonstrations, detail shots, comparisons, time-change sequences and reactions as creative presentation techniques. The plan and media provenance SHALL distinguish illustrative simulation, explanation grounded in supplied facts and actual measured evidence. Generated images or acting MUST NOT create purported measurements, user experiences or product results without supporting source facts.

#### Scenario: A simulated use scene is planned
- **WHEN** the user selects a generated interaction or time-change treatment
- **THEN** the treatment remains available as illustration while unsupported measured values and purported personal experience are not invented or reported as verified evidence

### Requirement: Reference reinterpretation and controlled variants are explicit
Reference-based works SHALL identify retained structural or stylistic elements and intended changes to product, people, scene or text. They SHALL NOT be restricted to exact recreation. A source video SHALL be attached to model generation only where the selected route actually supports that input; storyboard reconstruction SHALL remain a distinct usable route. Controlled variants SHALL declare their common baseline, changed dimensions and selected count through existing work/version mechanisms without automatic paid batch creation.

#### Scenario: A reference is reconstructed with image-conditioned shots
- **WHEN** the selected model route lacks reference-video input
- **THEN** the analyzed reference can guide new storyboards and prompts while the execution accurately reports its actual image inputs rather than claiming the source video was sent

#### Scenario: The user compares two openings
- **WHEN** two works are created with only the declared opening variation
- **THEN** the common configuration/source is recorded, the outputs are independently reviewable and no performance winner is claimed without relevant results


### Requirement: Referenced methods are independently authored stage contracts
This revision SHALL abstract observed principles from researched projects into independently authored methods using the platform's existing method selection and version contracts. It SHALL NOT import third-party Skills, prompt templates, recipe libraries or runtime implementations. Each adopted method SHALL identify its research provenance, applicable work types/stages, required inputs, decisions, outputs, review criteria and correction destination. Applicability SHALL be checked for the actual execution node; disabled creative methods SHALL NOT disable factual, permission or artifact-identity contracts.

#### Scenario: A researched camera technique becomes a local method
- **WHEN** the technique is included in the selected product method version
- **THEN** the original local instructions and their scope are inspectable, the actual package contains that version, and output review checks the intended technique without claiming the source plugin was installed

### Requirement: Shared visual and sound setup precedes dependent generation
Each video work SHALL retain the selected product, person where applicable, scene and style references alongside its speech mode and relevant dialogue/timing intentions. Existing accepted references MAY be used without mandatory regeneration. Narration planning SHALL distinguish actual audio duration from provisional estimates; synchronized presenter planning SHALL retain exact dialogue and timing intent without requiring a separate TTS track. No-speech works and optional scene music SHALL remain valid. Accepted returned audio SHALL determine subsequent actual edit timing.

#### Scenario: A presenter work has no separate voice recording
- **WHEN** exact dialogue, intended person reference and a supported website route are ready
- **THEN** the work can prepare image-conditioned speaking clips with provisional timing, and returned speech is checked before the edit uses actual durations

#### Scenario: A music-led work needs no presenter
- **WHEN** no speech is selected
- **THEN** irrelevant person and narration inputs do not block supported work, and optional music retains its scene tags and explicit selection state

### Requirement: Shot references preserve identity and scoped dependencies
Shot preparation SHALL retain original product evidence separately from generated continuity references. Referenced setup and frame versions SHALL be explicit and resolvable; cross-shot dependencies SHALL reject cycles and missing references while allowing independent scenes. Plans SHALL distinguish camera motion, subject action, and start/end state. Optional target end frames SHALL be represented as model inputs only when actually supported and supplied. Changing a referenced artifact SHALL identify affected downstream items for review without rewriting frozen history, invalidating unrelated scenes or automatically regenerating media.

#### Scenario: A later shot depends on a changed scene reference
- **WHEN** a new scene reference is selected
- **THEN** dependent current shot preparations show a review need, original product evidence remains available for fidelity checking, and independent scenes and historical executions remain preserved

#### Scenario: A website accepts only a start image
- **WHEN** a planned shot has a target end state
- **THEN** its package reports the actual start-image input and descriptive end-state intent without claiming dual-frame conditioning

### Requirement: Candidate comparison allows rejecting every result
When candidate evaluation is selected, it SHALL inspect actual images or clips against the original product evidence, chosen setup and shot purpose. Recommendations SHALL state observable defects and uninspected dimensions, permit rejecting all candidates, and remain distinct from user keyframe selection or explicit clip adoption. Candidate counts SHALL be explicitly selected within existing execution limits; this evaluation method SHALL NOT silently multiply generation or dispatch paid work.

#### Scenario: All candidate images have altered product structure
- **WHEN** image evaluation compares the candidates
- **THEN** all can be marked unsuitable with concrete correction feedback, and no relative best candidate becomes an approved keyframe automatically
