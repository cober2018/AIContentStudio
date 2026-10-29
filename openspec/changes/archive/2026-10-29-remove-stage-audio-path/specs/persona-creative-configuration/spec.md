## ADDED Requirements

### Requirement: No stage-based audio production

The platform SHALL make voice audio only through the one-click voiceover. Stage-based TTS, audio QC and audio-stage ASR, the voice-director / tts / qc skills, audio quality profiles and the audio creative profile SHALL not exist. Video master loudness, video subtitle ASR suggestions, the spoken-adaptation writing skill and audio materials SHALL remain. Historical runs of removed stages SHALL stay readable and show as retired.

#### Scenario: Persona configuration
- **WHEN** a user opens a persona's creative configuration
- **THEN** only text, graphic and video are offered, and the persona's voice is chosen on its profile page

#### Scenario: Old text work
- **WHEN** a text work that once ran audio stages is opened
- **THEN** it uses the default text recipe and its past audio runs show as retired stages without errors
