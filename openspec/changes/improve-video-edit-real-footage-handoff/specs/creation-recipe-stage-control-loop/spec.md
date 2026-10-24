## ADDED Requirements

### Requirement: Video planning stages see the project material catalog
For persona video units, script and shot-plan stage context SHALL include the project's actively referenced MaterialRevisions that allow model use (image, video, audio), each with kind, title, source kind, duration when known and rights flags including local-only status, as exact reference catalog entries. Plans MAY cite these entries in structured references such as the shot-plan reference index; any reference outside the supplied catalog SHALL still be rejected. Restricted local-only material SHALL stay marked so plans do not treat it as publishable. Product-domain video units keep their existing product material context.

#### Scenario: Real demo footage is referenced in the project
- **WHEN** a project references two model-use demo videos and a shot-plan stage runs
- **THEN** the stage receives both as catalog entries and an accepted plan can cite them by exact revision

#### Scenario: A plan cites unregistered material
- **WHEN** a shot plan cites a MaterialRevision not in the supplied catalog
- **THEN** the attempt is rejected as invalid output
