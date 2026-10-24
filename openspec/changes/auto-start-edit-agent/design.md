## Flow

```
准备剪辑（导演包已接受）→ 准备剪辑任务（auto_start）→ 调度器每分钟看一次
→ 启动 claude -p（平台 MCP + 达芬奇 MCP + resolve-edit / ae-motion）
→ 领任务 → 达芬奇剪辑调色 + AE 特效镜头 → 渲染粗剪 → 回传
→ 制作内容页：粗剪待审 → 你接受或写修改意见
```

## Decisions

- The dispatcher only starts sessions; all task state changes go through the existing execution API (claim, start, progress, submit), so the platform stays the single record.
- The session prompt is fixed text plus the task id; it tells the assistant to use the 导演包 as the only brief and to stop and report when DaVinci or AE is unavailable.
- Concurrency 1, session timeout 90 minutes, log per task in `~/AIContentStudio/edit-logs/<task>.log`.
- Codex option runs `codex exec` with the same prompt; only one assistant is used per task.
- The dispatcher is installed by `scripts/install_edit_dispatcher.sh`; uninstalling stops auto-start but leaves tasks prepared, so the user can still say 「剪」 by hand.
