# findings

- 日志核实：`logs/api.log` 第 322405 行，2026-11-05 02:05:02 `POST https://api.minimaxi.com/v1/t2a_v2` 200。
- 平台已有三种「盘没接」报法：`materials.library_guard`（素材库未连接）、`project_folders` 外部文件夹导入（素材库盘没连接）、剪辑任务 `video_chain_drive_unavailable`。这次用 `material_library_unavailable` +「素材库盘没连接」。
- MCP 的 `domain_error` 对不在白名单、前缀也不匹配的错误码一律改写成 `creative_domain_<类别>`；提示文字只对部分前缀透出。
- 素材自动补齐（`material_autofill`）原本就把 `material_library_unavailable` 显示成「素材库未连接」。检查放在 `_Images.make` 和 `start_shot_video`，自动补齐也会在调用供应商前停下。
