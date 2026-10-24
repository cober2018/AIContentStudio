## ADDED Requirements

### Requirement: Fill storyboard material automatically

The 分镜表 SHALL offer one user-started action that fills material for every row with no material yet. It searches the own library and licensed stock sites first, then uses a ready AE template, and leaves the row as a gap with a reason when neither fits.

#### Scenario: Stock footage fits
- **WHEN** a row's best search candidate is eligible
- **THEN** the platform accepts it into the project under its licence and the row shows the source and score

#### Scenario: Row made in post
- **WHEN** a row is marked as made in post and a ready template fits
- **THEN** the platform renders the template with content from the row and the row shows the template and version

#### Scenario: Nothing fits
- **WHEN** neither a candidate nor a template fits
- **THEN** the row shows 缺口 with the reason

### Requirement: The user's choices are kept

The auto-fill SHALL NOT replace a row's existing pick or bound material, and SHALL NOT bind material into the master or save it.

#### Scenario: Row already picked
- **WHEN** the user picked material for a row before auto-fill
- **THEN** that row is left as it is

#### Scenario: After auto-fill
- **WHEN** auto-fill finishes
- **THEN** the master is unchanged until the user puts the picks into the draft and saves

### Requirement: Every automatic pick is traceable

Each automatic pick SHALL record its source (stock site and score, or template id, version and content hash) and the reason, and the 素材 column SHALL show it.

#### Scenario: Look at a filled row
- **WHEN** the user looks at an automatically filled row
- **THEN** it shows 自动 with the source, and the slot shows the reason
