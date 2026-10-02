# 模型与 AI 设置页整理

## 需求背景

用户要求只整理“模型与 AI”，融合原管理员工具的简洁布局，保留当前厂商登记、用途路由和生成能力配置。此切片是前端呈现调整，不修改连接、密钥、配置数据或后端。

## 目录结构

```text
organize-model-ai-settings/
├── .openspec.yaml
├── proposal.md
├── design.md
├── tasks.md
└── specs/product-settings/spec.md
```

## 已完成 / TODO

- 已完成：三视图布局、可读模型名称、渐进展开、稳定草稿 owner、独立保存范围、未保存离开确认和只读权限，四项批量任务 4/4。
- 本轮实际门禁：既有模型路由状态脚本 PASS；TypeScript/Vite/FE-P1 PASS；85 项既有后端模型路由/安全设置测试 PASS（1 项既有弃用警告）；全量 OpenSpec strict 34/34、diff-check PASS。
- 性能：Settings 初始 JS 236.53 kB raw / 77.28 kB gzip；Projects 224.89 kB raw / 72.96 kB gzip；技术指引及 legacy 按需加载，无 TipTap/XYFlow 混入。
- 浏览器实际覆盖桌面、390px 窄屏、三个视图间草稿保留、展开、继续编辑/丢弃离开及独立 origin 的 viewer 只读；未保存正式配置、未运行发现/生成。原生 Back/Forward 未验证，不记 PASS；该保护仅获源码复核。
- 两轮独立源码复核：SPEC APPROVED、四文件质量 APPROVE；只基于本切片前快照评审，不把其他 F7/F8 改动算入。
- 收尾已完成：本 change 新增六条要求已同步 `openspec/specs/product-settings/spec.md`，原有 10 条要求/15 个场景全文保留；共 16 条，无 Purpose TBD。CLI 归档到当前目录；归档后 strict 33/33、diff-check PASS。未提交、推送、部署、迁移或修改密钥/默认/路由数据。

## 本轮实际使用的技能

`using-superpowers`、`writing-plans`、`executing-plans`、`openspec-apply-change`、`design`、`subagent-driven-development`、`systematic-debugging`、`requesting-code-review`、`verification-before-completion`、`openspec-archive-change`、`finishing-a-development-branch`。用户要求在本地 main 开发且不新增测试代码，因此不另建工作树、不提交/推送；只运行既有回归和浏览器验收。

## 关键设计决策

- 厂商与模型 / 用途路由 / 生成能力与插件；局部侧导航、紧凑面板、小屏横向导航。
- 可读模型名，技术绑定和协议指引默认折叠；不嵌套完整 legacy 页面。
- 草稿状态 owner 稳定、独立保存范围与 CAS、密钥留空保留；不伪造多接口原子保存。
- 其他设置分区和全部旧契约保留；不更改实际模型选择。

## 依赖与启动

无新依赖或迁移，沿用根 README 的本地 API/Web 启动方式。前端工作目录 `apps/web`，使用 `npm run dev`；正式实施前先确保当前 API 已提供 `/settings/product`、`/settings/model-registration` 和 `/settings/model-capabilities`。

规格校验：`OPEN_SPEC_TELEMETRY=0 openspec validate organize-model-ai-settings --strict`。
