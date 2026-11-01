# progress

- 2026-11-01 方案已写，等用户确认。
- 2026-11-01 已本地实施，未提交：`IdentityProfileView.tsx` 新增 `PersonaMedia`（声音、形象照、逐字稿样本只读块，复用 `/settings/voice`、`/content-personas/{id}/portraits`、`StoredThumb`）；`KNOWN` 加入 brand、portrait_material_revision_ids、speech_sample_folder；`IdentityWorkspace.tsx` 角色概览传 `personaId`。
- 验证：tsc 通过；用正式库逐个算现有角色的生效资料，已无字段落进「其他资料」；萌柚老爸形象照接口返回 1 张。
