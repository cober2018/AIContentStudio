# align-creative-orchestration-product：阶段 0–2

> 执行方式：`superpowers:executing-plans`，在已授权的本地 main 按批实施和核验。

架构：只复用现有 Project/Unit/Source/Fact/FactPack/Material/ProviderGenerationTask APIs；所有新入口均为投影或明确操作，不建立第二套真源。技术栈沿用 React/TypeScript/TanStack Query、FastAPI、SQLite、本地素材存储。

## 目标

在不改动 F8 未提交文件、不执行正式 SQLite 迁移、不调用外部供应商或发布接口的前提下，先完成产品入口统一和旧操作承接：

- 固化当前基线与 F8 文件所有权边界；
- 建立旧页面的操作级承接矩阵；
- 让 `/` 进入 `/home`；
- 让 `/production` 展示现有项目/内容单元的真实生产入口；
- 让新 `/assets` 与 Project Evidence 直接承接 Source、FactPack、Material 的既有 API 操作；
- 保留所有旧 URL，直到对应操作完成 parity 验收。

## 执行步骤 ///

1. 记录仓库、迁移、前端构建、OpenSpec、Ruff、diff-check 与现有路由基线。
2. 从 `App.tsx`、现有页面和 API 路由生成操作级 parity inventory，并记录不隐藏旧入口的理由。
3. 更新首页入口与生产队列，保持 Project/Unit/ProviderGenerationTask 为真源。
4. 把现有 Source、Fact、FactPack、Material 操作嵌入新 Assets/Project surface；不新建第二套资源真源。
5. 运行 TypeScript/Vite、相关后端回归、OpenSpec strict、Ruff、git diff-check，并核对 F8 文件哈希。
6. 阶段 0–2 完成后暂停，交付变更清单、门禁结果和剩余 parity 项。

## 当前进度

- [x] 已确认 `main@341ead8` 与 F8 脏文件边界。
- [x] 已确认新 change 共 147 项任务，按实际证据在 `tasks.md` 勾选。
- [x] 操作级 parity inventory 已建，旧菜单仍保留。
- [x] `/` → `/home`。
- [x] `/production` 真实 Project/Unit/原生任务投影。
- [x] `/assets` 与 Project Evidence/Assets 操作承接。
- [x] 后端、构建、bundle、规格、Ruff、diff 与隔离浏览器 15 组验证通过。
- [x] 独立操作清单与前端复核，记录发现和纠正；两路定向复核 APPROVE。

证据及限制：`docs/ALIGN_CREATIVE_PHASE_0_2_ACCEPTANCE.md`。本 change 的独立 `task_plan.md`、`progress.md`、`findings.md` 承接后续记录；不修改根目录 F8 owned 版本。

## 约束

- F8 现有 13 个脏文件保持 byte-for-byte 不变。
- 不新增 migration、不升级正式 SQLite、不写入正式素材库。
- 不调用 CPA、MiniMax、公众号或其他外部服务。
- 不删除旧路由；新界面只调用已有业务 API。
