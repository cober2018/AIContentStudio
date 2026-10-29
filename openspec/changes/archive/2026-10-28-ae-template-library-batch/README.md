# AE 模板库第二批（46 个竖屏模板）

- 阶段：已完成并归档（2026-10-28）
- 结果：口播、AI 科技短片、生活短片用的 46 个 9:16 AE 模板入库（全部 ready），分关键词与标题、金句与对句、标注与聚焦、人物与图形、数字与图表、步骤流程对比、开场章节转场、素材与地图、结尾引导九类；透明叠加类出 ProRes 4444 .mov。播放安全区规格（用户提供）收进 craft-ae/safe-zones/，每个工程带安全区参考层，check_safe_area.py 零越界。
- 代码：`apps/api/craft_skills/craft-ae/scripts/make_templates.py`（构建）、`scripts/check_safe_area.py`（安全区检查）、`templates/<id>/v1/manifest.json`（说明书）、`safe-zones/`（规格）、`apps/api/app/services/craft_skills.py`（alpha 渲染、参考图拷贝）。工程在本机 `~/AIContentStudio/ae-templates/`。
- 预览：`output/template-preview/index.html`（本地审片页，未进版本库）。
- 下一步（另起需求）：横屏 16:9 版本 + 预览视频进模板库与设置页展示 + 「默认大模型选模板、用户明确要求才指定」规则；之后做商品工作台的模板（参考 clipforge 方向）。
