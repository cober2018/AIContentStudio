## ADDED Requirements

### Requirement: Guided real capture preserves step hierarchy and durable handoffs
The product workspace SHALL retain its six-step navigation and expose a script-first director view followed by a shooting-assignment view. Real-capture shot rows SHALL present shot task, filming instructions and upload/review; AI rows SHALL retain their existing image/prompt/return flow. Mobile presentation SHALL show readable per-shot tasks and a versioned downloadable shooting list. Current status and next action SHALL derive from persisted records, while method settings and history remain available on demand.

#### Scenario: A mobile user hands over materials through an authorized agent
- **WHEN** the agent saves task data or uploads raw material through the supported CLI/MCP/API
- **THEN** the workbench reads back the same shot IDs, versions and review status without requiring a separate browser-only state

#### Scenario: An existing AI work is reopened
- **WHEN** its records predate real-capture assignment fields
- **THEN** its historical selected images, prompts, execution and acceptance remain readable without fabricated capture confirmations or automatic route changes


### Requirement: SKU content assets remain reusable across production projects
The primary creation path SHALL begin with selecting an existing product or creating a SKU with basic product information. Saving a new SKU SHALL continue directly to video creation. Existing information SHALL be reused without mandatory re-entry. Browsing the SKU management areas and selecting a reusable creative plan SHALL NOT be prerequisites for entering production.
The product workspace SHALL expose a searchable SKU catalog with category filtering. A SKU SHALL have a stable internal identity, a workspace-unique readable code, explicit category and supplied variant details. New SKUs SHALL receive an automatically allocated SKU-000001 style code on save, using at least six decimal digits. Allocation SHALL be atomic and workspace-unique; codes SHALL never be reused or changed by renaming or reclassification. Distinct sellable variants SHALL have distinct SKUs. External merchant/supplier codes SHALL be stored separately and searchable. Existing legacy codes SHALL remain searchable without forced renumbering. Product facts, original references and evidence SHALL be versioned reusable assets; projects SHALL remain production containers whose units reference exact SKU asset versions. Unknown facts MUST remain unknown and legacy unassociated works MUST NOT be matched by name heuristics.

#### Scenario: Similar products have different SKUs
- **WHEN** two variants share a display name
- **THEN** their distinct codes and supplied variant details identify them and materials or accepted works are not mixed

#### Scenario: The required product does not exist
- **WHEN** the user creates a SKU and saves its basic product information
- **THEN** the user enters video creation with that product context, without being required to browse saved creative plans first

#### Scenario: A user opens an old unassociated work
- **WHEN** no stable SKU association exists
- **THEN** the work remains accessible with an explicit pending association state rather than a fabricated SKU

### Requirement: SKU plans and Persona configuration have independent versioned ownership
A SKU SHALL support multiple reusable creative plans and an explicitly selected default. Plans SHALL identify applicable style, shooting type, stage methods and versions, model-setting references, sound and reference choices. Persona identity and AI configuration SHALL remain separately versioned. New works SHALL record selected plan and asset versions plus explicit task overrides; later default changes MUST NOT overwrite previous works. Credentials SHALL remain in existing settings, not copied to creative plans.

#### Scenario: A default plan is updated
- **WHEN** the user sets a new default version for a SKU
- **THEN** new work may select it while existing scripts, prompts, accepted assets and plan references remain tied to their prior versions

#### Scenario: One SKU uses multiple presenters or styles
- **WHEN** distinct product works select different plans, presenter assets or voice settings
- **THEN** their creative choices remain independent while they reference the same SKU facts without a content Persona dependency

### Requirement: Accepted work can become a durable reference and an explicit plan source
Users SHALL be able to mark a saved work version as a reference and separately choose settings to save as a new SKU creative-plan version. Reference works SHALL retain exact script, storyboard, image, prompt, clip, audio, project-file and final-output references where available; unavailable components SHALL be explicit. Retained media SHALL use existing durable asset storage rather than transient execution paths. Starting another work from a plan SHALL create an independent work without inherited acceptance or automatic generation.

#### Scenario: A completed work is retained
- **WHEN** its saved version is marked as a reference
- **THEN** that exact version and its available production assets remain reachable from the SKU after later works or plan updates

