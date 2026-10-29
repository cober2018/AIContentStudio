## ADDED Requirements

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
