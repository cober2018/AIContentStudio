# 本 change 执行计划

## R1 / R2 收尾复核（2026-10-05）

/// 只读确认正式aco/null身份与仓库缺口 → 先补本change规格/任务 → 主线程对齐schema/F8/恢复文档并测试默认head → 三组独立测试并行固化execution/MCP/capability → 隔离定向/全量、Web预算、strict/Ruff/diff → 更新回执并交回最终收尾复核。正式API/Web/Worker保持运行，不改正式数据库/凭据、不提交归档。

- [x] 复核R1/R2事实并明确仅授权F8 schema/current-state窄修。
- [x] 对齐当前approved head与历史证据；迁移/default/inert测试。
- [x] 固化三组核心域测试，均用临时存储，不访问真实供应商。
- [x] 完整门禁与本轮执行回执；后端1768/28 skipped、Web/FE-P1、strict35/35、app＋新测试Ruff及空白检查。
- [ ] 同工作区最终closeout复核（15.7）；通过前不sync/archive/commit。

原147项实施已通过；新增7项收尾任务中6项完成，当前153/154，ARCHIVE_READINESS=PENDING_FINAL_CLOSEOUT_REVIEW。此前ARCHIVE_READY为复核前快照；R1只改默认head和当前schema文档，R2固化108项，保持正式服务运行。

## 整体执行回执（2026-10-05）

/// 只读核对147项任务/12份delta、当前Git与正式运行状态 → 对齐各批验收/独立复核证据 → 在既有最终验收文档加入可转交回执 → 同步本change记录并检查空白与F8 ownership。只写回执，不提交、归档、调用模型或发布。

- [x] 核对任务数、真实main基线、schema与API/Web健康，重跑strict和diff-check。
- [x] 汇总完整实施范围，区分隔离业务链路、正式联通、历史证据和未执行的生命周期动作。
- [x] 更新既有最终验收回执、README和本change记录，不覆盖F8根记录。

## 本机正式启用（2026-10-05，用户已授权）

目标：同一台电脑、原SQLite/本地素材/loopback，完整使用已验收新版。范围包含备份、正式schema升级、API/Web/原Worker重启、本机MCP接入及正式环境验收；不含公开发布、付费生成、提交/push、canonical归档或兼容页删除。

/// 核对现有进程/私有配置/真实库及媒体根/任务状态 → 暂停原API/Worker写入 → 同快照SQLite在线备份＋引用媒体copy/hash＋私有配置保全 → 副本升级明确aco000000001并逐历史行比较 → 正式升级明确目标并复验 → 最小补现有runtime.env的head/MCP身份配置 → 原launchd/API/Worker与loopback Web启动 → readiness、九入口/历史、受限MCP及本地闭环验收。

- [x] 启用前基线、无未决运行任务、配套备份和隔离恢复/迁移验证。
- [x] 正式SQLite增量升级、历史行/素材hash及外键基线不漂移。
- [x] 原API/Worker和Web启动、稳定私有MCP接入、健康与loopback范围验证。
- [x] 正式环境联通、内容与历史读取及准确记录；完整业务写链沿用隔离验收，不在正式库重复制造示例，既有风险/未来专业工具范围继续保持真实。

本机正式启用完成：head `aco000000001`，API8000/Web5173只监听127.0.0.1；原API/Worker已恢复，正式MCP及真实Codex客户端只读连接通过。83张历史表/5145行原始列hash、97条既有外键异常集合和7条媒体引用/5份字节hash保持一致。启用记录与配套快照见 `docs/ALIGN_CREATIVE_LOCAL_ENABLEMENT.md`；无新业务记录、外部调用或全局Codex配置改动。

回退：升级/启动任何失败先保留失败库与同快照，停止写入，不自动降级/删历史；只有新域无正式写入且旧原始行hash一致才可回原快照。未改APP_ENV技术口径/媒体根/凭据/Worker拓扑。

## 当前结果（2026-10-05）

147/147、IMPLEMENTATION_ACCEPTED / ARCHIVE_READY，现已另行授权完成本机正式启用。三类最终复核及导航窄复核APPROVE；以下步骤、旧计数与“不迁移正式库”描述保留为启用前历史。canonical归档与提交仍未执行。

## 范围与批次

六批领域实施及第七、八批日常 Text/旧历史/Assets/Settings parity 修正已实施，累计 141/147。导航退出和三类独立最终复核等 6 项未关闭。按用户要求直接在本地 main 开发，不建立新工作树。完整任务清单位于 `tasks.md`。

