# 执行进度

## R1 / R2 修正完成，待最终closeout复核（2026-10-05）

当前main@341ead8，原147项实施APPROVE；新增7项收尾中15.1–15.6完成，153/154。R1先补规格，默认head回归先复现f7d错误，再只改常量/注释到aco；F8/readiness/恢复/parity当前契约对齐，保留原f7d历史。R2新增四文件108永久用例，实际验证stale/Unknown/多输出替换/权利、MCP鉴权/白名单、Capability晋升/冲突/秘密/Skill分离及迁移/default/inert。

四组定向13＋66＋18＋11均PASS；Mendel独立R2 SPEC复核APPROVE并隔离复跑108 passed，随后Zeno Python代码质量复核APPROVE、亲跑Ruff。原R1旁路review容量失败没有结论，不记APPROVE；主执行者已完成R1定向规格核对。新鲜完整后端1768 passed/28 skipped/72 warnings、101.02秒；Web TypeScript/Vite/FE-P1通过，Projects224.09/72.70、Production278.68/89.07 kB；OpenSpec35/35、app＋新测试Ruff和空白检查通过。全部scripts尝试发现seed_dreamo_data_service.py三条原HEAD既有lint错误，原HEAD复核同样失败，未改无关脚本、不称全scriptsPASS。内部复核不冒充最终15.7。

末次正式只读核对head=aco、integrity=ok、7/0/0身份计数，API ready=true/Web200、原PID与127.0.0.1监听未变。没有写/回滚正式库、改身份/配置/凭据/Worker、重启、模型或公众号请求。F8仅授权8份schema/current-state窄修，其余5文件SHA256一致；root trackers不变。ARCHIVE_READINESS=PENDING_FINAL_CLOSEOUT_REVIEW；15.7确认前不sync/archive/commit。完整回执复用docs/ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md。

## 整体回执已整理（2026-10-05）

用户要求汇总本次整个OpenSpec执行。重新实读tasks为147/147、remaining0；12份delta；Git仍main@341ead8c30390bd48519d0a5af05ab2a20f6fa19且本change未提交。新鲜strict35/35、diff-check、F8十三文件hash通过；正式库headaco000000001/integrity ok，API ready=true/Web200及两端loopback监听均重新核对。完整后端1660/28skipped、构建/预算和三类独立APPROVE按既有实施记录引用，不冒称本轮重跑。整体回执加入既有 `docs/ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md`，与正式启用记录分层；没有新增业务代码或执行提交/归档/模型/发布。

## 本机正式启用完成（2026-10-05）

用户已明确授权备份、正式SQLite升级、服务重启和正式环境验收，解除3.12/14.12中对应运行启用门槛；147/147仍指实施验收。沿用原launchd API/Worker、SQLite、本地素材和loopback，不执行公开发布/付费生成/push/归档。新增仅本change内运行计划，不覆盖根F8记录。

停写后私有快照 `backups/creative-local-enable-a63DyjDV/`：SQLite在线备份integrity ok；7条媒体引用/5份字节逐条hash一致，同时保存32MB完整媒体目录及原私有配置。副本明确升级aco000000001、降回f7d再升级，83张历史表/5145行的全部旧列hash不变、97条既有FK异常集合不变。此迁移链经过已有f8a的两列nullable身份字段，不切换APP_ENV/登录/存储。

正式升级至aco000000001完成；升级后及原服务重启后都重新核对83张历史表/5145行旧列hash、97条原外键异常集合、integrity，全部一致。媒体7引用/5文件再验无缺失或hash变化。只在现有ignored/0600 runtime.env补明确schema head和随机MCP token/原用户1绑定，原配置/凭据保留；没有把真实token写入日志、文档或仓库。

原launchd API/Worker恢复，Web沿用npm dev且显式loopback，8000/5173均只监听127.0.0.1；readiness HTTP200、ready=true/reasons=[]。Worker真实ping成功、active/reserved/scheduled均0，原3条历史queued记录未重发。正式HTTP MCP完成初始化、15工具及owned context读取；真实已安装Codex app-server通过子进程临时配置再次握手/工具清单/正式项目资源读取成功，0模型turn/全局配置改动。

实际浏览器核对根→Home、九日常入口、15兼容目录、运行状态、方法库、Text Master与创意执行面板。GET API核对原Video Master5仍stale、Text Master9仍current；现有identity/rights/check风险仍阻断，不冒充稿件已可发布。没有创建示例或执行业务写链；此前完整隔离验收不被描述为本次正式库写验收。另存启用后enabled.db与配套素材、原私有配置快照，integrity ok；详细启动/停止/备份边界见 `docs/ALIGN_CREATIVE_LOCAL_ENABLEMENT.md`。

