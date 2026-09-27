# 当前进度

## 2026-09-27：FE-F2-R1 复核通过，归档与本地提交

- 外部复核已明确给出 `REVIEW_PASSED`，范围仅限 R1 五项收尾问题，不把结论外推为完整 PRD/V1 或生产验收。
- 已勾选 OpenSpec 6.3；按用户授权归档 `fe-f2-persistent-production-workflow` 并提交当前 `codex/fe-f2-persistent-production-workflow` 分支。最终命令输出及 commit hash 以本轮实际执行结果为准；不推送、不合并、不部署、不运行生产迁移。
- 归档命令完成：`openspec/changes/archive/2026-09-27-fe-f2-persistent-production-workflow/`；主规格更新 `fe-f0-f1-project-experience` 一项、新建 `fe-f2-persistent-production-workflow` 八项。归档后重新验证：后端全量 279 passed、前端 build 通过、12 份主规格 strict 校验通过、`git diff --check` 通过。归档工具给 FE-F0-F1 主规格增加的末尾空行已修正；待暂存快照核对及本地提交。

## 2026-09-27：FE-F2-R1 review 收尾

- 用户确认：仅保存项目覆盖但尚无 Run、快照、产物的单元，身份/形态/工作流可原地修改；一旦有执行历史，替换为新单元并归档旧单元。
- 已补 OpenSpec 场景并落地：unit-scoped effective-workflow 保持 Designer 与 pinned version 一致；矩阵恢复身份/形态/工作流重绑编辑，历史单元归档且可回读；模板可移植性仅在运行时解析的 config 中参数化；Step 保存 Kind；失败 rerun 不携带旧输出。
- 定向测试先红后绿；全量后端 279 passed，前端 `npm run build` 通过。首次全量出现 1 个新增测试夹具不符合模板 config allow-list，修正夹具后复测通过。OpenSpec strict 与 `git diff --check` 通过；主 JS 包体积警告仍在。归档、提交、推送和生产迁移均未执行，等待 R1 小补丁外部复核。

## 2026-09-27：FE-F2 apply

