## 开关

| 开关 | 写作类内置 skill | craft-resolve / craft-ae | AE 模板 |
|---|---|---|---|
| 开（默认） | 可读 | 可读 | 可用 |
| 关 | 拒绝 | 可读 | 可用 |

写作类内置 skill = 平台内置 skill 中 `kind == "skill"` 的条目（`studio_creative_catalog.SKILLS`），按作品形态列出（视频作品列视频、商品、研究、文字类；写稿作品列研究、文字、图文类）。

## 存储

每条作品一个布尔值 `third_party_platform_skills`，存在一个按作品记的系统设置里（`SystemSetting` 键 `unit_platform_skills`，`{unit_id: false}` 只记关闭的作品），不改表结构；没记录 = 开。读写接口：`GET/PUT /content-projects/{p}/units/{u}/platform-skills`，写需要编辑权限并记项目事件。

## MCP

- brief 附 `platform_skills: {writing_skills: "on"|"off", always_on: ["craft-resolve", "craft-ae"], readable: [{name, purpose, read}]}`，并写明「只用 readable 里的；off 时不用平台写作 skill」。
- `get_craft_skill(project_id, unit_id, skill, entry?)`：`skill` 为 `craft-resolve` / `craft-ae`（不校验开关）或内置 skill ref（校验开关，返回 SKILL.md 说明）。关闭时返回 `platform_skills_disabled`。

## 不做

- 不按阶段控制（用户改为统一开关）。
- 不改平台模型的「制作阶段方法」。
- 开 = 可以用，不强制必须用。
