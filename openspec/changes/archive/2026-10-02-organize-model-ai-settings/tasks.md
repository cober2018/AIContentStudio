## 1. 一批完成界面整理

- [x] 1.1 /// 用户明确确认本提案后，整理 ProductSettingsPage 模型分区为三视图局部导航；移除该分区嵌套旧全页，保持其他五分区及 legacy 路由不变；父组件汇总登记/路由与能力两个编辑器 dirty 状态，加入离开分区的保留/丢弃保护。
- [x] 1.2 /// 重排 ModelRegistrationSettings 为厂商摘要/展开编辑、分组模型列表及独立用途路由表；保留单一草稿 owner、获取/手动登记、完整 save envelope、密钥语义、actor 隔离和 409 编辑保留；保存栏清楚列出跨视图草稿范围。
- [x] 1.3 /// 重排 ModelRoutingSettings 和 ProviderGuidancePanel 为可读模型名、能力摘要、展开绑定、插件/回退/限额及按需技术指引；保留独立草稿/CAS与真实 capability 状态，不改配置数据、不触发任何供应商请求。

## 2. 验收与收尾

- [x] 2.1 /// 使用既有 `node apps/web/scripts/test-model-routing-state.mjs`、Web TypeScript/Vite/FE-P1、OpenSpec strict及diff-check；浏览器验证桌面/窄屏布局、模型名称、视图切换草稿保留、dirty 离开提示、展开动作与只读状态，不调用真实 discovery/generation或写正式配置。需要保存/409验证时仅用既有隔离验收基础设施，不生成新测试代码；完成文档与独立范围复核后按授权同步本delta并归档，不推送/部署、不混入其他dirty改动。
