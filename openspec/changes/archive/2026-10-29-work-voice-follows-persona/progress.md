# 进度

## 2026-10-29 本地实施
- 后端：`voiceover.settings_for` 只按 角色 → 默认；删 `set_work_preset` 和 `PUT …/units/{id}/voice-preset`；声音设置不再存 `works`（库里原有的作品 84 一条已清掉）。
- 前端：删 `GuidedProductionProfile.WorkVoice`；配音面板显示「声音『女声』（来自所属角色 / 没选角色，用默认）」；设置 → 配音、角色声音的说明改口径。
- 验证：后端 `5 failed, 2449 passed, 28 skipped`（5 个已知失败）；tsc、node --test 37/37、build 通过；作品 83（懒羊羊小王）女声·角色，作品 80（AI科技研发技术博主）男声·角色，作品 84（无角色）男声·默认；作品选声音接口已 404。
