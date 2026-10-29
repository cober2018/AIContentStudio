## ADDED Requirements

### Requirement: A new project guides the user to start a work

A project with no works SHALL show a guide offering 角色内容 and 商品视频. Choosing 角色内容 SHALL open the existing add-work dialog.

#### Scenario: Empty project
- **WHEN** the user opens a project that has no works
- **THEN** the page shows 「这个项目要做什么？」 with 角色内容 and 商品视频

### Requirement: A product video can be added to an existing project

Choosing 商品视频 SHALL let the user pick an existing product or create one, then SHALL add a product video work to this same project without creating a new project. The project's materials SHALL stay attached, and the work SHALL appear in 商品视频工作台 under that product.

#### Scenario: Project with imported materials
- **WHEN** the user has imported a raw folder into project 42 and chooses 商品视频 with product 益生元无麸饼干
- **THEN** project 42 gets a product video work, its 7 materials are still there, and the work is listed in 商品视频工作台 under that product

#### Scenario: Workbench entry unchanged
- **WHEN** the user clicks 为此商品新建视频 in 商品视频工作台
- **THEN** a new project is created as before
