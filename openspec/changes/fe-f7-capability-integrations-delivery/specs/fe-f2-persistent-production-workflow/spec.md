## ADDED Requirements

### Requirement: Mapped Connector Data Nodes preserve typed execution gates
The typed Data Source Plugin registry SHALL remain authoritative even when an explicit CapabilityRegistration maps one plugin key to a ConnectorEndpoint. Mapping SHALL include exact endpoint/version, caller/project authorization and safe configuration identity; Workflow Run SHALL freeze a bounded DataSnapshot with source/version/checksum/lineage and retain existing changed-versus-unchanged stale propagation. A generic Connector pull MUST NOT implicitly bind Fact Boundary or make other plugin keys executable.

#### Scenario: Exact mapped endpoint changes
- **WHEN** a mapped endpoint returns changed normalized data during a Data Node refresh
- **THEN** a new snapshot records the endpoint/source identity and dependent succeeded outputs become stale under the existing engine

#### Scenario: Unmapped plugin key
- **WHEN** a Connector is configured but the selected Data Source Plugin has no authorized mapping
- **THEN** the node is blocked with a reason and records no successful synthetic snapshot
