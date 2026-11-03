# raw-folder-refresh

- 阶段：用户已确认（2026-11-03「对，不用新增存储……新加一个更新素材这个按钮」），已开发，等验收
- 需求：项目素材页列出已引入的原始素材文件夹，每个可「更新素材」补进新放的文件
- 代码位置：apps/api（project_folders.imported_folders、GET /content-projects/{id}/materials/folder-imports）、apps/web（ProjectAssetsTab）
