## ADDED Requirements

### Requirement: Agents run stages and read options through MCP
The creative MCP server SHALL expose `preview_stage`, `run_stage` and `get_stage_result` for production stages of units owned by the MCP owner. They SHALL use the same resolution-hash, invocation-key and tunable-field rules as the web stage routes. `get_stage_result` SHALL include a `review_url` pointing to the platform page where the user decides.

#### Scenario: Agent runs the graphic layout stage
- **WHEN** the agent calls `run_stage` for a graphic `master` stage with the current resolution hash
- **THEN** the platform records the attempt as on the web, and returns its status and a review URL without accepting anything

### Requirement: Agents cannot decide on the user's behalf
The MCP server MUST NOT expose any tool that accepts, accepts with edits, rejects, records feedback for, binds, approves or publishes stage results or materials.

#### Scenario: Tool list
- **WHEN** an MCP client lists tools
- **THEN** no tool maps to stage adoption, stage feedback, material match acceptance, shot binding, approval or delivery

### Requirement: The user's decision is readable as a signal
`get_stage_decision` SHALL return one of `waiting_for_you`, `accepted`, `accepted_with_edits`, `rejected`, `rerun_requested` or `commented`. It SHALL also return the user's note, the chosen candidate id, the accepted result id and hash, and the continuation stage when present. With `wait_seconds` between 1 and 25 it SHALL return as soon as the state leaves `waiting_for_you`, or when the wait ends.

#### Scenario: User rejects with a reason
- **WHEN** the user rejects a graphic option on the platform with the note "封面太空"
- **THEN** `get_stage_decision` for that attempt returns `rejected` with note "封面太空"

#### Scenario: User accepts
- **WHEN** the user accepts option 2 and the platform continues to `quality`
- **THEN** `get_stage_decision` returns `accepted`, the candidate id of option 2, the new Master revision and continuation `quality`

### Requirement: Graphic options are shown as images before deciding
The stage review page SHALL show each canvas of each graphic candidate as a PNG rendered by the platform renderer, before any acceptance. Previews SHALL be cached by payload hash and canvas id. They MUST NOT create materials, render attestations or Master revisions.

#### Scenario: Review a card set
- **WHEN** a graphic layout attempt is waiting for the user
- **THEN** the review page shows a thumbnail per card for each option, and a larger view on click

#### Scenario: Renderer not configured
- **WHEN** the renderer runtime is unavailable
- **THEN** the review page shows the existing text view with a "预览不可用" note, and acceptance still works

### Requirement: Footage choices support pick and reject with signal
Agents SHALL start material match runs and read them through MCP (`start_material_match`, `get_material_match`). Each segment SHALL let the user pick one candidate ("用这个", existing) or reject all with a short note ("都不合适"). `get_material_match` SHALL return each segment's picks and rejection notes, and a review URL.

#### Scenario: User rejects a segment
- **WHEN** the user marks shot 9's candidates "都不合适" with note "要现代布缆船"
- **THEN** `get_material_match` returns shot 9 as rejected with that note, and the agent can start a new search
