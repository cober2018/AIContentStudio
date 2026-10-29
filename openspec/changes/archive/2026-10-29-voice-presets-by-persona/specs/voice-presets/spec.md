## ADDED Requirements

### Requirement: Named voice presets

Settings SHALL hold several named voice presets (voice, emotion, rate, volume, pitch and audio format), one of them the default. The existing single voice setting SHALL become a preset named 男声 and the default. A preset in use as default or by a persona SHALL not be deleted.

#### Scenario: Add a female preset
- **WHEN** the user creates a preset named 女声 with a female voice
- **THEN** it appears in the list and can be chosen by personas and works

### Requirement: Voice follows the owning persona

A persona SHALL choose one voice preset. A product work SHALL be launched under an optional account persona, borrowing only its voice and account identity. A work MAY override with another preset. Voiceover SHALL use the work override, else the persona's preset, else the default, and report which preset it used; drama-type role voices stay per role with the narrator on that preset.

#### Scenario: Product work under the e-commerce persona
- **WHEN** a product work is launched under a persona whose preset is 女声 and has no override
- **THEN** its voiceover uses the 女声 preset

#### Scenario: Work override
- **WHEN** that work picks 男声 as its own preset
- **THEN** its voiceover uses 男声 while the persona keeps 女声
