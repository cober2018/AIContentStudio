# Creative Orchestration：最终实施验收与操作承接

## 当前 R1 / R2 收尾回执（2026-10-05）

R1和R2已经实施并完成新鲜门禁，交回同工作区最终closeout review；这不是canonical同步、归档或提交授权。原147项核心实施的APPROVE保留，追加7项收尾任务中15.1–15.6完成，15.7最终closeout复核待确认，当前153/154。下文147/147、ARCHIVE_READY、F8十三文件不变和1660项后端结果均保留为上一轮历史快照，不作为当前收尾结论。

```yaml
C2C: ALIGN-CREATIVE-ORCHESTRATION-R1-R2-CLOSEOUT
STATE: EXECUTED
WORKSPACE: AIContentStudio
BASE: main@341ead8
WORKING_TREE: dirty - core implementation and closeout remain uncommitted
CORE_IMPLEMENTATION: APPROVE - prior independent review
R1_SCHEMA_LIFECYCLE: CORRECTED
R2_RETAINED_REGRESSIONS: 108 tests in 4 repository files
TASKS: 153/154
REMAINING: 15.7 final same-workspace closeout review
LOCAL_RUNTIME: KEEP_ENABLED
FORMAL_SCHEMA: aco000000001
IDENTITY_ANCESTRY: f8a columns present; 7 users, 0 issuer, 0 subject
JWT_ACTIVATION: NOT_PERFORMED
LIVE_DB_ROLLBACK: NOT_PERFORMED
ARCHIVE_READINESS: PENDING_FINAL_CLOSEOUT_REVIEW
CANONICAL_SYNC: NOT_EXECUTED
ARCHIVE: NOT_EXECUTED
LOCAL_FEATURE_COMMIT: NOT_CREATED
PUSH: NOT_EXECUTED
```

### R1：当前schema只有一个真相

- `LOCAL_APPROVED_SCHEMA_HEAD`和默认readiness目标改为`aco000000001`。默认head测试先复现旧f7d错误，再验证aco修正；本轮业务代码只改该常量和解释注释，`init_db`的migration-only保护是此前核心实现，不冒称本轮新增。
- F8 design/spec/tasks、根README、F8状态/能力矩阵和两份运维手册当前口径统一为`f7d → f8a → aco`。历史f7d验收仍明确保留，不把旧1660项或旧恢复演练改写为aco新结果。
- f8a两列nullable身份字段仅作为Alembic ancestry存在；正式7个User两列均null/inert，不启用或验收JWT/production身份。现有Header身份、SQLite、素材、私有凭据、API/Web/Worker拓扑和运行配置不变。
- parity顶部与末尾已改成正式库已获准升级和新版继续运行，不再同时声称“尚未升级”。不回滚、降级或再次迁移正式SQLite。
- 原13份F8-owned文件只窄修其中8份当前schema/运维文档；根`task_plan.md/progress.md/findings.md`、F8 proposal及F8 product-settings delta这5份SHA256仍与本change开始时完全一致。8份授权窄修的hash变化不是保全失败，其余F8历史范围不重写。

### R2：四组永久回归

| 仓库文件 | 用例数 | 保护的合同 |
| --- | ---: | --- |
| `apps/api/tests/test_aco_creative_executions.py` | 13 | Master/Brief stale拒绝claim/start；Unknown不重发；min_count与immutable replacement；派生public/model/commercial权利不升级；撤权/归档/解绑与事务回滚 |
| `apps/api/tests/test_aco_creative_mcp.py` | 66 | loopback/Host/Origin、Bearer与固定owner、15工具精确白名单、其他用户项目隔离、禁止审批/发布/SQL/任意文件操作，读取零写入 |
| `apps/api/tests/test_aco_capability_memory.py` | 18 | 显式candidate→saved/pinned及append-only修订；7种适用scope并列；content/args秘密整体拒绝；同名Installed Skills分离、不改skills_enabled；部分接受不能capture |
| `apps/api/tests/test_aco_schema_lifecycle.py` | 11 | 实际f7d旧形状→f8a→aco、六表/约束与intent列、旧User原列保全、null/inert Header身份、隔离up/down/up、保留历史时拒绝downgrade、默认schema/readiness |

