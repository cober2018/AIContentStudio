# 设计

| 项 | 做法 |
|---|---|
| 取资料 | 新 `persona_brief(db, user, unit)`：`content_identity.effective(persona, account, series)` 取合并资料；去掉 `*_creative_profile` 和内部键，只留第 1 条列出的字段；声音取 `voiceover.settings_for(unit)` 的名称 |
| 定制方法 | 取 `{modality}_creative_profile`：`mode == "composed"`（页面「在这里完整设置」）时输出 `skill`（ref + `get_craft_skill` 读法）、`style_preset`（ref + config）、`quality_profile`（ref + checks）、`stage_instruction`、`parameters`、附加方法 / 参考风格（按 revision 取名称和正文，正文截断到 4000 字）；其他 mode 输出 null |
| 接入 | `video_chain.brief` 和 `article_chain.brief` 各加 `persona` 键；规则里加一句用法；无角色的作品为 null |
| skill 读取 | `craft_skills.read_skill` 允许读这条作品角色配置里指定的 skill ref |
| 商品 | `production_domain == "product"` 时 `creative` 固定为 null |
