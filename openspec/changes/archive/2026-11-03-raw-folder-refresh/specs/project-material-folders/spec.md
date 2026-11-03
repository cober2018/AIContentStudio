## ADDED Requirements

### Requirement: Imported raw folders are listed and can be refreshed

The project materials page SHALL list the raw folders the project imported, worked out from the imported files' original paths without storing them again, with file counts and how many were already moved into the project folder. Each folder that still exists and is allowed as a raw folder SHALL offer 更新素材, which imports that folder again so only new files are added.

#### Scenario: New file in an imported folder
- **WHEN** the user puts a new video into 外部素材库/20261102如何判断过敏体质 and clicks 更新素材
- **THEN** the video is added to the project and the 8 earlier files count as already in the project
