## Why

平台已接 6 个免费素材库，但 API Key 只能写在后台启动配置文件 `scripts/startup/runtime.env` 里，页面没有入口；现在只配了 Pixabay，Pexels 因为没 Key 一直搜不到。用户要在设置页统一配置素材数据源，并先接入 Coverr（视频）。音频来源（Freesound、Jamendo）和配乐 / 音效搜索留到下一个需求。

## What Changes

- 设置里新增「素材数据源」页：每个来源一张卡片——说明（擅长什么、许可）、是否需要 Key、Key 输入与掩码显示、启用开关、「测试」按钮、申请 Key 的链接。
- 已有 6 个来源（Pexels、Pixabay、Openverse、Wikimedia Commons、NASA、Internet Archive）改由这里管理；页面保存的值优先，没保存过时沿用 runtime.env 里已有的 Key，现有配置不丢。
- 新接 Coverr 视频来源，进入现有镜头素材搜索；许可按 Coverr 许可登记。
- 关掉的来源不参与搜索；没配 Key 且必须要 Key 的来源显示「未配置」。
- Key 只存后台，接口和页面只返回掩码，不进日志和回执。

## Capabilities

### New Capabilities
- `stock-sources`: 素材数据源的设置、启用与测试，以及 Coverr 来源。

### Modified Capabilities
（无）

## Impact

- 后端：`apps/api/app/services/open_media.py`（来源读取设置、Coverr 来源）、`apps/api/app/runtime_config.py`（新 key）、`apps/api/app/routers/settings.py`（读写与测试接口）。
- 前端：`apps/web/src/product/` 新增设置页组件并挂到设置导航。
- 无数据库迁移（沿用 `system_settings` 表）。无新依赖。
