## MODIFIED Requirements

### Requirement: Voice follows the owning persona

A persona SHALL have exactly one voice preset; one preset MAY serve several personas. A product work SHALL be launched under an optional account persona, borrowing only its voice and account identity. A work SHALL NOT pick its own preset: voiceover SHALL use the persona's preset, else the default, and report which preset it used; drama-type role voices stay per role with the narrator on that preset.

#### Scenario: Product work under the e-commerce persona
- **WHEN** a product work is launched under a persona whose preset is 女声
- **THEN** its voiceover uses the 女声 preset

#### Scenario: Two videos of one persona
- **WHEN** two video works both belong to 懒羊羊小王
- **THEN** both voiceovers use 懒羊羊小王's voice preset

#### Scenario: No per-work pick
- **WHEN** someone tries to set a voice on a single work
- **THEN** the platform offers no such option and the API has no such route
