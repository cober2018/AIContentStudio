# Creative Orchestration：第一批入口整合验收

日期：2026-10-04。范围：`align-creative-orchestration-product` 阶段 0–2，不是整个 change 的最终验收。

## 基线与所有权

本地 `main@341ead8` 加本批未提交前端修改。正式数据库只读核验 head 为 `f7d000000001`；当前已有代码的 Alembic head 为 `f8a000000001`，只在隔离库应用现有迁移。没有新迁移文件，也没有升级正式库。

F8 的 13 个已有 tracked dirty 文件（包括根 README、根三份进度文件、F8 change 和现有 runbooks）通过 `/tmp/aics-f8-before-align-creative.sha256` 全部核验一致。本批只读这些文件，不覆盖现有 F8 工作。F6E tasks 和 active lifecycle 未修改。

## 已实现的入口

| 入口 | 本批结果 | 没有隐式执行的动作 |
| --- | --- | --- |
| `/` | 进入 `/home`；旧 `/dashboard` 和 `/legacy/landing` 保留 | 不自动创建项目或任务 |
| `/production` | 原 Project/Unit 列表、筛选、20 条分页；最近最多 50 条原生任务投影 | 不生成、恢复、重发、接受结果 |
| Project | 原七个 Tab 保留，新增渠道变体和执行入口 | 打开 Tab 不适配内容、不改 Master |
| Assets / Project Evidence | Source 导入与事实操作、FactPack 创建/编辑/冻结/克隆、精确 Project 引用/事实边界 | Source / Collection 不自动成为 Fact Boundary |
| Assets / Project Assets | 上传、原生预览/接受、搜索入口、版本与权利、撤权、精确引用 | 接受 MaterialRevision 不自动改 Master |
| Settings | Connector 配置/显式拉取和既有模板工具按需展开；高级工具保持显式 | 读清单不探测、不拉取、不生成 |

相关流程：

```text
来源导入 → 候选事实 → 人工核对/确认 → FactPack → 明确冻结
                                                    ↓
                                 ProjectSourceBinding + 显式 Fact Boundary

全局 / 旧临时生成预览 → 人工核对许可并接受 → exact MaterialRevision
                                                    ↓
                                       另行明确 Project 引用 → 显式 Master 保存

项目绑定的持久生成任务 → 人工核对许可并明确接受 → MaterialRevision + Project 引用
                                                                    ↓
                                                            独立显式 Master 保存
```

旧路由及 `LEGACY_NAV` 均保留。操作级清单见 `LEGACY_OPERATION_PARITY.md`；入口能访问不是全部操作已终验。

## 隔离浏览器/API 验收

临时目录：`/tmp/aics-align-acceptance.XgX4KU`。API 绑定 `127.0.0.1:18264`，Web 绑定 `127.0.0.1:15664`，SQLite/素材与正式目录分离。仅临时 API 进程安装固定图片 Provider；源码注册表和正式配置未改。

| 检查组 | 实际断言 |
| --- | --- |
| root_home_readonly | 根地址显示 Home，读取没有业务 mutation |
| idea_to_project | 从新 Projects 页面显式创建并回读项目 |
| source_import_extract_edit_confirm | 导入文本，rule 抽取，人工编辑/确认，回读日期与事实状态 |
| factpack_create_add_remove_clone_freeze | 在新 Assets 添加/移除事实、冻结、克隆；原 frozen checksum 不变 |
| source_and_frozen_boundary_by_reference | 新 Project 页面引用 exact Source、绑定 frozen pack；回读版本/checksum并打开事实 Drawer |
| material_upload_exact_rights_reference | 上传真实 PNG 字节，核对 SHA256，默认无公开许可，明确引用与撤权，hash 不变 |
| controlled_native_preview_explicit_accept | 未接受时不新增素材；明确接受后只新增一个精确版本，不自动新增项目单元/引用；撤权后 public true→false，原字节 hash 不变 |
| queue_exact_unit_and_project_paths | 只读队列指向精确 Unit；Project 渠道变体/执行 Tab 可用，读取无写入 |
| settings_embedded_and_legacy_urls | Settings 内打开 Connector/模板工具；旧 Source/Pack/Material/Dashboard/Landing URL保留实体路径 |
| project_source_file_as_of | Project 页面上传文本文件，真实回读 as_of=2026-10-01 及项目 Source 引用 |
| project_durable_accept_reference_refresh | 隔离签名任务接受前无引用；UI 明确接受后真实 API 写入 MaterialRevision + ProjectMaterialReference，当前列表立即更新，Master/Unit 不自动新建 |
| task_deeplink_read_refresh_recover_no_resend | deep link 和刷新无 mutation；显式 recover 只有一次原任务查询；无原 job 时保持 unknown，不 dispatch |
| archived_task_deeplink_readonly_and_accepted_history | 归档任务结果可读而接受禁用；已接受任务原字节可读，不再显示接受按钮；均无写入 |
| viewer_owned_active_project_readonly | viewer 自己的活跃 Project 可读；来源 Drawer 不显示事实写控件，新包/上传/生成操作不开放 |
| viewer_and_archived_readonly | viewer 无导入/事实写操作；归档 Project 无新包/事实写入口，原历史可读 |

