## ADDED Requirements

### Requirement: A product created from a project starts with the project's details

When the user comes from a project to 商品视频工作台 and clicks 新建 SKU, the form SHALL be prefilled with the project title as the product name and the project objective as the product description. The user SHALL be able to edit them before saving.

#### Scenario: New product from project 42
- **WHEN** the user opens 商品视频 from project 「儿童麸质饼干」 (objective 「售卖儿童麸质饼干」) and clicks 新建 SKU
- **THEN** 商品名称 shows 「儿童麸质饼干」 and 商品介绍 shows 「售卖儿童麸质饼干」, and 品类 is empty

#### Scenario: Workbench without a project
- **WHEN** the user clicks 新建 SKU in 商品视频工作台 without coming from a project
- **THEN** the form is empty as before