最后保全启用后runtime.env.enabled（0600），验证原配置前缀字节完全不变、只新增3个绑定；before/after数据库分别配对应运行配置。正式历史/完整性与API/Web200再次通过，strict35/35、diff-check、29个owned untracked文档空白/冲突检查、F8十三文件hash通过，浏览器console error0。首页new-home.jpg仅作本地启用凭证。无本轮业务代码改动，不重跑或冒称重跑此前全量后端/构建；保留正式API/Web/Worker运行，无commit/archive。

## 实施验收快照（正式启用前，2026-10-05）

**147/147，IMPLEMENTATION_ACCEPTED / ARCHIVE_READY；以下各轮进度保留为历史。** 最终后端/数据/安全14.7、前端/产品14.8、MCP14.9 均独立 APPROVE。偏好表单仅接入既有 dirty 聚合，父层 Chrome、mock 409/成功解除与 reviewer 13 项独立内存断言分别验证；不能互相冒充。

三类 review 全部通过后，13.7 仅移除 App 的 LEGACY_NAV 及 sidebar details。新的独立窄复核确认九个 NAV、全部 lazy 旧页面/实体 URL 与 Settings 十五个入口保留，TypeScript/diff PASS。父层 fresh Chrome 验证根地址→Home、九入口、十五兼容、零写/零错误；旧历史全表 dump hash 不变；方法编辑 route/native history/beforeunload guard 再验零 API 写入。

最终导航修正后 `npm run build`（TypeScript/Vite/FE-P1）exit0；Projects224.09/72.70、common Production278.68/89.07、Settings242.16/78.99、Assets261.21/83.89、Learning252.59/82.06 kB raw/gzip。Text Studio TipTap 闭包605.43/189.28，通用 Production/Graphic/Video 无 TipTap/XYFlow 首包污染。最后后端修正后完整既有 suite1660 passed/28 skipped/8 existing warnings（92.22秒）；随后只改前端导航和文档，没有再次修改后端。

strict35/35、Ruff、tracked diff-check、56 owned untracked 文件空白检查、F8十三文件 SHA256 通过。正式 SQLite 用 mode=ro 精确核对迁移六表及 head：仍 f7d000000001，新表不存在；最初宽泛 creative_% 查询误含既有 CreativeBrief，已改精确六表查询，不为诊断误匹配改代码。OpenSpec 可选 telemetry TLS 上报失败不改变 validate 的35/35、exit0。

0.6/3.12持续边界据完整实施及独立安全结论关闭：无破坏性迁移/第二内容真源/任意代码执行/权利门禁削弱，未升级正式库。canonical sync/archive、本地提交、push、正式启用、外部 dispatch 和兼容页面删除均未执行。正式 API/Web/Worker 保持不动；只关闭本轮临时进程并保留证据。

最后收尾再验：CLI apply实际返回total147/complete147/remaining0、all_done；文档更新后关闭可选遥测重跑strict35/35、exit0，无遥测警告。diff/56文件空白/F8哈希再次通过。按分支收尾skill保留main工作区、不提交/归档；仅在校验PID/命令/临时端口后停止48595/48708两个隔离进程，证据目录保留。全部审批和验收文档已同步当前状态，没有改根F8记录。

## 2026-10-05：偏好候选离开保护定向收口

最终前端 reviewer 已通过其余日常入口/53-row parity/内容优先/Video/legacy routes 等审查，只追加发现 PreferenceCaptureForm 未报 dirty。父层实际 Chrome RED 复现分区切换字段丢失后，复用既有 dirty 聚合补 project/unit/name/preference/exact selected edits，以及 busy/409/成功解除条件。真实只读 GREEN 保留字段/明确离开，内存 mock 两条来源选择、hide/show、409 后原选择/正文保留、显式 mock success 清除 guard 都通过，零真实 API 写入；新鲜 TypeScript/Vite/FE-P1 PASS。已送同一 reviewer 窄复审，14.8 仍不提前勾；最新 143/147。

## 2026-10-05：最终后端 / MCP 复核通过

后端 reviewer 对两轮恢复窄修完成实际独立验证，最终 **APPROVE**；空/partial exact-bound 恢复、500 staging/1101 扫描边界、未知输入/旧 partial/外链/权利/CAS 保持拒绝，限定 Ruff/diff 通过。原迁移/范围授权/Unknown/派生素材祖先权利/方法非执行边界已通过范围保持。14.7 关闭，连同 MCP14.9 已通过，当前 **143/147，剩余 4 项**。最终前端/产品14.8 待返回；13.7 及持续停止/正式库不迁移条件尚待完整关闭。不以执行者全量门禁冒充 reviewer 亲跑。

