## ADDED Requirements

### Requirement: One visual system across the studio

Every page SHALL use shared design tokens for colour, type, spacing, radius and shadow, and the shared shell and components. Pages MUST NOT introduce one-off hex colours or bespoke button styles.

#### Scenario: Consistent pages
- **WHEN** a user moves between home, projects, production and 角色与账号
- **THEN** headers, sections, buttons, badges and spacing look and behave the same

### Requirement: Navigation follows the content workflow

The main navigation SHALL group pages by the confirmed workflow (today, content, review & publishing, assets, growth review, identity, settings) and SHALL list only modules that exist.

#### Scenario: Module not built yet
- **WHEN** a workflow module such as brand deals has no implementation
- **THEN** it does not appear in navigation

### Requirement: Structured data is readable

Profiles, creative configuration and other structured records SHALL render as labelled, human-readable sections; raw JSON or `key: value` dumps MUST only appear inside an explicit raw-data disclosure.

#### Scenario: Persona overview
- **WHEN** a user opens a persona's overview
- **THEN** positioning, audience, domains, expression, boundaries and creative stages are shown as readable sections, and the raw profile is available only on request
