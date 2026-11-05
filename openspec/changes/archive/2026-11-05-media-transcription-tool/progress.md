# progress

- 2026-11-05 写好方案，待用户确认。
- 2026-11-05 用户确认，实施：
  - 新增 `services/media_transcription.py`（单线后台、切段转写、截图、写 txt / srt / md、记录存设置表 `media_transcriptions`）
  - `reference_video.scene_cuts` 加可选 timeout（默认不变）
  - `creative_mcp`：两个工具，`media_transcription_` 错误码和提示可透出
  - `mcp_settings`：「小工具」组和说明
  - 新路由 `routers/small_tools.py`：`GET /api/v1/tools/media-transcriptions`、`POST …/{id}/reveal`
  - 前端：导航「工具 → 小工具」，`SmallToolsPage.tsx`
- 验证（数据库副本 + 临时输入输出文件夹，素材盘上的参考视频只读）：
  - 30 秒视频：12 句、9 张截图；md 每段「标题 + 截图相对路径 + 文字」
  - 30 秒音频：txt / srt / md，没有截图
  - 11 分钟音频：切段转写，字幕最后一句在 10:58，覆盖全长
  - 同一文件连续提交两次：分到「短视频」和「短视频-2」两个文件夹
  - 拒绝：非媒体文件、文件不存在、相对路径
  - 默认位置 + 盘不可写：返回 material_library_unavailable「素材库盘没连接」
- 第一次测试发现：同一文件排队时两次算出同一个文件夹，第二次报 FileExistsError。已改为提交时就占用文件夹，失败时删掉空文件夹。
- 测试：全量 2441 通过，5 个失败与改动前相同；tsc 通过；MCP 白名单测试补上两个工具名（get 为只读）。
- 2026-11-05 已重启 API 和后台，健康检查正常；`/api/v1/tools/media-transcriptions` 返回空列表；无头 Chrome 截图：导航「工具 → 小工具」、工具说明卡和空记录提示显示正常。
