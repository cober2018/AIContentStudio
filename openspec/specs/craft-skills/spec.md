# craft-skills Specification

## Purpose
TBD - created by archiving change distill-editing-course-into-craft-skills. Update Purpose after archive.
## Requirements
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

### Requirement: One switch per work controls platform writing skills for third-party models

Each work SHALL have one switch, set by people on its production page and on by default. When on, a third-party model SHALL be able to read the platform's built-in writing skills through get_craft_skill. When off, those reads SHALL be refused. craft-resolve and craft-ae SHALL always be readable regardless of the switch. The model SHALL NOT be able to change the switch.

#### Scenario: Switch off
- **WHEN** the user turns off the switch for project 42's video and the model reads studio.video.product-script@1
- **THEN** the platform refuses with platform_skills_disabled

#### Scenario: Editing skills stay on
- **WHEN** the switch is off and the model reads craft-resolve choose.md
- **THEN** the platform returns choose.md

#### Scenario: Default
- **WHEN** the switch was never touched and the model reads studio.video.product-script@1
- **THEN** the platform returns that skill's instructions

### Requirement: The model is told the switch state

get_video_brief and get_article_brief SHALL include the switch state and the list of platform skills the model can read, with how to read them.

#### Scenario: Brief with switch off
- **WHEN** the switch is off and the model reads the video brief
- **THEN** platform_skills says writing skills are off and lists only craft-resolve and craft-ae as readable

### Requirement: Persona and product skills are separate systems

Platform writing skills SHALL belong to the product system, the persona system or the shared system. A product work SHALL only be offered and allowed product and shared skills; a persona work SHALL only be offered and allowed persona and shared skills. craft-resolve and craft-ae SHALL be available to both.

#### Scenario: Product work reads a persona skill
- **WHEN** the model reads studio.video.script@1 for project 42's product video
- **THEN** the platform refuses it as not available for this work

#### Scenario: Product work skill list
- **WHEN** the model reads the brief of a product video
- **THEN** platform_skills lists craft-resolve, craft-ae, product skills and shared skills, and no persona skills

### Requirement: Absorbed recipes are rewritten for DaVinci and AE

Techniques absorbed from video-shotcraft and video-talkcraft SHALL be written in the platform's own words as DaVinci or AE methods in the craft arsenal, with status 试用 and their source repository (the commit recorded in the craft-arsenal log), and SHALL NOT include upstream text, code, prompts, media or music.

#### Scenario: A shot recipe kept
- **WHEN** a shotcraft shot recipe is kept in triage
- **THEN** craft-ae or craft-resolve has an entry with 用在 / 不用在 / DaVinci or AE steps / 状态 试用 / 来源 video-shotcraft, readable through get_craft_skill

### Requirement: Selling-video methods become product skills

Methods absorbed from clipforge SHALL be written as product-system or shared-system platform skills in the platform skill package format, executing through the platform's director draft, materials, voiceover and DaVinci / AE, without clipforge's rendering or text.

#### Scenario: New product skill loads
- **WHEN** a new product skill package is added
- **THEN** the platform loads it, a product work can read it through get_craft_skill, and a persona work cannot

