## ADDED Requirements

### Requirement: Import a raw material folder into a project

The project 资料 page SHALL let the user import a folder on the library drive by path; folders off the drive, project folders and 通用素材库 SHALL be refused. Every supported video, image and audio file in it and its subfolders SHALL be linked in place as this project's material, marked as coming from that folder. Unsupported files SHALL be skipped and counted.

#### Scenario: Import a folder
- **WHEN** the user imports `/Volumes/T1000/原始素材/手机评测/` with 30 mp4, 20 jpg and 3 docx files
- **THEN** 50 materials are attached to the project, the files stay where they are, and the result says 3 files were skipped

#### Scenario: Import the same folder again
- **WHEN** the user imports the same folder after adding 5 new photos
- **THEN** only the 5 new photos are added

### Requirement: Raw folder material is filed when the final cut is approved

When the user approves the 成片, every material imported from a raw folder that is still in that folder SHALL be moved into the project folder by type: video → `视频/其他素材`, image → `图片/图片素材`, audio → `音频/音效`. Files already moved on 准备剪辑 SHALL stay where they are.

#### Scenario: Unused footage
- **WHEN** an imported clip was never used and the user approves the 成片
- **THEN** the clip is now at `<项目名>/视频/其他素材/` and no longer in the raw folder

#### Scenario: Drive unplugged
- **WHEN** a file cannot be moved
- **THEN** it is listed as 待归档 with a 重新归档 action on the 资料 page; the approval still stands; file names are kept