- 当前分支 `codex/fe-f2-persistent-production-workflow` 从干净的 `main@c044085` 创建；先前脏工作树已由其他提交收敛，本轮不搬运旧改动。
- OpenSpec `fe-f2-persistent-production-workflow` 是 spec-driven，0/21 任务完成；已建立实施计划，先处理持久化与旧 API 权限。
- 基线：`test_workflows.py` 10 passed，前端 `npm run build` 通过（主包体积警告）；Alembic head 为 `d4audit00004`。没有执行生产迁移或发布。
- OpenSpec 1.1：新增项目/单元/内容 Persona、两类工作流绑定、DataSnapshot、项目产物关联与可空 `WorkflowRun.content_unit_id`；定向模型测试先红后绿。隔离临时 SQLite 上从旧版本升级到 `e5fef2000001`、回退到 `d4audit00004`、再升级均成功。未修改已有正式数据库。
- OpenSpec 1.2/1.3：项目、角色、单元 CRUD 与创建者隔离已接 API；旧 Workflow 的 run/attempt/重跑/人工完成/取消/列表和 definition 列表、clone/publish/raw create-run 均接统一项目权限。项目工作流版本增加持久 owner/scope，阻断绑定变更后的遗留旁路。`test_fe_f2_projects.py` 与 `test_workflows.py` 共 14 passed；隔离 SQLite 全量迁移至新 head 成功。下一步补工作流校验和双保存。
- OpenSpec 2.2：项目覆盖另存生成不可变 Workflow 新版本，绑定修订号比较并在失配时返回 409；旧 Run 保留版本/checksum。角色默认另存入口已有初版，但可移植性 allow-list 仍须收严，2.3/2.4 暂不勾选。
- OpenSpec 3.1–3.3：Data Source 六类描述符及断连状态已接服务端；Studio Source 只读快照限制 20k 字、保留 source/version/lineage/checksum。项目 Run 经原引擎记录 Attempt；相同快照不使下游 stale，变化只标记依赖后代；断连插件在启动前被拒绝。快照可按所属单元读取。当前项目/工作流/Data 定向回归与旧工作流回归共 21 passed。
- OpenSpec 2.1/2.3–2.5、4.1：六类节点校验、条件/失败策略及映射参与真实执行；角色默认对同项目/单元 ID 使用上下文占位，对数据 source_ref 用运行参数占位，其他绑定值拒绝。已有 Draft、批准 Candidate 和真实 MaterialRevision 才能被关联项目。定向测试包含生成图实际字节落 MaterialRevision→共享池、历史 checksum、旧 API 旁路和副作用重跑。
- 前端当前接入真实项目 CRUD、角色默认版本选择、单条画布、Inspector、双保存和实际 Run；Mock 单独保留在 `/projects/demo`。隔离 SQLite `e5fef2000001` + 本地 18080/15173 联动浏览器实测：创建项目/身份/单元 → 保存 System 工作流 → Run succeeded/Attempt 输出 → 刷新后仍可读取。没有触碰原 8000 端口上的进程或已有数据库。
- 2026-09-27 续作：隔离 API 旧进程导致 `/outputs` 404，重启后为 200；文字/图文/视频三形态工作台均在浏览器读到持久单元。AI Provider/Model 只允许绑定后端当前执行路由，保存和启动均验证，不暴露密钥；UI 已选中 mock/mocked model 并显示在 Inspector。素材关联增加真实文件与哈希复核，缺失字节不入池。定向后端 30 passed、前端构建通过（包体积警告仍在）。
- FE-F2 最终本地验收：角色默认 v1 另存后，后续单元固定新版本，原单元仍固定项目覆盖；带 snapshot_id 的默认模板保存 422 且绑定不变；Notion 断连启动 409，隔离库对应 Run/Snapshot 均为 0；非所有者走遗留裸 run API 为 404。浏览器验证文字/图文/视频壳层及项目共享素材抽屉。后端 274 passed（需清除本机异常 NO_PROXY/no_proxy）、前端 build 通过、OpenSpec strict 与 diff-check 通过；待规格同步/归档。
- 最终双保存按钮复核：已保存项目覆盖且页面无未保存修改时，“另存为角色默认”现在仍可点击；服务端可移植性 Gate 继续决定能否成功，项目绑定不会被此操作改写。待最新前端构建复核。
- 隔离库保存项目 v2 后发现 Run #1 的冻结定义与当前草稿不同；已修正画布为运行模式显示 Run #1 原节点/成功状态，设计模式显示项目 v2 新节点且不混用旧状态。最新前端 build 通过。
- 全量后端测试 253 passed / 12 failed；12 项均是旧 DSH 代理端口 `:1` 导致的 `httpx.InvalidURL`，与本轮定向链路一致未扩大。前端 `npm run build` 和 OpenSpec strict 通过，主 JS bundle >500 kB 警告仍在。FE-F2 尚有专属三形态界面、Provider/Model/Tool 选择语义及最终本地验收，不可归档。

## 2026-09-27：FE-F2 正式 review 补强（未 apply）

- 已核对旧 Workflow API：除裸 run 详情、attempt、retry、节点重跑和人工完成，运行列表、取消、定义列表/clone/publish 及 raw create-run 也需要纳入同一项目权限边界。
- 已在 FE-F2 proposal/design/spec/tasks 补入统一授权、角色默认模板服务端可移植性 Gate、视觉顺序与依赖图分离、以及现有测试基础上的定向回归覆盖。
- 用户明确要求 FE-F2 新增回归测试，因此旧任务中“不新增测试代码”的限制已在该变更任务条款中替换；本轮只订正规范，尚未新增或运行测试、业务代码和迁移。
- 新版 `openspec validate fe-f2-persistent-production-workflow --strict` 和 `git diff --check` 均通过；未将规范校验误当成功能验收。

## 2026-09-27：FE-F2 V5 规格校准（未 apply）

- 用户确认 FE-F2 须真实持久化“角色 × 内容形态”默认工作流新版本，并供后续 Content Unit 选择；项目覆盖与角色默认保存须分离。
- 已订正 FE-F2 proposal/design/specs/tasks：六类节点、拖拽排序、可扩展 Data Source Plugin 六类来源及断连不可执行、快照 stale、项目共享素材产物关联。
- `openspec validate fe-f2-persistent-production-workflow --strict` 与 `git diff --check` 均通过；本轮未运行应用构建，因没有改业务代码。
- 仅修改规范和记录；没有业务代码、迁移、真实 Connector 或远端动作。校准后的完整提案仍待用户确认后才可 apply。

