## Why

“模型与 AI”页面把厂商登记、用途路由、逐模型能力、插件限额、Provider 指引和完整旧管理员工具堆在一起；重复的模型列表、内部 ID 和多层页面壳让配置流程难以理解。用户确认只整理这一分区，沿用老管理员工具的紧凑配置风格，其他设置分区不动。

## What Changes

- 保持 `/settings` 的六个一级分区不变，只在“模型与 AI”内提供三个清晰的配置视图：厂商与模型、用途路由、生成能力与插件。
- 采用老版的左侧局部导航、右侧紧凑配置面板；小屏使用横向可滚动导航。统一标题、表单行、状态和保存栏，不嵌套完整旧 Settings 页面。
- 厂商摘要默认只展示名称、连接地址、密钥是否配置和模型数量，编辑时展开表单；模型使用可读名称，内部 Profile ID 收进技术详情。
- 全局默认与业务用途选择集中在用途路由；生成能力、插件和回退限额集中在独立视图。Provider 协议指引和旧兼容配置默认收起。
- 保留全部已实现配置动作、现有安全/CAS/权限边界。切换内部视图不丢本地编辑，不调用供应商、不自动保存、不改变模型选择。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `product-settings`: 规定模型分区的任务导向布局、可读模型标识、局部草稿生命周期、真实能力状态与独立保存反馈；所有现有要求保留。

## Impact

- 仅涉及 `apps/web/src/product/ProductSettingsPage.tsx`、`ModelRegistrationSettings.tsx`、`ModelRoutingSettings.tsx`、`ProviderGuidancePanel.tsx` 的布局和展示；必要时增加一个局部布局组件，优先编辑现有文件。
- 原 `apps/web/src/pages/Settings.tsx` 仅作风格/兼容能力参考，`/legacy/settings` 保持原样；不复制其无版本模型 writer。
- 使用现有 React、Tailwind、UI 组件与懒加载；不新增依赖、后端 API、持久对象或迁移。
- 保留当前脏工作区的其他改动；本提案等待用户明确确认后 apply，不提交、推送或部署。
