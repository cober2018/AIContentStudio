# edit-files-in-project-folder

- 阶段：用户已确认方案，本地实施完成（未提交）；待第三方模型实跑一次、用户决定删除旧任务文件后归档
- 需求：第三方模型经 MCP 剪辑时，素材直接用原文件，临时文件放在项目文件夹里的固定位置，小样 / 成片导出一次就登记，不再层层复制；代理素材做成开关（默认关）；旧任务文件清理。
- 成果文件：proposal.md / design.md / findings.md / specs/ / tasks.md
- 代码位置：`apps/api/app/services/{project_folders,creative_executions,creative_media_stream,video_chain,web_video_handoff,creative_mcp,storage_locations}.py`、`apps/api/app/routers/{creative_orchestration,settings}.py`、`apps/web/src/product/StorageSettings.tsx`、`.codex/skills/video-production-handoff/SKILL.md`
- 旧任务清单 / 改指脚本：`/Users/mshengran/.claude/jobs/1765d66a/tmp/old_executions.py`
- 进度：progress.md；决定：findings.md
- 下一步：用第三方模型实跑一次小样；用户确认后删除 `apps/api/app/media/.creative-executions`；`/opsx:archive`