## 2026-09-27：FE-F0-F1 复核补丁

- 主规格缺口已补：异常项目的总览与内容矩阵显示五种状态说明；生产页原有说明仍保留。
- 本轮 `npm run build` 成功；浏览器已看到异常项目矩阵和总览的状态说明。正在隔离 FE-F0-F1 暂存范围，历史 API/迁移和 FE-F2 提案不纳入本次提交。

## 2026-09-27：FE-F2 提案（未实施）

- 用户明确工作流调试器须后端持久化并真实执行，不能只做前端 mock。
- 已核对现有 Workflow/Run/Step/Attempt 与重跑接口；它们仍以 Topic/渠道组织，FE-F0-F1 项目数据仍在浏览器 `localStorage`。
- 已建立 `fe-f2-persistent-production-workflow` 的 proposal/design/specs/tasks，`openspec validate --strict` 通过；等待用户确认，未运行 apply、未改业务代码或数据库。
- 建议以新增项目/内容单元持久化和项目级不可变工作流版本复用现有引擎；此处原“首个 Data Source Plugin”表述已被上面的 V5 校准覆盖：契约可扩展，首个可执行适配器才是 Studio Source。

## 2026-09-27：FE-F0-F1

- 已确认当前工作区为 AIContentStudio；North Star V2、V5 原型、前端契约和 HANDOFF 均已核对本切片范围。
- OpenSpec `implement-fe-f0-f1-product-shell` 的提案、设计、规格和任务齐全，严格校验通过并已实施、归档。
- 当前工作树已有大量用户改动，本切片只改前端相关文件和本任务文档。
- 已建立类型化本地模拟项目、内容单元和素材版本数据；含健康、异常两类项目，扩展状态徽标且沿用已有弹窗/抽屉。
- 已实现九入口主导航、项目列表、七个 URL 标签、内容单元增删改、本地持久化、共享素材抽屉和生产入口；`npm run build` 已通过，Vite 提示现有主包较大。
- 浏览器实测：项目列表、七标签、内容单元新增/编辑/删除、生产入口、共享素材来源筛选和异常样本的受阻/已过期/待核对区分可见；删除改为站内确认弹窗，验收样本已清理。
- 最新核验：`apps/web` 的 `npm run build` 成功；`openspec validate implement-fe-f0-f1-product-shell --strict` 和 `git diff --check` 成功。前端无单独 lint/test 脚本，本轮未新增测试代码。
- 交付边界：项目数据只在浏览器本地演示，未接后端、未增加迁移、未实现 FE-F2 工作流调试器；旧审核/素材页改用 `/legacy/review`、`/legacy/assets` 别名访问。
- OpenSpec 已归档到 `openspec/changes/archive/2026-09-27-implement-fe-f0-f1-product-shell/`，新增主规格 `openspec/specs/fe-f0-f1-project-experience/spec.md`。

## 2026-09-24：PRD 三渠道补齐提案

- 用户明确 `03_ai_content_studio_PRD.md` 是产品长期目标，并纠正三渠道误读：完整 V1 还包括百家号等 11 个文章/图文/社交平台，另保留抖音脚本。
- 已核对抖音和小红书具备旧生成/导出入口，但缺 M1 受控成品交付；其余长文/问答/社交平台缺原生适配。已把完整范围补入 PRD §3.1，正在修订 OpenSpec `complete-prd-v1-channel-deliverables`；当前仅规划文档，未改业务代码。
- OpenSpec 严格校验通过，4/4 产物齐全；`git diff --check` 通过。下一步是用户确认具体提案，然后按 OpenSpec 流程实施与归档。

- 已配置固定域名连接：`kayoyo.top`
- 已创建连接器：`Codex with ChatGPT · AIContentStudio`
- 已完成 ChatGPT 授权与安全配对
- 已为新 ChatGPT 账号 `Austin` 重新完成同一连接器授权
- 已绑定项目「AIContentStudio」，记忆为「仅限项目记忆」
- 已完成工作区读取验证，返回当前工作区 `AIContentStudio`

## 2026-09-22：V1 蓝图对齐