测试使用临时文件SQLite/素材目录、隔离配置和mock LLM，真实执行service/router/middleware/migration守卫；不读取正式runtime.env、不访问正式库/素材或供应商。初始Alembic使用当前metadata，因此migration夹具先在一次性空库降到f7d并断言新表/身份列不存在，避免名义旧head配上新schema的假回归。允许降级只发生在无保留历史的一次性库；保留数据的拒绝用例先断言head/表/行均未丢失。

### 本轮实际重新运行的门禁

| 门禁 | 新鲜结果 |
| --- | --- |
| 四文件定向 | 13＋66＋18＋11＝108 passed；R2独立复核另行隔离复跑108 passed、0 skipped、65 warnings |
| 完整后端 | `apps/api` cwd，独立临时aco数据库/素材，`1768 passed, 28 skipped, 72 warnings in 101.02s`，exit0；原1660项＋新增108项 |
| TypeScript / Vite / FE-P1 | `npm run build` PASS；Projects224.09/72.70、common Production278.68/89.07、Settings242.16/78.99、Assets261.21/83.89、Learning252.59/82.06 kB raw/gzip；TipTap仍仅Text lazy闭包 |
| OpenSpec | `openspec validate --all --strict`，35 passed、0 failed；本change仍12份delta，未同步canonical |
| Ruff | 全`app`＋四新增测试文件PASS；扩大到全部scripts的尝试发现无关`seed_dreamo_data_service.py`三条既有问题，直接用HEAD源验证同样失败；未改无关脚本，不虚报all-scripts PASS |
| 空白检查 | tracked `git diff --check`与本轮owned untracked文件检查PASS |
| 正式只读复验 | SQLite headaco、integrity ok、7/0/0身份计数；API ready=true/reasons=[]、Web200；8000/5173仍只监听127.0.0.1，原API/Web PID未变 |

72条warnings来自既有依赖/服务API：Starlette/httpx、`Session.flush(objects=...)`、旧workflow外键反射及NULL主键调用；新增测试增加覆盖触发次数，不将warnings说成零，也不为本轮收尾重构无关代码。28项原有skip保留，不把skip当成通过。

R1规格一致性由主执行者定向复核；R2 SPEC独立复核Mendel（`01a10aed-dce8-76c1-afcd-dd6c5bf1be1e`）APPROVE，且亲跑108项定向。随后Python代码质量复核Zeno（`01a10af3-e75e-7991-b3bf-84a000a16229`）对默认head与四测试文件APPROVE，确认断言、隔离、清理及配置覆盖，无可执行缺口；其亲跑Ruff，不冒称重跑全量。原R1旁路reviewer因模型容量失败未返回结论，不记APPROVE；R1由主执行者完成定向规格核对。这些内部复核不替代15.7要求的同工作区最终closeout review。

### 下一步边界

只等待同一工作区最终closeout复核；通过后再按授权同步12份delta、归档、校验和本地feature commit。当前没有canonical改动、归档、提交、push、正式迁移/回滚、重启服务、生成或公众号发送。本地运行继续启用；专业工具pilot和公开发布仍不在本change第一版范围。

本轮实际使用skills：using-superpowers、receiving-code-review、openspec-apply-change、writing-plans、executing-plans、test-driven-development、verification-before-completion、dispatching-parallel-agents、subagent-driven-development、requesting-code-review。

## 上轮整个 OpenSpec 执行回执（历史快照，早于R1/R2）

