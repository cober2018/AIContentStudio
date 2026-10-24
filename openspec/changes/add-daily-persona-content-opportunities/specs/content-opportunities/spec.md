## ADDED Requirements

### Requirement: Automated opportunity provenance and manual authority

ContentOpportunity SHALL support nullable Persona/revision, generation run, event-version and angle provenance while preserving legacy manual records. Automatically generated opportunities SHALL start in new status. A trusted worker path SHALL create system assessments with provider and evidence provenance, while public manual assessment writes MUST continue rejecting forged automatic provenance. Automatic processing MUST NOT set qualified/converted status or create projects, fact packs, approved facts, identity snapshots or delivery authorizations.

#### Scenario: A system-generated opportunity is saved
- **WHEN** the worker saves a validated candidate
- **THEN** its new opportunity and initial assessment identify the exact role, run, model and evidence without claiming human approval

#### Scenario: Manual caller forges provenance
- **WHEN** a public manual assessment request claims system analysis or provider provenance
- **THEN** the request is rejected and no assessment is written

#### Scenario: User chooses a topic
- **WHEN** the owner judges an opportunity qualified and explicitly invokes the existing project conversion
- **THEN** the existing atomic/idempotent conversion contract applies; external research signals remain references until imported through the ordinary Source flow and do not automatically become confirmed facts

## MODIFIED Requirements

### Requirement: Opportunity workspace projection

The system SHALL expose an owner-scoped opportunity workspace with lifecycle/priority filtering, latest assessment summary, signal lineage, risks, confidence, and an explicit conversion action. The workspace MUST link to the resulting project and existing source/evidence routes without duplicating their state. It SHALL additionally support Persona and generation-business-date filters and display automated provenance, why-now, source links and source dates. Source-registry and run-status views SHALL distinguish discovered candidates, active collectors, unavailable credentials/adapters, partial runs and successful zero-candidate runs. Manual opportunities without Persona metadata SHALL remain visible through the ordinary unfiltered/manual view.

#### Scenario: Filter opportunities
- **WHEN** an owner filters by status or priority
- **THEN** the workspace returns only matching owned opportunities and stable pagination metadata

#### Scenario: Show converted opportunity
- **WHEN** an opportunity is converted
- **THEN** the workspace shows its linked project and disables duplicate conversion while retaining assessment and signal history

#### Scenario: Filter a Persona and date
- **WHEN** the owner selects a Persona and a generation business date
- **THEN** only matching owned automatic opportunities are shown with exact provenance and a link to that run's status

#### Scenario: No automatic result
- **WHEN** the selected role/date has no opportunity
- **THEN** the view distinguishes not-yet-due, researching, no suitable topics, paused, partial and unavailable/failed states using persisted facts

### Requirement: Curated recommendations retain editorial history

The normal opportunity page SHALL default to the current Taipei business date and current recommendations, with explicit access to backup and historical records. Automated backup topics SHALL NOT appear as current Home recommendations. Moving a topic to backup, deferring it for missing evidence, or merging it SHALL preserve the prior assessment and source history and record the editorial reason.

#### Scenario: Reviewing corrected daily recommendations
- **WHEN** an editor merges or defers today's generated topics
- **THEN** only current recommendations appear in the default view while the original records and appended assessments remain accessible from status/history filters
