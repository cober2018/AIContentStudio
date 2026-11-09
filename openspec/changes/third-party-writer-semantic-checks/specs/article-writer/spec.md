## ADDED Requirements

### Requirement: Graphic semantic checks follow the writer switch
For a graphic piece, the semantic checks graphic_fact and graphic_identity SHALL be run by the model that the writer switch selects: the platform's configured model when the writer is 平台模型, and the third-party model over MCP when the writer is 第三方模型. The platform SHALL NOT call the platform-configured model for a third-party-written piece.

#### Scenario: Third-party writer waits for the third-party check
- **WHEN** a graphic piece's writer is 第三方模型 and its semantic checks have not been submitted
- **THEN** the checks show 等待第三方复核, are not recorded as pass, and the piece cannot be frozen as a candidate

#### Scenario: Third-party submits a check result
- **WHEN** the third-party model submits a result for the current input_hash through MCP
- **THEN** the check records the submitting model's identity, its coverage shows semantic verified, and the piece can proceed to freeze

#### Scenario: Stale submission is rejected
- **WHEN** a submitted result carries an input_hash that no longer matches the current draft
- **THEN** the platform rejects it and the check stays waiting

#### Scenario: Platform writer is unchanged
- **WHEN** a graphic piece's writer is 平台模型
- **THEN** the checks run on the platform-configured model exactly as before
