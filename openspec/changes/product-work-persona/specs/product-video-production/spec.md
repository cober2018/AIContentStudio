## ADDED Requirements

### Requirement: Every product work can choose and change its persona

A product video work SHALL let the user choose a persona at creation and change it later on the work page, including choosing none, until the 成片 is finalized. Only the user's own active personas SHALL be selectable. The chosen persona SHALL drive the voiceover voice and the persona portrait used for generated people from then on, without changing already generated audio or images, product facts, production settings or the 导演稿, and without creating an identity snapshot. Each change SHALL be recorded as a project event.

#### Scenario: Setting a persona on an existing work
- **WHEN** the user sets work 92's persona to 懒羊羊小王
- **THEN** the next voiceover uses 懒羊羊小王's voice and the brief's people rule follows that persona's portraits

#### Scenario: Finalized work
- **WHEN** work 90's 成片 is finalized
- **THEN** its persona cannot be changed

#### Scenario: Persona without a voice
- **WHEN** the user picks a persona that has no voice yet
- **THEN** the work page notes that voiceover will use the default voice, and the change is still saved