```yaml
C2C: ALIGN-CREATIVE-ORCHESTRATION-EXECUTION-RECEIPT
STATE: EXECUTED
WORKSPACE: AIContentStudio
CHANGE: align-creative-orchestration-product
BRANCH: main
BASE_COMMIT: 341ead8c30390bd48519d0a5af05ab2a20f6fa19
WORKING_TREE: dirty - implementation not committed
TASKS: 147/147
REMAINING_IMPLEMENTATION_TASKS: 0
DELTA_SPECS: 12
IMPLEMENTATION: ACCEPTED
INDEPENDENT_REVIEWS: APPROVE - recorded implementation reviews
LOCAL_RUNTIME: ENABLED
ALEMBIC_HEAD: aco000000001
ARCHIVE_READINESS: BLOCKED_PENDING_R1_R2_CLOSEOUT_REVIEW
CANONICAL_SYNC: NOT_EXECUTED
ARCHIVE: NOT_EXECUTED
FEATURE_COMMIT: NOT_CREATED
PUSH: NOT_EXECUTED
REMOTE_DEPLOY: NOT_EXECUTED
PUBLIC_PUBLICATION: NOT_EXECUTED
```

### 已完成的全部范围

| 工作范围 | 执行结果 |
| --- | --- |
| North Star与旧功能盘点 | 新方向落地；53项操作级parity记录，旧操作承接后才退出日常导航 |
| 日常入口统一 | Home/Opportunity/Project/Production/Review/Identity/Assets/Learning/Settings九入口；旧历史URL及十五个兼容入口保留 |
| Content-first生产体验 | 内容Master为默认中心，Workflow/Debugger独立放入高级自动化；两者dirty/save状态分离 |
| Creative Intent | Master/Variant随显式修订保存创作意图，不成为另一套可编辑正文真源 |
| Execution/Director Package | 从精确已保存Master/Variant生成不可变包，冻结来源/hash/context/refs/权利与多输出合同；stale/historical只读 |
| CreativeExecution持久化 | 准备、领取、执行、进度/blocker、unknown核对及确认未dispatch失败分开；CAS/幂等/尝试和终态历史保留 |
| 结果回传与人工接受 | 成果先staging；role/index/attempt、MIME/数量/bytes/hash校验；拒绝后新attempt替换、不覆盖旧成果；全部必需输出接受后才整单accepted |
| 正式素材回接 | 明确接受后成为MaterialRevision(source_kind=external_execution)，可明确建立项目引用；来源权利不升级，祖先撤权继续阻断 |
| 本机受限MCP | 15白名单工具、固定owner与Bearer、loopback/Host/Origin约束，共用既有CAS/审计；真实Codex连接读取已验证 |
| checkpoint/recover | 执行者能力声明、精确绑定checkpoint/观察hash/原身份、受控文件恢复；Unknown不自动重发 |
| Capability Memory | 六类方法/偏好candidate→saved/pinned→archived/deprecated、append-only修订、显式使用/结果回填、受控导入导出 |
| Learning/偏好与Skills分离 | Learning只显式桥接candidate；重复已保存人工编辑可明确捕获偏好；Installed Skills独立清单，不自动安装/启用/覆盖 |
| Director-first Video与渠道 | 复用video.master.v1/v2和现有timeline/render/v4历史；无render可创建导演包；五种受控内容形态的Variant正文修订/409保留本地草稿 |
| Review/交付与历史兼容 | 明确接受素材后仍须显式保存Master/Variant，再走Candidate/Approval/本地包；保留旧v1/v2/v3/v4/v5及历史ZIP |
| 安全/恢复/正式启用 | 精确文件路径与中断恢复、派生权利/秘密拒绝、SQLite/素材配套备份演练；原本机SQLite正式升级，API/Web/Worker/MCP启用 |

业务闭环已经在隔离环境实际验证：

`Creative Intent → Frozen Package → Execution → Staged Outputs → Human Acceptance → MaterialRevision → Explicit Master/Variant Save → Candidate → Review/Approval → Local Package`

ProviderGenerationTask继续承接原简单图片/视频/TTS原生生成；没有被CreativeExecution替换。结果接受不自动修改Master、Variant、Candidate、Approval、PublishedContent、Identity或事实边界。Capability方法第一版不在后端执行任意代码，所有匹配scope并列返回，由调用方明确选择。

### 验收证据

