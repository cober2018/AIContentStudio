# Creative Orchestration：Legacy parity 与最终验收

> 执行技能：openspec-apply-change、writing-plans、executing-plans、subagent-driven-development、requesting-code-review、verification-before-completion。

## 目标与批准边界

沿用已批准的 `align-creative-orchestration-product`；开始时本地 main@341ead8，131/147。关闭剩余 Legacy 操作承接、兼容导航、完整隔离链路与独立最终复核，不新增产品能力。

正式环境仍为本机 SQLite、素材目录、loopback API/Web；本批只使用 `/tmp` 库/素材副本。F8 13 个 owned 文件保持 byte-for-byte。不动正式库/配置/凭据/Worker，不外发模型、公众号或专业工具，不新增表、迁移、依赖、永久测试，不提交、push、deploy、canonical sync/archive。

## 执行步骤 ///

1. /// 固定所有 remaining tasks 与 parity 行，复核本计划；Assets、Settings、历史操作由独立 worker 在不同 `/tmp` fixture 核验。
2. /// 父层核验日常入口创建项目 → Source/Fact/FactPack → 手工 Text Master → Checks → Candidate → Approval → 本地 ZIP；历史 Draft/Candidate/Receipt 精确读取，不做隐式迁移。
3. /// 仅修实际复现的承接缺口；Assets/Settings worker 写集彼此隔离，父层持有 App 导航与文档。完整 inventory 通过后，旧入口只移至 Settings 明确高级兼容入口，保留所有旧 URL 和 record identity。
4. /// 用隔离浏览器覆盖新首页/队列、三种内容、五种 Variant、执行与方法库闭环；既有批次证据按日期合并，不把旧门禁冒充本轮重跑。
5. /// 独立 SPEC、后端/数据安全、MCP、前端/产品复核；先复现发现，再做最小修复与复审。
6. /// 新鲜全量后端、TypeScript/Vite/FE-P1、OpenSpec strict、Ruff、tracked/owned untracked whitespace 与 F8 hash 门禁。
7. /// 按实际结果更新 parity、North Star、change-local README/task_plan/progress/findings 和最终验收；仅通过后勾选剩余任务。保持生命周期/正式启用待单独授权，停止本批隔离进程。

## 文件责任

- 父层：`apps/web/src/App.tsx`、`docs/LEGACY_OPERATION_PARITY.md`、North Star、change-local 记录、本计划及最终验收。
- Assets worker：只可窄修 `Sources.tsx`、`FactPacks.tsx`、`Materials.tsx`、`SystemAssetsKnowledgePage.tsx`、Project Evidence/Assets tab；发现后端契约缺口先报告。不得改 Settings/App。
- Settings worker：只可窄修 `ProductSettingsPage.tsx`、`Connectors.tsx`、`Templates.tsx`；不得改 App、Assets、后端或根文档。
- 所有 review agent 只读；临时断言/证据用自己新建的 `/tmp` 目录。共享工作树不回滚别人修改。

## 完成判据

操作级 parity 有准确分类和可达位置；旧页面只退日常导航、不删除。完整链路及全部独立复核通过；严格区分实现验收、正式 SQLite 尚未启用、canonical/archive/本地提交待授权。

## 本批结果

六路独立 agent 因额度限制未完成，父层接手可执行的操作核验，未把复核标为通过。本批实际修正五个现有前端文件，完成日常 Text 到 ZIP、旧历史原路由/全表不变、证据授权/撤权取消/周期明确保存/模板草稿归档/兼容目录与权限失败关闭；新鲜门禁通过。累计 138/147，9 项保持后续。旧菜单继续显示，不把本批部分验收当作整个计划完成，完整证据见第七批验收记录。
