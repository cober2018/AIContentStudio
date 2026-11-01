# progress

- 2026-11-01 方案已写，用户确认。
- 2026-11-01 已本地实施，未提交：
  - 后端 `services/obsidian_knowledge.py`：去掉 `_sample_scope`；`check_speech_folder` 只校验在库内且存在；`speech_samples` 读取时 `read_note(..., scoped=False)` 跳过子目录名单，路径安全检查不变。
  - 前端：新建 `product/KnowledgeSettings.tsx`（设置 → 知识库，与项目页共用 `obsidian-connection` 缓存）；`ProductSettingsPage.tsx` 加「知识库」分区；`project/ObsidianKnowledgePanel.tsx` 去掉连接表单，只留状态与「设置 → 知识库」指引；`PersonaSpeechSamples.tsx` 提示改为库里任意文件夹。
- 验证（数据库副本，根目录改成真实库位置）：名单外 `areas` 能保存并读到 3 篇样本；`../outside`、不存在的文件夹被拒；项目检索读名单外笔记仍被拒（`knowledge_path_outside_scope`）。全量后端 2466 通过，失败 5 个均为已知老问题；tsc 通过；API 已重启。
