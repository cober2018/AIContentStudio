## ADDED Requirements

### Requirement: Home includes Creative Execution decisions from authoritative state

Home MAY project owned CreativeExecution actions including `result_ready`, `blocked`, `unknown` and explicit human-review requests. Home MUST NOT create duplicate execution task state. Unknown external execution SHALL have the same high operational precedence as other unresolved uncertain side effects.

#### Scenario: Professional execution result is ready
- **WHEN** a CreativeExecution has bounded staged outputs awaiting human acceptance
- **THEN** Home shows one result-review action linking to the exact execution without claiming content approval or publication

#### Scenario: External execution is unknown
- **WHEN** the system cannot prove whether a professional tool mutation completed
- **THEN** Home prioritizes reconciliation and does not offer an automatic retry action

### Requirement: Home supports direct creation without forcing opportunity flow

Home SHALL provide a direct path to create/open a ContentProject for a known idea while keeping Opportunity triage optional and authoritative for opportunity-backed projects.

#### Scenario: User has a direct idea
- **WHEN** the user chooses to start content without an Opportunity
- **THEN** a normal Project can be created and no fake Opportunity/assessment is inserted
