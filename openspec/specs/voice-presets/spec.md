# voice-presets Specification

## Purpose
TBD - created by archiving change voice-presets-by-persona. Update Purpose after archive.
## Requirements
### Requirement: Named voice presets

Settings SHALL hold several named voice presets (voice, emotion, rate, volume, pitch and audio format), one of them the default. The existing single voice setting SHALL become a preset named 男声 and the default. A preset in use as default or by a persona SHALL not be deleted.

#### Scenario: Add a female preset
- **WHEN** the user creates a preset named 女声 with a female voice
- **THEN** it appears in the list and can be chosen by personas

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