#### Scenario: A user extracts a reusable plan
- **WHEN** settings are selected from a saved work
- **THEN** a new plan version records the source and selected settings without silently promoting one-off claims, prices, acceptance or publication grants to defaults

### Requirement: Simplified workspaces preserve the project and identity architecture
ContentProject SHALL remain the business root. Both workspaces SHALL retain the current project and unit context with access to project overview, matrix, shared sources and related units. For Persona-domain works, Persona identity and its selected version SHALL remain distinct from optional stage methods; identity includes positioning, audience, viewpoints, style, voice and boundaries. Disabling a method MUST NOT disable factual, permission or version contracts.

#### Scenario: A user returns to a mixed project
- **WHEN** a user opens the project breadcrumb from a product video
- **THEN** the same project's overview, matrix and related units remain accessible without creating or copying a project

#### Scenario: A user inspects the selected identity
- **WHEN** the identity entry is opened in the Persona workspace
- **THEN** the selected identity version and its attributes are visible separately from stage method enablement

### Requirement: Guided steps retain advanced workflow access
The normal step sequence SHALL be a presentation of existing production contracts rather than a replacement workflow engine. An advanced workflow entry SHALL expose existing configuration and run views, node status, inputs, outputs, saved versions and explicit local rerun actions. Existing node editing, ordering, data-source selection, project overrides SHALL retain their supported entry points. Identity-modality defaults SHALL apply only to Persona works; product works SHALL use independent product defaults. Implementation SHALL document actual capability gaps without presenting planned capabilities as available.

#### Scenario: A user inspects an unsuccessful node
- **WHEN** the advanced workflow is opened from a guided step
- **THEN** the existing run and node input/output context can be inspected and the user can return without losing the step's unsaved draft

#### Scenario: A user requests a local rerun
- **WHEN** the user explicitly prepares a supported node rerun
- **THEN** it uses saved exact input versions and existing execution gates rather than being triggered by navigation

### Requirement: Local acceptance reconnects to the complete delivery lifecycle
Accepted local masters and films SHALL provide access to existing channel adaptation, complete Candidate review, target-account publication authorization, delivery receipts and learning views. Review SHALL bind the complete content, assets and metadata at exact versions or hashes. Local acceptance, content approval, publication authorization and actual publication SHALL remain distinct states.

#### Scenario: A restricted local film is accepted
- **WHEN** the user opens review and delivery
- **THEN** the film remains accepted locally while missing public-use permissions prevent publication authorization

#### Scenario: A reviewed candidate changes
- **WHEN** any reviewed content, asset or metadata version changes
- **THEN** the previous approval remains historical and does not authorize the changed candidate

#### Scenario: A work has not been published
- **WHEN** its receipts or learning view is opened
- **THEN** the view shows the actual pending or unavailable state rather than fabricated publication or performance results

### Requirement: Distinct workspaces reuse production records
The platform SHALL expose separate Persona content and product video workspace entries over existing project, unit, brief, recipe, master, material and execution records. Routing SHALL use an explicit persisted unit production domain. Reliable existing SKU-work or product-launch associations SHALL support compatible classification; project-wide product context or video modality alone MUST NOT classify a unit as product. Legacy URLs and mixed projects MUST remain accessible without copying records or silently rebinding identity. Unresolved classification and read failures SHALL be visible and SHALL NOT appear as an empty queue.

#### Scenario: An ordinary Persona video is continued
- **WHEN** a video unit has no saved product association
- **THEN** it opens in the Persona workspace with video-specific production steps, not the product workspace

#### Scenario: A legacy product video has only product context
- **WHEN** the user opens its existing production link
- **THEN** the same unit, versions and history remain accessible; ambiguous legacy domain assignment is shown for resolution rather than silently applying product defaults

#### Scenario: A mixed project is listed
- **WHEN** the project contains product video and non-video units
- **THEN** each unit remains reachable in its applicable journey and the project is not duplicated

### Requirement: Production presents a focused current step
Both workspaces SHALL present the task identity, saved/unsaved state, navigable step sequence, one current-step main work area and one emphasized contextual action. Other production stages SHALL NOT appear simultaneously as expanded full forms. Methods, model details, historical versions and technical execution information SHALL be available on demand. Queue pages SHALL foreground actionable works rather than simultaneously expanding all execution lists.

