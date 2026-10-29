## ADDED Requirements

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
