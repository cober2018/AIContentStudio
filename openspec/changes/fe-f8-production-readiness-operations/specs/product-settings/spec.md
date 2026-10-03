## ADDED Requirements

### Requirement: Settings reflects the active authentication and runtime mode
Team & Permissions and Advanced Settings SHALL project the actual active development/test/production auth and required runtime configuration from the backend without pretending that Organization, Invite, Tenant or SSO administration exists. Safe read views SHALL not expose token issuer secrets, raw storage locations, provider credentials or internal diagnostics, and editability SHALL still derive from durable API support plus caller role.

#### Scenario: Production auth active
- **WHEN** a user opens Team Settings while the secure production identity adapter is active
- **THEN** the UI shows that mode and the mapped durable User/Role without claiming Header authentication or rendering an unsupported SSO-management control

#### Scenario: Read operational status
- **WHEN** a non-admin inspects safe Advanced Settings
- **THEN** required readiness categories may be summarized without disclosing raw error text, filesystem paths, secret values or admin-only configuration

#### Scenario: Explicit operational refresh
- **WHEN** an authorized operator explicitly requests an operational status refresh
- **THEN** the UI reads the existing readiness endpoint and shows only bounded required-dependency statuses, distinguishing a failed check from an unreadable result; ordinary Settings inventory and navigation do not trigger the probe and no model/publisher is called
