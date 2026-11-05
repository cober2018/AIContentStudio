## 1. 实现
- [x] 1.1 `project_folders.require_library()`：素材库不可写就抛 409 `material_library_unavailable`「素材库盘没连接」
- [x] 1.2 在配音、生图、镜头图、图生视频、九宫格五个入口调用供应商之前调用它
- [x] 1.3 `creative_mcp`：`material_library_unavailable` 可透出，带上提示

## 2. 验证（数据库副本，模拟盘不可写）
- [x] 2.1 盘不可写：五个入口都返回 `material_library_unavailable`，供应商调用次数为 0；MCP 返回码和中文提示
- [x] 2.2 盘可写：检查放行（不实际调用付费接口）
- [x] 2.3 相关已有测试
