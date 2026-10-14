## ADDED Requirements

### Requirement: Daily Persona → Series → content → targets journey

The primary product journey SHALL let users begin from a Persona and editorial Series, enter the existing Project/Creation Recipe creation chain without requiring a destination Account, and later select one or more explicit channel Accounts for Variant review and handoff.

#### Scenario: Technology creator multi-target end-to-end
- **WHEN** the AI technology Persona creates an article Master in a Persona-owned Series
- **AND** selects valid WeChat, Zhihu and Xiaohongshu target Accounts
- **THEN** the product can prepare separate platform forms, validate them, obtain review and create the corresponding independently traced handoff/authorized draft outcomes

#### Scenario: Lifestyle Persona is isolated
- **WHEN** the lifestyle Persona creates another Unit with its own editorial Series
- **THEN** its skills/styles/voice/target selections are derived from that Persona's explicit configuration
- **AND** no configuration from the technology Persona is implicitly inherited
