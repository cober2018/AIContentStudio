## ADDED Requirements

### Requirement: Persona speech sample folder

A persona MAY name one folder in the connected Obsidian vault holding real spoken transcripts. The folder SHALL exist and lie inside the connection's allowed folders when saved.

#### Scenario: Set the folder
- **WHEN** the user sets 逐字稿/懒羊羊小王 on the persona 懒羊羊小王
- **THEN** the persona keeps that folder and shows it on its profile

### Requirement: Video brief carries speech samples

The video brief of a persona work SHALL include that persona's speech samples: Markdown notes from the folder and its subfolders, newest first, at most 6000 characters in total, with skipped notes counted. The brief SHALL tell the writer to follow the samples' way of speaking and never their facts or experiences. When the folder cannot be read, the brief SHALL still be returned with the reason. Product works SHALL NOT carry speech samples.

#### Scenario: Two personas, two styles
- **WHEN** two video works belong to different personas with different sample folders
- **THEN** each brief carries only its own persona's samples

#### Scenario: Obsidian not connected
- **WHEN** the Obsidian connection is off
- **THEN** the brief is returned and speech_samples says the samples could not be read
