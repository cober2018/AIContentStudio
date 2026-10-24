## ADDED Requirements

### Requirement: Saved MiniMax voice settings are used as given

The platform SHALL keep one saved voice setup and SHALL send every field of it to MiniMax when generating a voiceover.

#### Scenario: Default from the user
- **WHEN** the user opens 设置 → 配音
- **THEN** it shows verify_clone_v2, 开心, speed 1, volume 1, pitch 0, MP3, 32000 Hz, 128 kbps, mono

#### Scenario: Generate
- **WHEN** a voiceover is generated
- **THEN** the MiniMax call carries all those values and the result records the values applied

### Requirement: One-click voiceover for a video

The 制作内容 page SHALL generate the voiceover from the 台词 column, add it to the library and save it as the master's voice track, with line timings kept.

#### Scenario: 海底光缆
- **WHEN** the user clicks 生成配音
- **THEN** a voice file appears in the library, the master's voice track points to it, and the page plays it

### Requirement: The re-cut follows the voice and the storyboard

An edit of a video with a voice track SHALL time shots to the narration, apply each row's 景别 and 运镜, and not reuse the same footage in two shots.

#### Scenario: Ship shots
- **WHEN** two rows' material is the same file
- **THEN** one of them uses a close crop or a motion graphic instead of the same frame