结果：15/15 通过、零 page error。最后一轮 fixture IDs：Project #13、Source #11、FactPack #19、上传 MaterialRevision #17、接受的生成 MaterialRevision #18、Unit #8；追加受控任务 Project #14、归档 #15、viewer #16，均仅存在于临时库。原始报告和截图在临时目录的 `browser-report.json`、`production-queue.png`、`assets-source.png`。

持久任务 UI 检查通过临时脚本建立有效签名的 fixture row，再由既有服务 `_output` 保存受控 PNG 并产生 result receipt；接受、素材引用、原结果读取和 recover 均走真实本地 API，没有替换这些 API 的响应。Provider 的 runtime identity 与图片仅在临时进程替换；未执行真实 prepare/dispatch、未消耗供应商额度。它证明入口边界与原生接受数据流，不代替真实模型能力验收。

浏览器最终显式阻断外部请求。既存字体与旧 Landing 演示视频有被阻断的请求尝试；没有模型/搜索/公众号请求。不将受控生图称为真实模型能力，不将前端阻断当作整个测试宿主无网络调用的证明。

## 执行门禁与启动纠正

| 门禁 | 最近实际结果 |
| --- | --- |
| 全量后端 | 1660 passed / 28 skipped / 8 warnings，最终隔离复跑 82.13 秒 |
| TypeScript / Vite | PASS |
| FE-P1 / import graph | PASS；`/projects` 225.02 kB raw / 72.99 kB gzip |
| 新 Production 队列首包 | 228.09 kB raw / 74.03 kB gzip，无 TipTap/XYFlow |
| Assets / Settings 首包 | 262.14 / 239.83 kB raw，无 TipTap/XYFlow |
| Common Production 首包 | 284.61 kB raw / 90.52 kB gzip，无 TipTap/XYFlow |
| OpenSpec strict | 35/35 PASS |
| Ruff / git diff --check | PASS |
| F8 文件 SHA256 | 13/13 一致 |

后端命令使用测试环境和已初始化的独立路径，在 `apps/api` 中运行。最终复跑采用另一临时库，避免与浏览器 API 共用文件：

```sh
APP_ENV=test DATABASE_URL=sqlite:////tmp/aics-align-backend-ready.9xpuJU/studio.db AI_STUDIO_MEDIA_ROOT=/tmp/aics-align-backend-ready.9xpuJU/media .venv/bin/python -m alembic upgrade head
APP_ENV=test DATABASE_URL=sqlite:////tmp/aics-align-backend-ready.9xpuJU/studio.db AI_STUDIO_MEDIA_ROOT=/tmp/aics-align-backend-ready.9xpuJU/media .venv/bin/python -m pytest -q
```

最初的 `.venv/bin/pytest` + 默认 development 启动曾出现 `scripts` import 和 health fixture schema 失败；调整为 `python -m pytest` + `APP_ENV=test` 后通过。随后用未初始化的新临时库复跑得到 1659 passed / 1 failed，失败是旧 Worker 的独立连接缺少 `content_job` 表；初始化上述隔离库后，定向队列测试 4/4 和最终完整复跑均通过。没有为这些启动差异修改后端。此处是本批工作区的新鲜验证，未声称改动前的 pristine 前端已单独重建。跳过项不是本批已验收功能。

## 复核与未完成范围

首轮独立产品/操作清单与前端复核发现入口边界问题：项目绑定持久任务接受的引用说明/列表回读不符；任务 deep link 缺少状态刷新/查询原任务；viewer 自己的活跃项目及归档 task 的写控件未完整只读；Project 文件导入未承接资料日期。已核对既有后端语义并修正入口，未改生成/发布规则。追加隔离检查通过，两路独立定向复核均为 APPROVE，没有剩余本批 blocker。独立复核没有声称重新执行上述 gate；产品复核批准清单与本次修正，不代表 full legacy-operation acceptance 或旧导航退场授权。

本批状态：EXECUTED / REVIEW_PASSED；OpenSpec 22/147，125 项未勾选（含全程停止条件 0.6）。后续持久化、Creative Intent、Execution、MCP、Capability Memory、Video 收敛及完整验收仍待实施。

未验收：真实 URL 抓取/Commons/Provider 联调、每个旧高级操作的全量终验、Creative Intent/Execution/MCP/Capability Memory/Director-first Video、完整生成质量与成品发布闭环。

未执行：正式 SQLite/素材写入、真实供应商或公众号调用、新业务表/迁移、canonical sync/archive、本地 commit、远端 push/deploy。后续范围继续由已批准的同一 change 约束。
