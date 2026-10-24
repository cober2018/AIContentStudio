# progress

- 2026-10-24 提案写好，用户确认。
- 2026-10-24 实现完成（本地，未提交），API 已重启。
  - `storage_locations.library_reachable`：试写 `AIContentStudio/.probe-<pid>`，5 秒缓存。
  - `materials.py`：新增 `file_location` / `local_file_checked`（校验按 路径+大小+修改时间 缓存）；`read_bytes_checked` 在素材库断开时返回「素材库未连接」。
  - `routers/materials.py`：raw 接口本地文件用 `FileResponse`（支持 Range，无大小上限）；新增 `GET .../location`、`POST .../reveal`。
  - `project_folders.py`：抽出 `sample_name`，新增 `sample_copy`；`video_chain.cut_location`；`routers/edit_agent.py` 新增 `video-chain/cuts/{output}/location|reveal`。
  - Web：新增 `FileLocationActions.tsx`；`VideoChainPanel.tsx`、`MaterialDetailDrawer.tsx` 播放器右上角挂上；视频进度「已完成」时也显示「看成片」。
- 验证：
  - raw 读 119MB 成片：200，119,602,598 字节，0.34 秒；Range 请求 206。
  - 模拟写入失败：`library_reachable` = False；读取、校验、保存都返回 409「素材库未连接」。
  - 浏览器：视频进度面板「看成片」播放 75.0 秒 1080 宽；「复制路径」剪贴板为 `/Volumes/T1000/自媒体素材/海底光缆/导出/成片/海底光缆｜竖屏视频 · final.mp4`；「在访达中显示」后访达选中该文件。素材详情抽屉同样有两个按钮，视频可播。
  - 相关测试 90 通过；全量 2808 通过，7 个失败均为之前已知的（schema_lifecycle、migrations ×3、models_plugins ×2、topic_suggest）。
