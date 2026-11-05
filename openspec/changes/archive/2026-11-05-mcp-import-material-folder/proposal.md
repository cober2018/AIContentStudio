# MCP 工具 import_material_folder：模型把素材盘上的文件夹登记进本项目

## Why
做视频时，第三方模型会自己截网页证据图、裁文章配图，放在素材盘 `外部素材库/<文件夹>` 下。`render_ae_template` 的图片槽只收本项目的图片素材。现在 MCP 没有登记入口，模型只能在本机渲染，平台上没有记录。

用户已明确授权模型自己登记。

## What Changes
- **新 MCP 工具 `import_material_folder`：**
  - 参数：`project_id`、`unit_id`、`path`（素材盘上文件夹的完整路径）。
  - 效果和项目「素材」页的「引入原始素材文件夹」完全一样。
- **执行步骤：**
  1. 校验作品属于该项目（和其他做视频工具一致）。
  2. 做和页面接口相同的项目可改检查（`mutable_project`）：已归档（锁定）的项目拒绝。
  3. 直接调用 `project_folders.import_folder`。路径校验、报错、事件记录（`asset.attached`，origin `project_folder_import`）、成片通过后搬进项目目录，全部沿用现有逻辑。
- **`import_folder` 返回值加 `files` 列表：**
  - 每项含文件的相对路径和 `material_revision_id`。新登记的和已在项目里的都列出，跳过的不列。
  - 原有的数量字段不变，页面多收一个字段不影响显示。
- **工具登记：**
  - `creative_mcp.py` 工具表加一条英文说明：只登记到本项目、不绑镜头，只收素材盘上非项目、非通用素材的文件夹，返回的 id 可用于 `render_ae_template` 的图片槽。
  - 把它加进 `_VIDEO_TOOLS` 并分发。
  - `mcp_settings.py`：「做视频」组和 `SUMMARIES` 各加一行中文说明。

## 不在本次范围
- 不改页面。
- 不改 `CANNOT` 列表：这是把素材登记到项目，不是给镜头绑素材。

## Impact
- 代码：`apps/api/app/services/{project_folders,creative_mcp,mcp_settings}.py`
- 生效要重启 API；第三方模型重新连接后才能看到新工具。
