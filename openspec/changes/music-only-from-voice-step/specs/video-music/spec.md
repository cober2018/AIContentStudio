## ADDED Requirements

### Requirement: Music comes only from the voice and music step

A video work's music SHALL be decided only in 配音与音乐 and stored on the master as one of: a chosen music revision, an explicit no-music choice, or undecided. Production settings SHALL NOT carry a music direction; one in an old record SHALL be dropped when read and never reach an edit task.

#### Scenario: Never chosen
- **WHEN** the user has not touched the music section
- **THEN** the edit task says music is undecided, not that the user wants none

#### Scenario: User chooses no music
- **WHEN** the user clicks 不用配乐
- **THEN** the master records no music and the edit task says the user chose no music

#### Scenario: Old default
- **WHEN** a work's saved settings still hold music_direction 不使用配乐
- **THEN** new edit tasks for it carry no music direction
