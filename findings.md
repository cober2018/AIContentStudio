# 配置记录

## 2026-09-27：FE-F2 正式 review 的代码核对

- `apps/api/app/routers/workflows.py` 的旧 run detail、complete、retry、rerun、rerun-from-here、attempts 与 cancel 仍按裸 `run_id` 读取；`list_runs` 列出运行记录，`list_workflows` 的序列化还嵌入最近运行。只保护新 project-scoped URL 会留下读写旁路。
- 同文件的 clone/publish 使用裸 Workflow ID，raw create-run 也按 workflow ID 启动；若 FE-F2 把项目版本写入现有 Workflow 表，这些定义入口亦须授权或明确拒绝。统一检查必须以持久化项目/单元归属为准，不能相信请求携带的项目 ID。
- `workflow_engine.advance` 根据 `definition_json.edges` 判断依赖，`ready[0]` 从待执行节点取下一项；因此视觉顺序可以作为独立节点的稳定排序，但拖拽不能隐式改写 edges 或映射。
- Persona 默认模板从项目流程派生时必须服务端只保留通用结构与可共享 profile；项目、运行、快照、素材、稿件、候选、attempt 和实际输出要参数化或拒绝，不能直接复制 definition/context。
- FE-F2 回归测试现经用户明确要求；测试旧 API 权限、模板隔离、冲突、快照 stale、断连插件、副作用重跑、素材归属和历史 checksum 是该变更本身的验收，不是额外功能。

## 2026-09-27：FE-F2 V5 校准依据

- `AIContentStudio_Frontend_Product_Contract_V1_2026-09-27.md` §10–11 明确六类节点、拖拽与键盘替代、项目覆盖和显式另存角色默认版本，以及可扩展 Data Source Plugin 的六类起始来源。
- 旧 FE-F2 proposal/design 把角色默认版本推至 F3，并将首个 Data Source Plugin 描述得过于接近 Studio Source 专用适配；用户已明确要求前者在 FE-F2 真实持久化。
- 当前 `Workflow` 已有 key/version/checksum，`WorkflowRun` 可冻结版本，`WorkflowStepAttempt` 记录审计；可扩展绑定和输出关联而不新造引擎。当前模型未见持久化的内容 Persona/Role，FE-F2 需最小身份归属；鉴权角色 editor/reviewer 不能代替内容角色。
- 插件“已注册”不等于“已连接/可执行”。Notion、Obsidian、媒体数据、API、SQL 可以先有描述符和配置体验，但执行结果必须由服务端真实连接能力决定；缺连接时不得生成成功 Attempt、Snapshot 或素材。
- 用户只确认了角色默认版本这一边界；完整校准后的 FE-F2 OpenSpec 尚未被批准 apply。

## 2026-09-27：FE-F0-F1 复核补丁范围

- 反馈属实：`STATUS_EXPLANATION` 原先只在 ProductionShellPage 读出；项目默认总览和矩阵缺解释。
- 已在异常项目的总览/矩阵复用说明；非异常项目不增加图例。前端构建和浏览器观察通过，未新增测试代码。
- 本地 `main` 仍包含更早未提交的 API、迁移、Materials/ReviewPublish 路由等改动；提交必须精确暂存本切片，不能 `git add -A`。

## 2026-09-27：FE-F2 真实工作流提案核对

- `apps/api/app/models.py` 已有 Workflow、WorkflowRun、WorkflowStep、WorkflowStepAttempt；现有运行通过 `topic_id`/channel/content_form 追踪，尚无持久化 ContentProject/ContentUnit 归属。
- `apps/api/app/routers/workflows.py` 已提供版本 clone/publish、启动、人工节点完成、节点重跑、从节点重跑和 attempt 查询，但没有项目覆盖保存/设计编辑接口。
- `workflow_engine.rerun_node` 对 side-effect plugin 禁止泛化重跑，`rerun_from_here` 也检查受影响节点；FE-F2 必须沿用闸门，不能为 UI 绕过。
- FE-F0-F1 的项目模型还在 `apps/web/src/product/mockProjects.ts` 的 `localStorage`；要实现跨会话持久化，需要显式后端项目/单元迁移与 UI 切换，不能把浏览器 mock 当真实记录。
- 原变更提案把角色默认模板发布留给 F3；这一历史观察已由上面的用户确认和 V5 校准取代。

## 2026-09-27：FE-F0-F1 前端基线

