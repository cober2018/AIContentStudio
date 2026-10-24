# 工作台任务原型实施计划

**Goal:** 全站未优化模块完成入口/页面盘点，交付可点击原型供确认。
**Architecture:** 独立静态HTML/CSS/JS；不接正式API；主导航覆盖全部日常模块，深度验证机会链，其余验证页面关系。
**Tech Stack:** 浏览器原生HTML/CSS/JS、Python静态服务、现有浏览器检查工具。

用户已经授权本轮原型设计，未授权正式改造。复用本目录，不新建第二套计划。无新增持久测试，检查使用临时脚本；不提交/推送/归档未确认设计。

- [x] /// 1. 阅读README、现有路由、主要页面和架构蓝图；写module-audit.md。
- [x] /// 2. 建立proposal/design/spec，明确保留边界。
- [x] /// 3. 在prototype/index.html、style.css、app.js实现原型；不改apps代码。
- [x] /// 4. 检查机会列表→详情→调整→确认→工作台，以及资料列表详情、审阅和复盘路径。
- [x] /// 5. 桌面/手机、空失败状态、键盘、草稿返回、分页、无网络业务写入验证。
- [x] /// 6. 独立设计/代码复核；更新README/progress/findings/review，向用户展示原型。
- [x] /// 7. 用户确认后细化首批正式模块delta并apply；整体archive移至tasks第5节。

验证：`node --check prototype/app.js`；`openspec validate redesign-studio-task-navigation --strict`；浏览器实际操作与截图。不把原型覆盖当业务功能通过。

## 首批正式实施计划（2026-10-19用户已确认）

- [x] /// 8. 更新同一proposal/design、content-opportunities与content-home-workspace增量规范；读取当前业务实现。
- [x] /// 9. OpportunityPages.tsx/opportunityTypes.ts及必要局部组件：列表/详情/方向/选源/历史/运行页；原API和权限保留。
- [x] /// 10. HomePage.tsx：三块任务概要与独立记录页；保留导出链接函数与优先级。
- [x] /// 11. App.tsx仅按需要集成；现有商品/角色工作台、数据和并行改动不重置。
- [x] /// 12. npm build、既有机会/主页检查与临时隔离交互检查；无新增持久测试。
- [x] /// 13. 独立规范和代码评审，修复并回写同一README/progress/findings/review。

当前大量相邻未提交代码是正式运行基线的一部分；本轮按用户授权在原工作区定向叠加，避免创建不含这些依赖的旧提交工作树。不会checkout、clean或整文件还原。后续模块仍按tasks第5节推进，不把首批交付标为全站结束。

## 第二批实施（tasks 5.1）

- [x] /// 14. 核对实际队列/项目实现，补同一design与project-core规范，原五/六步不改。
- [x] /// 15. ProductionQueuePage.tsx：作品与执行记录独立URL、筛选/分页保留、懒加载和生命周期回归。
- [x] /// 16. PersistentProjectsPage.tsx：档案列表、新建独立页、权限和草稿；PersistentProjectPage.tsx/ProjectOverviewTab.tsx：职责分组及继续制作。
- [x] /// 17. 现有project/lifecycle/API检查、Web构建、隔离交互和正式GET页面手机/桌面验收。
- [x] /// 18. 独立规范/代码审查、修复、回写README/progress/findings/review，勾选5.1；其余后续任务保留。


## 第三批实施（tasks 5.2；2026-10-19用户授权）

- [x] /// 19. 核对FE-F4合同与当前页面，更新同一design、proposal和review增量规范，明确商品账号与旧深链边界。
- [x] /// 20. ProjectReviewCenter.tsx列表/详情/四步/历史URL、草稿/权限/失败状态；原审批交付合同保持。必要复用子组件，不改已优化工作台。
- [x] /// 21. project_review_projection.py仅添加production_domain只读字段，商品走owned accounts目录，避免null或历史persona依赖。
- [x] /// 22. Web构建预算、既有FE-F4/多账号/交付/对账检查；临时全拦截浏览器写链和正式GET布局/数据不变回读。
- [x] /// 23. 独立规范和代码/TS/Python复核、修复、更新同一成果文件，验收通过才勾5.2；其他批次不扩展、不提前归档。


## 第四批实施（tasks 5.3；用户已授权）

