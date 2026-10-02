## Why

现有模型配置仅支持mock/openai_compatible聊天，生图配置独立，Video/TTS/ASR未加载真实实现。用户要求平台负责适配模型与插件，并按手动标注能力自动规划路由，而不是先要求用户提供已经集成好的接口。

## What Changes

- 扩展既有模型Profile：明确协议适配器、模型标识、连接/密钥引用，以及聊天、生图、生视频、TTS、ASR等手动能力声明；声明、配置、真实验证分开。
- 增加统一能力路由：所选模型具备可执行能力则直连，否则自动调用管理员预配置的对应插件与其模型；只在已授权预算内执行。
- 配置插件能力、版本、所调用模型与参数限制；复用Registry，不执行任意用户脚本或自动安装插件。
- 用户的 Gemini 与 `grok-4.7` 均通过第三方 CPA 网关接入：复用可配置的 OpenAI-compatible 接口，不要求 Google 或 xAI 官方专用适配器。只有网关确实提供、且逐操作验证过的兼容协议才可执行；聊天模型名称不得自动获得生图/视频等能力。MiniMax 本地 CLI 仍按其独立的受控协议接入。
- Settings提供完整配置/能力/默认路由/插件fallback/执行解释；Workflow和Production复用同一resolver，冻结执行选择与安全provenance。
- 未配置、超预算、协议不支持时明确阻塞；请求已发出后结果Unknown不得自动换供应商重试。
- 2026-10-01 用户同意持久生成任务规格修订：增加最小 `ProviderGenerationTask` 记录，使本地重启后可读取原任务、按原job恢复、校验结果并人工接受入库；不把独立素材任务伪装成Workflow Run。
- Commons继续暂缓、保留未验证。生成内容不得替代真实截图、新闻照片或事实证据；不改变Candidate审批或公众号副作用授权。

## Capabilities

### New Capabilities
- `model-capability-routing`: 手动能力声明、模型/插件配置、统一路由、生成适配与安全执行。

### Modified Capabilities
- `product-settings`: 增加能力标注、生成插件与路由编辑入口，复用现有SystemSetting和安全投影。

## Impact

主要涉及runtime_config、routers/settings、services/system_settings、generation/providers、content_harness/providers/registry、provider_media/provider_calls、Workflow节点与Settings/Production前端。配置仍复用SystemSetting；修订方案仅新增一个ProviderGenerationTask任务表及加法迁移，不新建Asset/Workflow/计费账本。本轮仅提案，修订稿确认后才实施；迁移开发不等于执行本地生产库迁移。

本变更是F7生成能力补充，不自动关闭F7真实验收、不跳过F8安全前置。2026-10-01修订稿独立APPROVE后用户已授权apply；不push/deploy/生产迁移/公开发布/微信Unknown重试。