- 当前 `apps/web/src/App.tsx` 以旧 Source/Topic/Workflow 导航为主，已存在用户未提交的 Materials 与 ReviewPublish 路由；实施时保留它们。
- 前端为 React Router + TanStack Query + Tailwind；已有 Button、StatusBadge、Modal、Drawer、EmptyState、Spinner、ErrorBanner 可复用；`apps/web/package.json` 仅提供 build，无独立 lint/test 脚本。
- FE-F0-F1 只做本地 mock 的 ContentProject/Unit/AssetRevision 视图与交互；FE-F2 工作流设计器和后端结构均不在本切片。
- 浏览器已核对项目列表、七标签、矩阵增删改、共享素材抽屉/筛选和选中单元生产入口；异常样本同时显示受阻、已过期、待核对，状态不合并成“失败”。
- `/review` 与 `/assets` 用作新一级工作区占位页；旧页面仍在 `/legacy/review` 与 `/legacy/assets`，其他旧路由保持不变。前端 mock 由 `localStorage` 保存；已存在的浏览器数据优先于最新初始样本，因此素材数可能与新会话初始值不同。
- `npm run build` 成功，Vite 提示主 JS 包约 1.0 MB、超过 500 kB 建议值；这是性能待办，不影响本切片构建。仓库前端没有独立 lint/test 脚本，未声称完整自动化测试通过。

## 2026-09-24：PRD 作为产品长期目标

- 用户确认 `03_ai_content_studio_PRD.md` 是指导项目开发的最终产品需求基线，并纠正“三渠道就是全部”的误解。PRD 原文称三项为“首选渠道”；原对话的 V1 目标包含 11 个文章/图文/社交平台，另保留抖音脚本。已把此范围以 §3.1 补入 PRD，避免文件本身继续遗漏完整目标。
- 当前静态核对：`models.py:Channel`、生成 renderer、工作台已有抖音/小红书/公众号；旧导出支持抖音 MD/TXT/JSON/SRT、小红书 MD/TXT/JSON。`article_handoff.py` 的新候选/交付目标只接受公众号与 X Thread；小红书 renderer 当前输出图片 Prompt，未证明有序实际图片组成品。
- PRD §15 的 15 项验收与 §16 的 30 个真实 Topic 门槛尚未在本轮完成运行核对；M1 成果不能直接等同整个 V1 达标。

- 当前工作区：`AIContentStudio`
- 连接方式：固定域名
- 连接器名称：`Codex with ChatGPT · AIContentStudio`
- 当前本地连接检查：通过
- 新账号连接状态：已授权，账号显示为 `Austin`
- 新账号项目状态：已绑定正确的 `AIContentStudio` 项目合集
- 工作区读取验证：通过

## 2026-09-22：V1 范围基线

- 指定原对话：自媒体平台对比总结（6ab23aa1-ce20-83e9-9acb-c6ffeda87191）。
- 用户最新明确需求：内容中心服务量化平台、媒体采集分析工具及其建设过程；V1 文章/图文，V2 视频。内容中心不重做上游量化与采集。
- 对话整理的 V1 渠道清单：公众号、头条、百家号、知乎、小红书、X、微博、B站专栏/图文、搜狐号、企鹅号、网易号。具体账号可用性和自动分发权限仍须核验。
- 本地 `docs/AI_CONTENT_STUDIO_REQUIREMENTS_REFINED.md` 仍以抖音、小红书、公众号三渠道为主，与最新文章全渠道目标存在差异，不可直接作为本轮实施基线。
- 页面旧架构回答和最新需求整理同时存在；以用户最后说明与三产品矩阵定位优先，不把未来架构全部塞入 V1。

### 本地源码核对（静态证据，非本轮运行验收）