#### Scenario: A user reviews product images
- **WHEN** the materials step is active
- **THEN** shot imagery and the relevant confirmation action are prominent while complete recipe, script, sound and editing forms are not simultaneously expanded

#### Scenario: A user opens method settings
- **WHEN** the stage method drawer is opened and closed
- **THEN** the user can inspect the applicable methods and return to the same work and focus without losing edits

### Requirement: Next actions reflect accepted records and dependencies
Step status and next actions SHALL derive from persisted source revisions, candidate acceptance and actual outputs. Navigation, upload or generation success MUST NOT imply acceptance or completion. Users SHALL be able to inspect other steps and prepare independent work; only the requested operation's actual prerequisites SHALL block that operation. Historical acceptance SHALL remain intact when changed upstream versions require affected downstream references to be reviewed.

#### Scenario: A clip has been uploaded but not accepted
- **WHEN** the materials step is loaded
- **THEN** the clip shows pending review and the workspace does not report adopted or completed video production

#### Scenario: Website output is pending
- **WHEN** one shot is awaiting manual return
- **THEN** the exact shot return action and pending state are shown while unrelated preparation remains available

#### Scenario: An upstream source changes
- **WHEN** a current downstream result refers to the prior source
- **THEN** affected references show a review-needed indication without deleting the original receipt or automatically rerunning generation

### Requirement: Step navigation preserves drafts and existing links
Step navigation SHALL preserve current unsaved edits and selected candidates. Leaving the editing context SHALL offer save, discard or cancel where supported and native unsaved-change warning for browser unload. External executions SHALL consume only explicitly saved versions. Existing stage, panel and execution deep links SHALL resolve to their relevant view. Failed save or conflict MUST preserve local input and MUST NOT advance as if save succeeded.

#### Scenario: A user changes steps with an unsaved script
- **WHEN** the user switches to materials and returns
- **THEN** the script edits remain present and are still identified as unsaved

#### Scenario: An old execution link is opened
- **WHEN** the URL identifies an existing execution and panel
- **THEN** the same execution is visible in the applicable step without creating another task

#### Scenario: Accept succeeds but saving fails
- **WHEN** a multi-operation continue action cannot save the adopted changes
- **THEN** the UI reports the actual accepted and unsaved states, retains the draft and offers recovery instead of claiming complete success

### Requirement: Persona journeys reflect the selected output form
The Persona workspace SHALL guide topic/evidence, content planning, modality-specific production, review and delivery using existing contracts. Audio SHALL remain a derivative of accepted text rather than a new content-unit modality. Unneeded modality editors SHALL NOT be expanded. Existing identity, source rights, explicit generation/acceptance and channel delivery requirements MUST remain effective.

#### Scenario: Audio is made from text
- **WHEN** the user chooses the existing audio creation flow
- **THEN** accepted source text, spoken-script review, voice settings and audio results are presented as a coherent branch with a route back to the original text

#### Scenario: A graphic work is edited
- **WHEN** the user enters production for a graphic unit
- **THEN** the current graphic planning/canvas/render actions are presented without requiring video or audio steps

### Requirement: Assistance and feedback remain contextual
Existing blank-only drafting and focused-field polishing SHALL remain available within the current step. The target field and candidate confirmation SHALL be explicit. Whole-plan creation SHALL use the recipe proposal path, not empty-field filling. Stage method controls SHALL show applicability, versions and enablement without cluttering the default page. Feedback SHALL default to the current task; broader scope adoption MUST be explicit and versioned, never automatic global learning.

#### Scenario: A partially filled product form is drafted
- **WHEN** the user requests completion of missing information
- **THEN** existing filled inputs are retained, suggestions remain reviewable, and missing facts are not invented

#### Scenario: A creative method is disabled
- **WHEN** the next execution is prepared
- **THEN** its request reflects the changed method selection while the existing factual, permission and artifact contracts remain enforced