| 门禁 | 结果及证据口径 |
| --- | --- |
| 本轮任务与规格数量核验 | tasks147/147、remaining0、12份delta，重新读取确认 |
| 本轮OpenSpec/空白检查 | `openspec validate --all --strict`35/35、git diff--check通过；不是此前stdout的转述 |
| 完整后端实施门禁 | 既有最终验收记录1660 passed/28 skipped/8 existing warnings（92.22秒）；本回执轮没有重跑suite |
| 前端/性能实施门禁 | 既有TypeScript/Vite/FE-P1通过；Projects224.09/72.70、commonProduction278.68/89.07 kB raw/gzip；TipTap仅Text lazy闭包，不污染通用Production/Graphic/Video |
| 独立复核 | 既有最终后端/数据/安全14.7、前端/产品14.8、MCP14.9及导航窄复核均APPROVE；本回执不声称新增独立复核 |
| 隔离浏览器/业务链 | 前述各批验收包含结果接受、三形态/五Variant、409、unknown/恢复、引用/权利、旧历史、Candidate/Review/ZIP；受控executor不冒充专业工具自动化 |
| 正式数据库升级与保全 | 启用时副本up/down/up及正式升级通过；83张历史表5145行旧列hash、97条原FK异常集合不变；7引用/5素材字节hash一致 |
| 本轮正式环境复验 | headaco000000001、SQLite integrity ok；API ready=true/reasons=[]、Web200，8000/5173仅127.0.0.1监听 |
| 原Worker与正式MCP | 启用记录含真实Worker ping且active/reserved/scheduled0；正式HTTP和真实Codex客户端15工具/owned资源读取通过，0模型turn/全局配置改动 |
| 范围保护 | 本轮F8十三个owned文件SHA256再次通过；未修改其既有dirty内容，未披露私有token或凭据 |

隔离写链验收与正式环境联通是两组不同证据；正式启用没有重复制造示例、发模型任务或公众号草稿。既有内容的stale、identity/rights/check阻断仍保持真实，不能把“新版已启用”写成“所有旧稿可直接发布”。

### 当前交付及未执行动作

- 新版正式入口：`http://127.0.0.1:5173/`；本机SQLite+本地素材+原API/Worker仍是最终使用方案，不是等待服务器化的临时环境。
- 升级前/后数据库、完整素材和对应私有配置快照：`backups/creative-local-enable-a63DyjDV/`。启动、停止、恢复和正式启用证据见 `ALIGN_CREATIVE_LOCAL_ENABLEMENT.md`。
- 本change批准的实施/验收任务没有剩余项；canonical同步/归档、本地提交仍未执行，不能将当前main基线误报为已包含新feature commit。
- 专业工具真实自动化pilot、供应商生成质量及公开发布不在本change第一版验收范围；本地ZIP不等于公开发布。
- 本回执不授权下一轮实施、远端推送或新的内容发送。下一步若授权生命周期收尾，可单独同步12份delta→canonical→archive→校验→本地提交。

本回执使用skills：using-superpowers、writing-plans、verification-before-completion。

## 核心实施阶段的需求背景与状态（历史快照）

范围是已批准的 `align-creative-orchestration-product`，不是新需求或业务重写。目标是让日常入口承接原操作，并保留旧记录与兼容地址；完整 parity 和独立产品复核通过前不能隐藏旧导航。

核心实施验收时点为 **147/147，IMPLEMENTATION_ACCEPTED / ARCHIVE_READY**，后续R1/R2复核已将当前归档门槛改为本文顶部状态。基线为本地 `main@341ead8` 加未提交 change 工作区。用户另行授权后的本机正式启用已完成：SQLite head `aco000000001`、原API/Worker和新版Web已启动，MCP联通通过；证据见 `ALIGN_CREATIVE_LOCAL_ENABLEMENT.md`。文件名保留 PARTIAL 以免破坏已有引用，以下表格与“不改正式库”是实施/隔离验收快照，不冒充本次正式运行验收。

## 最终关闭（2026-10-05）