- [x] /// 24. 核对身份/栏目与素材知识既有合同，补同一design和两项capability delta，保留范围与数据。
- [x] /// 25. IdentityWorkspace.tsx：对象目录与URL列表/概览/编辑/历史/关联分层，兼容persona旧链接与独立账号、权限/草稿/竞态；创作子组件保持。
- [x] /// 26. SystemAssetsKnowledgePage.tsx及必要systemLibraryTypes：分类URL列表→独立详情/版本/引用/管理；工具单独入口；精确引用/集合修订/权利不改。
- [x] /// 27. App.tsx仅必要账号兼容入口定位；LearningWorkspace仅MemoryPanel增加只读参数；既有API检查、构建预算、全拦截临时写链、正式只读桌面/手机及数据/保留组件指纹核对。
- [x] /// 28. 独立规范/TS代码复核并修正，回写README/progress/findings/review，验收后勾5.3；5.4/5.5继续保留。


## 第五批实施（tasks 5.4；用户已授权）

- [x] /// 29. 更新同一design/spec，冻结模型组件与现有工作台指纹，读取复盘与设置合同。
- [x] /// 30. LearningWorkspace：复盘列表/详情/分析/候选/记忆分层，表单按明确任务打开，权限/缺失/深链保留。
- [x] /// 31. ProductSettingsPage：用途目录/URL分类与分页；元信息折叠，模型内部及离开草稿保护保留。
- [x] /// 32. 既有合同检查、构建预算、隔离交互、真实只读桌面/手机、数据/组件不变核对。
- [x] /// 33. 独立规范/TS审阅与修复，回写成果；通过才勾5.4，未完成不得归档。

- [x] /// 34. 五批均通过后同步7个canonical规格的21新增要求，19/19完成并执行OpenSpec archive；回读规格和归档路径。


## 归档后主链回归（用户明确授权发现问题直接修）
沿用已确认的任务导航/返回路径规范，本轮补充验收和修复，不重开已关闭的原型范围。
- [x] /// 35. 从主页经机会/项目/创作/审阅/复盘实际读取，记录断点与数据基线。
- [x] /// 36. 仅修跨页入口、返回上下文和角色/商品文案；保留制作内部和模型配置。
- [x] /// 37. 正式只读走链、隔离转换/交付/复盘操作及跨页返回、异常深链/手机/草稿返回验证及构建。
- [x] /// 38. 独立规范/代码复核并修复，回写归档同一成果和README。


## 真实科技内容本地交付验收（用户授权，不公开发布）
- [x] /// 39. 选择现有科技机会，核验冻结来源，建立真实项目与文字作品。
- [x] /// 40. 使用正常模型创作链生成、审阅并保存主稿；真实检查、冻结和本地交付。
- [x] /// 41. 检查交付文件与页面回读，修复阻断并记录证据；禁止公开发布。


## 角色检查提醒修复
- [x] /// 42. 复现输入截断，按文字职责投影身份并提升检查版本。
- [x] /// 43. 既有检查、独立代码审阅、真实模型检查和交付状态复核，回写证据。


## Real lifestyle opportunity acceptance (authorized; no public publication)
- [x] /// 44. Select real persona3 opportunity, verify source and freeze evidence, create project/unit.
- [x] /// 45. Execute existing creative stages and review actual outputs; fix only observed blockers.
- [x] /// 46. Approve local candidate, verify ZIP and live UI, preserve prior workflows and record evidence.

- [x] /// 47. Scope identity semantic review to role rules; retain independent fact gate; run existing checks and actual lifestyle pipeline.


## Real two-persona graphic/audio acceptance (authorized; no public publication)
- [x] /// 48. Preserve model/default/workspace state, create scoped graphic and audio units under existing real projects35/36.
- [x] /// 49. Run two graphic recipes, review rendered PNGs and local delivery.
- [x] /// 50. Run two audio recipes using existing voices, inspect actual audio and local handoff.
- [x] /// 51. Fix observed blockers only, verify normal UI and artifacts, record limits and no-publication proof.

/// 本轮限定修复：保留stage.graphic.compose的固定工具身份，复用现有合同与检查；不改变模型配置、方法开关和公开门禁。修复后重新跑实际预览及既有回归。

48–49已完成；50仅生活通过，科技TTS原任务结果未知，保留未勾选。51已完成限定修复/独立审查/748项既有检查及组件保留核对，整体验收待科技音频完成。

/// 科技音频续验：用户明确授权保留原参数重试。先复现捕获CLI诊断，再沿正常阶段完成TTS、ASR、QC和本地交付；保留旧unknown记录，不改模型与音色。

/// 额度刷新续验：旧run21未知任务不能在同一运行自动重发；按用户明确授权，在同一unit44启动run24重试，旧回执保留。保持workflow33、原音色/模型参数，逐项接受口播/声音方向后执行TTS→ASR→QC→本地ZIP。

额度刷新后run24五阶段和本地ZIP闭环完成，50–51已勾选；前述未完成描述为历史状态，以最新闭环记录为准。