### Requirement: Guided workspaces provide accessible states
Step controls, fields, drawers and contextual actions SHALL support keyboard operation, visible focus and text status. Desktop and narrow layouts SHALL preserve reading/action order without whole-page horizontal overflow. Empty, loading, failed, waiting and read-only states SHALL be distinct and provide applicable recovery or continuation actions. Navigation and opening a page MUST NOT trigger model generation.

#### Scenario: A narrow-screen user returns a clip
- **WHEN** the three-column layout cannot fit
- **THEN** the current shot identity remains clear and image, prompt and upload controls follow the same order in a usable vertical layout

#### Scenario: The task list fails to load
- **WHEN** the records request fails
- **THEN** the page shows a recoverable read failure rather than claiming no unfinished work exists

### Requirement: SKU search results show the matching product image
Search by SKU code, product name or external code SHALL display each matching SKU with its own image on the right and a clear selection action. Product creation and product facts SHALL allow uploading an original product image and explicitly assigning the primary image through existing asset storage. Missing or failed images SHALL show a meaningful placeholder, with retry for a load failure, without blocking product selection. A labelled reference group photo MAY be shown separately from a confirmed primary image; unrelated variants and AI scene images MUST NOT be substituted as product evidence.

#### Scenario: Search returns several product variants
- **WHEN** a name query matches several SKUs
- **THEN** each result shows its own code, variant information and bound image or missing-image state, and the user selects the intended SKU

#### Scenario: A new SKU receives its permanent code
- **WHEN** two users save different new SKUs concurrently
- **THEN** the service assigns different permanent sequential codes and does not trust a client-side preview number

#### Scenario: A SKU has no primary image
- **WHEN** the SKU appears in search results
- **THEN** the result shows a missing-image placeholder or a clearly labelled bound reference photo without borrowing another SKU's image

### Requirement: Product creation guides a new work through reviewable handoffs
A new product work SHALL enter the same six-stage workspace after product selection. It SHALL retain filled task fields, present a deliberate drafting action when no director candidate exists and require explicit candidate acceptance. Visual and sound settings SHALL be accessible as local views. Postproduction SHALL identify missing selected materials, the handoff contents and returned work version. A missing returned cut MUST NOT be presented as an accepted film. Editing dependencies SHALL require renewed downstream review without deleting historical assets.

#### Scenario: A new SKU starts a video
- **WHEN** the user saves basic product information and continues
- **THEN** the work presents its own task inputs and director drafting action without copying another SKU's facts or accepted materials

#### Scenario: Feedback requires a shot change
- **WHEN** the user records a reason and selects a shot to revise
- **THEN** the workspace returns to that shot and marks dependent editing and final acceptance for renewed review while retaining other shots and historical assets

#### Scenario: A returned cut is accepted locally
- **WHEN** the user reviews and explicitly accepts the returned cut version
- **THEN** the workspace records local acceptance and offers the existing channel review and delivery process without claiming publication

#### Scenario: No configured channel supports a video film
- **WHEN** a product video is created and available channels support only text, images or scripts
- **THEN** the default is to create without a channel and choose one during delivery; the intake does not silently assign an incompatible graphic channel, and old works remain readable

### Requirement: Product creation is independent of content Personas
Product works SHALL use SKU facts and versioned product production configuration, without requiring, selecting, creating or implicitly inheriting a content Persona or IdentitySnapshot. Shared storage and execution primitives MAY serve both domains. Persona works MUST retain their identity requirements. Presenter references and voices SHALL be selectable production assets rather than content Persona prerequisites.

#### Scenario: A workspace has no Personas
- **WHEN** its user saves a SKU and starts or continues product production
- **THEN** product task creation, director preparation, material handoff, optional sound, editing handoff and local film acceptance operate with their actual product prerequisites and do not require Persona creation

#### Scenario: Product configuration is missing
- **WHEN** a product work prepares a stage without a required product setting
- **THEN** it requests that specific setting and does not fall back to a Persona profile or block unrelated stages

### Requirement: Product context governs every creative entry point
Recipe preparation, form assistance, stage requests, media prompts, sound generation, editing packages, readiness checks and reusable-plan extraction SHALL resolve the same versioned product context. Model credentials and executor implementations MAY be shared, but product defaults, stage methods, quality criteria and feedback ownership MUST NOT implicitly inherit Persona values. Product configuration SHALL be separately accessible from product pages.

