## ADDED Requirements

### Requirement: Language boost and voice modify per preset

A voice preset SHALL carry an optional language boost and voice modify values (pitch, intensity, timbre, each −100 to 100, default 0), and voiceover SHALL send them to MiniMax.

#### Scenario: Male preset
- **WHEN** the 男声 preset has language boost Chinese and voice modify pitch 2, intensity −2, timbre 0
- **THEN** a voiceover with 男声 is requested with exactly those values and the applied parameters record them
