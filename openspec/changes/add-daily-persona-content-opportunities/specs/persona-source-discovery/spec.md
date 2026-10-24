## ADDED Requirements

### Requirement: Persona changes automatically initiate research

The system SHALL persist a source-discovery task in the same transaction that creates the first eligible Persona revision or changes its discovery-relevant profile hash. Eligibility SHALL require an active owner-controlled Persona with positioning, audience and domains. Tasks SHALL be picked up by the background worker without a page visit or a manual command. The system MUST NOT hard-code the two starter Persona IDs. Voice-only or presentation-only changes MUST NOT schedule new discovery.

#### Scenario: A new eligible Persona
- **WHEN** the user saves a new Persona with the required profile fields and automatic discovery is enabled
- **THEN** a durable pending research task is created and the worker researches sources and creates the first opportunity batch automatically

#### Scenario: A placeholder or voice-only change
- **WHEN** a Persona has no eligible profile, or only its voice configuration changes
- **THEN** no new source-discovery task is created and the UI distinguishes incomplete positioning from pending research

#### Scenario: Relevant changes and repeated delivery
- **WHEN** positioning changes and the same task is delivered twice
- **THEN** one logical research run exists for the new profile hash and an old-profile run cannot replace current subscriptions or produce current-profile recommendations

### Requirement: Evidence-backed source and creator discovery

The system SHALL derive bounded search queries from Persona positioning, audience, domains and boundaries and execute them through a verified background web-search provider. Candidates SHALL include relevant official sources, media, creators and communities. Every saved candidate MUST contain a real reference URL, discovery-run reference, relevance explanation, language and available identity evidence. Model-recalled URLs or fabricated follower counts MUST NOT qualify as verified discoveries.

#### Scenario: Discover a creator
- **WHEN** search results identify a relevant creator and the worker verifies their public homepage or linked platform identity
- **THEN** the system saves the creator and public entry points with verification evidence and the relevant Persona subscription

#### Scenario: Search is unavailable
- **WHEN** no configured searchable runtime is available
- **THEN** the run reports search_unavailable, stored healthy sources remain usable, and the system does not report successful autonomous expansion

### Requirement: Source registry and automatic activation

The system SHALL retain owner-scoped source records and Persona subscriptions. Canonical endpoints SHALL be unique per owner and reusable by multiple owned Personas. New public sources SHALL be automatically activated only after a supported collector successfully validates item titles, links, dates and content scope and the approved model-processing policy permits their use. No per-source manual click SHALL be required for this normal path. Unavailable adapters, credentials, parsing or identity verification SHALL produce distinct retained candidate states. A manually paused source MUST NOT be silently re-enabled by rediscovery.

#### Scenario: A valid RSS source
- **WHEN** a newly discovered site exposes an RSS or Atom feed and validation succeeds
- **THEN** the source is stored and scheduled automatically for all relevant enabled subscriptions

#### Scenario: A restricted platform account
- **WHEN** a creator's identity is verified but its feed requires an unavailable login or adapter
- **THEN** the registry keeps the account and evidence with credential_required or adapter_unavailable while other sources continue

#### Scenario: Two Personas share a source
- **WHEN** the same owner discovers the same canonical source for both Personas
- **THEN** one source is collected and two distinct relevance/subscription records are maintained

### Requirement: Incremental collection preserves source time

Collectors SHALL support RSS/Atom and validated public HTML/JSON lists, including configured third-party hotlists. They SHALL store canonical item identity, original URL, source published time when verified, collection time, content checksum, bounded text scope and adapter provenance. Identical repeated fetches MUST NOT create duplicate evidence. Changed content SHALL retain an immutable new version. Cursors SHALL advance only after successful persistence; per-source failures MUST NOT discard other successful sources. HTTP 304 SHALL mean no new data, not an error.

#### Scenario: Newly imported old material
- **WHEN** initial collection encounters material older than the current 48-hour hot window or without a verified publication time
- **THEN** it is retained as background/undated material and cannot be labeled today's new event because it was collected today

#### Scenario: One source fails
- **WHEN** one source times out while other sources return valid items
- **THEN** its cursor remains unchanged, its failure is recorded for backoff, and valid evidence from other sources is committed

### Requirement: Automatic maintenance and Persona lifecycle

The system SHALL run weekly bounded source expansion and source-specific refresh/recovery schedules. Pausing or archiving a Persona SHALL prevent new provider dispatches and opportunity writes for that Persona, including queued tasks. A shared source SHALL remain active while another enabled subscription requires it. New valid Personas SHALL automatically use the same policy after global setup.

#### Scenario: A Persona is archived during research
- **WHEN** a Persona is archived after a task was queued or while a provider response is pending
- **THEN** no subsequent dispatch or new opportunity for it is allowed; already received response and accounting remain recorded

### Requirement: Source handling and execution boundaries

Automatic public research SHALL use the approved public-source model-processing policy and recheck it at dispatch. It MUST NOT grant public reproduction rights, expose private project/knowledge data to search, automatically confirm facts, or execute commands found in pages or model-generated collector configurations. URL access SHALL reuse the application's destination, redirect and size controls. All registry reads, retries and settings mutations SHALL enforce owner/editor access.

#### Scenario: A page contains instructions
- **WHEN** a retrieved page or model response contains instructions to execute code or change application configuration
- **THEN** the content is treated only as source data and does not gain execution authority

#### Scenario: Another owner's source
- **WHEN** an unrelated owner requests a source, its items, settings or run
- **THEN** access is denied without revealing source content or credentials