## 最终复核继续执行 ///（2026-10-05）

/// 最终产品复核修订/范围及其他面已通过，仅偏好候选表单遗漏 dirty 上报 → 浏览器复现字段丢失 → 复用现有聚合/离开保护，覆盖 exact 来源选择、busy/409 与成功解除 → 浏览器定向/构建 → 同一 reviewer 窄复审。

/// MCP 最终独立复核 APPROVE；后端复核追加发现 link→unlink 中断会留下双硬链接/pending 文件 → 真实临时文件注入复现 → 锁保护下精确字节/归属验证后恢复临时副本 → 保持累计 manifest 和未记录输入拒绝 → 定向复审。前端离开保护独立验收继续，不提前勾完整收尾。

/// 恢复复审追加零字节/半写与合法 500-output 容量边界 → RED → pending 绑定 exact target/content hash，仅可恢复预期前缀/零字节的单链接私有副本 → 扫描预算复用现有 500 输出/100 输入上限 → GREEN/全量 → 定向复审。前端 worker 已完成并交回 ownership，父层 readonly 浏览器复验通过，独立产品 review 尚待结论。

/// 三类最终复核返回六处窄缺口：编码令牌/MOV、unknown 稳定范围、输入暴露前持久记录、派生素材祖先 live rights、方法编辑离开保护 → 合成/隔离数据先复现 → 最小实现修正 → 定向与全量门禁 → 再次独立复核。当前仍 141/147，旧导航不提前退出。

/// 三类 reviewer 分别只读核验后端/数据安全、前端/操作 parity、MCP 限权；父层同时复跑隔离全量后端、前端/预算和规格门禁 → 处理具体发现并复审 → 仅复核全部通过后移除侧栏旧导航，保留 Settings 兼容目录和全部旧 URL → 最终准确更新任务与验收。

新鲜既有后端 1660 passed / 28 skipped / 8 warnings，前端/FE-P1、strict 35/35、Ruff、tracked 与 40 个 owned untracked 文件空白检查通过。正式库仍 f7d000000001，F8 13 文件哈希不变。三项最终复核尚未返回有效结论，仍为 141/147；不提前退出旧导航，不做正式迁移或文档生命周期操作。

## 第七批步骤 ///（部分验收，最终复核待完成）

计划：`docs/superpowers/plans/2026-10-05-align-creative-orchestration-final-parity.md`。

/// Assets/Settings 逐操作核验 → 日常新项目到成品包与旧历史读取 → parity 通过后退出旧日常菜单、保留明确高级兼容入口 → 独立 SPEC/后端/数据安全/MCP/前端复核 → 新鲜最终门禁与准确交付记录。

开始 131/147；不提前勾选，不动 F8/正式库/凭据/Worker，不做 canonical/archive/commit/push。两类操作 worker 写集隔离；父层持有导航和汇总文档。

六路 agent 因额度限制未进入实施/完成复核，父层接手可执行部分。真实日常新项目到 ZIP、旧历史零写/全表不变、逐条证据授权/撤权取消/周期明确保存/模板草稿归档/兼容目录通过。新鲜完整后端、前端/性能、strict/Ruff/diff 与 F8 ownership 通过。本批关闭 10 项至 141/147；旧导航和三类最终独立 review 仍待完成。验收见 `docs/ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md`。

## 第五批步骤 ///（已验收）

计划：`docs/superpowers/plans/2026-10-05-align-creative-orchestration-director-variants.md`。

/// 导演日常入口 / 五种 Variant 正文编辑 → 明确绑定 accepted 素材并保存 → 受限暂存清理 → Home / frozen Review provenance → 隔离完整视频链路、历史比较与独立复核。

只按实际验收勾选本批任务；正式库、根 F8、旧导航、canonical lifecycle 不动。

新增 13 项；五种 Variant 实际修订/刷新/POST 409、Director→人工接受→Master→v4→Review→ZIP、历史/hash、受限 cleanup、Home/frozen provenance 均通过。独立复核两项发现先复现后修正，最终 1660 passed / 28 skipped、TypeScript/Vite/FE-P1、strict/Ruff/diff 通过，见第五批验收记录。下一批不需要重新讨论既有产品方向，但不能把本批控制夹具当真实专业工具验收。

## 第六批步骤 ///（已验收）

计划：`docs/superpowers/plans/2026-10-05-align-creative-orchestration-recovery-preferences.md`。

