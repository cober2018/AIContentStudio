## ADDED Requirements

### Requirement: Direct product creation bypasses opportunity discovery

The normal project creation surface SHALL offer a product-driven entry accepting a product URL, pasted description or uploaded document, plus optional product media. The user SHALL select an owned Persona, content objective, channel/modality and CTA as applicable; existing Persona and Recipe defaults MAY prefill these choices for review. The system SHALL prepare an editable ordinary CreativeBrief and content-unit/Recipe selection. It MUST NOT require a ContentOpportunity, an assessment score, qualified status, an active daily-discovery schedule or a trending event. Existing manual creation and qualified-opportunity conversion SHALL remain supported.

#### Scenario: Create without an opportunity
- **WHEN** the user provides sufficient product information and selects a valid Persona and video Recipe while the opportunity list is empty
- **THEN** Start Creation creates an ordinary project and Brief and starts the first ready generation stage through the shared pipeline without creating a placeholder opportunity

#### Scenario: Role-specific expression
- **WHEN** the same product is used with technology and lifestyle Personas
- **THEN** creative framing follows each selected Persona while the product identity and factual claims remain tied to the same supplied evidence, without invented personal experience

#### Scenario: Unreadable product URL
- **WHEN** a product page cannot be fetched or parsed
- **THEN** the entry explains the failure and accepts pasted or uploaded product information without requiring a successful URL fetch

### Requirement: Supplied evidence takes precedence and external research is optional

Product creation SHALL first use supplied and authorized project evidence/materials. External research SHALL be used only to fill relevant gaps through the shared search adapter and normal source intake, retaining real citations and retrieval time. Search SHALL use necessary public product identifiers/topics rather than uploading private documents or media. The system MUST NOT require trend discovery or successful web search when inputs already satisfy the selected stage. Missing critical product facts or conflicting claims SHALL be exposed for correction; unsupported claims MUST NOT be invented. Price, promotion and expiry SHALL be required only if the requested content uses them. Supplementary product research MUST NOT automatically subscribe the product or modify the Persona's long-term source library.

#### Scenario: Search is unavailable but evidence is sufficient
- **WHEN** configured web search is unavailable and supplied inputs meet the selected Recipe's requirements
- **THEN** product creation can start and does not wait for daily discovery or an external search result

#### Scenario: Missing critical specifications
- **WHEN** a requested script depends on an unverified specification or conflicting variant information
- **THEN** the project retains its inputs, explains the specific gap, and can resume after correction without inventing the specification or requiring a topic assessment

#### Scenario: Video does not mention price
- **WHEN** the requested video demonstrates a product without price or promotion claims
- **THEN** absent price or promotion information alone does not block generation

### Requirement: Both entry paths share production and evidence gates

Product and opportunity entries SHALL converge on the same ContentProject, immutable Brief, source/material references, evidence permissions, Fact Boundary rules, content matrix and existing Recipe/stage execution. The product entry SHALL expose required readiness actions in its intake flow and MUST NOT silently accept claims, freeze/bind facts or bypass material rights. Product context SHALL be included in shared preview and generation inputs as specified by fe-f3a-content-project-core. Existing candidate acceptance, Content Master, MaterialRevision, review and delivery SHALL handle both entries; no separate commerce production engine or automatic publication SHALL be introduced.

#### Scenario: Existing factual gate is not ready
- **WHEN** the chosen stage requires a frozen Fact Boundary that is absent
- **THEN** the product flow presents the normal explicit fact confirmation and freeze/bind steps, retains the project, and starts only after those requirements are met

#### Scenario: Ready product starts actual generation
- **WHEN** the product Brief, selected content unit, evidence, permissions and Recipe are ready and the user starts creation
- **THEN** the shared generation path creates or resumes the first stage Run and returns its status rather than stopping at an empty project

#### Scenario: Review product output
- **WHEN** a product script or storyboard candidate is generated
- **THEN** the same project production page and acceptance/version controls used by opportunity-derived content display and manage it

#### Scenario: Video production is unavailable
- **WHEN** script/storyboard generation succeeds but a required filming, asset generation or editing capability is unavailable
- **THEN** the project shows the completed stage artifacts and the concrete pending production step, and does not label text artifacts as a finished video

### Requirement: Product launch is durable and retry-safe

Start Creation SHALL persist the project and committed inputs before dispatch and use a stable launch identity across retries to associate one project and first-stage Run. The existing execution mechanisms SHALL provide a recoverable dispatch state so a crash after persistence does not lose the requested start. Resumption SHALL reuse the saved project and completed stages. Repeated clicks MUST NOT duplicate projects or paid generation. Unknown provider outcomes SHALL retain their unknown state without blind paid resubmission. Product generation SHALL use normal creative Run accounting and model configuration independently of daily-opportunity quotas.

#### Scenario: Double click Start Creation
- **WHEN** the same launch is submitted twice
- **THEN** both responses identify the same project and initial generation operation without duplicate provider calls

#### Scenario: Dispatch fails after project persistence
- **WHEN** the project and Brief commit but generation dispatch fails or the process stops
- **THEN** the saved launch can resume on the same project and report its actual state without creating a second project

#### Scenario: Foreign source or material reference
- **WHEN** product intake references a Persona, source or material outside the user's authorized scope
- **THEN** the input is rejected before generation and does not disclose or pass the foreign content to a provider