## 2026-10-05：最终复核追加恢复修正

最终 pending 身份/容量修正后 full backend 新鲜复跑 **1660 passed / 28 skipped / 8 existing warnings，92.22 秒，exit0**。定向完整/零字节/半字节恢复、500 staging 容量、错误内容/私有模式/外链/未知 partial 拒绝均 PASS；Ruff、diff-check、F8 13 文件哈希再验通过。最终独立后端与前端 review 待返回；未提前关闭剩余项。

前端两文件 worker 已交回 ownership，tsc 与 artifact/分区/路由/native history/beforeunload、真实 revision/scope 409 验证通过。父层独立运行 `/tmp/aics-memory-guard.9xFsGi/recheck-guard.cjs` exit0、零 API 写入；cancel 保留字段、confirm 明确丢弃后离开。该执行者复验不替代 14.8 独立 review。

后端第二轮窄复审已关闭 post-link 问题，追加发现未完成写入遗留零/半字节文件以及扫描 200 条误伤 500-output 合同。真实文件 RED 后，pending 改为 exact destination/content hash 稳定绑定，只清理归属/私有模式/单链接且为 expected prefix 的不完整副本；完整双链接仍须 exact target inode/bytes。扫描预算共享已存在的 500 输出/100 输入常量（不改变合同上限）。零/半字节、500 staging、错误字节/模式/外链、未绑定 partial 拒绝均 GREEN；已提交定向复审、全量重跑进行中。

恢复修正后的新鲜全量：**1660 passed / 28 skipped / 8 existing warnings，87.58 秒**，隔离 `/tmp/aics-align-recovery.EdJYSi`。第一次 env-i 命令遗漏仓库 PYTHONPATH，旧 F7 runner 的 23 项仅 import 失败；补回显式 root/API import path 后定向 23/23 及全量通过，没有为命令环境问题修改代码。TypeScript/Vite/FE-P1、strict 35/35、Ruff/diff/F8 哈希通过；`/projects`225.03/72.98、common Production279.62/89.35、Settings243.10/79.27、Assets262.15/84.16 kB。service 级 `/tmp/aics-link-service.0tppEc` 实测 same-execution 的 link/unlink 故障→新 Session/CAS→累计 manifest→重试→人工接受，以及祖先撤权/Unknown negative 均 PASS。

MCP 最终只读复核实际返回 APPROVE：441 项独立合成内存断言通过，覆盖编码 bearer/ID、工具委托、路径、MIME、认证和所属关系；不冒充真实 Provider/专业工具或完整 HTTP 重跑。关闭 14.9，当前 **142/147，剩余 5 项**。

后端复核原三项已通过，另复现 link→unlink 中断留下 pending 文件/双硬链接的恢复缺口。父层用真实临时文件先 RED，再增加目录 descriptor 锁和仅 exact bytes/uid/600/regular-file/inode 可证明的 pending 恢复；累计数据库 manifest 不变，外部硬链接、未记录输入、符号链接继续拒绝。中断后重试、12 次并发重试、matching orphan、负向安全和 cleanup 检查 GREEN，Ruff 通过；已提交独立定向复审，14.7 不提前关闭。方法编辑离开保护与前端最终独立复核继续。

## 2026-10-05：最终独立复核修正（进行中）

- 三类最终复核均提出具体缺口，不能标为通过。保持 141/147 与旧导航可见，正式库和 F8 文件不动。
- MCP 令牌编码和 MOV MIME 先 RED 复现，后窄修：扫描 bounded key/value 的 NFKC/percent 副本、不改原内容/hash；QuickTime brand 不再走 MP4。合成正负向检查通过。
- 后端三个 RED 闭合：unknown 按 owner/project/unit 阻止新尝试，不受新 package metadata/hash 绕过；materialization 先 CAS+审计 commit 累计边界再开放文件，失败/子集重试不能缩小边界，未记录输入阻断接受；外部素材复用递归重验 accepted lineage、精确输入 hash/live rights/bytes 与继承义务。
- `/tmp/aics-review-flow.Pc3g93` 真实隔离服务检查通过：post-exposure 故障、新 Session 回读、旧 CAS 409、子集保留、成果接受、祖先撤权拒绝、restricted 不升级、无 Material 部分写、未记录输入拒绝，以及新 package 无法绕过 unknown。
- 修正后新鲜全量既有后端：**1660 passed / 28 skipped / 8 existing warnings，87.84 秒**；新库 `/tmp/aics-align-review.4Gjmkq`。没有新增永久测试、迁移或业务对象。前端编辑保护及最终复审仍进行中。

