## Why

用户需要先注册厂商 API/密钥，再获取和保存模型，最后在各业务环节选择模型。现有 Settings 能力编辑器没有完整厂商入口；旧 models 路由也没有可管理的全局默认。用户指定 CPA 的 gemini-3.8-flash-high 为默认。

## What Changes

- Settings 增加厂商登记、写入型密钥编辑、模型获取/手动补录和已注册模型列表。
- 复用现有 SystemSetting 配置及 CAS，不增加业务表或迁移；保存不覆盖现有能力、插件、路由。
- 支持 OpenAI-compatible CPA 网关；可信局域网 HTTP 仅允许管理员明确登记的精确 endpoint，不放宽媒体下载/其他网络边界。
- 全局默认为用户选择的 gemini-3.8-flash-high；各环节可选择已注册且适合该能力的模型或继承默认。
- 模型列表不证明聊天/生图/视频支持；能力仍人工标注并经真实 adapter 验证。

## Capabilities

### New Capabilities
- `provider-model-registration`: 厂商、模型发现/登记、默认与业务环节选择。

### Modified Capabilities
- `product-settings`: 新增厂商登记及环节选择产品入口，不删除原有要求。

## Impact

主要影响 apps/api/app/routers/settings.py、services/system_settings.py、services/model_capability_routing.py、services/generation/providers.py、apps/web/src/product/ModelRoutingSettings.tsx 和 ProductSettingsPage.tsx，以及实际调用这些场景的消费者。与 add-model-capability-routing 共享配置真源并协调版本化写入。此次先提案，等待 apply 确认；不调用生成、不提交/推送/部署、不记录实际密钥。
