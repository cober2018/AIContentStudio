# product-settings Specification

## Purpose

Define the product-facing Settings workspace over existing model/runtime settings, Data Source Plugin descriptors, Connectors, Channel Registry, Rule Registry, templates and current user/role data. Preserve each underlying registry/configuration as the source of truth and distinguish editable, read-only and unavailable capability states.

## Requirements

### Requirement: Settings uses product-oriented sections

The Settings workspace SHALL organize Models & AI, Data Sources, Channels, Rules & Templates, Team & Permissions, and Advanced Runtime/Security as distinct sections.

#### Scenario: Open Settings
- **WHEN** the user opens `/settings`
- **THEN** product concepts are visible without requiring ordinary users to understand raw provider/registry internals

### Requirement: Editability is truthful

Every settings item SHALL expose whether it is editable, read-only or unavailable based on real backend capability.

#### Scenario: Read-only channel registry
- **WHEN** a Channel Registry field has no durable mutator
- **THEN** Settings displays it read-only and does not render a fake Save action

#### Scenario: Disconnected Data Source Plugin
- **WHEN** Notion/Obsidian/media/API/SQL plugin descriptor is unavailable
- **THEN** Settings shows the registered reason and does not claim connection success

### Requirement: Model settings reuse existing persistence

Models, routes, LLM/image provider configuration and secret masking SHALL continue using existing SystemSetting/runtime configuration services.

#### Scenario: Secret display
- **WHEN** the user views a configured API key
- **THEN** only masked/configured metadata is returned and plaintext secrets are never serialized

### Requirement: Data Source settings mirror typed plugin registry

Data Source settings SHALL expose the FE-F2 typed plugin descriptors and existing Connector configuration without introducing a second plugin registry.

#### Scenario: Studio Source
- **WHEN** `studio.source` is listed
- **THEN** its actual executable/internal capabilities are shown from the descriptor

#### Scenario: Generic Connector exists
- **WHEN** an API Connector is configured
- **THEN** it is shown as connector configuration but MUST NOT automatically mark unrelated Data Source Plugin keys connected unless an explicit mapping contract exists

### Requirement: Channel settings mirror Channel Registry

Channel settings SHALL display channel/content-form/workflow/renderer/rule/discoverability/publisher metadata from the existing Channel Registry.

#### Scenario: Channel capability changes
- **WHEN** registry configuration changes
- **THEN** Settings reflects the new registry state without copying it into another table

### Requirement: Rules and templates remain distinct

Deterministic Rule descriptors SHALL be shown separately from PromptVersion, ChannelTemplateVersion and Discoverability profile/template resources.

#### Scenario: Inspect rule
- **WHEN** a deterministic rule is listed
- **THEN** it is labeled Rule with key/version and not represented as a Prompt

### Requirement: Team reflects current auth reality

Team & Permissions SHALL show existing users/roles and current development-header auth mode without claiming production organization, invite, SSO or tenant administration that is not implemented.

#### Scenario: Open Team
- **WHEN** the user opens Team settings
- **THEN** current users/roles and auth-mode limitations are explicit

### Requirement: Existing authorization remains enforced

Admin-only Settings/Connector/Template mutations SHALL remain admin-only; safe read views follow current authenticated-user contracts.

#### Scenario: Non-admin mutation
- **WHEN** a non-admin invokes an admin-only settings mutation
- **THEN** the existing authorization denial remains effective