## 2026-10-05：第六批，恢复 / 客户端 / 偏好 / 备份（已验收）

- 继续同一已授权 change，从 122/147 进入计划复核；目标为 8.11/9.1/9.7/9.8/11.5/14.2–14.4/14.10。
- 复用原表/API/Master revision，不新增业务对象/迁移。实际 Codex MCP 仅在隔离子进程验证，不改用户全局配置，不发模型 turn。
- 本机正式库/F8/旧导航保持不动，完整 Legacy parity 与最终收尾仍保留后续。
- 真实 `codex-cli 0.160.0 app-server` initialize/工具清单/owned context 资源读取通过，0 模型 turn/领域写入/全局配置修改；不是自写 Test Agent。
- 既有配套恢复脚本验证 6 新表逐行一致、15 引用/7 文件/13 accepted 成果 hash 与历史 ZIP 完全一致，无需 disposable staging。独立只读复核额外核对全部 90 表/约束并 APPROVE；正式目录不动。
- 五个日常页面实际只读打开，11 类业务表记录数不变、0 业务写请求/0 page error；旧外部字体请求被隔离浏览器阻断，不扩大本批为字体改造。
- Executor 完整自声明含三种 support bool、有界唯一 output kinds 与 exact kind/key/version；旧未声明/partial 历史可读，runtime_verified 始终 false。页面 prepare/刷新真实回读，0 自动 dispatch。
- 临时 executor 实际 checkpoint→文件损坏→unknown/readback→明确 revert/recover→新结果，两条链均一次 dispatch，新进程读取 hash/恢复证据通过；原 checkpoint/binding、CAS/currentness 不被绕过。修正后父层定向 28 passed / 1 warning（7.53 秒）。
- 重复已保存正文编辑→显式 project-scoped preference candidate→另行人工 saved 通过。服务端核验 exact Master/parent/actor/context/AI receipts，不接纳首稿、seed/upgrade、仅 metadata/render 改动或伪造/未保存来源。33 类负向及真实页面 409 保留选择/重新读取/晋升刷新通过，不改其他正文/身份/事实/方法。
- 安全首轮发现 shared execution/MCP checker 漏 Google/Stripe/编码赋值/签名 URL；临时 RED 后只补扫描副本，不改变 canonical bytes/hash。57/57 合成输入拒绝，真实 MCP 10 请求预 ID 拒绝且 90 表逐行不变。独立安全复核最终 APPROVE，父层新鲜 23 source / 325 全边界检查通过，29 只读 surfaces / 89 ORM 表零副作用。
- 修正后全量后端 1660 passed / 28 skipped / 8 existing warnings（89.89 秒）；TypeScript/Vite/FE-P1、Ruff、strict 35/35、tracked/54 owned-untracked whitespace/F8 13 hash 通过。Projects 225.03/72.99 kB，common Production 279.62/89.36，Execution/Capability lazy 267.66/86.37 与 267.60/85.69（raw/gzip）。
- 独立计划/SPEC、实施、TypeScript/产品、安全、配套恢复复核 APPROVE，限定本批。9.8 记录 professional pilot 范围外，不声称实际专业工具/生成质量通过。
- 新增 9 项，累计 **131/147，剩余 16**。正式只读 head 仍 f7d000000001；仅停止隔离 15431/15432，保留证据，无新增迁移/依赖/永久测试，无正式库/素材/凭据/Worker 写入、外部生成/公众号、commit/push/deploy/canonical sync/archive。详情 `docs/ALIGN_CREATIVE_RECOVERY_PREFERENCES_ACCEPTANCE.md`。

## 2026-10-05：第五批，Director / Variant / 成果绑定（已验收）

