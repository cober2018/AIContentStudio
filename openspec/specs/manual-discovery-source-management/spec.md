# manual-discovery-source-management Specification

## Purpose

让用户在现有来源库手动登记新闻网站、RSS/Atom与博主公开主页，配置角色关联并与自动发现统一管理。后台验证公开入口，保护人工设置和历史证据，复用既有采集、权限及每日选题质量规则。

## Requirements
### Requirement: Manual source entry in the existing registry

The system SHALL allow an editor to add a news website, an RSS/Atom feed or a public creator homepage from the existing opportunity source panel. The form SHALL accept a public HTTP(S) URL, source type, optional display name, zero or more owned Persona IDs, collection pause state and model-processing permission. Product source type SHALL remain distinct from the detected collector adapter. A saved source URL SHALL remain its identity; another URL can be added as another source or recognized as a verified alias.

#### Scenario: Add a feed for two Personas
- **WHEN** the editor submits a valid feed URL and selects two owned Personas
- **THEN** one source and the intended two associations are persisted and its actual validation state is shown

#### Scenario: Reserve a source without a Persona
- **WHEN** the editor saves a source with no selected Personas
- **THEN** it remains in the registry and can be validated, but it is not periodically collected or used for daily recommendations

### Requirement: Durable and bounded source validation

Saving a new source SHALL persist a validation intent processed by the existing background worker independently of the page. Validation SHALL reuse supported RSS/Atom and public HTML/JSON collection and safe HTTP controls, without requiring search or model availability. Websites and creator pages SHALL be checked for declared public feeds and supported public collection structures. A successful page request alone MUST NOT establish collectability. Validation failures SHALL preserve the source, associations and an actionable reason. Revalidation SHALL be explicit or follow existing bounded recovery and MUST NOT reset pauses, generate topics or replay unknown provider requests.

#### Scenario: A website exposes RSS
- **WHEN** background validation finds and successfully validates a public RSS endpoint for the submitted website
- **THEN** the source retains the submitted URL and the verified collection endpoint and becomes eligible for the existing scheduler when its settings permit

#### Scenario: A restricted or unsupported creator page
- **WHEN** the homepage requires unavailable login or lacks a supported collection entry
- **THEN** it remains saved with credential-required or adapter-unavailable status and is not presented as successfully collecting

#### Scenario: A user changes configuration during validation
- **WHEN** a validation result returns after the source was paused, its processing permission revoked or its association set changed
- **THEN** the worker checks the latest configuration and cannot restore revoked use or publish results under an obsolete association set

### Requirement: Unified identity and origin history

Manual and automatically discovered sources SHALL share the owner-scoped registry, collection history and subscriptions. The list SHALL distinguish manual, automatic, both and initial-inventory origins from evidence; unknown legacy origin SHALL remain unknown. Repeated normalized URLs or positively verified identical collector endpoints SHALL reuse one source identity per owner. Same-domain URLs alone MUST NOT be merged. Existing names, permissions, pauses, associations and historical discovery evidence SHALL survive duplicate registration and alias resolution.

#### Scenario: Add an automatically discovered source again
- **WHEN** a user submits a URL already represented by an automatically discovered source
- **THEN** the system returns and opens the existing record without creating a duplicate or overwriting its settings, and allows an explicit subsequent configuration save

#### Scenario: Homepage and feed resolve to the same source
- **WHEN** validation establishes that a submitted homepage uses an already registered feed endpoint
- **THEN** the registry reuses that identity atomically, retains the alias and existing associations and does not collect the same endpoint twice; conflicting new settings are shown as unapplied until the user explicitly saves the existing record configuration

#### Scenario: Concurrent duplicate submission
- **WHEN** the same owner submits the same source concurrently or repeats a request after an uncertain HTTP response
- **THEN** one source identity remains and no duplicate subscriptions or validation execution are created

### Requirement: Manual Persona configuration overrides automatic maintenance

