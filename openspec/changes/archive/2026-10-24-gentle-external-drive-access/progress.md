# Progress

- 2026-10-24 查清现状（见 findings.md），方案写好，等用户确认。
- 2026-10-24 用户确认后实施完成：
  - `storage_locations.library_reachable` 改只读（能列出根目录且含 AIContentStudio，5 秒缓存）；新增 `library_writable`（原写探测），只在 `project_folders.ensure_library_dirs / ensure_project_dir / move_into` 和 `material_storage._writable` 前调用。
  - `materials`：完整校验后记 `metadata_json.verified`（路径/大小/修改时间/哈希），由后台线程批量写库（只读请求不提交事务）；`verify_bytes_checked` 记录一致时只读开头 64 字节。
  - `creative_executions._earlier_copy`：物化剪辑输入时优先用同一用户早先任务在 Mac 上的同名同大小副本做克隆源，克隆后照旧核对哈希。
  - 验证：页面轮询 8 轮，硬盘上平台文件夹修改时间不变（不再写探测文件）；主稿就绪检查第一次 0.35s、之后 0.02s；重启后新进程就绪检查整读 0 次（18 条记录已落库）；输入复用能找到 Mac 上已有副本、大小不符时不用；后端全量 2808 通过，7 个失败均为原有。
  - 未在真实剪辑任务上跑第 3 项（需要 Claude Code 开一个新剪辑任务时自然生效）。
