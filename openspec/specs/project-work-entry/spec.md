# project-work-entry Specification

## Purpose
TBD - created by archiving change start-work-from-project. Update Purpose after archive.
## Requirements
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

### Requirement: A product created from a project starts with the project's details

When the user comes from a project to 商品视频工作台 and clicks 新建 SKU, the form SHALL be prefilled with the project title as the product name and the project objective as the product description. The user SHALL be able to edit them before saving.

#### Scenario: New product from project 42
- **WHEN** the user opens 商品视频 from project 「儿童麸质饼干」 (objective 「售卖儿童麸质饼干」) and clicks 新建 SKU
- **THEN** 商品名称 shows 「儿童麸质饼干」 and 商品介绍 shows 「售卖儿童麸质饼干」, and 品类 is empty

#### Scenario: Workbench without a project
- **WHEN** the user clicks 新建 SKU in 商品视频工作台 without coming from a project
- **THEN** the form is empty as before

### Requirement: Opening a product in the workbench never creates a project

Clicking a product in 商品视频工作台 SHALL open that product's works, where the user can continue an existing work. A new project and work SHALL only be created by the explicit 为此商品新建视频 action.

#### Scenario: Product with an existing work
- **WHEN** the user clicks 进入商品 on 「儿童麸质饼干」, which already has a work in project 42
- **THEN** the product's works list shows that work with 继续制作, and no project is created

### Requirement: The production page belongs to its workbench

The production page of a product video SHALL highlight 商品视频工作台 in the side menu, show its place as 商品视频工作台 / product name, and its back link SHALL return to that product in the workbench. A persona work SHALL do the same for 角色内容工作台. The page address SHALL stay unchanged.

#### Scenario: Back from a product video
- **WHEN** the user is on the production page of project 42's 「儿童麸质饼干」 work and clicks the back link
- **THEN** 商品视频工作台 opens on 「儿童麸质饼干」's works

### Requirement: Product videos use the third-party video chain page

A product video's production page SHALL show 商品与本条目标, 导演稿, 素材, 配音与音乐, 小样, 成片 and 交付, with the user reviewing the 导演稿, 小样 and 成片 on the page as for persona videos. The 导演稿 step SHALL show the platform writing skill switch. The old product steps SHALL no longer be shown.

#### Scenario: Review a product director's draft
- **WHEN** a third-party model saves a director's draft for project 42's 「儿童麸质饼干」 video
- **THEN** the 导演稿 step of that work shows the draft with 采用 and modification notes, and the platform writing skill switch

#### Scenario: Old link
- **WHEN** the user opens that work with an old step link such as workstep=edit
- **THEN** the page lands on the chain's current step