| 门禁 | 实际最终证据 |
| --- | --- |
| 14.7 后端/数据/安全 | 独立 APPROVE；实际检查迁移/授权/Unknown/派生权利，以及写入中断、exact-bound 零/半字节 pending、500 输出容量恢复。 |
| 14.8 前端/产品 | 独立 APPROVE；完整日常入口与53行操作承接、内容优先/Video/兼容路径；偏好表单追加问题关闭，13项独立内存断言通过。reviewer 本轮未完成独立浏览器 GREEN，不把父层证据当它亲跑。 |
| 14.9 MCP | 独立 APPROVE，441项合成内存断言；父层另有实际HTTP检查。没有任意文件/SQL/正文写入或批准/发布能力。 |
| 13.7 导航窄复核 | 独立 APPROVE，8项静态检查/TypeScript/diff；仅移除LEGACY_NAV及旧sidebar，九个NAV/全部旧lazy routes/Settings十五入口保留。 |
| 最终实际Chrome | 新context验证 `/`→Home、九个日常入口、十五个兼容入口、无自动运行配置/写入/page error。旧历史脚本再验原实体地址、全部表dump hash不变；方法编辑route/history/beforeunload保护再验零API写入。 |
| 完整后端 | 最后后端修正后1660 passed / 28 skipped / 8 existing warnings，92.22秒、exit0。后续仅前端导航/文档修改，无后端变更。 |
| 最终前端 | 导航修正后 `npm run build`：TypeScript/Vite/FE-P1全部通过、exit0。 |
| 路由预算 raw/gzip | Projects224.09/72.70、Production278.68/89.07、Settings242.16/78.99、Assets261.21/83.89、Learning252.59/82.06 kB。 |
| 重依赖隔离 | Text Studio TipTap lazy闭包605.43/189.28 kB；通用Production、Graphic、Video不加载TipTap/XYFlow首包。 |
| 规格/空白/ownership | strict35/35、Ruff、tracked diff-check、56个owned untracked文件空白检查通过；F8十三文件原SHA256不变。CLI可选遥测TLS失败不改变validate的exit0。 |
| 正式库保护 | mode=ro核对head及迁移中精确六表，仍f7d000000001/六表不存在。未改变正式SQLite、素材、凭据或Worker。 |

当前入口关系：九个日常工作区 → Settings高级运行环境 → 十五个兼容工具；旧实体深链接仍直接打开原记录。旧页面没有被删除或统一重定向到项目列表。

0.6/3.12 的持续安全/不迁移条件在完整独立复核与只读正式库核验后关闭。**代码实施和隔离验收完成，不代表正式启用。** canonical sync/archive、本地提交、push/deploy、正式schema升级、删除兼容页仍未执行，按14.12保留为分别授权的后续动作。只停止本轮临时15441/15442；保留临时证据，正式8000/5173和Worker不动。

实际Premiere/AE/Resolve/Photoshop自动化及生成质量不是本change第一版验收范围；受控媒体/恢复结果不冒充专业工具或供应商已验证，本地ZIP不等于公开发布。

## 本批实际修正

| 文件 | 缺口与修正 |
| --- | --- |
| `apps/web/src/pages/FactPacks.tsx` | 逐条公开使用授权接上既有 exact-item PATCH；默认不授权，明确确认后保存并回读，冻结只读。不根据 Source trust 推断权利，不猜测模型使用授权。 |
| `apps/web/src/pages/Materials.tsx` | 取消撤权原因不再提交默认原因；空原因不提交，失败提示可见，精确版本/清单回读。查看者和未知角色不能撤权、挂载或上传/生成。 |
| `apps/web/src/pages/Connectors.tsx` | 拉取周期先在本地选择，再明确保存；保存失败保留选值。不自动拉取，配置/拉取分别遵循 admin 与 editor 权限。 |
| `apps/web/src/pages/Templates.tsx` | 旧工具按真实角色关闭写操作；补已有 BrandVoice 草稿归档入口。发布版本仍不可原地修改，沿用 clone/新版本发布规则。 |
| `apps/web/src/product/ProductSettingsPage.tsx` | 高级区增加 15 个旧数据/兼容工具入口；不提前加载运行配置、不触发写入，不删除旧日常菜单。 |

这五个文件在前批已被修改；本表只列本批新增修正，不把整个 Git diff 归因于第七批。后端、迁移、依赖、正式配置和 Worker 本批均未改。

