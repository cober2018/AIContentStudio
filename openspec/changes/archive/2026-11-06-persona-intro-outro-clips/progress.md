# 进展
- 2026-11-06 写规范，待确认。
- 2026-11-06 实现：角色资料加 intro_clip/outro_clip（_persona_clip 检查，账号/系列不收）；品牌删字段，保存时丢掉旧字段；接口换成 /content-personas/{id}/clips；成片从 unit.persona_id 当前资料取片段；全链路 brand_* → persona_*、文字「品牌」→「角色」；BrandClips.tsx → PersonaClips.tsx（角色编辑页「收尾 / 进门片段」，自带保存），只读页显示，品牌页删除。
- 验证（库副本，加载运行配置）：超 5 秒、不可公开、不是自己的都被拒并说明原因；账号上设片段被拒；角色 6 存 618/619 成功；品牌 6 带旧字段重存成功、新版本无片段字段；作品 95（16:9）取到 618，提示「加角色收尾 4.2 秒（知数Talk收尾_深墨_横版，素材 618）」，执行包 director.persona_clips 与 assets role persona_clip 都有；清单不写 persona_clips 被拒，写对通过；没片段时「本作品没有角色收尾」。全量测试 2441 通过、5 个原有失败；tsc 通过。页面未在浏览器里点过（新接口要重启后才有）。
- 2026-11-06 已重启；/content-personas/6/clips 返回空，/content-brands/6/clips 404；无头 Chrome：角色 6 编辑页有「收尾 / 进门片段」及横竖各「从素材库选视频」，只读页显示「进门 / 收尾片段」，品牌 6 编辑页无片段块、可「保存为 v4」。
- 2026-11-06 上线：备份 ~/AIContentStudio/db-backups/content_studio-before-persona-clips-20261106.db；经接口存品牌 6 第 4 版（无片段字段）、角色 6 第 2 版（outro_clip 16:9=618、9:16=619，无进门）；/content-personas/6/clips 返回两条 4.2 秒；素材 576 仍在。
- 2026-11-06 已归档并提交。