- 从 109/147 继续既有 apply。目标为 6.9/7.6/7.7/7.9、12.3–12.9、13.1/13.5；不存在新的用户方向问题，不重复 propose。
- 先计划复核，再并行限定文件实现；隔离库和素材承接实际绑定/保存/冻结/包验收，不改正式环境。
- 本批 13 项全部按实际验收完成；累计 122/147，剩余 25 项。阶段 9、11.5、真实 MCP 客户端、Legacy retirement、全 change 最终验收未提前勾选。
- Video 日常入口以脚本/镜头意图/配音/字幕/封面/导演包为中心，旧时间线/渲染留在 Advanced；五种 Variant 有界正文复用 manual_edit CAS，真实 POST 409 保留本地正文/意图，Master 与其他系列不改。
- 隔离 Director Package 6（无最终 render）→受控 Test Agent Execution 14→三项必需输出人工接受为 MaterialRevision 12/13/14→明确绑定并保存 Video Master→attestation/checks→Candidate 1 v4→Review/Approval→local ZIP 通过。后续 Master 修订/暂存清理不改变历史 Candidate 或 ZIP；三次 ZIP SHA256 一致。
- Home 从真实 Execution 投影 unknown/blocked/result_ready，优先级、owner/归档和 exact deep link 实测；GET 不新增执行/模型/审批记录。缺表明确 unavailable，不假装零待办。
- v4/v5 只冻结实际已纳入源内容的安全 external_execution provenance；受控跨项目精确引用实测通过，来源 project/unit 保持原值，旧 Candidate 无 backfill/hash 改写。
- Cleanup 的 exact-key/no-follow/hash/shared-attempt/CAS 检查及拒绝/unknown/权限/失败重试通过；实际仅清理隔离的三个 staging 副本，已接受 Material bytes、所有 output/history 行和 ZIP 保留。迟到旧失败不能覆盖新成功，32 项临时断言含 6 个审计竞争场景全部通过。
- 独立计划/SPEC、后端安全、TypeScript 最终 APPROVE；首轮清理审计乱序和 system_shared 跨项目引用问题先 RED 再窄修，最后重验。
- 修正后完整后端 1660 passed / 28 skipped / 8 existing warnings（86.85 秒）；TypeScript/Vite/FE-P1、Ruff、strict 35/35、diff-check 通过。Projects 225.03/73.01 kB，通用 Production 279.62/89.38 kB，Variant lazy closure 302.98/97.51 kB（raw/gzip）；无通用 TipTap/XYFlow 依赖。
- 隔离 API/Web 为 15421/15422，证据 `/tmp/aics-director.pFKi2i`；浏览器只允许 loopback，零 page error，Workflow 与 Master dirty/save 独立且开合面板保留两份本地草稿。正式库只读 head 仍为 f7d000000001，F8 13 文件 hash 不变。
- 详细证据见 `docs/ALIGN_CREATIVE_DIRECTOR_VARIANTS_ACCEPTANCE.md`。无新增迁移/依赖/永久测试、无正式库/素材/凭据写入、无真实供应商或公众号调用、无 commit/push/deploy/canonical sync/archive；仅停止本批隔离进程并保留证据。

## 2026-10-04–05：第四批，Capability Memory（已验收）

- 开始 85/147；沿用已批准阶段 10/11。先独立计划复核，再并行服务/页面，主 agent 负责 MCP/成果捕获与隔离验收。
- 使用既有三表，不新增 migration，不改正式库/F8/skills_enabled；任务按实际验证勾选。
- 独立 SPEC 复核 APPROVE。第一轮实际接口 12 组、MCP find/use、成果接受后候选捕获及捕获失败隔离、不同来源相同内容保留各自来源、页面 5 组通过。
- 独立实现复核发现凭据格式扫描、Unicode canonical hash、最大正文渲染预算及使用结果 409/历史回填问题；均先临时 RED 复现再窄修正。最终任务数与门禁使用修正后重验，不沿用第一轮结果冒充最终通过。
- 上述问题及迟到回执串记录已全部窄修正并重验；SPEC/后端安全/TypeScript 最终定向复核 APPROVE。结果回读绑定同一 use/revision，历史结果回填与新使用权限分开。
- 修正后父层 12 组 API、成果接受/捕获失败隔离、跨来源同 hash、真实隔离 MCP find/use、页面 5 组与延迟回读/409/归档回填追加验收通过；零 page error。
- 最后全量后端 1660 passed / 28 skipped / 8 existing warnings（89.87 秒）；TypeScript/Vite/FE-P1、strict 35/35、Ruff、tracked/owned-untracked diff-check 通过。Projects 225.02/72.99 kB，通用 Production 279.51/89.40 kB，方法库 lazy closure 260.21/83.78 kB（raw/gzip）。
- 新增 24 项完成，累计 109/147，剩余 38。11.5、实际 Codex/Claude client、专业恢复、Video/Variant/Legacy/全 change 验收未提前勾选；方法库不会隐式执行代码、改变正文/Identity/事实/Workflow 或 Installed Skills。
- 隔离 SQLite/素材 `/tmp/aics-capability.lochl9`；正式库只读确认仍为 `f7d000000001`，F8 13 文件 SHA256 一致。无新增迁移/依赖/永久测试，无正式库/素材/凭据/运行环境写入，无本地提交/push/deploy/canonical sync/archive。
- 第四批 EXECUTED / REVIEW_PASSED，完整证据见 `docs/ALIGN_CREATIVE_CAPABILITY_MEMORY_ACCEPTANCE.md`；验收后仅停止隔离 15411/15412，保留证据。