## 实际浏览器验收

隔离 API/Web 为 15441/15442，库及证据位于 `/tmp/aics-final-parity.qN9Cps`。只允许 loopback 网络。临时断言和夹具不进入仓库，也不调用实际模型、公众号或专业工具。

| 验收 | 实际结果 |
| --- | --- |
| 日常新项目完整路径 | Home → Projects → Brief → 新 Source → 抽取/确认 Fact → Pack → 明确公开授权 → 冻结/绑定 → Text v2 → Checks → Candidate v4 → Review/Approval → 本地交付授权 → ZIP。全程无需旧日常入口。 |
| 精确内容与成品包 | Project 15 / Unit 15 / Master 25 / Candidate 6；Candidate 无 Draft/Topic/Mother/Run source。ZIP 的 `content.md` 来自冻结正文，manifest 含 exact Master payload hash，下载前后 Master hash 不变。 |
| 权利默认与冻结 | 新条目默认 public=false；明确 PATCH 后 true；冻结回读后没有可写授权控件。先前未授权证据被 evidence gate 阻断，不放宽后端门禁。 |
| 撤权取消 | 修正前复现 1 条错误请求并拦截，未实际撤权；修正后取消 0 写请求。 |
| 周期保存 | 修正前选值即写；修正后选择 30 分钟仍保留原值，仅点击保存才产生 1 次 PATCH，持久回读 30 分钟，没有 pull。 |
| 模板承接 | 新日常 Settings 内 BrandVoice Clone → 草稿归档 → 明确确认删除隔离克隆；原版本保留。只清除本脚本新建的临时克隆，不删除用户正式数据。 |
| 权限故障关闭 | viewer 与 `/users/me` 503 两种情况，四个旧操作页均关闭写控件，0 写请求、0 page error。 |
| 兼容目录 | 15 个既有入口可达，目录读取 0 写请求，不加载运行配置工具。 |
| 历史读取 | 原 Topic、`/workspace/1`、`/review-publish/1`、旧审核“已批准”、Handoff、旧资产/目标/回执及 Workflows 原路由读取通过，没有泛化重定向。 |
| 历史不漂移 | exact Draft/Mother/Candidate/Target/Receipt API 响应不变；0 写请求、0 page error；全部 SQLite 表 `.dump` 哈希在整次只读浏览器前后完全一致。 |

历史夹具是本批在 `/tmp` 明确创建的 synthetic Topic 1 / Mother 1 / Draft 1 / v2 Candidate 7 / Target 4 / Receipt 1，不冒充用户真实发布历史。查询现有历史是只读，本批不验证旧稿重新发布或隐式升级。

日常 ZIP SHA256：`19b7b0883793647a0c29fabf849b7b4fcf2705549860ca963118d6bf330dbb38`。隔离模型未配置、部分 evidence 不允许模型使用，语义检查明确 unavailable；人工处置 warning 不把它改为 pass。包下载不等于公开发布。

## 新鲜门禁

| 门禁 | 本批执行结果 |
| --- | --- |
| 完整既有后端测试 | 1660 passed / 28 skipped / 8 existing warnings，101.10 秒；独立初始化 `/tmp/aics-final-backend.jLNnSh`。 |
| TypeScript / Vite / FE-P1 | `npm run build` 通过，包含 bundle gate。 |
| `/projects` | 225.03 kB raw / 72.98 kB gzip。 |
| 通用 Production | 279.62 / 89.35 kB；不加载 TipTap/XYFlow。 |
| Settings / Assets | 242.64 / 79.14、262.15 / 84.17 kB raw/gzip。 |
| OpenSpec | `openspec validate --all --strict`：35/35。 |
| Python lint | `.venv/bin/ruff check app`：PASS。 |
| 空白与 ownership | tracked diff-check、新增 owned 文件空白检查通过；F8 13 文件 SHA256 一致。 |
| 正式库 | 只读 head 仍 `f7d000000001`；未 migration、写入或重启。 |

