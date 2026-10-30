# 设计

## 位置
- `project_folders.STRUCTURE` 加 `工作`。新函数 `work_dir(db, project_id, unit_id, execution_id)` → `<项目>/工作/<作品名>-<作品号>/任务<N>/`，代理放 `<项目>/工作/代理/`。
- 硬盘没插（`_writable_root()` 为空）时开任务直接报「素材硬盘没连上」，不退回平台目录。

## 准备素材（materialize_inputs）
- 返回 `files[]`：`material_revision_id`、`path`（原始绝对路径，`materials.local_file_checked`）、`content_hash`、`size_bytes`，代理开时加 `proxy_path`；另返回 `work_dir`、`export_dir`（导出/小样 或 导出/成片）。
- 不再 clone / link；保留现有授权检查和 `_input_snapshot` 指纹记录。

## 交付结果（submit_output）
- 新参数 `path`（绝对路径）替代 `relative_path`。只接受本项目文件夹内：主片在 `导出/小样` 或 `导出/成片`，其他角色在本次 `work_dir` 下；解析真实路径后再判断，拒绝符号链接和跳出目录。
- 原地流式计算指纹、校验 MIME / 时长 / 响度 / 剪辑清单（沿用 `streams.validate`），`CreativeExecutionOutput` 记 `file_path` 代替 `staging_key`；不复制。
- 交付后到页面审片前文件被改：读取时指纹不符就标「文件已变化」，要求重新交付。
- `after_execution` 不再复制到 `导出/小样`（文件本来就在那里）。

## 通过成片（decide_output）
- 本地素材存储时，直接以原路径登记 `MaterialRevision`（复用素材库「文件在项目文件夹里」的现有登记方式），不经 staging、不 `move_into`。

## 代理
- 设置项 `edit_proxy_enabled`（默认 false），放在 设置 → 素材 / 剪辑。
- 打开时 `materialize_inputs` 对视频素材（长边 > 1920 或码率高的）用 ffmpeg 生成 720p 代理，按素材指纹命名，已存在就复用。

## 清理
- 新小样交回：同一作品更早任务的 `work_dir` 里未登记的文件删除。
- 成片通过：作品 `工作/` 下除本次任务外全部删除。
- 删除只删平台建的 `工作/` 子目录里的文件，从不删 `导出/` 和素材原件。

## 迁移
- 一次性脚本：列出 `.creative-executions` 每个任务的大小和状态给用户；确认后，把仍在「小样待你看」的 83、84 小样登记到 `导出/小样`（文件已在），其余删除，最后删 `.creative-executions`。
- 交付说明（`video_chain.RULES`、`prepare_video_edit` 返回）改写为新路径约定。

## 日志
- `creative_mcp.call_tool` 出错时 `log.warning` 记 `tool`、`execution_id`、`code`。