## 2026-10-04：第三批，页面与受限本机 MCP

- 实施计划独立复核 APPROVE；保持同一已批准 change，不新增范围。计划见 `docs/superpowers/plans/2026-10-04-align-creative-orchestration-ui-mcp.md`。
- 创作意图、Package/成果人工审阅已接入；工作流设计/Inspector/Run 放入显式 Advanced lazy 面板，队列连接精确执行；修正 Production viewer 角色检查，读取角色失败时保持只读。
- Package 和 Execution 共用原子 ProjectEvent/AuditLog；重复 prepare 不重复记录。检查点只能在 claimed 后建立，并存储 exact execution/package/executor/revision binding。
- 隔离浏览器通过意图保存/刷新/双窗口 409、Variant 仅意图修订、包预览/prepare、MCP Test Agent 与逐成果接受、多输出拒绝/同槽位替换、同记录详情、显式重新读取、viewer/归档、高级工作流读取和只读队列 deep link。
- 最后安全修正后全量后端 1660 passed / 28 skipped / 8 warnings（88.63 秒）；TypeScript/Vite/FE-P1、strict 35/35、Ruff、tracked/owned-untracked diff-check 通过。独立 SPEC/Python/TypeScript/安全均 APPROVE，限定本批范围。
- 领取证据使用保留的 ProjectEvent，不依赖可清理 AuditLog；verified recovery 必须有观察证据，更换 checkpoint 不继承旧验证；外来 executor 不能对账。
- 有界敏感文本正则两处回溯问题已修正，保留秘密拒绝语义；实际 254119 字节 MCP ping 为 0.1458 秒。
- 新增 21 项，累计 85/147，62 项未勾选；8.5 Capability、8.11 实际 Codex/Claude client、完整恢复/Video/Legacy/最终验收未提前勾选。
- 临时 API/Web 为 `127.0.0.1:15401/15402`，SQLite/素材位于 `/tmp/aics-align-ui-mcp.cVc6Qr`；正式 API 未重启、正式库未迁移，F8 13 文件核对不变。
- 第三批：EXECUTED / REVIEW_PASSED。下一批 Capability Memory、明确适用范围与显式复用；不提前归档未完成 change。
- 验收后仅停止本批隔离 15401/15402 进程，保留临时证据；正式 API/Web/Worker 不动。

## 2026-10-04：第一批，阶段 0–2

- 基线：`main@341ead8`；本批代码尚未提交。
- 正式 SQLite head：`f7d000000001`；现有代码 head：`f8a000000001`。正式库仅通过只读连接核验，未升级。
- F8 已有 13 个 tracked dirty 文件通过 SHA256 快照逐一核验不变。
- F6E 的既有 tasks 全部完成，change 仍 active；本批未改其 tasks/spec lifecycle。
- 第一批入口实现：Home 根入口、只读创作队列、Project 渠道变体/执行入口、Assets/Project 的 Source/Fact/FactPack/Material 操作、Settings 的按需 Connector/模板操作。
- 15 组隔离浏览器检查通过，零 page error；供应商生成/签名任务是受控图片夹具，不是真实能力复验。
- 最新隔离复跑全量后端：1660 passed / 28 skipped / 8 warnings（82.13 秒）；TypeScript/Vite 与 bundle gate 再次通过。
- OpenSpec strict 35/35、Ruff、diff-check 通过；文档收尾后再次核对 strict、diff 和 ownership。
- 当前任务已据实施/验收证据勾选 22/147；0.6 全程停止条件和阶段 3–14 保持未勾选。
- 独立前端代码复核：APPROVE；独立产品/操作清单定向复核：APPROVE。两路首轮反馈均已闭合，未发现具体新增本批阻断。1.7 已完成清单复核；不是全部 legacy 操作的最终验收，也不据此隐藏旧导航。
- 首轮独立复核要求修正项目绑定接受提示/共享素材回读、task deep link 刷新/恢复、viewer/归档只读、Project 文件资料日期。已按真实 API 契约补齐前端，修正后 TypeScript/Vite/bundle 和 15 组隔离浏览器检查通过。
- 第一批阶段 0–2：EXECUTED / REVIEW_PASSED。下一批为阶段 3–7 的持久化、Creative Intent、Package/Execution 和结果接受；尚未开始，不把本批入口接入当作外部执行已可用。