#### Scenario: A role default changes
- **WHEN** a Persona voice, style or workflow default is edited
- **THEN** product work configuration and prepared requests remain unchanged and a new product work still resolves only product-owned defaults

#### Scenario: A product plan is retained
- **WHEN** selected work settings become a SKU plan
- **THEN** only the explicitly selected product-effective settings are versioned and no missing group is filled from a historical Persona snapshot

### Requirement: Domain migration preserves original production evidence
Existing product snapshots, runs, master versions, assets and acceptance history SHALL remain unchanged. Continuing a legacy role-bound product work SHALL prepare a new product context version with visible reusable inputs and settings requiring confirmation. Existing approval or publication grants MUST NOT transfer to changed outputs. Mixed-project units SHALL retain their respective domain routing.

#### Scenario: A legacy product draft is continued
- **WHEN** the user prepares its next run under product mode
- **THEN** historical identity-bound runs remain readable, the new run uses product context, and legacy Persona defaults are not automatically promoted to SKU defaults

#### Scenario: A project contains both kinds of video
- **WHEN** its product and Persona video units are listed
- **THEN** each opens the correct workspace using unit-level domain, independent of project-wide product context

### Requirement: Product account authorization is independent of creative identity
Product delivery SHALL verify user or workspace account access, channel compatibility, exact target account revision, complete candidate approval and publication permission without requiring a shared Persona. Missing accounts SHALL NOT prevent local creation or acceptance. Persona delivery SHALL retain its existing identity association contract. Compatible account ownership migration MUST NOT grant access where ownership is unresolved.

#### Scenario: A product film selects an authorized account
- **WHEN** the product work has no Persona and its owner chooses an accessible channel account
- **THEN** delivery checks the actual account and content permissions without requiring a content Persona, and local acceptance alone does not authorize publication

#### Scenario: Another user's account is selected
- **WHEN** the target account is outside the user's authorized scope
- **THEN** preparation or authorization is rejected even though the product work has no Persona

### Requirement: Product goal assistance uses explicit independent method switches
Product goal assistance SHALL support independently selectable self-authored audience-and-purchase-need and purchase-reason-and-expression methods for corresponding product_brief fields in autofill and focused polish. Applicable enabled methods SHALL be rendered and frozen with exact versions, hashes and effective switch states. Disabled methods MUST NOT remain executable through duplicated context or fallback. Existing works without this selection SHALL retain ordinary assistance. Changes SHALL require re-resolution before applying suggestions under changed configuration. Switches SHALL NOT disable factual, authorization or acceptance contracts or change director stage enablement.

#### Scenario: Only audience analysis is enabled
- **WHEN** a product goal request enables audience analysis and disables purchase-reason expression
- **THEN** only applicable enabled method instructions execute and the stored request records both switch states

#### Scenario: Both methods are disabled
- **WHEN** both methods are disabled
- **THEN** ordinary assistance remains available without hidden method fallback

#### Scenario: Method choices change for one work
- **WHEN** a user saves different method switches for a product work
- **THEN** that work uses the selection while SKU defaults, other works and Persona configurations remain unchanged and history stays readable

### Requirement: Product intent blanks receive reviewable suggestions without overwriting intent
Only product_brief SHALL permit suggestions and explicit adoption for empty objective and primary_audience when usable product or user context exists. Whole-form autofill SHALL preserve nonempty and skipped fields. Focused polish SHALL affect only the selected field or range and preserve stated intent. Unsupported commercial claims and audience assumptions SHALL be identified as unconfirmed rather than product evidence. Generation SHALL NOT save fields automatically; other surfaces SHALL retain protected-field rules.

#### Scenario: Audience is empty but a use case exists
- **WHEN** autofill receives a product use case with an empty audience
- **THEN** it may propose an audience with assumptions for review, preserving supplied fields and requiring adoption and save

#### Scenario: A filled purchase reason is polished
- **WHEN** the user focuses a purchase reason and requests polish
- **THEN** only that field or range changes without changing the audience or inventing performance

#### Scenario: Context is missing
- **WHEN** no usable product or user context exists
- **THEN** assistance identifies missing basis rather than fabricating product or purchase promises