- `models.py:Channel`、`routers/topics.py:VALID_CHANNELS`、`generation/renderers.py:render_body`、`pages/Topics.tsx` 均为抖音/小红书/公众号三渠道。不能仅加菜单便算全渠道完成。
- `generation/orchestrator.py:run_generation_for_job` 直接从 Topic + FactPack 各自生成平台 Draft；尚无中立母稿和平台稿之间的版本依赖。已有 TopicBrief、ContentJob、Draft、Review、ContentAsset 可复用，不宜重建一套同义实体。
- `routers/generate.py:update_draft` 新建 revision，但保留旧 `structured_json`；正文编辑后的结构、图片文案和引用可能脱节，需要定义统一内容真源及重校验机制。
- `routers/fact_packs.py:freeze_fact_pack` 只固化状态/checksum，FactPackItem 仍引用可变 Fact；`routers/facts.py:update_fact` 未检查冻结包引用；生成时读取当前 Fact。冻结事实包不等于冻结事实值，必须补不可变证据快照或等价保护。
- `routers/reviews.py:approve` 检查事实校验、包状态、最新稿件版本，复制批准正文至 ContentAsset；这是可复用的文字审批基线，尚非完整的账号/素材/规则/声明发布快照。
- `services/asset_media.py` 是图片说明占位及上传入口；上传追加数据库行却可能按原 media.id 写同一路径，不能把记录追加直接当成素材字节不可变保证。小红书最终图片组未见完整生产和打包链路。
- `workflow_templates.py:build_gen_export` 当前公众号封面节点位于批准之后；`workflow_engine.py:_h_publish_wechat` 还会截断标题、选择动态封面/占位封面，再调用 wewrite 建草稿。批准内容与最终交付内容必须先统一。
- `workflow_engine.py:advance` 保存步骤状态且可人工暂停，但自动节点在调用内串行推进；任一失败/人工等待均会返回整次运行。`retry_run` 将失败节点直接重置，因此对外建稿结果未知时存在重做风险。代码尚非持久化可靠的独立发布任务系统。
- `tasks/worker_tasks.py` 已有 Celery 生成与拉取任务，保留该技术栈；`dispatch_generation` 在外层生成请求 commit 前 `.delay()`，任务投递与数据库持久化需要可靠衔接，不能只把函数改成异步。
- `routers/external.py` 外部内容目前是独立 ExternalContent 汇聚入口，可直接人工改 published；它没有自动进入事实/母稿/审核链，不能等同候选池及可信发布回执。
- `services/writing_pipeline.py` 已有风格、润色和安全扫描薄封装，但依赖本机其他目录；缺失可降为黄词扫描。`routers/reviews.py:approve` 未统一强制安全扫描，所以不能声明已有全入口安全阻断。
- `routers/dashboard.py` 聚合生成/审核/导出内部计数，未实现平台效果与产品反馈闭环。`deps.py:get_current_user` 是开发身份头，不能用于对外商业服务验收。

### 讨论状态

- 第一轮 INIT（任务 c2c_a173）曾显示思考中，但刷新后消息未保存；不能视为实际完成讨论。恢复聊天模式后再次请求当前工作区及 README 读取，出现生成错误，单次重试仍报错。经已保存会话 → 项目列表 → 原蓝图对话重新进入，仍只保留旧对话内容。
- 本轮最后一次本地连接检查全部通过，无需重新授权/重建的指示；原聊天的新文件读取未得到成功答复，未证明端到端可用。未删除连接器、另开对话或向其他工作区发送请求。协作检查点已标记阻塞，需原会话恢复回复后继续。
- 后续恢复：用户确认能回复后，本轮在同一原对话点击发送最小读取核验，约 1 分 25 秒后返回 AIContentStudio 及 README 第 3、9–13 行两项具体事实；端到端读取验证现已通过，未重建连接器。此前报错的根因未查明。
- 第一轮 ChatGPT 完整 PLAN 已收到：认可保留现有栈与 Topic 聚合，建议首批缩为“已有满意文章 → 公众号 + 一个新增渠道 → 可核实交付”，独立目标、人工凭证和最小反馈必须提前；内容审批与目标交付授权分开记录，界面可一次确认。建议 X 线程作为新渠道样本，但尚非用户选定。
- 第一轮新增源码观察已由本地定点复核：REST 接入指纹只哈希排序后的 statement，需防日期/单位/来源版本变化被误去重；默认抽取器只提取数字及日期类候选，纯观点/建设经验需显式类型化入口；AssetMedia 强制关联批准后才创建的 ContentAsset，最终成品审批需补稿件期素材关系。
- 第二轮已提出设计挑战：不扩建通用证据平台；在现有冻结边界补值快照；保留 Markdown 主数据并失效派生物；明确非数值文章的证据门槛，以及内容审核/账号授权的分工。首批可用人工交付证明价值，自动草稿需独立准入，旧路径不得绕过新门槛。
- 第二轮完成：M1 采用类型化 FactPackItem（事实/事件、引述、作者观点）及冻结值，不把非数值文章伪造为数值事实；审核严重程度和是否完整覆盖分开。已定点复核 factchecker.py：只取前 50 条事实/前 4000 字，模型不可用或失败透传确定性结果；不能据此声称全篇语义审查完成。
- 已定点复核 assets.py：素材删除可直接移除关联记录；导出仅按渠道格式检查。后续需保护批准清单引用、区分存档下载与正式交付包，且不得把内部证据默认放进公开包。所有建议仍为规划，未修改这些源文件。
- 已在原对话文档预览中补读完整附件 `AI_Content_Center_Requirements_R2.md`。与摘要相比，还需显式保留版本比较/锁定、定时栏目数据就绪、来源公开及模型使用权限、排期首发冲突、发布后勘误、收益资格/收入状态和四类样本验收。已加入对齐草案的 A01–A64 分组追溯表，不把附件建议自动视作用户逐项确认。
- 第三轮已完成，工具输出确认方案全文读取且未截断、findings.md 全文读取；ChatGPT 判定规划 DONE，无严重修正，OpenSpec 未创建且实施 HOLD。提醒历史证据显式 legacy_untyped、可空 fact_id 的相关读取路径兼容，以及 M1 重复/中断/未知结果验收；这些是实施约束，不是现有功能结论。
- 本轮新版独立复审通过：X 单帖/线程/长帖/Articles 均保留 V1 成品适配，逐“平台 × 形态”验收；M1 仅取公众号 + X 线程作为建议样本。自动化下限和首批渠道尚待用户确认，账号分发能力未验收。
- ChatGPT 最终复核结论：规划 DONE，无严重修正。必须保留三类门槛：证据一致性、交付安全、失败/重复安全；内容审批与目标账号/动作授权分离；Markdown 是母稿真源，结构化内容、引用、检查和包均为可失效派生物。
- 用户已确认按该思路继续落地：首批接受“完整成品包 + 人工发布回填”，公众号自动进入草稿箱不作为同时完成条件。
- OpenSpec 已落地为 `openspec/changes/add-evidence-bound-article-handoff/`，严格校验通过。实现前提是新 M1 目标不调用远端平台 API，旧入口不能绕过新快照、审批和目标授权边界；历史记录保持可读，不通过迁移伪造新批准。
- 执行中新增 API：`/api/v1/article-handoff/...`，覆盖母稿导入、公众号/X Thread 适配、目标授权、本地成品包、人工回执和反馈；人工确认状态不会写成 `published` 或平台已验证。
- 迁移实测：`alembic upgrade head` 已成功到 `d31415926535`。第一次迁移尝试暴露 SQLite 不支持直接 `ALTER COLUMN`，已改为兼容增量迁移并复跑通过；仍需在 PostgreSQL 路径复核约束差异。
- 测试实测：虚拟环境 129 passed / 12 failed；失败共同原因为既有插件状态地址 `:1` 触发 `httpx.InvalidURL`，不属于本次链路。该问题未修复，避免扩大范围。

