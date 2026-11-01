## ADDED Requirements

### Requirement: Third-party model creates projects and works over MCP

The MCP server SHALL let the third-party model list personas, create a content project, and create a work inside a project, acting as the token's owner and reusing the existing project and work creation rules. Creating a project SHALL NOT take a persona; creating a work SHALL require one.

#### Scenario: Topic from broad research
- **WHEN** the model creates a project with a topic rationale and no reference links
- **THEN** the project is created, its page shows 「由第三方模型创建」 and the rationale, and shows no link section

#### Scenario: Work for a persona
- **WHEN** the model creates a video work in that project for persona 3
- **THEN** the work is created with persona 3's identity snapshot and default workflow, and its id is returned

#### Scenario: Missing rationale
- **WHEN** the model calls create_project without a topic rationale
- **THEN** the call fails with the field name and rule, and no project is created