后端命令运行在 `apps/api`，隔离环境为 `APP_ENV=test`、独立 `DATABASE_URL` 与 `AI_STUDIO_MEDIA_ROOT`，清空继承的运行凭据。不把旧批次命令记录冒充本批执行。前六批的媒体生成、三形态、五 Variant、执行/MCP/方法库/恢复证据仍按各批验收文档保存，本批不声称全部新鲜重跑。

## 第八批追加：Assets/Settings parity

本批在同一隔离库重新运行六组浏览器脚本：

- `daily.cjs`：新日常 Source→Fact→FactPack→Project Boundary→Text Master→Candidate v4→Approval→local ZIP。
- `revoke-cancel.cjs`：取消撤权不发出写请求。
- `connector-controls.cjs`：周期选择只改本地状态，明确保存后才 PATCH，不自动拉取。
- `settings.cjs`：14 个兼容链接、管理员运行配置入口、BrandVoice Clone→草稿归档→确认删除。
- `history.cjs`：旧 Topic/Draft/Mother/Candidate/Target/Receipt/Workflow 只读，零写入且全表 dump hash 不变。
- `roles.cjs`：viewer 与 `/users/me` 读取失败时，旧写操作均 fail-closed。

另外完成了静态 parity gate：53/53 操作行、17 个 Web/兼容路由、16 个 OpenAPI 资源前缀和 14 个 Settings 兼容链接均能对应到当前实现；管理员 `/legacy/settings` 另有明确入口。

同时完成 14.6 的跨批浏览器证据汇总：直接 idea 起点、Source/Fact/FactPack、Material 原生生成、Text/Graphic/Video、五种 Channel Variant、Candidate/Approval/local ZIP、Creative Execution round trip、Capability candidate→promotion→reuse、legacy historical read 均在前六批与本批隔离浏览器记录中有实际 PASS 证据。汇总脚本检查了 10 个场景与 6 份验收文档的对应关系；不把此汇总扩展为真实 Provider/公众号/专业工具质量验收。

这关闭了 OpenSpec 任务 13.3、13.4，但不把入口存在误报成真实 Provider、公众号或专业工具验收，也不提前关闭旧导航。

## 独立复核与剩余任务（历史过程，非当前状态）

最终产品 review 已通过日常面、operation parity、Content-first/Video、legacy deep links与前次修订/范围保护，唯一发现 PreferenceCaptureForm 漏报 dirty。父层 actual Chrome RED/GREEN 后仅接入既有聚合；名称/正文/项目单元/两条 exact edit 选择、hide/show/分区取消、409 后原状态、显式成功解除均通过。409/200 是浏览器内 mock，真实 API 写入零；先前 actual durable/save/409 的 worker 证据单独保留，不混为一谈。修正后新鲜 build/FE-P1 PASS，等待独立窄复审。

后端最终定向复审 **APPROVE** 已返回，原 three-findings 及后续恢复的 post-link、零/partial pending、容量回归全部闭合；reviewer 独立检查实际函数/内存文件系统、本机 flock、lint/diff，未把父层 full suite 当本人亲跑。14.7 关闭；MCP14.9 也已 APPROVE。最新 **143/147，剩余 4 项**：14.8 最终产品复核、13.7 旧导航退场、0.6/3.12 持续停止/不迁移边界。旧导航和正式库仍不改。

写入未完成/容量边界修正后的最新 full backend 为 **1660 passed / 28 skipped / 8 existing warnings，92.22 秒**（exit0）。父层浏览器重新跑 worker 的只读 guard 脚本 exit0、零 API 写入，源文件 SHA256 与 worker 证据一致。后端/产品最终独立复核未返回前，142/147、旧导航与正式库边界保持。

恢复修正后执行者新鲜门禁：`/tmp/aics-align-recovery.EdJYSi` full backend **1660/28/8，87.58 秒**；首轮隔离命令缺少 root PYTHONPATH 的 23 个旧 F7 import 失败，经定向 23/23 和全量复跑排除，不算代码门禁通过。构建/FE-P1、strict 35/35、Ruff/diff/F8 哈希 PASS；Settings 新 baseline243.10/79.27，Projects225.03/72.98，Production279.62/89.35，Assets262.15/84.16 kB。`/tmp/aics-link-service.0tppEc` 实际业务服务验证 same-execution 写入中断→累计记录→新 Session/CAS→精确恢复→人工接受，及祖先撤权/Unknown 阻断通过。独立 reviewer 结论仍单独记录。