/// executor 声明/恢复与偏好候选分开实施 → 真实本地 Codex MCP 客户端（不发模型 turn） → SQLite/素材隔离配套恢复 → 安全/只读零 dispatch → 独立复核与整批门禁。

开始 122/147；本批目标 8.11/9.1/9.7/9.8/11.5/14.2–14.4/14.10。正式 migration、旧导航退出和整 change 终验未提前完成；不新增永久测试或改 F8 owned 文件。

9 项已据实测勾选，累计 131/147。实际 Codex client/资源读取、controlled 文件两条恢复链/新进程 hash、编辑偏好来源/409/独立晋升、全部 90 表/accepted 媒体与历史 ZIP 恢复通过。安全两项发现先 RED 后窄修，独立复审 APPROVE；修正后完整后端/前端/FE-P1/strict/Ruff/diff/F8 通过。仅停止隔离 15431/15432，正式 head 仍 f7d000000001。

## 第一批步骤 ///（已验收）

1. 固定 `main@341ead8`、正式 SQLite head、F8 ownership 和 F6E lifecycle 基线。
2. 盘点旧路由及操作，记录三个直接创作起点，不隐藏旧入口。
3. 复用既有 API 承接 Home/Production/Project/Assets/Settings 日常入口。
4. 在临时库中完成浏览器/API 回读；生成只能使用受控夹具，不调用真实供应商。
5. 并行做操作清单与前端只读复核，修正实际问题，刷新构建和规格门禁。
6. 报告本批结果、限制和下一批持久化范围；不归档未完成 change。

## 第二批步骤 ///（已验收）

1. 新增 additive schema/迁移，在当前库副本 up/down/up 并比较历史原始列哈希；正式库不升级。
2. 接入 bounded Creative Intent，复用 Master/Variant CAS、幂等、history/diff。
3. 建立不可变 current-source Package/Director Package，冻结精确素材、证据和多输出数量合同。
4. 完成执行状态、私有工作目录、精确输入与不可变 output attempts；unknown 只能显式核对。
5. 完成人工接受到 MaterialRevision/可选项目引用，保护派生权利、许可归因和正文独立保存。
6. 隔离 API、并发、新进程回读、迁移及现有 full suite；先独立 SPEC 复核，再代码/数据安全复核。
7. 记录准确完成项与尚未实施的 UI/MCP/cleanup/Capability 服务，不用 API gate 替代页面验收。

## 不变量

## 第四批步骤 ///（已验收）

计划：`docs/superpowers/plans/2026-10-04-align-creative-orchestration-capability-memory.md`。

/// 方法库生命周期与 CAS → 按范围发现/显式 use → 整单 accepted 捕获与 Learning 独立桥接 → lazy 页面与 MCP → 隔离验收/独立复核。

阶段 10/11 的核心契约及 8.5/14.1 已据实测完成，新增 24 项；累计 109/147。11.5 没有真实重复编辑证据，保持未完成。独立复核发现的校验/结果回填问题已先 RED 再修复，最终复审通过；证据见第四批验收记录。

## 持续边界

F8 已有文件不变；新入口不新增数据真源；旧历史/归档/unknown 不被改成成功；不升级正式 SQLite、不写正式素材库、不生成/发布真实外部结果、不 commit/push/deploy。

## 最终步骤 ///（2026-10-05）

/// 记录三路最终独立 APPROVE → 仅移除日常 LEGACY_NAV（保留全部兼容路由及 Settings 目录）→ 实际浏览器复验九个日常入口/十五个兼容入口/旧历史零写 → 重跑构建、性能、strict、lint、空白和 F8/正式库只读核验 → 关闭持续边界并记录 147/147 / ARCHIVE_READY。

14.8 已经独立窄复审通过，PreferenceCaptureForm dirty 聚合无剩余发现；执行者浏览器与 reviewer 内存断言分开记录。以上步骤不包含 canonical sync/archive、提交或正式环境启用。
## 第三批步骤 ///（已实施）

计划：`docs/superpowers/plans/2026-10-04-align-creative-orchestration-ui-mcp.md`。

/// 意图表单与原保存门禁 → 冻结执行包/人工成果接受 → 同进程 loopback MCP → 内容优先与共用审计 → 隔离页面/Agent/完整门禁。

由 64/147 推进到 85/147，新增 21 项。实际页面/API/Test Agent 证据见 `docs/ALIGN_CREATIVE_UI_MCP_ACCEPTANCE.md`；不改正式库和 F8 owned 文件，不新建持久化真源，不把 Capability/真实专业工具或正式启用算成本批完成。
