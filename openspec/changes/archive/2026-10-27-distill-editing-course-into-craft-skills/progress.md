# 进度

- 2026-10-27：核对另一个 Agent 的产出（100 张卡、格式完整、截图引用无缺失、无成段照抄）；确认平台已有 resolve-edit / ae-motion 两个技能，新条目放子目录即可被 MCP 读到；写好方案，待确认。
- 2026-10-27：方案确认。读完 100 张卡，写 `triage.md`：保留 62、合并 22、舍弃 16；去向 11 个条目（resolve-edit 7、ae-motion 4）。等用户看过梳理表再写条目。
- 2026-10-27：范围确认（选用表、状态与复盘、维护技能、统一命名）。完成：
  - 改名 craft-resolve / craft-ae（平台目录、本地技能、`craft_skills.SKILLS`、MCP 参数与说明、`edit_dispatcher.py`、handoff 与根 README 引用）。
  - craft-resolve：`choose.md` + `techniques/` 7 个条目；craft-ae：`techniques/` 4 个条目；两个 SKILL.md 目录、edit-combos 引用；handoff 导演稿步骤要求先读 choose.md 并在镜头 notes 写手法。
  - 新建 `.codex/skills/craft-arsenal/`（SKILL.md、rules.md、distill-prompt.md、log.md）。
  - 验证：服务层按新名读到 2 个目录 + 12 个条目，7 个模板仍可列出；重启 API 后经 MCP stdio 读 choose.md、titles.md、craft-resolve 目录均成功，旧名 resolve-edit 被拒；`test_aco_creative_mcp.py` 74 passed；条目与逐字稿无 12 字以上连续重合。
  - 另发现：API 健康检查 503 `schema_head_mismatch`，因本机 `scripts/startup/runtime.env` 仍写 `REQUIRED_SCHEMA_HEAD=matmatch0001`，而数据库与代码已是 `legacy0001`（上一需求遗留，本需求未改）。
- 2026-10-27：修复本机 runtime.env 的 REQUIRED_SCHEMA_HEAD（matmatch0001 → legacy0001），重启后健康检查 200、无告警。用户验收，归档。
