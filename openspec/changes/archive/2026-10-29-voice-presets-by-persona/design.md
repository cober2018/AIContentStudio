# 设计

| 项 | 做法 |
|---|---|
| 存储 | `SystemSetting` 键 `voice_presets`：`{default: id, items: {id: {name, voice_id, emotion, rate, volume, pitch, ...}}}`；首次读取时把现有 `voice_default` 迁成一套「男声」并设默认；`voice_default` 之后不再写（只留新版本） |
| 设置 → 配音 | 列表 + 新建 / 改名 / 删除（默认那套和被角色引用的不能删）/ 设默认；编辑项沿用现有字段 |
| 角色 | 角色 profile 的音频配置加 `voice_preset_id`，替代原 `parameters.voice`；角色页「音频」里用下拉选声音配置 |
| 商品作品 | 发起（SKU「发起作品」和商品发起对话框）加「属于哪个账号角色」下拉，写入作品 `persona_id`；作品「制作设置」用 `voice_preset_id`（可空）替换 `voice_id` |
| 配音解析 | `voiceover.settings_for(db, unit)`：作品 `voice_preset_id` → 角色 `voice_preset_id` → 默认；`generate` 和多角色配音都用它；结果里写明用的是哪套 |
| 视频简报 | `voice_settings` 改成这条作品实际会用的那套（带名字） |
