## ADDED Requirements

### Requirement: Brands keep brand information, separate from personas

A brand SHALL have its own profile: introduction, proposition, offerings, tone rules, preferred and forbidden words, logo materials, colors, fonts, and red lines. Personas, accounts and series SHALL NOT inherit persona fields from the brand.

#### Scenario: Persona under a brand
- **WHEN** a persona with no positioning belongs to a brand
- **THEN** the persona's effective positioning stays empty and the brand appears as its own block

### Requirement: Brand information reaches creation

Video and article briefs for the third-party model, and platform-model task packages, SHALL include the brand block frozen in the work's identity snapshot. Brand forbidden words and red-line phrases SHALL be checked deterministically on the master together with the persona's forbidden phrases.

#### Scenario: Forbidden brand word in a draft
- **WHEN** a text master under a persona of brand 知数造物 contains a word on the brand's forbidden list
- **THEN** the master check reports a blocker naming the brand rule

#### Scenario: Existing works
- **WHEN** a work was created before this change
- **THEN** its identity snapshot is unchanged
