## ADDED Requirements

### Requirement: Voiceover can cover only marked shots

A 导演稿 shot MAY carry `dub_persona` naming a persona; its line SHALL be voiced with that persona's fixed voice, and a persona without a voice SHALL be refused with a prompt to set it first. When any shot is marked, voiceover generation SHALL synthesize only the marked shots' lines in their personas' voices, fit each line within its shot (speeding up to 1.25× once, otherwise failing with the needed and available length), place them at their shots' start times on one full-length track with silence elsewhere and matching subtitle times, and SHALL NOT change any shot's duration. Without marked shots, generation SHALL behave as before.

#### Scenario: One mother line in a live-sound video
- **WHEN** work 92's shot 10 has a line and `dub_persona` naming the mother persona and voiceover is generated
- **THEN** only that line is synthesized, it starts at shot 10 and fits within it, and every other shot keeps its duration and live sound