## 2026-10-04：第二批，阶段 3–7 后端

- 新增 42 项完成，当前 64/147，83 项未勾选；不是整个 change 完成。
- 新增六张表、Master/Variant nullable intent、`aco000000001` additive migration；Capability Memory 服务尚未实施。
- Intent 使用原 CAS/幂等/history/diff。Package 冻结精确 current source/context/profile/intent/refs/输出合同；Director 支持无最终 MP4 的 Video v2。
- Execution 具有 prepare/claim/start/report、unknown/reconcile、确认未 dispatch 的新记录重试、私有素材 materialize/暂存、多输出 index/attempt/替换及人工接受。
- 接受只入 MaterialRevision/明确项目引用；权利不升级，归因/许可继承，source 不被自动修改。
- 隔离实际 API 检查通过；双线程 claim 200/409、submit 201/409、accept 200/409；新 Python 进程读取 accepted 成果，准确字节 hash 不变。
- 当前库副本 up/down/up、历史原始列哈希、10 组 retained-row/intent downgrade guard 通过；正式库仍为 `f7d000000001`，未升级。
- 三处数据安全补丁后最终全量后端：1660 passed / 28 skipped / 8 warnings（85.03 秒）；TypeScript/Vite/FE-P1、strict 35/35、Ruff、diff-check 通过。命令见验收记录。
- 独立 SPEC / Python / 数据安全复核全部 APPROVE，限定本批已实施后端范围；不把代码复核冒充页面或正式库验收。
- 首轮复核的来源伪造、换 key 绕过 unknown、required rejection 数量旁路已修正并实际负向验证；补了 accepted-result provenance 回读和终态不重开的保护。
- 数据安全复核追加的已接受输出输入边界漂移、metadata 合并后的假 verified、读取前总量预算已修正；真实 API/存储负向与独立定向复核通过。
- 第二批阶段 3–7 后端：EXECUTED / REVIEW_PASSED。下一批接入 Intent/Package/人工接受页面和本机 MCP；正式启用仍需要另外明确授权的 SQLite 迁移。
- 最终空白检查覆盖 tracked diff 和本 change 新增文件；North Star 三行 Markdown 行尾空格改为显式引用分段，产品语义未变。F8 13 文件再次逐项核验不变。

## 2026-10-05：第七批，Legacy parity（部分验收）

- 从 131/147 继续；最终独立复核因账户额度未完成，不能勾选复核或隐藏旧导航。
- 使用 `/tmp/aics-final-parity.qN9Cps` SQLite/素材副本、15441/15442；正式环境不动。父层接手 worker 未执行的操作核验。
- 新鲜完整后端：1660 passed / 28 skipped / 8 existing warnings（101.10 秒），当前批后端未改。
- 证据逐项公开授权入口及角色未知只读已补，真实 PATCH/冻结回读通过。旧素材撤权取消的错误请求先复现并拦截，修正后零请求；日常 Text v2→v4 审批→本地 ZIP 通过，Project 15 / Unit 15 / Master 25 / Candidate 6，没有 Draft/Topic/Mother/Run source。
- 周期改为本地选择＋明确保存，真实 PATCH 回读 30 分钟、不自动拉取通过。Settings 15 个兼容入口、BrandVoice Clone→草稿归档→确认删除、viewer 只读通过。没有修改 backend/API/迁移。
- 原 Topic/Draft/Mother/v2 Candidate/Target/Receipt 用明确 synthetic fixture 在原页面/API 读取；0 写请求、0 page error，全部表 `.dump` hash 前后一致。viewer 与角色读取 503 时四个旧操作页均只读、零请求；没有隐式迁成 Master/Execution/Capability。
- TypeScript/Vite/FE-P1、strict 35/35、Ruff、tracked/owned-untracked diff-check 与 F8 13 hash 通过。Projects 225.03/72.98、通用 Production 279.62/89.35、Settings 242.64/79.14、Assets 262.15/84.17 kB raw/gzip。
- 第七批先关闭 13.6/13.8/13.9/13.10/14.5/14.11/14.12 共 7 项，累计 **138/147，剩余 9**；第八批关闭 13.3/13.4，随后汇总关闭 14.6，当前 **141/147，剩余 6**。三路最终 review 未完成，不能用父层或前批定向 review 替代，不隐藏 LEGACY_NAV，不标 ARCHIVE_READY。
- 详情 `docs/ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md`。正式 head 仍 f7d000000001；仅停止本批隔离进程，保留证据，无正式写入/重启、外部调用、提交/push/deploy/canonical/archive。