最新 **142/147**：MCP 最终 reviewer 返回 APPROVE，独立 441 项合成内存断言通过；父层另有实际 HTTP 编码 ID/metadata 拒绝和普通 ping 证据。14.9 关闭，不声称重跑专业工具/Provider。后端 reviewer 的原三项已闭合，但追加发现 link→unlink 崩溃恢复缺口；真实临时文件先 RED 后窄修（目录锁、归属/精确字节/inode 验证后恢复），并发/未记录输入/外部硬链接/symlink/cleanup GREEN，独立复审待返回。前端实现与最终产品复核仍待完成，旧导航不提前退出。

最终三类 review 均返回实际 REVIEW_NEEDS_FIX，共六处。父层已修 MCP 编码令牌/MOV、Unknown 稳定范围、输入开放前累计 manifest/Audit commit、派生素材祖先 live rights；方法编辑保护仍实施。纯合成 RED/GREEN 与 `/tmp/aics-review-flow.Pc3g93` 真实隔离服务检查通过，包含 post-exposure 故障/新 Session/子集重试、restricted 不升级/零部分写、未记录输入阻断及祖先撤权。修正后新鲜既有 full backend **1660 passed / 28 skipped / 8 warnings，87.84 秒**（`/tmp/aics-align-review.4Gjmkq`）。这些是执行者证据，不替代尚待返回的最终独立复审；仍 141/147，旧菜单与正式库保持不动。

2026-10-05 本轮重新执行隔离最终门禁：既有后端 **1660 passed / 28 skipped / 8 warnings，88.47 秒**；TypeScript/Vite/FE-P1、strict **35/35**、Ruff、tracked diff-check 和 40 个 owned untracked 文件空白检查通过。正式 head 仍 f7d000000001，新执行/方法六表未启用，F8 13 文件 SHA256 一致。无业务代码、正式数据库/配置、外部调用或文档生命周期操作。

原三路后续尝试没有有效复核结论（前置提问不计通过，后端 usage limit，其余本轮 not_found）。本轮另安排三个只读、明确范围的 reviewer；等待实际结论，任务状态仍 141/147。

六路独立 agent 在只读准备阶段因账户额度限制终止，没有产生最终 APPROVE，已关闭 agent。不以父层自查或前批定向 APPROVE 代替本 change 最终独立复核。

本批累计关闭 13.3 / 13.4 / 13.6 / 13.8 / 13.9 / 13.10 / 14.5 / 14.6 / 14.11 / 14.12。剩余：

- 0.6、3.12：持续停止条件与正式库不迁移边界，保留至完整收尾。
- 13.7：完整 parity 和独立产品复核前不隐藏旧导航。
- 14.7、14.8、14.9：最终后端/数据安全、前端/产品、MCP 独立复核。

canonical sync/archive、本地提交、push、正式 SQLite migration、外部 dispatch 与兼容页删除均未执行，待各自明确授权。本批只停止隔离进程，保留临时证据；原 API/Web/Worker 不动。

## 执行技能与依赖

实际使用：using-superpowers、openspec-apply-change、writing-plans、executing-plans、subagent-driven-development、dispatching-parallel-agents、requesting-code-review、receiving-code-review、systematic-debugging、test-driven-development（仅临时断言）、verification-before-completion、finishing-a-development-branch（按既定授权边界保留main工作区，不提交/归档）。原agent额度限制是历史阻断，后续实际独立复核已经完成，具体范围/证据如最终关闭表；不以父层自查替代独立结论。

收尾修正没有新增依赖、迁移、永久测试或示例；整个change的additive迁移仍为既有 `aco000000001`。目录与日常启动方式见 change README；验证脚本是临时证据，不是第二套正式运行配置。
