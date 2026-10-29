## ADDED Requirements

### Requirement: Stock sources are configured on the settings page

The settings page SHALL list every open media source with its description, license, whether a key is required, configuration state, an enable switch and a link to get a key. Keys SHALL be saved on the server and SHALL only be returned masked.

#### Scenario: Save a key
- **WHEN** an admin enters a Pexels key and saves
- **THEN** Pexels shows as configured with a masked key, and material search includes Pexels

#### Scenario: Key never returned
- **WHEN** the settings are read
- **THEN** no source key appears in plaintext in the response

#### Scenario: Existing env key kept
- **WHEN** a source has a key in runtime.env and was never saved on the page
- **THEN** it shows as configured and keeps working

### Requirement: Disabled sources are not searched

A source switched off on the settings page SHALL NOT be used by material search.

#### Scenario: Switch off a source
- **WHEN** an admin turns off Pixabay
- **THEN** the next material search returns no Pixabay candidates

### Requirement: Source test

The settings page SHALL let an admin test one source; the platform SHALL run one small search and report success or the failure reason without downloading media.

#### Scenario: Wrong key
- **WHEN** an admin tests a source with an invalid key
- **THEN** the page shows the test failed and why

### Requirement: Coverr video source

The platform SHALL search Coverr for video when it is configured and enabled, and register its license on accepted candidates.

#### Scenario: Coverr candidate
- **WHEN** Coverr is configured and a shot needs video
- **THEN** material search can return Coverr candidates with the Coverr license
