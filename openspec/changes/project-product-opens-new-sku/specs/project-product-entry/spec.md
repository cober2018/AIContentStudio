## ADDED Requirements

### Requirement: Product video from a project opens a new SKU

Entering the product video workbench from a project SHALL open the new SKU form at once, still naming the target project, with a way back to the catalog to pick an existing SKU. Entering without a project SHALL open the catalog as before.

#### Scenario: New project, choose product video
- **WHEN** the user creates a project and clicks 商品视频
- **THEN** the workbench shows the 新建 SKU form for that project

#### Scenario: Pick an existing product instead
- **WHEN** the user clicks 改选已有商品 on that form
- **THEN** the catalog opens and a chosen SKU's video goes into the same project

### Requirement: Paste the product image

The product main image field SHALL accept an image pasted from the clipboard (PNG, JPEG or WebP) the same way as a chosen file, and SHALL say so when the clipboard holds no image.

#### Scenario: Paste a screenshot
- **WHEN** the user clicks the paste box and presses ⌘V with a screenshot on the clipboard
- **THEN** the image uploads and the form says it takes effect on save
