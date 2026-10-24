## ADDED Requirements

### Requirement: Auditable module coverage
The design SHALL map every current App.tsx route to a task, destination, and keep/change/compatibility decision, with evidence and explicit prototype depth.

#### Scenario: Existing improved workflow
- **WHEN** a route belongs to the improved product six-step or persona five-step workflow
- **THEN** the design preserves its internals and demonstrates only its entry and exit boundaries

### Requirement: Isolated interactive prototype
The prototype MUST use labeled simulated data without production writes, generation, or publication and SHALL provide navigable module pages and browser history.

#### Scenario: Simulated save
- **WHEN** a user saves or confirms in the prototype
- **THEN** only prototype state changes and the receipt explicitly identifies the action as simulated

### Requirement: Task-based information hierarchy
Each page SHALL have a clear purpose and primary action; list, detail, edit and history SHALL have distinct places without forcing resource management into a linear wizard.

#### Scenario: Opportunity detail
- **WHEN** a user opens a recommended topic
- **THEN** the page presents the recommendation, proposed direction, reference sources and unresolved gaps before technical history or manual evaluation

### Requirement: Preserve decision and evidence boundaries
The prototype SHALL distinguish automatic results, human revisions, absent analysis, failures and existing projects; project evidence selection, content approval, delivery authorization and reusable preference activation remain explicit separate decisions.

#### Scenario: Missing results
- **WHEN** no evaluation exists or processing fails
- **THEN** the page explains the current state without inventing scores or claiming a successful analysis

#### Scenario: Delivery confirmation
- **WHEN** a user approves sample content
- **THEN** the prototype does not label it publicly published or implicitly approve a delivery account

### Requirement: Usable pagination and return paths
The prototype SHALL demonstrate list filtering and pagination, independent detail URLs, browser return, persistent in-session drafts, keyboard operation and responsive layouts.

#### Scenario: Return from detail
- **WHEN** a user returns to a filtered list
- **THEN** the chosen filter and page remain available and the action does not silently modify business data

### Requirement: Production work list separates operational records
The production entry SHALL prioritize existing works and their continue actions while task and execution records use a separate addressable view. Filters and pagination SHALL persist in the URL and permission-checked lifecycle actions SHALL retain existing historical protection. Default navigation and refresh SHALL NOT request operational records while that view is closed.

#### Scenario: Continue an existing work
- **WHEN** a user selects continue from a work list
- **THEN** the existing unit production route opens without changing its workflow, identity snapshot or data

#### Scenario: Inspect task records
- **WHEN** a user explicitly opens operational records
- **THEN** the page reads the bounded native/external records, preserves unknown and read-error states, and does not execute or retry tasks

#### Scenario: Return to filtered work list
- **WHEN** a user returns from production or project details
- **THEN** the list URL restores filter, archive visibility and page state


### Requirement: Published performance review has separate task views
The learning entry SHALL separate published works, individual observations, comparable analysis, improvement candidates and reusable memory decisions. Default reading SHALL NOT display every mutation form or trigger an analysis or write. Existing learning deep links SHALL remain usable.

#### Scenario: Missing measurements
- **WHEN** a published work has no observations or comparable metrics
- **THEN** the page explains what is missing without filling missing values with zero or claiming an automatic analysis

#### Scenario: Explicit reuse
- **WHEN** an accepted candidate is opened
- **THEN** adopting its frozen claim as scoped memory and creating a reusable method remain separate explicit actions and read-only users cannot mutate them

### Requirement: Task-oriented settings preserve existing model configuration
The settings entry SHALL show a purpose-based directory with separate addressable categories and bounded record pages. Existing model configuration internals, lazy mounted drafts and leave confirmation SHALL be preserved. Raw metadata SHALL be secondary to task actions.

#### Scenario: Enter model configuration
- **WHEN** a user enters the models category
- **THEN** the existing provider, routing and capability tools retain their original behavior and saved values

#### Scenario: Return from a settings category
- **WHEN** the user returns or reloads a category URL
- **THEN** category and pagination remain located and unsaved edits require an explicit discard before leaving