An explicit configuration save containing Persona IDs SHALL establish the exact human-managed association set for that source. An omitted association field SHALL leave associations unchanged; an empty array SHALL remove all current associations. Subsequent automatic discovery SHALL NOT add unselected Personas, remove selected Personas or overwrite human-controlled name, type, pause or permission settings. Removing an association SHALL preserve its history and prevent automatic rediscovery from silently restoring it. It SHALL NOT stop collection for another eligible associated Persona.

#### Scenario: Remove one of two roles
- **WHEN** the user removes Persona A and keeps Persona B
- **THEN** future selection for A excludes the source, B can continue using it, history is retained and automatic discovery cannot restore A

#### Scenario: A profile changes after manual selection
- **WHEN** a selected Persona's discovery-relevant profile is revised
- **THEN** the manual source association remains selected, execution uses the current profile snapshot and source relevance is evaluated against the revised positioning

#### Scenario: Selected role is paused or incomplete
- **WHEN** a selected Persona is paused, archived or lacks an eligible profile
- **THEN** the association remains visible with its inactive reason while collection/use for that Persona is prevented until it becomes eligible

### Requirement: Unified configuration and visible operational state

The source panel SHALL allow editors to configure display name, source type, Persona associations, collection pause and model-processing permission for either source origin. It SHALL display source origin, submitted and collector URLs, associated Personas, validation/collection status, last success and failure reason. It SHALL support role and origin filtering and pagination so all saved sources remain reachable. Existing pause-only or permission-only API clients SHALL remain compatible without altering association mode. Configuration mutations SHALL be auditable.

#### Scenario: Configure an existing automatic source
- **WHEN** an editor opens its configuration form
- **THEN** current values and associations are prefilled and an explicit save records the chosen manual settings without losing its automatic-discovery provenance

#### Scenario: Search for a manually reserved source
- **WHEN** the user filters by manual origin and browses the source list pages
- **THEN** saved manual sources including unassociated and unavailable entries remain accessible with accurate state

### Requirement: Manual sources use the same scheduling and quality boundaries

Validated manual sources SHALL enter the existing collection and daily opportunity pipeline only when owner settings, source permissions, Persona eligibility, subscriptions and existing capacity allow. Capacity limitations SHALL be visible without silently evicting other sources or expanding the configured budget. Global automatic-research pause SHALL still prevent automatic use while permitting source configuration and explicit validation. Manual selection SHALL NOT guarantee an opportunity, bypass article-body/date/grounding checks, change the daily time, reset quotas or trigger a same-day top-up. Original, republication/update and event dates, evergreen/current classification, duplicate merging, source diversity and the maximum of five daily opportunities per Persona SHALL apply unchanged.

#### Scenario: A manually selected source has only weak or old material
- **WHEN** collected items lack usable body evidence or only republish an old event
- **THEN** existing quality gates exclude unsupported candidates or treat supported older material as evergreen, without filling a quota

#### Scenario: Existing active-source capacity is full
- **WHEN** a newly selected source cannot be activated within the existing role capacity
- **THEN** the chosen configuration is retained with a visible pending-capacity reason, other sources are not evicted and the background process rechecks when capacity becomes available

#### Scenario: A source is added after today's daily batch
- **WHEN** a source becomes ready after the Persona has completed today's generation
- **THEN** normal future scheduled work can consume it without resetting today's generation count or creating a manual top-up

### Requirement: Ownership and evidence permissions remain enforced

All source reads, writes, role associations and validation requests SHALL enforce existing owner/editor access. Cross-owner Persona IDs SHALL be rejected atomically. Source URLs SHALL use existing destination, redirect, size and time controls, and page content SHALL remain untrusted data. Manual selection or verification SHALL NOT grant public reproduction rights, authorize arbitrary code execution or automatically confirm project facts.

#### Scenario: Cross-owner association attempt
- **WHEN** an editor submits a role belonging to another owner together with otherwise valid roles
- **THEN** the request is rejected without partial source or association updates

#### Scenario: The source requests commands or credentials
- **WHEN** fetched content contains instructions to run commands or supply credentials
- **THEN** it is processed only as source data and does not alter application authority or configuration

