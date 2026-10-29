## ADDED Requirements

### Requirement: Editing techniques distilled from reviewed course cards

The craft-resolve and craft-ae craft skills SHALL include technique entries distilled from the reviewed course cards. Each technique SHALL state its reasoning, when to use it, how to do it in DaVinci Resolve or After Effects, whether it can be scripted, how to check the result and common mistakes, and cite the course episode. Entries SHALL be written in the platform's own words, without transcripts, screenshots or tool steps from other editors.

#### Scenario: Read a technique entry
- **WHEN** a third-party model asks the MCP for craft-resolve with entry `techniques/rhythm.md`
- **THEN** it receives the rhythm techniques with DaVinci steps and checks

#### Scenario: Index lists the techniques
- **WHEN** a third-party model reads the craft-resolve or craft-ae index
- **THEN** the index lists each technique entry and what it covers

#### Scenario: Card without a DaVinci or AE equivalent
- **WHEN** a course card relies on a feature that only the course's editor has
- **THEN** the entry gives an alternative in DaVinci or AE, or keeps only the reasoning and check, and the triage record says which

### Requirement: Choosing techniques with restraint

craft-resolve SHALL provide a selection table `choose.md`, listed first in its index, that maps a problem in the piece to one or two candidate techniques. Each technique SHALL state when not to use it and its status (trial, common, retired). Retired techniques SHALL NOT be recommended. The default SHALL be plain cuts on the voice rhythm; a director draft SHALL note for each shot the technique used and the problem it solves.

#### Scenario: Pick for a problem
- **WHEN** a third-party model drafts a shot whose job is the opening hook
- **THEN** it reads choose.md, picks at most the listed candidates whose conditions its material meets, and notes the technique and reason in the shot

#### Scenario: Retired technique
- **WHEN** a technique is marked retired
- **THEN** choose.md does not list it and its entry keeps a line saying why

### Requirement: Arsenal maintenance skill

A local agent skill `craft-arsenal` SHALL define how to add techniques from a new source (distill prompt, card format, triage, DaVinci / AE conversion, entry and table update) and how to review past films (read director-draft technique notes and the user's decisions, then promote, add a not-for condition, or retire). Every maintenance run SHALL append a dated record of what changed and why.

#### Scenario: New course
- **WHEN** the user provides a new tutorial course
- **THEN** the maintainer follows craft-arsenal: distills cards, triages them against existing entries, writes new techniques as trial, updates choose.md and logs the run

#### Scenario: Review
- **WHEN** the user asks to review editing techniques
- **THEN** the maintainer reads approved and changed films, adjusts statuses and choose.md by the stated thresholds, and logs each change with its evidence