## 2026-09-22：M1 实施复核与验收

- 成品包不能只返回受登录保护的下载路径；现已提供受目标授权保护的 ZIP，包含 Markdown、HTML 或 Thread JSON、manifest、说明和按批准哈希复核的媒体字节。
- 已人工确认、失败或待核对的目标重新读取成品包时不再回退到等待回填。相同授权目标和相同回执请求在并发冲突后回读既有记录。
- 授权操作人是 M1 账号边界：非授权 editor 不能取包、下载 ZIP 或写回执。该边界不等同于未来的组织/多账号权限模型，后者须单独设计。
- 冻结快照、母稿、候选 manifest 与资产记录保留历史；公开使用权限撤销另存控制记录，并阻止未完成目标，而非篡改已批准历史。
- Alembic 迁移优先回填可从关联资产/目标恢复的 hash；无从恢复的旧记录保留为不具 M1 资格的 legacy 行，避免迁移伪造审批或丢失数据。
- 旧工作流边界已收口：`gen_export` 默认不再生成 `publish_wechat`，仅显式遗留配置才保留；执行器还要求节点带遗留开关，并继续拒绝绑定 `MotherRevision` 的 M1 资产。
- ChatGPT 对最终修复返回 `DONE`；OpenSpec 变更已归档，未同步 delta spec，因为当前仓库没有对应的主 specs 目录。
# 2026-09-27：连接器故障检查

- 用户提供四项独立调用均为 `internal error`。再次核验发现公开 MCP 返回 530、该工作区 cloudflared 的 HA 连接数为 0，虽然 `doctor` 显示绿灯且协议为 HTTP/2。
- 对 AIContentStudio 定向执行 `c2c restart --tunnel` 后，工作区 cloudflared 使用 HTTP/2，HA 连接数大于 0，公开未授权 MCP 请求返回 401；这确认传输链路现已恢复。
- ChatGPT 连接器的端到端调用尚未由当前会话复验；需要在 ChatGPT 中重试 `workspace_info`。未重建或重新授权连接器。
- 2026-09-27 后续复查：bridge、MCP、OAuth、named tunnel 均为 green；公开 MCP 返回 401、对应 cloudflared 使用 HTTP/2 且 HA 连接数大于 0。状态详情出现“no free edge addresses”警告，但不足以推翻当前健康探测，故未重启。ChatGPT 端如仍失败，需按具体工具错误继续定位。
