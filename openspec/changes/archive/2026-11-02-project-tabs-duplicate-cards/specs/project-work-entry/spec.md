## ADDED Requirements

### Requirement: Project sub-tabs render only their own content

Switching between a project's sub-tabs SHALL render only the selected sub-tab's components, with no leftover copies of other sub-tabs' cards.

#### Scenario: Switching to 项目素材 after 创作任务书
- **WHEN** the user opens 创作任务书 and then 项目素材 several times on project 48
- **THEN** 项目素材 shows no 「商品创作」 card
