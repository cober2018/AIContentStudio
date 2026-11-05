# progress

- 2026-11-05 写好方案，待用户确认。
- 2026-11-05 用户确认，实施：
  - `project_folders.require_library()`
  - 配音（`voiceover.generate`）、生图（`_Images.make`）、镜头图、图生视频、九宫格的入口在调用供应商前调用它
  - `creative_mcp`：错误码和提示可透出给模型
- 副本验证：网络全部拦截，模拟盘不可写，五个入口都回 `material_library_unavailable`，供应商请求 0 次。MCP 返回 `{'code': 'material_library_unavailable', 'status': 409, 'message': '素材库盘没连接'}`。盘可写时检查放行。
- 九宫格两个已有测试替身没有素材库，补了一行把检查替换掉。全量测试 2441 通过，5 个失败与改动前相同。
- 待用户重启后实测：拔盘调配音、接盘正常生成。
- 2026-11-05 已重启 API 和后台，健康检查正常。
