---
name: craft-arsenal
description: Use to maintain the AIContentStudio editing technique arsenal (craft-resolve / craft-ae techniques and choose.md): add techniques from a new tutorial course, reference film or user lesson, or review past films (「复盘剪辑手法」) to promote, restrict or retire techniques. Not for making a video.
---

# craft-arsenal · 武器库维护

武器库在平台：`apps/api/craft_skills/craft-resolve/`（`choose.md` 选用表 + `techniques/`）和 `apps/api/craft_skills/craft-ae/techniques/`。做片子的第三方模型通过 MCP 只读它们；这个技能负责让武器库增长、变准。规则全部在 [rules.md](rules.md)，每次维护都在 [log.md](log.md) 末尾追加一条。

## 加新招（新课程、参考片、用户总结的经验）

1. **提炼**：把 [distill-prompt.md](distill-prompt.md) 填好视频目录和输出目录，交给提炼 Agent（或自己执行）。输出放 `output/<来源名>/`，不进 Git。
2. **核对产出**：卡片格式齐全、截图引用存在、没有成段照抄原话（用 15 字以上连续重合检查）、REPORT.md 里的低置信度卡片逐张回看截图。
3. **梳理**：每张卡对照现有条目和 `choose.md`，按 rules.md 判定 新增 / 合并 / 替换 / 舍弃，写梳理表到本次 OpenSpec 变更目录（`triage.md`）。先给用户看梳理表。
4. **换算**：保留的招按 rules.md 的条目格式写进对应 `techniques/<类别>.md`，做法必须是 DaVinci 或 AE 的；接口名用 DaVinci Resolve MCP 的 `search_scripting_api` 核对。新招状态一律「试用」。
5. **选用表**：在 `choose.md` 加或改「问题 → 办法」行；新类别同时更新两个技能的 `SKILL.md` 目录。
6. **验证**：通过 MCP `get_craft_skill` 读每个改过的条目；记 log.md。

## 复盘（用户说「复盘剪辑手法」）

1. **取数据**（本地 API，`X-Studio-User` 用用户账号）：
   - 每条视频的链路记录：`GET /api/v1/content-projects/{p}/units/{u}/video-chain`；历史决定存于系统设置 `video_chain` 的单元记录 `decisions`（阶段、采用或修改、意见、时间）。
   - 导演稿镜头备注：`GET /api/v1/content-projects/{p}/units/{u}/master-revisions/{id}`，读每个镜头 `board.notes` 里的 `手法：…— 解决：…`。
   - 只统计上次复盘（log.md 最后一条复盘记录）之后有新决定的片子。
2. **对账**：每一招统计 用过几次、所在片子最终采用几次、有几条修改意见明确针对它（意见里提到该手法、或指向用了该手法的镜头和时间）。
3. **调整**（阈值见 rules.md）：升「常用」、补「不用在」、改 `choose.md` 候选顺序、退役。每个调整写清依据（片子、决定、意见原文摘要）。
4. **给用户看**：调整清单用表格列出，用户同意后再改文件；记 log.md。

## 不做

- 不改平台代码；武器库只是 Markdown。
- 不把课程逐字稿、截图、原话放进仓库。
- 不替用户决定上不上模板：值得做成 AE 模板的招只标「模板候选」，另提需求。