- 已找到指定原对话及用户最新需求；当前阶段仅做规划。
- 本地连接检查通过，复用原连接与浏览器，不重新配置。
- 正在核对代码并准备三轮讨论；尚未修改业务代码或运行对外发布。
- 源码核对完成，证据已记录到 findings.md；生成/审核/素材/工作流的可复用点及缺口已区分。
- 已形成 `docs/AI_CONTENT_STUDIO_V1_ALIGNMENT_PLAN.md` 讨论草案，等待 ChatGPT 回复及用户分发验收选择；正在做独立文档复核。
- 已补读原对话 R2 完整附件，并将需求编号映射到实施阶段；本轮尚未执行业务能力验收。
- 独立复核指出候选采纳及 Topic 创建顺序遗漏，已修正文档；ChatGPT 第一轮仍在生成，未重复发送。
- README 已增加下一版规划入口、当前未实现项及静态核对边界，原有用户改动保留。
- 文档二次复核要求将单目标交付可靠性前置；已补为自动建稿启用门槛，阶段 C 只做多目标扩展，待最终复核。
- 独立文档最终复核通过；两项问题已闭合。ChatGPT 三轮讨论尚未完成，不能据此宣称共同结论。
- 后续刷新发现首条 INIT 未保存；此前“正在生成”仅为页面提示，不构成有效讨论证据。恢复聊天模式后重新请求工作区/README 读取，页面再次报错，单次重试仍失败。当前连接检查全部通过，未重建连接器，正在核对原会话是否可继续。
- 经已保存会话及项目列表恢复原对话后，仍未取得新答复。已保留原对话和协作检查点，草案明确标为未完成 ChatGPT 讨论；本轮仅修改规划文档及 README，未运行生成/发布、未新增测试、未执行 OpenSpec 实施或提交推送。
- 用户确认可以回复后继续：原对话可见用户新消息“1”；已点击发送简短的当前工作区/README 核验请求，页面显示思考中。尚未取得实际文件读取结果，不将用户可发送消息等同于连接器核验成功。
- 本次核验成功：ChatGPT 返回工作区 AIContentStudio，并引用 README 第 3 行当前三渠道链及第 9–13 行新增 V1 草案说明；原会话恢复文件读取。已将本任务协作地址绑定到指定蓝图对话，开始三轮规划讨论。
- 第一轮规划请求已发送并可见；ChatGPT 已确认只规划，页面出现事实冻结、素材、选题及审批源码核对进展，尚未形成最终方案。
- 第一轮完整 PLAN 已收到并读完，新增源码观察已定点复核；第二轮设计挑战已发送。拟前置双渠道受控复用与最小反馈，尚待第二轮收敛及最终文档审阅。
- 对齐草案已补录第一轮结论与第二轮讨论问题，阶段正文待第二轮完整答复后统一修订；依旧未获得实施授权。
- 第二轮完整 PLAN 已收到并读完；已将首批 M1 与后续 A/B/C/D 分开，补类型化证据、语义检查覆盖、稿件期素材、双层审批、公开包隔离和旧调用入口防绕过。远端建稿独立准入，本轮不启用或停用任何业务功能。准备第三轮及新版独立复核。
- 新版独立复核指出 X Articles 范围及逐形态验收不够明确，已修正为按“平台 × 内容形态”验收，M1 仍仅做 X 线程，不以线程成功替代 X 全覆盖。ChatGPT 第三轮审阅进行中。
- 第三轮完成：ChatGPT 完整读取修订方案和 findings.md，判定规划 DONE，无严重修正；仅提醒历史类型迁移、M1 边界及重复/中断/未知结果验收。已补录这些提醒，明确本地防重不承诺人工或平台端绝对仅执行一次。
- 新版独立复审 Approved；三轮规划已形成建议共识，首批渠道与自动化下限仍待用户确认。没有创建 OpenSpec 提案，没有修改业务代码、生成测试代码、调用模型生成/发布、提交或推送。
- 收尾核对：已跟踪变更的差异检查通过；新增规划文件逐项检查未报告空白格式问题（与空文件比较的退出码 1 表示新增差异）。用户原有 PRD、澄清稿和 docs/superpowers/ 保留，未暂存或提交。本轮验证仅限文档和连接读取，不构成功能验收。
- ChatGPT 最终复核已确认规划层面 DONE：M1 采用类型化证据冻结、母稿版本、公众号 + X 线程成品包、人工交付回执与反馈；不把公众号自动草稿作为首批硬门槛。
- 已创建 OpenSpec 变更 `add-evidence-bound-article-handoff`，完成 proposal/design/specs/tasks 四类产物；严格校验通过，apply 前任务为 0/24。
- 当前执行边界：只实现本地成品包与人工回填，不调用远端发布 API；尚未修改业务代码、运行功能验收或归档 OpenSpec。
- 已开始执行 OpenSpec：完成数据模型扩展、X Thread 最小形态、增量迁移、类型化证据快照写入、母稿导入/适配、候选哈希、人工目标/本地包/回执/反馈接口，以及 M1 旧公众号远程副作用的部分工作流闸门。
- 本地迁移已执行到 `d31415926535`；API 模块语法检查、OpenAPI 路由读取、`git diff --check` 通过。新增人工交付包明确不调用平台 API，也不上传对象存储。
- 现有测试：项目虚拟环境中 129 通过、12 失败；失败集中在既有 DSH 配置值 `:1` 被 httpx 当成非法端口，未经过本次新增链路。系统 Python 的 `make test` 另因缺少 `pypdf` 在收集阶段失败。
- M1 本地实现与验收完成：类型化快照、母稿/适配稿、DraftMedia、完整候选批准、人工目标、ZIP 成品包、回填、反馈和旧工作流远端调用闸门均已落地。公众号实际封面字节被写入 ZIP 并按批准哈希校验；X Thread 路径已单独验证。
- 独立复核提出的四项问题已修复：ZIP 包含实际媒体、终态不因重新取包回退、目标与回执在并发重复请求下回读、目标只能由授权操作人处理；迁移先回填可关联历史 hash，无法关联的历史行保持 legacy/ineligible。
- 公开使用权限可以只撤销不能恢复；素材或冻结证据撤销会使未完成目标进入 `blocked`，已人工确认历史不被改写。
- 验证通过：空 SQLite 迁移到 `g31415926535`、`test_core_pipeline.py` + `test_workflows.py`（23 passed）、前端生产构建、严格 OpenSpec 校验、空白差异检查，以及临时本地数据的公众号实际媒体 ZIP / 账号隔离 / 终态保护 / 权限撤销链路。
- 全量测试仍为 129 passed / 12 failed；12 项均为既有 DSH 状态探测把环境代理地址 `:1` 传给 httpx 的非法端口，未扩大本次范围修复。
- ChatGPT 最终代码复核请求已发送到原对话；浏览器调试连接当前无法附着，因此暂未能读取其回复。OpenSpec archive 因此保持未归档。
- 已补完陈旧候选拒绝与人工结果未知（`reconciliation_needed`）的独立本地验收；同一未知回填重复提交不会新增第二条回执。
- ChatGPT 最终代码复核指出旧工作流默认仍生成公众号草稿节点；已将模板默认改为本地导出，并为遗留远端草稿增加显式开关与服务端闸门，M1 母稿仍不可进入该路径。
- ChatGPT 对上述修复返回 DONE；已完成 `add-evidence-bound-article-handoff` 的 OpenSpec 归档，归档目录为 `openspec/changes/archive/2026-09-22-add-evidence-bound-article-handoff/`。
# 2026-09-27：连接器故障检查

- C2C 更新检查无新版本；授权白名单已配置。
- 固定域名配置正常；`C2C_TUNNEL_PROTOCOL=http2` 已在当前环境及 `~/.zprofile` 配置。
- 用户确认四种独立读取均返回 `internal error`。进一步外部复核发现公开连接返回 530，且该工作区的健康连接数为 0；协议配置正确。
- 已执行 `c2c restart --tunnel`。复核通过：HTTP/2 正确、健康连接数大于 0、公开 MCP 未授权请求返回预期 401。
- 待用户在 ChatGPT 中重试 `workspace_info`，确认连接器端到端恢复。
- 2026-09-27 再次复查：本地诊断无修复项，外部探测仍返回 401，HTTP/2 与健康连接数正常；未重复重启。状态输出含一条 Cloudflare edge 地址警告，但当前传输探测通过。
