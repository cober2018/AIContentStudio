## MODIFIED Requirements

### Requirement: Snapshot-backed Data Node
A Data Node SHALL use a typed, extensible Data Source Plugin registry distinct from Tool nodes. Its descriptor SHALL expose key, name, category, connection mode, search/query/snapshot capabilities, configuration schema, result schema, and server-derived availability/reason. The registry and selector SHALL represent internal data, media data, Notion, Obsidian, API, and SQL/Database without making Studio Source the only possible implementation. A configured executable plugin SHALL persist an immutable bounded snapshot with source/version identity, checksum, lineage, normalized output, and refresh time; downstream nodes SHALL consume its snapshot ID. Changed refresh output MUST mark actual dependent outputs stale; unchanged output MUST NOT stale them. Disconnected or unverified plugins MUST be visibly unavailable and MUST NOT execute successfully.

#### Scenario: Changed source
- **WHEN** a configured read-only Data Node refreshes and its new snapshot hash differs
- **THEN** the previous snapshot remains inspectable and dependent succeeded outputs become stale

#### Scenario: Unavailable source
- **WHEN** the selected plugin is not configured or access is denied
- **THEN** the node is blocked with a reason and no synthetic successful snapshot is created

#### Scenario: Select a disconnected plugin
- **WHEN** an editor selects Notion, Obsidian, media data, API, or SQL without a verified connector
- **THEN** the selector retains the typed plugin configuration but labels it disconnected/unexecutable, and Run Node cannot produce a successful attempt

#### Scenario: Unchanged source
- **WHEN** a Data Node refresh produces the same normalized output checksum
- **THEN** the new refresh remains auditable without marking dependent successful steps stale

The typed Data Source Plugin registry SHALL remain authoritative for Data Node availability/capabilities. Product Settings MAY expose and manage related connector configuration, but MUST NOT create a second plugin registry or mark an unavailable plugin executable without verified runtime support.

#### Scenario: Settings shows disconnected plugin
- **WHEN** a registered Data Source Plugin is unavailable
- **THEN** Settings shows the same unavailable reason that prevents Data Node execution

#### Scenario: Connector configuration does not imply plugin executor
- **WHEN** a generic Connector is configured
- **THEN** Data Source Plugin execution eligibility changes only through its explicit verified runtime contract
