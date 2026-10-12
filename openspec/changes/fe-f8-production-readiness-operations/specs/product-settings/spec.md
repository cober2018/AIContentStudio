## ADDED Requirements

### Requirement: Settings reflects the active authentication and runtime mode
Team & Permissions and Advanced Settings SHALL project actual backend development/test/production technical auth/runtime values without pretending that Organization, Invite, Tenant or SSO exists. The owner's final deployment is single-machine production regardless of an unchanged development-labeled technical mode; documentation MUST NOT infer a formal-use blocker or require a new login/configuration system from that label. Safe reads SHALL not expose issuer secrets, raw storage locations, provider credentials or internal diagnostics, and editability SHALL derive from durable API support plus caller role.

#### Scenario: Production auth active
- **WHEN** a user opens Team Settings while the optional technical server-extension secure identity adapter is active
- **THEN** the UI shows that mode and the mapped durable User/Role without claiming Header authentication or rendering an unsupported SSO-management control

#### Scenario: Read operational status
- **WHEN** a non-admin inspects safe Advanced Settings
- **THEN** required readiness categories may be summarized without disclosing raw error text, filesystem paths, secret values or admin-only configuration

#### Scenario: Explicit operational refresh
- **WHEN** an authorized operator explicitly requests an operational status refresh
- **THEN** the UI reads the existing readiness endpoint and shows only bounded required-dependency statuses, distinguishing a failed check from an unreadable result; ordinary Settings inventory and navigation do not trigger the probe and no model/publisher is called
