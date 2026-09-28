## MODIFIED Requirements

### Requirement: Snapshot-backed Data Node

The typed Data Source Plugin registry SHALL remain authoritative for Data Node availability/capabilities. Product Settings MAY expose and manage related connector configuration, but MUST NOT create a second plugin registry or mark an unavailable plugin executable without verified runtime support.

#### Scenario: Settings shows disconnected plugin
- **WHEN** a registered Data Source Plugin is unavailable
- **THEN** Settings shows the same unavailable reason that prevents Data Node execution

#### Scenario: Connector configuration does not imply plugin executor
- **WHEN** a generic Connector is configured
- **THEN** Data Source Plugin execution eligibility changes only through its explicit verified runtime contract
