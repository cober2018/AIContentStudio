## ADDED Requirements

### Requirement: Persona cards show the brand logo

Each card in the persona directory SHALL show a small square image of its brand's most square saved logo below the brand name. Cards SHALL show no image when the persona has no brand or the brand has no logo.

#### Scenario: Persona under a brand with a logo
- **WHEN** the persona list shows 「AI科技研发技术博主」 under brand 知数造物, which has saved logos
- **THEN** the card shows the square logo as a small square below 「知数造物」

#### Scenario: Brand without logo
- **WHEN** a persona's brand has no saved logo
- **THEN** the card shows only the brand name