## 当前未完成边界

本批又完成 Assets/Settings 的完整操作 parity，并完成跨批浏览器证据汇总。当前 141/147，剩余 6 项：0.6、3.12 两项持续安全边界；13.7 旧日常导航退出；14.7/14.8/14.9 三类最终独立复核。日常 Text 到 ZIP 与旧历史零写通过，不冒充正式库启用或专业工具成功。

## 2026-10-05：最终门禁复跑与独立复核重启

- 原三路 reviewer 未给出实质复核结论：前置提问不记 APPROVE；之后后端 reviewer 返回 usage limit，另外两路在本轮查询为 not_found。不能用父层自查替代 14.7–14.9。
- 本轮为三个明确且只读的范围重新安排独立 reviewer；父层不写其结论，也不提前隐藏 `LEGACY_NAV`。只有实际返回并核验的结论才能关闭任务。
- 新初始化隔离库 `/tmp/aics-align-final.*` 执行现有迁移与完整既有 suite，**1660 passed / 28 skipped / 8 warnings，88.47 秒**，exit 0；清空继承环境、使用 mock，不接触正式 SQLite 或供应商。
- 新鲜 `npm run build`（TypeScript/Vite/FE-P1）、OpenSpec strict **35 passed / 0 failed**、Ruff、tracked diff-check 及 40 个 owned untracked 文件空白检查均通过。Projects 225.03/72.98、通用 Production 279.62/89.35 kB raw/gzip。
- 只读正式库 head 仍 `f7d000000001`，六个执行/方法新表不存在；canonical specs 无本轮 diff，F8 13 文件 SHA256 仍一致。当前保持 **141/147，6 项未关闭**，无业务代码/正式环境/提交/归档操作。

## 2026-10-05：第八批，Assets/Settings parity 复核

- 依据 `docs/LEGACY_OPERATION_PARITY.md` 逐项复核 53 条操作行：Sources/Facts/FactPacks/Materials、Connectors/Templates、普通运行配置和历史读取均有对应页面、API 真源或兼容入口；无新增第二套数据真源。
- 临时隔离库重新运行 `daily.cjs`、`revoke-cancel.cjs`、`connector-controls.cjs`、`settings.cjs`、`history.cjs`、`roles.cjs`：新日常 Source→Fact→FactPack→Boundary→Master→Candidate→Approval→local ZIP 通过；撤权取消零写入；周期明确保存不自动拉取；Settings 兼容目录、BrandVoice 草稿归档/删除、历史只读和 viewer/unknown fail-closed 通过。
- 静态 parity gate 通过：53/53 清单行、17 个 Web/兼容路由、16 个 OpenAPI 资源前缀、14 个 Settings 兼容链接及管理员运行配置入口均存在。该 gate 证明操作承接和入口完整，不替代真实 Provider、公众号或专业工具验收。
- 13.3、13.4、14.6 关闭；13.7 继续保留旧导航，直到三类最终独立复核完成。
- 14.6 通过跨批证据汇总：直接起点、Source/Fact/FactPack、原生素材生成、Text/Graphic/Video、五种 Variant、Candidate/Approval/local ZIP、Creative Execution、Capability Memory、旧历史读取均有对应隔离浏览器证据；不是把代码存在当成浏览器通过。

旧菜单及旧 URL 保留。F8 13 文件 SHA256 不变；未新增永久测试用例（既有 head 断言一处更新）；未修改正式数据库/素材/凭据；未真实调用 CPA/MiniMax/公众号；未本地提交、push、deploy、canonical sync 或 archive。

第一批快照见 `docs/ALIGN_CREATIVE_PHASE_0_2_ACCEPTANCE.md`；第二批证据见 `docs/ALIGN_CREATIVE_PHASE_3_7_BACKEND_ACCEPTANCE.md`；第三批证据见 `docs/ALIGN_CREATIVE_UI_MCP_ACCEPTANCE.md`；第四批见 `docs/ALIGN_CREATIVE_CAPABILITY_MEMORY_ACCEPTANCE.md`；第五批见 `docs/ALIGN_CREATIVE_DIRECTOR_VARIANTS_ACCEPTANCE.md`；第六批见 `docs/ALIGN_CREATIVE_RECOVERY_PREFERENCES_ACCEPTANCE.md`；第七批见 `docs/ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md`。根 F8 执行记录保持不变。
