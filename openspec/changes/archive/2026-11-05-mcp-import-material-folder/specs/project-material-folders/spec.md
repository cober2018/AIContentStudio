## ADDED Requirements

### Requirement: The model imports a raw folder through MCP

The creative MCP SHALL offer `import_material_folder` with `project_id`, `unit_id` and `path`. It SHALL apply the same editable-project check as the 素材 page (an archived project is refused) and then the same folder import, with its path checks, errors, `asset.attached` events (origin `project_folder_import`) and later move into the project folder. The import result SHALL list every imported or already-attached file with its relative path and `material_revision_id`, in addition to the existing counts. The tool SHALL attach files to the project only and never bind them to a shot.

#### Scenario: First import
- **WHEN** the model imports a folder of 10 images under 外部素材库 into project 50
- **THEN** the result lists 10 files with their material_revision_id and the project's imported folders show that folder with 10 files

#### Scenario: Second import
- **WHEN** the model imports the same folder again
- **THEN** all 10 count as already in the project, nothing is registered twice, and the same 10 ids are listed

#### Scenario: Archived project
- **WHEN** the model calls the tool for an archived project
- **THEN** the call is refused and nothing is imported
