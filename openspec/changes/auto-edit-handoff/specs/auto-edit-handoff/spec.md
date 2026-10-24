## ADDED Requirements

### Requirement: Adopted storyboard goes to an edit-ready master by itself

After the user adopts a video 导演稿, the platform SHALL place each row's single pick into the master, decide edit settings, save the master and rebuild the 导演包, without further clicks.

#### Scenario: All rows have one pick
- **WHEN** the user clicks 采用这版 and every row has exactly one pick
- **THEN** all rows are placed into a newly saved master and 专业执行准备 is current and accepted

#### Scenario: Row with several picks
- **WHEN** a row has more than one pick
- **THEN** that row is not placed, and its 素材 cell shows 待你选

#### Scenario: A step fails
- **WHEN** any step fails
- **THEN** the page names the step and the reason, and retry continues from it

### Requirement: Platform decides DaVinci and AE per row

Every row SHALL go to DaVinci. A row SHALL also go to AE when the platform judges from its 画面, 运镜 and 备注 that it needs effects, with the reason shown. Size and fps SHALL follow the video's aspect ratio.

#### Scenario: Row with on-screen graphics
- **WHEN** a row's 备注 asks for a map animation
- **THEN** its 素材 cell shows 达芬奇+AE with that reason

#### Scenario: Row already rendered from an AE template
- **WHEN** a row's material is an AE template render
- **THEN** it is DaVinci only

#### Scenario: Decision call fails
- **WHEN** the AE decision call fails
- **THEN** all rows are DaVinci only and the reason says so
