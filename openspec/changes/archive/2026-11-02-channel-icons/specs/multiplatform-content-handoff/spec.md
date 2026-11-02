## ADDED Requirements

### Requirement: Channel names show the platform's own icon

Wherever the studio shows a channel name outside a dropdown, it SHALL show that platform's own site icon, stored locally, before the name. A channel without an icon SHALL show the name alone. Icons SHALL only identify the channel in the studio's interface.

#### Scenario: Account cards with the same name
- **WHEN** the account directory lists 知数Talk on 公众号 and 知数Talk on 小红书
- **THEN** each card shows its platform's icon next to the platform name

#### Scenario: Unknown channel
- **WHEN** a channel has no stored icon
- **THEN** only the text name is shown and nothing breaks
