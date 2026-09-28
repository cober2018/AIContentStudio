# 当前进度

## 2026-09-29：FE-F6A 五份主规格已同步并归档

- 用户已明确授权五份canonical同步、F6A归档、strict/diff-check及本地main提交；不改业务代码，不启动F6B。
- 实核main d060428、工作区干净、4/4产物和214/214任务；仅新增production-content-master，并更新F2/F3A/F3B/F4，不覆盖原始包或其他canonical。
- 本轮使用using-superpowers、OpenSpec archive、writing-plans/executing-plans及verification-before-completion；计划按根task_plan维护，不新增无关方案或测试。
- 已完成：production-content-master新增19要求，F2/F3A/F3B/F4准确更新10要求块；四份主规格的40旧要求/149旧场景完整保留，未修改的要求块逐块一致。新Purpose已正式化，无TBD机械占位。
- 标准归档：openspec/changes/archive/2026-09-29-fe-f6a-production-core-content-master/；9文件（含.openspec.yaml）SHA256与归档前相同，原始包9文件也相同；active中不再有F6A。CLI UTC目录名09-28已仅校正为本地Asia/Taipei日期09-29。
- 实际归档后全量OpenSpec strict24/24通过、git diff --check通过，apps业务代码差异为空。CLI有“超过10个delta建议拆分”的非阻塞提示，不改变已验收范围。
- 仅规格/文档本地main提交，最终hash以git log -1为准；本轮不重跑后端/浏览器，也不将昨日753测试当新运行结果。F6A状态ARCHIVED；不push/deploy/生产迁移、不启动F6B。

### FE-F6A 最终验收完成（214/214，仅本地main收尾）

- 用户本轮明确限定：只完成F6A收尾；F6B及以后禁止启动，必须先出具体方案再确认。canonical同步/归档仍按21.9另待授权；不push/deploy/生产迁移。
- 最终新临时SQLite全量实际输出753 passed / 6既有warnings / 32.06s，包含206项F6A；实际PG约束和撤权行锁2项执行通过，未skip。相关Ruff通过；SQLite及真实隔离PostgreSQL16 fresh head→f5c→head往返通过。
- 最终TypeScript/Vite及FE-P1通过：projects224.68kB raw/72.86gzip，Production254.44/82.27；既有Assets/Settings/Learning预算保持，轻路由无TipTap/XYFlow。最终OpenSpec全量strict24/24与diff检查通过。
- 完整浏览器20.1–20.14实跑通过：三形态保存/刷新、409保留编辑、Brief stale、checks/真实render/v4 freeze、Preview/Changes/Checks、Approval/授权/下载ZIP、真实Draft seed、旧v3、节点rerun/from-here/Human和dirty隔离；额外归档只读回归先RED后GREEN。
- 最终浏览器证据：/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f6a-browser-evidence-KFiSr7/report.json；13 gates、consoleErrors=[]。AI provider显式mock，执行/Attempt是实际持久化；媒体是真实编码文件与明确manual attestation，不冒充真实AI/自动renderer/远端发布。
- 三项只读独立review均最终APPROVE：SPEC（旧MODIFIED要求/场景保留）、backend（live locks/embedded refs/bounds/latest warning）、frontend-review-package（form CAS/v3正文/stale历史/归档控件）。所有发现已修正并回归，主Agent独自写代码。
- 任务逐项验收映射、当前目录结构和长期不变量记录在docs/FE_F6A_FINAL_ACCEPTANCE.md；原始包和canonical未改。本轮只提交F6A白名单，最终hash以git log -1为准，规格状态ARCHIVE_READY；不得把本地验收说成生产验收。

### FE-F6A FINAL-CLOSE 实施增量（main@703d6c5）

- 完整后端初轮实跑745 passed/6既有警告（含实际PG测试），独立前端发现3项并先复现5失败后修复：合法form变更保留上游CAS、旧v3各modality正文schema分派、stale检查禁止执行且历史包按准确冻结input选latest。三形态真实浏览器save/reload/409/stale/check/freeze/Review/Approval/ZIP已通过；真实Draft seed/legacy v3/debugger正在补齐。最终全量仍待修复后重跑。
- 最新前端TypeScript/Vite与扩展Production预算检查通过：projects224.68kB/72.86gzip，Production254.46kB/82.28gzip；三最小壳独立lazy且无TipTap/XYFlow。归档单元/项目的Workflow设计、保存、执行也禁用，Master独立只读。
- 新增 verified Master Workflow Output、两会话 Freeze 幂等/历史保留、Review 三形态冻结预览与结构化 diff、Master Versions/Overview风险（Unknown优先）。相关定向37项及输出9项通过。
- 隔离本地 PostgreSQL16容器 `aicontent-f6a-postgres-acceptance`（127.0.0.1:15462/f6a_acceptance）实际 Alembic up/down/up 通过；真实唯一/FK/非破坏downgrade和两会话撤权行锁2项通过。不是生产数据库。
- 独立SPEC review APPROVE。独立后端首轮发现撤权窗口/嵌入引用/标题存储bounds/warning处置四项：已添加行锁、精确引用与路径校验、500字符标题上限、准确check-id+input-hash的审批warning处置。针对warning+原v4交付45项通过，Master/adapter/seed102项通过；还需独立复核。
- ProductionDesigner已拆分为controller + Workspace/Header/Canvas/Inspector/AssetDrawer/MasterPanel及三lazy最小壳；Review冻结渲染经项目权限/权利/字节校验后预览。TypeScript/Vite和既有route预算初跑通过；最终全量/浏览器/独立frontend仍未完成。
- 当前不勾214/214、不归档/同步、不push/deploy/生产迁移。临时PG仍运行供最终门禁；完成后仅停止本任务容器。

## 2026-09-28：FE-F6A FINAL-CLOSE

- 实核本地main703d6c5、tree clean，OpenSpec114/214；用户授权完成剩余100项并实际浏览器/独立评审验收。不进入F6B，不push/deploy/生产迁移，归档仍须另行授权。
- Skills：using-superpowers、OpenSpec apply、receiving-code-review、writing-plans/executing-plans、TDD、verification-before-completion；复用已批准设计，无新proposal或专业编辑器。新增独立评审工具现可用，仅用于只读评审，主Agent仍独自实施代码；graph MCP未提供，限定相关文件回退读取。
- 先完成project_outputs、Freeze历史/竞态、检查和迁移残余；再Review/Versions/Overview，然后Production最小壳和隔离浏览器。新门禁未执行前不引用上轮712通过作为本轮结果。

## 2026-09-28：FE-F6A v4 Approval/Authorization/Package窄闭环

- 基线main6ebc9e5、92/214，跟踪文件干净。按用户授权继续已有change，前端不动；采用OpenSpec apply、评审反馈、writing-plans/executing-plans、TDD和verification-before-completion。
- 实际确认审批draft=None阻断、项目package只接受schema3；抽共享v4 live validator，明确新审批/授权要求current Master，已有授权历史package不retarget，但持续检验冻结来源/check/render/rights。图MCP未提供，仅限定相关文件回退读取；未用无关记忆结果作为项目证据。
- TDD先复现12失败/4通过，再统一接Freeze/Approval/Authorization/Package：schema分派有Master-FK防降级；准确Candidate/Master/context/provenance与冻结check行和最新pass均验证。审批和授权在flush后刷新复核，提交前撤权时Review/Target/Event回滚。
- 无Draft/Topic/Mother/Run的Text完整走通checks→freeze v4→approve→copy/manual authorize→ZIP，检查manifest、content.md、精确媒体和guide；Master、Candidate/hash不变，Review/Target绑定准确hash，不创建DeliveryAttempt。已有Media Adapter仅输出明确manual确认的精确render，不新增能力。
- 新增44项闭环回归通过，含rights/evidence/bytes/tamper三阶段拦截、重算hash后的Master/identity/render/check/schema伪造、最新failed检查、raw asset授权旁路、提交前回滚、幂等、退改、新Master/Brief后旧target冻结历史、重跑checks不改Candidate及两种media输出；既有Freeze回归也在最终全量覆盖。
- 按requesting-code-review检查清单做单Agent复核，当前无subagent工具，不标独立APPROVE。最终实跑712 passed/6既有警告（29.22秒，165项F6A回归），新临时SQLite迁移到f6a000000001；strict24/24、触及文件Ruff、diff-check全部通过。前端未改未复跑，开发/生产库未动，不引用旧build作为本轮验收。
- OpenSpec仅新增22项已验收勾选，当前114/214。PRODUCTION CORE BACKEND MILESTONE（无Draft的Text→local ZIP）通过；并发冻结完整验收、Review v4 preview/diff、Versions/Overview、Production Workspace及浏览器验收仍未完成。原始包/canonical未动，change不归档；仅本地main阶段提交，不push/deploy/生产迁移。
- 实际skills：using-superpowers、openspec-apply-change、receiving-code-review、writing-plans、executing-plans、test-driven-development、systematic-debugging、requesting-code-review（单Agent回退）、verification-before-completion。

## 2026-09-28：FE-F6A Adapter及v4后端继续实施

- 已核main4b5c7c9，52/214；继续已批准fe-f6a-production-core-content-master（spec-driven）。用户要求保持Adapter→Draft映射→纯builder→Freeze/Approval/package顺序，前端不启动。
- 使用using-superpowers、OpenSpec apply、receiving-code-review、writing-plans/executing-plans、TDD、verification-before-completion。图MCP仍未提供，限定相关文件回退读取；原始规格包、canonical和生产库不动。
- 已完成Adapter三形态契约与readiness：人工render需明确追加保存确认，由服务端绑定actor/精确input hash/output；全canvas覆盖，字节/MIME/实时权利、非render资产与证据输入变化均回归。Channel Registry只接受真实注册的video能力，不增加或推断新渠道。
- Draft seed校验冻结Workflow version/checksum与最新成功Attempt；真实document/markdown/structured与内容hash冻结，精确素材/证据映射，source pack无法证明或素材不可见时明确unmapped并使检查incomplete。相同seed动作重试回放已冻结内容，不读取后来变化的Draft替代它。
- 已独立实现candidates_v4：load frozen inputs与纯build_manifest_v4分离，实际Identity/Brief/Boundary/FactPack checksum、Master哈希、refs/checks/render、workflow/edit provenance及citations/declarations均冻结；JSON深拷贝和key-order/hash覆盖回归通过。
- v4 Freeze已替换临时骨架：强制expected_payload_hash；latest/current context/current checks/live refs/真实render闸门；提交前刷新复核hash，漂移时Candidate/Event一起回滚。手工Text无Draft/Topic/Mother/Run可冻结；Graphic/Video只有明确manual确认可冻结。重复调用一Candidate/一事件，跨owner/归档拒绝。
- 本轮任务实核92/214；Approval仍Draft-only、copy package仍schema-v3入口，下一轮必须独立v3/v4 dispatch。完整无Draft的Approval→local package里程碑尚未通过；不勾选并发冻结/审批/交付或前端任务。
- 阶段复核使用requesting-code-review检查清单，但当前没有subagent工具，实际是单Agent逐项代码/门禁复核，不标为独立APPROVE。复核新增exact evidence checksum更换后重跑不得pass的回归；Ruff和OpenSpec all strict24/24、diff-check已实际通过。
- 最终全量实跑668 passed/6既有警告（26.25秒，包含展示标题入hash后的最终代码），新增63项（Adapter28、seed7、manifest16、Freeze12），连同58项旧Master回归共121项。使用新迁移临时SQLite，不涉及开发/生产库；strict24/24、Ruff和diff-check均通过。前端未改未复跑，不引用旧build作为本轮验收。
- 实际skills：using-superpowers、openspec-apply-change、receiving-code-review、writing-plans、executing-plans、test-driven-development、systematic-debugging、requesting-code-review（单Agent回退）、verification-before-completion。仅本地main阶段提交，不push/deploy/生产迁移/canonical同步/归档。

## 2026-09-28：FE-F6A 后端不可变量继续实施

- 基线main eb1156c，已完成44/214。按用户复核的后端顺序推进，先不改前端；当前读取确认跨Unit生成素材被错误限制，Channel/content_form尚未校验，CAS尚缺共享锁。
- 使用OpenSpec apply、receiving-code-review、writing-plans/executing-plans、TDD及verification-before-completion；图MCP未提供，回退限定文件读取。门禁结果待本轮实际执行。
- 本轮先RED再GREEN封严：共享项目事务锁覆盖Master和Project/Unit/Brief/Boundary写入；提交前刷新上下文，expected_context_hash冲突409；旧fingerprint继续可重放。SQLite双连接测试验证同键一版本/一事件、不同键同head一成功一409，锁竞争及提交时Unit/Brief/Boundary漂移均回滚。
- ProjectWorkflowOutput按project而非消费unit校验，核验成功历史Attempt、插件/Run/checksum及实际字节；外项目、裸全局ID、失败Attempt和被替换字节均拒绝。Evidence检查覆盖整个边界（含未显式引用项）；rights检查回读hash/public/status/父素材归档；live变化使旧检查stale。Candidate-only历史纳入Archive保护。
- 定向58项（新增31项），任务仅勾选已闭合8项，当前52/214；完整Adapter、Draft映射/警告、v4 builder/Freeze/Approval/package仍未完成，不能宣称里程碑已通过。没有前端改动或canonical归档。
- 最终实跑：迁移后的新临时SQLite，全量605 passed/6既有警告（22.44秒，含58项Master回归）；触及文件Ruff通过；仓库根目录OpenSpec all strict24/24、git diff --check通过。前端未改，本轮未复跑build/budget，不用上轮build冒充本轮结果；PostgreSQL实库并发及完整v4端到端仍未验收。仅本地main阶段提交，不push/deploy/生产迁移。

## 2026-09-28：FE-F6A 阶段代码本地main整合（已完成，F6A仍在开发）

- 用户授权当前阶段代码整合到main，后续直接在主工作区main开发。仍按已确认OpenSpec实施，不另开隔离开发分支；发布、生产写入、canonical同步归档不随此授权自动开放。
- 当前基线main661e30a，F6A44/214；本次不是完成F6A，只整合已实现/已回归的阶段代码及标准change、计划和文档。
- 本轮使用using-superpowers、finishing-a-development-branch（阶段整合）、writing-plans（维护计划）、verification-before-completion。
- 分支阶段提交`7c2be75`已白名单提交并快进合入main，合入前后均574 passed/6既有警告；main全量22.73秒，前端build/FE-P1预算通过（projects224.68kB raw/72.86kB gzip），strict24/24、Ruff/diff-check通过。主规格未同步，active change仍44/214。
- main原有重叠文档/标准change可恢复备份保留于stash `cbee2d1e66dfdd083814e1acdf5fce22a690782d`；核对后无main独有内容遗漏，不把旧stash重新覆盖新进度。原始包/ZIP仍未跟踪且未改动。保留原隔离分支作为阶段快照，后续实际开发路径为主工作区main。

## 2026-09-28：FE-F6A apply（隔离工作树，进行中）

- 用户提供ChatGPT连接器实际读取证据：AIContentStudio main@661e30a、两份FE-F5C主规格和f5c000000001迁移均成功；业务代码前硬门槛解除。该证据来自用户转述的连接器读取，不冒充本地工具直连。
- 复用干净的托管工作树，从main@661e30a新建codex/fe-f6a-production-core-content-master；校准后的标准change及本轮计划/记录机械复制到隔离工作树，原始规格包和main未跟踪资料未改动。
- 本轮进入持久化/服务实施。禁止push、merge、deploy、生产迁移；canonical同步与归档另待授权。
- 隔离工作树复跑：临时SQLite迁移到f5c000000001，547后端测试通过、6既有警告；首次因本机继承的畸形NO_PROXY导致12项环境错误，限定NO_PROXY后全绿。前端TypeScript/Vite/FE-P1预算通过（/projects 224.68 kB raw、72.86 kB gzip）；OpenSpec all strict 24/24、diff-check通过。Ruff基线在既有content_projects.py和project_review.py有两处import排序告警，非F6A引入，后续只对改动文件门禁并整理触及的import。
- 本轮重新核对任务和实际代码，撤销未验收的过早勾选：当前44/214。已实现持久化基础、有界详情读取、请求幂等重试、父版本检查、不完整/stale投影、检查追加历史/最新结果/输入时效、Draft当前成功Attempt血缘验证；不把唯一约束等同完整事务锁，也不把v4入口等同完整候选链路。
- TDD：先复现回退删除历史、归档写检查、假schema/假来源、上下文漂移重试、空文稿/结构深度、缺失详情/父版本、冻结输入500、检查缓存旧pass及失效Attempt seed，再按失败证据修复。当前定向27 passed（2既有依赖警告）。此前40项/12项记录不作为当前完成证明。
- 尚未完成：共享事务锁/上下文CAS、完整嵌入引用和生成素材血缘、权利与renderer/attestation、完整v4冻结/审批/交付、读模型、前端与浏览器验收；PostgreSQL实库未验收。canonical、main及原始包未改动。
- 本轮实际skills：using-superpowers、openspec-apply-change、executing-plans、writing-plans（校正计划/记录）、test-driven-development、verification-before-completion。
- 本轮新鲜门禁：临时SQLite upgrade→downgrade f5c000000001→upgrade成功；全量574 passed/6既有警告（21.22秒），包含27项F6A定向测试。前端TypeScript/Vite/build与FE-P1预算通过，/projects 224.68kB raw/72.86kB gzip；OpenSpec all strict24/24、触及文件Ruff、diff-check通过。前端本轮无功能改动，该build不代表F6A前端验收。

## 2026-09-28：FE-F6A apply 前置核验（授权，等待连接器证据）

- 用户明确授权进入apply；上一回合启动后被中断，未执行代码命令。本回合重新核对本地main `661e30a`、F5C archived、两份canonical与只读Alembic code head `f5c000000001`，OpenSpec 4/4产物齐备、214项实施任务未开始。
- F6A规格把ChatGPT连接器实际读取post-F5C main/主规格/迁移列为业务代码前硬门槛；本地git/bridge状态不能替代该证据。当前工具未提供合规的连接器端workspace_info调用，已请求用户在现有ChatGPT对话中实际读取并反馈。未创建工作树或修改业务代码。
- 在隔离临时SQLite `/tmp/aicontent-f6a-baseline-zkSC1c/studio.db` 上启动本地基线回归；不会运行生产迁移。OpenSpec all strict24/24和diff-check已通过，后端/前端结果待回收。
- 基线结果已回收：隔离SQLite迁移到f5c000000001；后端547 passed、6既有警告（22.23秒）；TypeScript/Vite/build与FE-P1 bundle预算通过，/projects 224.68kB raw/72.86kB gzip，Assets257.70kB、Settings229.76kB initial；strict24/24和diff-check通过。
- C2C本地status仅表明桥接进程在运行，近期bridge日志不包含post-F5C的ChatGPT侧workspace_info读取证据。当前缺少合规的ChatGPT端读取结果，因此按F6A硬前置停在业务代码前；无测试代码/业务代码、无工作树切换。
- 本轮实际skills：using-superpowers、openspec-apply-change、executing-plans、using-git-worktrees、test-driven-development、verification-before-completion；codex-with-chatgpt已检查但当前未通过其页面发送消息。

## 2026-09-28：FE-F6A 规格审计与归位（SPEC REVIEW通过，未apply）

- 用户确认本轮仅审计、调整和标准归位；apply仍需用户确认，不由代理自行授权。
- main实际为661e30a，FE-F5C五份canonical及归档已可在本地读取。外部ChatGPT connector是否已看到新提交尚未证实，不以本地读取冒充connector验证。
- 本轮skills：using-superpowers、writing-plans、openspec-propose、verification-before-completion。代码图MCP工具未提供，代码发现仅在相关服务范围内回退搜索。
- 标准change已生成：完整读取原稿proposal/design/tasks/五规格，四份MODIFIED保留canonical全文块。补Master-only历史、pinned身份而非latest、原子幂等/CAS、render输入hash及显式手工确认、最新检查权威、失败旧output拒绝、legacy schema/权限、v4远端能力和回退预检边界；业务代码及canonical未修改。
- 首轮全量strict实际24 passed/0 failed、diff-check通过；4/4产物done代表规格齐备，不代表业务实现完成。独立整包/计划审计进行中。
- 独立整包/计划复核发现旧F4冻结要求仍无条件强制Draft/Run，已拆为v3/工作流v4血缘校验与手工v4 Master所有权/上下文/引用/渲染闸门，并增加无Run手工Master可冻结场景；待复核确认。当前214项实施任务，未apply。
- 独立最终完整SPEC/plan复核APPROVE：上述冲突闭合，无剩余实质矛盾；批准仅规格/计划，不代表apply授权或connector验证。最终实跑全量strict24/24、diff-check及保留核验通过：23原要求标题/203原任务完整保留，10完整canonical块/33旧场景保留（4处兼容文字校准）。
- 标准proposal/design/tasks/五规格4/4产物齐备，214项实施任务0完成；原始目录与ZIP保留，canonical/业务/测试代码未改。文档未提交，未迁移/push/deploy/归档；等待用户apply及定向测试代码确认和真实connector基线证据。

## 2026-09-28：FE-F5C 五份主规格同步归档（通过）

- 基线main ac6d4dc含7956273功能提交；已跟踪文件干净，原始包/ZIP继续保留且排除提交。
- 已核对OpenSpec产物4/4 done、任务95/95；用户授权全部五份主规格同步、归档和本地提交。
- 仅文档收尾，不复跑与本轮改动无关的业务测试，不push/deploy/生产迁移；547测试/build为上轮实际证据，本轮重新运行规格保留检查、strict和diff-check。
- 本轮实际skills：using-superpowers、writing-plans、openspec-archive-change、verification-before-completion。
- OpenSpec CLI已同步五份主规格：新增system-assets-knowledge、product-settings（20项要求），更新FE-F0/F1、FE-F2、FE-F3A（4项要求），删除0项。归档路径 `openspec/changes/archive/2026-09-28-fe-f5c-system-assets-knowledge-settings/`，active change已不存在。
- 逐块核对24项delta要求与canonical完全一致；ac6d4dc中的22项既有要求和92个既有场景保留，未修改要求逐字保留。两个新增Purpose已补正式说明，修正归档工具生成的三个EOF空行。
- 归档后全量OpenSpec strict实际23 passed/0 failed、git diff --check通过；仅五份主规格、归档移动和四份记录进入本地提交。业务代码、原始包/ZIP、开发/生产数据库不变，没有push/deploy/生产迁移。

## 2026-09-28：FE-F5C 本地main整合（通过）

- 用户明确授权“融入main分支”；本轮仅本地提交/合入，归档与主规格同步仍待单独授权，不push/deploy/生产迁移。
- main及实现分支同在49d6c4b；四份根文档、标准change与计划逐项比较完全一致，主工作区没有业务代码差异。使用限定路径stash保留重叠资料后快进，不恢复旧记录覆盖新状态。
- 合入前后门禁使用新临时库/tmp/aicontent-f5c-main-integration-GvoX7B/studio.db，真实开发/生产库不变。工作树保留供F5C规格归档使用。
- 本轮实际skills：using-superpowers、writing-plans、finishing-a-development-branch、verification-before-completion。
- 功能提交 `79562731f4157bce74d7dab4c39a59f0c1f4a7e7`，36份白名单文件；本地main从49d6c4b快进合入，无冲突。原始包和ZIP仍未跟踪且未进入提交，canonical规格未修改，F5C change仍active。
- 合入前实跑547 passed（22.34秒）；合入main后复跑547 passed（20.96秒），均6既有警告。主工作区TypeScript/Vite build、bundle预算、OpenSpec all strict22/22、定向Ruff与diff-check全部通过；projects224.68kB raw/72.86kB gzip，Assets257.70kB、Settings229.76kB initial。
- main重叠资料已限定路径可恢复保存于stash `fcbbd3ed9db0c4db2f287a96e2cf17108c142e45`（fe-f5c-main-pre-integration-owned-docs）；内容已随功能提交合入，不重复apply旧文档覆盖当前进度。实现工作树和分支保留供后续主规格同步与归档，未push/deploy/生产迁移。

## 2026-09-28：FE-F5C apply 验收通过（隔离分支，未提交）

- 标准change：openspec/changes/fe-f5c-system-assets-knowledge-settings/，95/95完成；五份delta保留旧要求/场景，源包/ZIP未动，canonical尚未同步归档。
- 基线49d6c4b；业务代码仅在codex/fe-f5c-system-assets-knowledge-settings隔离工作树。main本轮只有标准规格与计划/记录变更，未合入业务实现。
- 已落地KnowledgeCollection/Item、f5c000000001、SQL有界Library/授权Usage、安全Settings投影、Assets五标签、Settings六分区、精确项目引用与显式Frozen FactPack边界；无新运行依赖或第二套Asset/Registry。
- 最终实跑：547后端测试通过（24.04秒、6既有警告）；TypeScript/Vite build与bundle门禁通过。Assets257.70kB、Settings229.76kB initial，无TipTap/XYFlow；projects224.68kB raw/72.86kB gzip。OpenSpec all strict22/22、定向Ruff（含models/main/既有引用接口）与diff-check通过。
- TDD首轮Library26 RED→33 GREEN；Settings最终53、Library+F3A最终51测试。临时SQLite迁移up/down/up、约束/并发单赢家及PG DDL编译通过；未实测PostgreSQL数据库并发。
- 独立完整SPEC/plan、Assets与Settings SPEC/QUALITY均APPROVE。闭合危险legacy库存admin权限、URL查询允许列表及地址重新输入、成员snapshot revision绑定、所选精确素材撤销回读/确认重置、Source sha256及后端撤销引用闸门。
- 隔离浏览器：集合CRUD/解除重启用/完整重排/刷新持久化；另一操作更新→旧UI409→显式刷新保留新备注；archive13只读。Source/固定素材版本项目引用、冻结包明确边界、真实PNG字节按需预览通过；撤销后固定原ID且权利/确认/引用禁用。
- 六设置分区和断连Plugin理由、只读Channel、Rule/Template区分、开发Header说明回读；viewer模型工具禁用、legacy入口拒绝。仅临时库用户样本，无真实配置/密钥保存、外网模型/Connector/发布调用或CLI配置写入。
- 临时库/tmp/aicontent-f5c-browser-mYr3Ek/studio.db；验收后停止自建API18106/Vite15186。测试PNG仅存隔离工作树忽略media；原开发/生产数据库不变。
- 实际skills：using-superpowers、openspec-propose/apply-change、writing-plans、executing-plans、using-git-worktrees、dispatching-parallel-agents、test-driven-development、receiving/requesting-code-review、systematic-debugging、verification-before-completion。用于先规范、隔离、失败证据与独立复核，不扩展发布权限。
- 待单独决定：canonical同步归档、本地commit/main整合。当前无commit/archive/merge/push/deploy/生产迁移；本地验收不是生产准入。

## 2026-09-28：FE-F5C 审计与隔离开发启动

- 实施首轮门禁：539后端测试通过（24.01秒、6既有警告），build/bundle通过，Assets255.74kB、Settings229.76kB initial，projects224.68kB raw/72.86kB gzip；strict22/22、定向Ruff/diff通过。旧F5B测试改为验证自身迁移版本，避免把旧切片写死成永远最新head。
- Settings独立SPEC通过；QUALITY发现少见URL凭据参数遗漏，已用version/api-version允许列表关闭，定向53测试通过，待独立复核。危险legacy库存新增服务端admin读取和前端入口闸门。
- Assets独立SPEC通过；QUALITY发现成员快照和父revision独立刷新、所选素材撤销回读两项竞态及Source sha256字段不齐，正在定点补齐。浏览器已实际完成集合创建/条目保存/解除与重启用、Source及精确素材项目引用、显式Frozen FactPack边界；六设置分区已回读。

- 用户明确授权完整规格review、标准归位及开发，另明确授权定向回归测试；无推送、部署或生产迁移权限。
- 真实main49d6c4b包含F5B归档与两份canonical；code migration head f5b000000001。复用干净工作树 `/Users/mshengran/.codex/worktrees/fe-f3b-content-identity/AIContentStudio`，新分支 codex/fe-f5c-system-assets-knowledge-settings 从main开始。
- 标准change已生成：五份delta，两份新增转换为ADDED格式、三份MODIFIED按完整canonical块保留旧要求/场景。补使用情况所有权、集合revision/归档竞态/排序、SQL有界筛选、false/NULL/撤销权利、安全Settings allowlist与角色能力、Assets/Settings首包门禁。源包及ZIP未更改。
- 首轮change strict及diff-check通过；独立Settings契约复核进行中，尚未修改业务代码。
- 隔离基线已实际完成：SQLite迁移到f5b000000001，pytest457 passed/6既有警告（19.12秒），前端build/bundle通过，/projects215.21kB raw/70.15kB gzip。标准全量strict22/22通过。
- Using change: fe-f5c-system-assets-knowledge-settings；OpenSpec apply为ready、93项任务。完整源包与五份规格已审查，校准不改变产品范围。按用户审查后开发授权进入apply；Assets后端与前端采用不重叠写集，Settings独立复核继续收严真实API边界。
- 独立完整SPEC/plan复核PASS：原始包要求保留，三份MODIFIED旧块完整，五份规格和实施计划一致。独立Settings反馈经代码核实补入11.7/11.8，当前95任务；冷启动Rule、版本动作、完整模型快照与显式文件/网络副作用已锁定。
- 前端两路由lazy与named budget检查先加失败断言：旧manifest实际失败“SystemAssetsKnowledgePage不是lazy route”；随后实现ProductSettingsPage安全六分区和显式按需配置工具。Library后端/Collection、Settings投影和Assets前端分不重叠写集实施，主控负责集成与验收。
- skills：using-superpowers、openspec-propose、openspec-apply-change、writing-plans、executing-plans、using-git-worktrees、dispatching-parallel-agents、test-driven-development、verification-before-completion、requesting-code-review；并行子任务仅限不重叠写集。

## 2026-09-28：FE-F5B 同步归档（通过）

- 当前真实基线 main `6452ad2` 已含功能提交 `9e0ce04`；tracked/staged/unstaged 干净，用户原始包/ZIP继续保留并排除提交。
- 归档前四项产物均 done，任务94/94；用户已授权全部六份主规格同步、归档和本地提交，不推送、部署或运行生产迁移。
- 本轮只修改规格和文档；457后端测试及前端build为上轮实际门禁，本轮重跑归档后的全量 strict、规格保留检查和 diff-check。
- 实际skills：using-superpowers、openspec-archive-change、writing-plans、verification-before-completion。
- OpenSpec内置archive实际同步六份：新增19项要求、更新4项、删除0项；归档路径 `openspec/changes/archive/2026-09-28-fe-f5b-performance-learning-memory/`。逐块比较全部delta与canonical一致，未修改的既有requirement逐字保留；Identity旧占位场景仅明确为pre-F5历史行为。
- 两份新增Purpose已补正式领域描述，修正归档工具生成的四份EOF空行；归档后全量strict实际21 passed/0 failed，git diff --check通过。仅规格及四份任务文档进入本地提交，原始包/ZIP继续未跟踪，不重跑业务测试，不推送、部署或生产迁移。

## 2026-09-28：FE-F5B 本地main整合（通过）

- 功能提交 `9e0ce04b8d076935e9b8182ce8154eb6e235e31d`，36份白名单文件；本地main从dd71a14快进到该提交，无业务冲突。
- 合入后从主工作区实际复跑：后端457 passed/6既有警告（17.64秒）；前端TypeScript/Vite/bundle PASS，/projects215.21 kB raw、70.15 kB gzip，Learning252.12 kB；OpenSpec strict20 passed/0 failed，工作区与提交diff-check PASS。测试使用隔离数据库 `/tmp/aicontent-f5b-regression-A7jHoA/migration.db`，没有改动开发或生产数据库。
- main原重叠审计资料限定路径保存于stash `756ed20db1f8dc29a5ad43e370b5f48b5c46bf50`（fe-f5b-main-pre-integration-owned-docs），其中独有SPEC审计段已整合到当前文档；标准规格除任务完成状态外一致，计划仅授权checkbox更新。备份仍保留，不重复apply旧状态造成文档/任务倒退。
- 用户原始包/ZIP仍原样未跟踪，没有进入36份提交；canonical `openspec/specs/` 与dd71a14完全一致，FE-F5B change仍active，未执行archive。保留实现工作树供后续规格收尾，无push/merge远端/deploy/生产迁移；只完成用户授权的本地main合入。

- 提交前本轮实际复跑：后端457 passed/6既有警告；前端build/bundle通过，/projects 215.21 kB/70.15 kB gzip，Learning252.12 kB；OpenSpec strict20/20及diff-check通过。标准包两边仅tasks完成状态不同，实施计划仅授权checkbox不同，其他规格内容一致。

- 用户已明确选择先将代码融入main，按分支收尾技能执行本地commit→快进→合入后门禁；不获取/推送远端、不部署或生产迁移。
- 主工作区四份重叠文档属于本任务审计与执行回链；独有SPEC审计段已保留到实施分支。用户原始包/ZIP继续排除，仅限定本任务路径备份与提交。
- 本轮skills：using-superpowers、writing-plans、executing-plans、finishing-a-development-branch、verification-before-completion。用户已选择本地合入，无需重复询问四种选项；工作树供未归档变更继续使用，不清理。

## 2026-09-28：FE-F5B apply启动

- 验收后已关闭本轮临时Chrome页并停止自建API18105/Vite15185；未停止用户原有服务。隔离数据库保留用于追溯，未删除数据。OpenSpec apply实际返回all_done、94/94，最终diff-check通过。

- 文档和94/94任务更新后的最终规格门禁：OpenSpec全量strict20 passed/0 failed，git diff --check通过。主工作区仅补执行回链，业务实现依旧在隔离分支。

- FINAL IMPLEMENTATION/REVIEW PASS：OpenSpec实施94/94。实际最终全量457 passed、6条既有警告；前端TypeScript/Vite及bundle通过，/projects 215.21 kB raw /70.15 kB gzip，Learning 252.12 kB initial，无重型编辑器。相关15份Python文件Ruff通过，最终文档后的strict/diff-check另复跑。
- 独立SPEC复审：历史/持久化/Receipt通过（63定向测试）、Learning通过；独立QUALITY复审后端与前端均APPROVE。质量反馈实际修复：AuditLog清理后恢复幂等仍受永久历史provenance保护；归档与观察写入用owner/active条件锁；异常嵌套引用在ORM前422；旧accepted只读派生可信可提升声明，不修改历史checksum/revision。
- 浏览器隔离验收完成：外部历史#1无发布时间/身份时诚实显示未知；Studio回收#2→80阅读观察#2→Insight#2→候选#2支持证据→人工accepted→角色#1记忆#1修订1。刷新身份Memory可见来源候选及single_sample/仅限隔离单样本限制；身份仍v1。DB实际readback：2条历史、1条Receipt、1条Memory/Revision、1条PersonaRevision、1条publication事件。Home已验证ready候选待办与accepted后消失。
- 本地Studio候选/目标为明确test_fixture，仅检验本地事务、浏览器和血缘，不代表真实平台发布。临时SQLite已验证升级/回退/升级、PostgreSQL方言DDL与驱动冲突注入；未实测PostgreSQL服务并发、生产迁移或真实Connector。
- 本轮实际skills：using-superpowers、openspec-apply-change、writing-plans、executing-plans、using-git-worktrees、subagent-driven-development、dispatching-parallel-agents、test-driven-development、systematic-debugging、receiving-code-review、requesting-code-review、verification-before-completion。Skill要求推动了隔离、失败优先回归、先SPEC后QUALITY复核；归档技能未执行。
- 代码尚未暂存/提交/合并/推送/部署；六份主规格同步和archive按已确认任务边界等待单独授权。用户原始规格包与主工作区无关文件保持不变。

- 最新实际门禁：437后端测试通过（6条既有警告）；前端build及bundle gate通过，/projects 215.21 kB raw /70.15 kB gzip，Learning 252.12 kB initial JS，无TipTap/XYFlow。后续契约补丁完成后仍需最终复跑。
- 浏览器项目回收发现未注册delivery.publication_confirmed事件，先补失败回归再注册事件；历史17项回归通过，浏览器现已真实保存Studio历史#2，发布时间未知仍未补成回填时间。
- 第二轮历史复核补幂等重试前当前状态/候选哈希/Receipt检查；超出分析上限coverage必须unknown而非missing，已补断言。学习验证已浏览器保存accepted，但可提升声明投影尚需后端/前端对齐后才能完成晋升。

- 用户确认校准规格及定向回归测试，使用change `fe-f5b-performance-learning-memory`，spec-driven，94项待实施。
- 复用已清洁且无需继续F5A开发的现有工作树，分支`codex/fe-f5b-performance-learning-memory`从main `dd71a14`开始；原始包与主工作区规格审计改动保留。
- 本轮不push/merge/deploy/生产迁移；主规格同步、归档和提交继续按tasks等待收尾授权。计划中的执行步骤采用`///`；先验证持久化测试失败，再实现。
- 基线实际复跑346后端测试及前端build/bundle通过。七资源模型与迁移先写失败测试，再实现通过；隔离临时SQLite升级→回退f5a→升级成功，当前head f5b000000001。
- 历史导入、快照最新值、同窗口修正与Home学习待办首批4项回归通过；时间窗口经UTC标准化比较，避免SQLite丢失时区后误拒绝修正。发布确认只回收有人工Receipt且可核实候选血缘的内容，回执提交时间不冒充发布时间。
- Skill驱动的并行实施按文件范围分离：Learning后端、Learning前端、Receipt兼容钩子；主流程维护历史/分析/Home/迁移与文档。仍在实现，不提前标记完整验收。
- 注册Learning正式路由后四个F5B测试文件71项通过；首轮全量实际424 passed，6条既有警告。此为中间结果，后续review修补后再复跑。
- 历史SPEC首轮7项边界修补：所有入库/查询时间统一UTC；数值修正不可变文字；大于10000观察明确不可计算不返回过期值；metric/key/unit/cutoff覆盖按实际选中观察计；日期缺失按同范围计；flush冲突整批回滚重试；恢复确认复用已有Receipt。补充granularity/cutoff及同目标反馈血缘，当前14项历史回归通过。
- 迁移历史回退再升级保留既有User记录且不自动创建发布历史；七资源DDL可按PostgreSQL方言编译，未实测PostgreSQL服务。Receipt worker完成新旧钩子与43项回归；全部原有路由测试亦通过。
- 前端SPEC通过，发现冻结证据数读取层级错误，正在补；浏览器完成外部历史导入、刷新、追加150浏览快照、保存人工Insight和创建候选，完整验证/晋升/身份投影待收尾。
- Learning SPEC发现任意记忆新主张借用旧候选、锁顺序和嵌套Insight覆盖3项，已交由原owned worker按TDD修补。不要将中间绿灯视作最终验收。

## 2026-09-28：FE-F5B 规格审计与归位（SPEC_REVIEW_PASSED / 待确认apply）

- 当前真实基线 main `dd71a14`，F5A 归档与两份canonical存在；Alembic代码head为`f5a000000001`，未核对或迁移任何生产数据库。
- 标准提案位于 `openspec/changes/fe-f5b-performance-learning-memory/`，原始 `openspec/fe-f5b-performance-learning-memory/` 与ZIP不改。
- 已补四份MODIFIED完整旧契约、新规格ADDED格式；修正Receipt确认时间与实际发布时间区别、receipt-less reconciliation不合成发布、指标测量粒度和修正链、候选验证冻结、Memory所有写入口及并发/幂等闸门。
- 单项strict PASS，4/4 artifacts done仅代表规格完整，不代表实现完成。全量门禁与独立规格复核待完成；实施计划在`docs/superpowers/plans/2026-09-28-fe-f5b-performance-learning-memory.md`。
- 按项目OpenSpec规则，在这份校准proposal获得明确确认前暂停apply；未创建业务实现、测试代码、迁移或提交，不push/merge/deploy。计划中的定向测试仍待apply授权。
- 独立规格复核首轮指出receipt-less reconciliation缺恢复入口；当前代码对账后目标human_confirmed，而两个Receipt API均拒绝此状态。已在spec/design/tasks/plan补显式confirm-reconciled人工确认动作及原子/幂等/权限/无远端副作用边界，等待针对性复核。
- 针对性复核最终APPROVE，该恢复入口问题已关闭，首轮其余边界无新增发现。校准后`openspec validate --all --strict`20/20 PASS，diff-check PASS；源包10/10文件未变，四份MODIFIED完整旧块保留（旧Memory占位明确为历史场景）。94项实施任务未执行，主规格未同步、未归档、未提交，业务代码未改。
- requesting-code-review安排独立只读复核，receiving-code-review核对代码证据并修正一项规格缺口；reviewer已关闭。下一步仅等待用户确认这份校准proposal及其定向回归范围后apply。
- 本轮实际skills：using-superpowers、openspec-explore、openspec-propose、writing-plans、requesting-code-review、verification-before-completion。explore用于只读审计，propose用于规格归位；writing-plans安排独立复核；不将严格校验等同于业务验收。

## 2026-09-28：FE-F5A 六份主规格同步与归档

- 用户已明确授权同步全部六份 canonical specs 并归档；当前 main `682df71`，4/4 产物与17/17任务完成。
- 本轮仅处理规格与收尾文档，核对旧契约保留后本地提交，不推送、部署、生产迁移或实施 FE-F5B。
- `openspec archive fe-f5a-home-opportunity --yes` 已同步全部六份主规格，报告 +11 / ~10 / -0 / rename 0，归档目录为 `openspec/changes/archive/2026-09-28-fe-f5a-home-opportunity/`，17/17任务完整。工具提示建议拆分超过10条delta，属于已完成切片的非阻塞建议。
- 已逐块验证21个delta与canonical一致、四份旧主规格全部37个旧要求及场景正文保留；新增两份 Purpose 已补正式说明。首次 strict 19/19 通过，diff-check发现工具生成的四处EOF空行，已修正，最终校验待复跑。
- 修正后的最终门禁：`openspec validate --all --strict` 19 passed / 0 failed（18份主规格及1个既有active change），`git diff --check` PASS。本次仅规格和文档变化，不重复执行已在main验证的346项业务测试与前端构建；待提交本地main，未推送、部署或运行生产迁移。
- 本轮实际 skills：using-superpowers、openspec-archive-change、writing-plans、verification-before-completion。归档 skill 用于完整性和同步检查，按明确授权使用 OpenSpec CLI 同步并归档；未新增业务或测试代码。

## 2026-09-28：FE-F5A 本地 main 整合

- 用户授权合入本地 main；已核对主工作区 main 与隔离分支共同基线 `2f52053`，主工作区无已跟踪改动，原始规格包保留。
- 功能提交 `3012fe5`（30 个本任务文件）已从 `codex/fe-f5a-home-opportunity` 快进合入主工作区 main；未将用户原始规格包加入提交。
- 提交前及合入 main 后均实际复跑：346 后端测试通过（6 条既有警告）、前端 TypeScript/Vite build/bundle gate 通过、OpenSpec all strict 18/18 通过、diff-check 通过。测试只使用已迁移的隔离临时库。
- 六份 delta 同步与归档仍待确认；未推送、部署或运行生产迁移，保留隔离工作树用于后续收尾。
- 本轮实际 skills：using-superpowers、writing-plans、finishing-a-development-branch、verification-before-completion；没有新增业务实现或测试代码。

## 2026-09-28：FE-F5A apply（IMPLEMENTED / REVIEW_PASSED，待归档确认）

- 基线：main `2f52053`；业务改动仅在隔离工作树、`codex/fe-f5a-home-opportunity`。
- 已实现 Opportunity、Signal、AssessmentRevision、Conversion，复用 AuditLog 和 ProjectEvent；转换不创建 Topic / FactPack / Fact Boundary / IdentitySnapshot。
- 首轮回归暴露并修正失败锁事务残留、Brief scope 类型检查、首页机会先截断后排序；独立复核补齐旧项目 unknown 不可遗漏与真实近期活动。
- 临时库 `/tmp/aicontent-f5a-yDS9qM/migration.db` 升级→回退→升级通过，head `f5a000000001`。初始迁移使用当前 metadata，新增迁移沿用既有幂等建表策略。
- 当前全量后端 331 passed（指定上述已迁移临时库，避免既有 worker 测试访问空默认数据库）；OpenSpec strict 18 passed，diff-check 通过。最终批量投影改动后须重跑，不将当前结果当作最终门禁。
- 浏览器实际完成新建机会、人工信号、评估 v1、qualified 转项目及刷新；项目 Brief v1、来源机会回链存在，Overview 为 evidence_needed。
- 最终门禁：346 后端测试 passed（含 15 F5A 领域测试和 13 批量投影测试）；前端 TypeScript/Vite build/bundle gate PASS；OpenSpec all strict 18 passed；Ruff 定向检查及 diff-check PASS。既有 6 条弃用/SQLAlchemy 警告未扩展修复。SQLite 独立 Session 并发回归通过，未进行 PostgreSQL 实测。
- `/projects` 首包 215.09 kB raw / 70.12 kB gzip，Home 231.11 kB、Opportunity 247.32 kB raw；三个入口均不包含 TipTap/XYFlow。
- 后端独立复核 APPROVE；前端两项阻断（Brief 身份对象损坏、HTTP LAN UUID 缺失）已关闭，前端最终 APPROVE。身份 Brand-only 转换后只改目标的 Brief v1→v2 实际浏览器保存/刷新验证通过，身份对象不变。UUID native/fallback 与稳定重试 key 已定向验证，未实际部署 LAN。
- Home 全部自有活动项目按 100 个批量扫描决策，近期卡片独立限额20；不读取历史候选/回执全文，实时证据/媒体权利门禁复用并回归。近期活动是真实 ProjectEvent。
- OpenSpec 17/17 apply 任务完成。四份 MODIFIED delta 已补成保留既有要求/场景的完整块，修正 Unknown 标题匹配，避免将来归档覆盖旧契约；canonical specs 尚未同步。归档同步问题已发给用户，等待确认。
- apply 收尾时未归档、未提交业务改动、未推送/合并/部署/生产迁移；随后本地 main 整合结果见顶部记录。临时验收服务已停止，临时数据库保留在隔离路径以便追溯。
- 本轮实际 skills：using-superpowers、openspec-apply-change、writing-plans、executing-plans、subagent-driven-development、test-driven-development、systematic-debugging、requesting-code-review、receiving-code-review、verification-before-completion；openspec-archive-change 完成同步评估并要求暂停等待用户确认，未执行归档。

## 2026-09-28：FE-F5A-SPEC-R1（规格修订完成，未 apply）

- 已核对 review 指出的 6 项阻塞与 2 项补充项，确认均适用于当前 OpenSpec。
- 已补充 Opportunity `converted/archived` 状态闸门、合法 triage/reopen、Assessment `expected_revision`/409/race/无部分提交、AuditLog 与 ProjectEvent 分工、Signal 派生来源类型、Home 排序/决策优先级/去重，以及核心投影失败的 `incomplete/section_errors` 语义。
- 已将 proposal 的 Modified Capabilities 补齐 FE-F0/F1、FE-F3A、FE-F3B、FE-F4；tasks 改为要求定向自动化回归。
- `openspec validate --all --strict`：18/18 通过；`git diff --check`：通过。
- 仍未执行业务代码 apply、数据库迁移、推送、部署或生产写入；状态为 `SPEC_R1_READY`，等待独立确认后再授权 apply。

## 2026-09-28：FE-F5A Home + Opportunity 标准包审计（SPEC_READY，未 apply）

- 用户提供并解压标准包于 `/Users/mshengran/Project/AIContentStudio/openspec/fe-f5a-home-opportunity/`；原始目录保留不改。
- 已确认本地隔离工作树基线为 `85b8c08`，FE-P1 canonical spec 与归档变更存在；connector 仍需外部刷新确认，未把本地证据冒充 connector 已同步。
- 已将 F5A 新规格及 FE-F0/F1、FE-F3A、FE-F3B、FE-F4 四份 delta 归位到 `openspec/changes/fe-f5a-home-opportunity/`。
- 审计并修正一个语义差异：转换只允许用户明确选择的 SourceDocument signal 建立普通 ProjectSourceBinding，但绝不自动创建、冻结或绑定 Fact Boundary；自动分析能力不可用时不得伪造 Assessment。
- `openspec validate fe-f5a-home-opportunity --strict` 通过；`git diff --check` 通过。未修改业务代码、未执行迁移、未 apply、未推送/合并/部署。
- 下一步前置：connector 真实可读 FE-F4/FE-P1 最终基线后，才可执行 `/opsx:apply fe-f5a-home-opportunity`。

## 2026-09-28：FE-F5A Home + Opportunity 规格提案

- FE-P1 已在本地提交为 `85b8c08`，随后创建分支 `codex/fe-f5a-home-opportunity` 作为下一阶段规格基线；未推送、合并或部署。
- 已审计现状：`/home`、`/opportunities` 仍由 `ProductPlaceholder` 提供；项目 Overview 已能派生 Brief/Evidence/Identity/blocked/stale/review/delivery 风险；SourceDocument、DataSnapshot、ProjectEvent、Review、DeliveryTarget 均可复用。当前没有 ContentOpportunity、HomeTask 或调度实体。
- 已创建 `openspec/changes/fe-f5a-home-opportunity/`，包含 proposal、design、三份 delta spec 和 tasks。F5A 明确分为 Opportunity（三类持久对象、评估版本、显式转项目）与 Home（现有事实 Projection），不自动绑定 Evidence、不创建 Topic、不自动更新 Identity、不引入新闻抓取系统。
- OpenSpec strict 校验和归档前复核待完成；F5A 业务代码 apply 必须先确认 connector 能读到 FE-P1 `85b8c08` 和 canonical spec。

## 2026-09-28：FE-P1 主规格同步与归档

- 用户明确选择将五条 FE-P1 长期要求全部同步到主规格并归档。`openspec archive fe-p1-frontend-bundle-performance --yes` 报告 10/10 任务完成、5 added / 0 modified / 0 removed；新增 `openspec/specs/fe-p1-frontend-bundle-performance/spec.md`，归档到工具实际生成的 `openspec/changes/archive/2026-09-27-fe-p1-frontend-bundle-performance/`。已将自动生成的 Purpose TBD 改为正式契约描述。归档后全部 16 份主规格 strict 为 16 passed / 0 failed；前端 TypeScript/Vite 构建及预算通过（`/projects` 初始 JS 214.45 kB raw / 69.98 kB gzip），`git diff --check` 通过。没有提交、推送、合并或部署。

## 2026-09-28：FE-P1 apply

- 用户明确输入 `/opsx:apply`；在已有隔离工作树 `codex/fe-p1-frontend-bundle-performance`（起点 `6d1ecbb`）实施，不改本地 `main`。OpenSpec `spec-driven` 4/4 产物完整、10 项任务待做；详细步骤见 `docs/superpowers/plans/2026-09-28-fe-p1-frontend-bundle-performance.md`。本轮不推送、合并、部署或执行生产操作。
- Task 1.1 基线复跑：TypeScript/Vite build 通过，单 JS 1,095.28 kB（gzip 351.06 kB），CSS 48.52 kB；隔离 preview 对 `/`、`/projects`、演示/数字项目、生产、review、identity 与两条重型旧路由均返回 SPA HTML 200。该 HTTP 检查只证明直接链接服务回退，不等于页面交互已验收。端口 15176 已关闭。
- Task 1.2–1.4：真实项目列表、详情、生产 wrapper 与共享类型已拆成独立模块；`App.tsx` 现以 `React.lazy` 加载页面，并在保留 sidebar 的 route 区域显示状态/可重载错误。`npx tsc -b` 通过，静态导入检查显示项目列表不再连到七标签或生产设计器、详情不再连到生产设计器；浏览器交互见下方 Task 3.2。
- Task 2.1–2.3：正常 `npm run build` 生成 manifest 并执行预算脚本；按入口加 `/projects` 静态导入闭包去重后为 214.45 kB raw / 69.98 kB gzip（4 个 chunk），比 FE-F4 1,095.28 kB raw 基线低 80.4%；全站生成 JS 1,138.41 kB raw / 375.65 kB gzip，独立报告而非首包门禁。详情与生产 chunk 均不在项目列表静态闭包；构建时还从 Rollup module ID 生成重型模块归属表，明确 TipTap 只在 Workspace chunk、XYFlow 只在 Workflows chunk，预算脚本会拒绝它们进入 `/projects` 静态闭包。未设置 `manualChunks`。最新 `npm run build`（TypeScript + Vite + 预算）通过。
- Task 3.2：生产 preview 直接进入 `/`、`/projects`、数字详情/生产、`/review`、`/identities`、`/workspace`、`/workflows` 和非数字演示路径，页面模块均可加载；preview 无 API 代理，故数字项目真实内容仅在随后隔离 API 联调验收。慢网条件下可见有可访问状态的“正在加载页面…”且导航壳层保留；拦截 Workflows chunk 后出现错误说明/重载按钮，转回项目列表恢复。隔离临时 SQLite + 127.0.0.1:18083/15177 下创建项目 #1、身份 #1、文字单元 #1，进入生产保存 System 常量节点项目覆盖 v1、启动 Run #1 succeeded；刷新仍可见固定工作流 #1、Run #1 和冻结定义 checksum。验收服务已停止，仅含测试数据的临时 SQLite 已删除，未操作正式数据库。
- 首轮独立代码复核发现 `location.key` 会因 query-only 导航变化而重挂载整个页面；已改为按 `pathname` 重置错误边界，避免项目标签或 Review 筛选切换丢失本地状态。复核还指出仅排除路由 chunk 不足以证明重型依赖缺席；现已增加 Rollup module 归属门禁，构建证实 TipTap/XYFlow 分别位于 Workspace/Workflows。README 已更新；复核后的浏览器检查和最终记录仍待完成，不提前归档。
- 修正后已重新通过 `npm run build`（含 TypeScript/Vite/预算）、`openspec validate fe-p1-frontend-bundle-performance --strict` 和 `git diff --check`。生产 preview 再次验证演示项目同路径 `?tab=matrix` 标签切换；拦截 Workflows chunk 后错误说明/重载按钮可见，点击侧栏项目路由恢复。preview 无 API 代理时列表显示 `Not Found`，真实 API 联调结果以上述独立临时库为准。第二次独立只读复核正在进行。
- 第二次独立针对性复核已给出 `APPROVE`，没有新的高/中风险发现；复核者只读核对模块拆分、pathname 边界、重型依赖模块归属和现有构建产物，构建与浏览器复测由本轮直接执行。OpenSpec 10/10 任务均完成；后续同步与归档结果见本文件顶部。

## 2026-09-28：FE-P1 前端首包性能规格审计

- 用户授权审计 FE-F4 分支并提出 FE-P1 OpenSpec，未授权 apply。已在干净的 FE-F4 `2f3ced2` 上创建 `codex/fe-p1-frontend-bundle-performance` 与标准变更目录。
- 重新运行 `npm run build`：JS 单文件 1,095.28 kB（gzip 351.06 kB），CSS 48.52 kB；`App.tsx` 静态加载全部现有/旧页面，`PersistentProjectPages.tsx` 同时承载列表、详情、生产并静态加载 `ProductionDesigner` 和七标签。当前 web 包无独立测试脚本；规格和门禁待完成。
- FE-P1 proposal、design、新能力 delta spec、tasks 已按 OpenSpec `spec-driven` 顺序写入；范围为路由/项目生产边界、初始 JS 预算、可恢复加载与路由冒烟；不含业务代码或后端变更。规格验证与独立复核待执行。
- `openspec validate fe-p1-frontend-bundle-performance --strict` 通过；OpenSpec 状态 4/4 artifacts complete，JSON 回读确认 5 条 ADDED 要求与对应场景均被解析。`git diff --check` 通过；仅提案、README、任务/进度/发现文件发生变化。独立复核未执行，不将 strict 校验称为正式 review；等待用户确认后才进入 apply。

## 2026-09-28：FE-F4 apply 启动

- 用户明确选择五份 delta 全部同步主规格。归档前比对四份 MODIFIED 的 9 条要求、28 个旧场景标题全部保留；`openspec archive fe-f4-project-review-distribution --yes` 报告新增 11 条、修改 9 条、删除 0 条，归档实际路径是 `openspec/changes/archive/2026-09-27-fe-f4-project-review-distribution/`（工具使用宿主机日期）。新增主规格的机械 Purpose 已改成正式产品契约说明。归档后五份主规格保留 delta 与旧契约，全体 15 份主规格 strict 校验 15 passed / 0 failed，`git diff --check` 通过；本地提交待执行。
- 归档后重新隔离运行后端全量 318 passed / 6 warnings，前端构建通过（主包 1,095.28 kB 警告）。此前 FE-F4 定向 8 passed、Ruff F 通过；`openspec status` 四类产物均 done，tasks 57/57 勾选。未推送、合并、部署或运行生产迁移。
- 独立复核最终一项（历史 Candidate 裸审批）已确认关闭，无剩余高风险问题。FE-F4 OpenSpec 任务现全勾选；非 Draft v3 包回归实际检查 PNG 字节和正确素材文件名，定向 8 passed。OpenSpec strict、`git diff --check`、本次后端 Ruff F 通过；最终后端全套正在复跑。五份 delta 同步主规格的归档选项已向用户确认，回复前不归档。
- 二次独立复核仅剩历史 Candidate 仍可从裸审批 API 再次批准或退改；现已按当前 Candidate ID 在服务端同时封住 approve/request-changes，并增加历史候选负例。定向 FE-F4 8 passed；复核最后一项正在回读。前端 build 和上一轮后端全量均通过，最终全量需在最后改动后复跑。
- 独立代码复核首次指出四项阻断：旧项目 Draft 素材裸 ID、Unknown 普通回执绕过对账、历史 Candidate 新增授权、批准后前端详情不刷新。现分别补上共享 Project Run 所有者闸门（覆盖旧 Draft/Job/素材/检查/文档/Discoverability）、Unknown 回执拒绝并要求对账、当前 Candidate 判定、审批后重取详情。定向 FE-F4 7 passed；第二轮独立复核进行中。修后全量后端 317 passed / 6 warnings，前端 build 通过；新增更细断言后定向 7 passed。归档/提交仍未执行。
- 最终门禁首轮复跑：隔离 SQLite 全量后端 317 passed / 6 warnings；前端 TypeScript/Vite build 通过（1,095.18 kB 主包警告）；FE-F4 OpenSpec strict 与 `git diff --check` 通过。旧 article-handoff 与通用 DeliveryTarget 授权入口已调整为先核验项目所有者再返回状态，避免跨项目状态探测。独立代码复核已发起；尚未归档/提交。
- FE-F4 浏览器门禁补齐：隔离验收库（与用户当前服务分离）依次验证 Blocked 无 Draft 输出时 Freeze 禁用、Unknown 展示人工对账且无重发按钮、更新 Candidate 后旧 Unknown 不覆盖当前 Stale、Stale 当前候选 Approve/Authorize 禁用、历史 Candidate 仅显示只读提示。首次鼠标 click 自动化未切换 tab，改用真实键盘 Enter 后交付 tab 控件与状态均在可访问树中核验；此非产品逻辑错误。临时浏览器页与 18082/15175 服务已关闭。验收库内造数仅用于 UI 状态，不当成真实 Freeze→Approve→Delivery 业务验收；真实链路由后端集成测试覆盖。
- FE-F4 第五批：独立临时 SQLite 上后端全量 317 passed / 6 warnings；另一独立临时库 Alembic 从空库升到 `f4a000000001`、退回 FE-F3B、再升 FE-F4 均通过。隔离 127.0.0.1:18082/15175 浏览器验证 `/review` 可显示真实项目/单元受阻状态；在隔离验收库注入待核对目标后，页面可见 `unknown` 与“先对账、不可自动重发”说明。交付标签点击的 UI 自动化未产生状态变化，浏览器交互门禁尚不算通过；不会把截图/页面加载误报为完整交互验收。OpenSpec strict、diff-check 通过；任务 4.4、5.4、8–9 仍待收口。
- FE-F4 第四批：`/review` 从 placeholder 改为真实项目审核页，分项目/单元、状态筛选、候选预览/变更/检查/交付四栏，区分 Freeze、审批、授权、ZIP、人工作业回填与 unknown 对账；历史 Candidate 的交付操作隐藏，自动草稿因无已验证账号映射不开放。项目 Overview/Versions 接入相同审核投影，旧 `/review-publish` 未改。前端 TypeScript/Vite build 通过（bundle 1,095.18 kB，原有体积警告）。服务端额外封闭已批准候选的退改状态歧义，ZIP 下载本身推进待人工回填，并按实时 FactPack item 权利检查交付（避免 ORM 关系缓存掩盖撤权）；FE-F4/F3A/delivery 定向 28 passed。浏览器验收与最终全量门禁未完成。
- FE-F4 第三批：Project Review Center 新增项目/单元/候选只读投影及 Candidate diff；状态只按当前 Candidate/Target 计算，旧 Candidate 的 unknown 不污染新候选，当前目标的 unresolved unknown 优先。旧 article-handoff 的 project-bound alias 已做所有者检查并拒绝混用 v1 包路径；旧 Topic Review read model 排除 project-bound run。冻结来源不能悄悄替换成同 Job 的较新 Draft；并发同 Project/Unit/hash 冻结有数据库唯一键与冲突回读。交付授权、结果、对账、回执开始与项目事件同事务记录。FE-F4 + delivery + review + v2 candidate 定向 21 passed。全量测试首次因本机 `NO_PROXY/no_proxy` 配置出现 13 个无关失败；去掉二者后为 316 passed / 1 个既有 worker 默认 SQLite 未初始化失败；已建立独立临时测试库供最终复跑，不改生产或主工作区。
- FE-F4 第二批：Draft-backed WorkflowOutput 可冻结 v3 Candidate，Freeze/Content Approval/退改分离；项目账号授权沿稳定 ContentAccount 键幂等。旧裸 `/assets` 的项目候选读取按所有者隔离，项目候选不能经旧素材增删/导出接口修改；匿名封面/媒体直链对项目候选关闭。项目 manual_handoff 已改走 v3 manifest 成品包（真实媒体字节与实时权限校验），随后可人工回填 Receipt；旧 v1 手工交付路径保持。定向 FE-F4 + delivery + v2 candidate 测试 17 passed。项目 Review Center 投影、前端、其他 raw-ID/alias 审计及全量门禁仍待完成。
- 持久化 1.1–1.4 完成：稳定 `authorization_account_key` 取代仅 `account_ref` 的唯一约束；同引用不同 ContentAccount 可分别授权、同账号幂等，引用改变须新授权版本。用旧 FE-F3B checkout 构造真实旧结构并插入 Asset/Review/Target/Attempt/Receipt，隔离库升级→回退→再升级后 5 类旧行及历史 account_ref 均保持，未伪造项目或账号链接。新建库往返亦通过。相关定向测试 10 passed。
- 首批模型与迁移：ContentAsset 新增 Project/Unit/IdentitySnapshot/Run 与独立 `candidate_hash` 字段；Review 可绑定 Candidate 且项目原生行可无旧 Draft；DeliveryTarget 增加 ContentAccount 和稳定授权账号键。隔离 SQLite 新建库往返通过；旧 delivery/review 与新 schema 定向测试 10 passed。此时稳定账号幂等及旧行往返尚待补齐，已由上一条闭合。
- 用户明确授权 FE-F4 apply；在隔离分支 `codex/fe-f4-project-review-distribution` 执行，不改本地 `main`。OpenSpec `spec-driven` 起点为 57 项、已完成 3 项基线任务；计划见 `docs/superpowers/plans/2026-09-28-fe-f4-project-review-distribution.md`。启动时业务代码、迁移和验收均未完成；本轮不推送/合并/部署/运行生产迁移。

## 2026-09-28：FE-F4 规格审计

- 后续本地主工作区 `main` 已从 `c044085` 快进到 FE-F3B `55eba02`。已核实 FE-F3B 四份主规格、`ContentAccount`/`IdentitySnapshot`、身份路由和迁移 head；隔离 SQLite 基线后端 310 passed、前端 build、14 份主规格 strict 均通过。连接器自身回读未验证；FE-F4 尚未 apply。
- 初审时主工作区 `/Users/mshengran/Project/AIContentStudio` 为 `1fa4520`，仅有用户提供的未跟踪 FE-F4/FE-F3B 来源包；当时看不到 FE-F3B 代码。因而复用隔离工作树并从 FE-F3B `55eba02` 建 `codex/fe-f4-project-review-distribution`；后续本地 `main` 已同步，见上条。
- 来源目录无 README，9 个文件与 zip 清单一致。初审发现四份 MODIFIED delta 只有新增句子，直接归档将覆盖原主规格场景；现有 ContentAsset/Review 的 Topic/Draft 必填列也需要在 FE-F4 设计中明示兼容迁移。准备归位与校准；来源包保持原样。
- 标准 `openspec/changes/fe-f4-project-review-distribution/` 已建立；五份 delta 均归位。四份 MODIFIED 已从 canonical specs 复制完整同名 Requirement 与所有旧场景，再加入 FE-F4 合同；逐条场景比对无丢失。新能力规格补齐权限、v3、候选冻结/批准/授权、Unknown、投影、前端和项目历史场景。设计/任务明确迁移可空列、候选哈希、受支持来源适配、账号能力验证和 raw-ID 保护。当前 OpenSpec strict 与 `git diff --check` 通过；独立只读规格复核进行中。
- 进一步检查 OpenSpec 解析 JSON 发现第二段规范文字不进入 `requirement.text`；九个 MODIFIED 要求的新增句子已并回首段，CLI JSON 回读确认。保留的旧场景未改写；本轮仍只修改规格与记录。
- 独立审阅第一轮指出 v3 非 Draft 人工成品包不可直接走 v1 `article_handoff`，以及两个同 `account_ref` 的 ContentAccount 会被旧唯一约束合并。已补 v3 manifest-based 本地包路径、不可用形态阻断、稳定授权账号键/迁移/幂等任务与场景；OpenSpec strict、diff-check 再次通过，等待针对性复核。
- 独立针对性复核 `PASS`：上述两处高风险规格缺口均闭合，没有新的 critical/high/medium/low 问题。仅为规格复核，不是实现或 apply 授权；当时 FE-F3B 主工作区可见性门槛尚未满足。
- 本轮规格门禁：`openspec validate fe-f4-project-review-distribution --strict` 通过，`git diff --check` 通过，`git diff --exit-code -- apps/api apps/web` 无业务代码变更。标准变更位于 FE-F3B `55eba02` 基线的隔离工作树；本地主工作区 `main` 现已具有 FE-F3B canonical spec、IdentitySnapshot 和 ContentAccount。状态为 `SPEC_READY / APPLY_AWAITING_EXPLICIT_APPROVAL`；连接器回读未独立验证。本轮仅准备在 FE-F4 分支本地提交规格，不推送、合并 FE-F4、部署或执行迁移。

## 2026-09-27：FE-F3B 审计与 apply 起点

- 用户明确授权四份 delta 全部同步。`openspec archive fe-f3b-content-identity --yes` 已更新 FE-F0/F1、FE-F2、FE-F3A 主规格并新增 FE-F3B 主规格；工具实际归档目录是 `openspec/changes/archive/2026-09-27-fe-f3b-content-identity/`。四份主规格的 Purpose 已校正；归档后主规格 strict、diff-check 和本地提交待完成。未推送、合并、部署或执行生产迁移。
- 归档后核验：四份主规格均包含各自 FE-F3B delta，`IdentitySnapshot`、Series > Account > Persona、`identity_unready` 和 Brief identity scope 均可检索；全体 14 份主规格 strict 校验 14 passed / 0 failed，`git diff --check` 通过，受影响主规格无 `Purpose: TBD`。提交前重新完整运行后端 310 passed / 5 既有 warnings、前端构建通过；现有主 JS bundle 1,079.36 kB 提醒未在本切片处理。
- 2026-09-28 独立复核修补：任何 Unit 身份/形态/工作流重绑均生成新快照；同层级纯身份刷新保留兼容的项目覆盖（含有 Run 后 fork 的新 Unit），旧 Run 仍固定旧快照。长期观点改为保留结构的 JSON 编辑；修订 409 后锁定旧草稿并要求显式加载最新版本；历史 Run 仅以冻结 ID/快照表示历史身份，当前名称明确标注为当前值。FE-F3B 定向回归 14 passed；全量门禁与二次复核待运行。
- 2026-09-28 修补后门禁：清除本机异常 `NO_PROXY/no_proxy`，用独立临时 SQLite 初始化 worker 数据库后，全量后端 310 passed / 5 既有 warnings；前端 `npm run build`、OpenSpec strict、`git diff --check` 通过。未改环境持久配置、未碰生产库；等待独立二次复核。
- 2026-09-28 独立二次复核 `REVIEW_PASSED`：五项收尾问题均闭合；复核者另跑 FE-F3B 14 项、FE-F2/F3A 27 项及 TypeScript/diff-check。OpenSpec 11.8 已完成，归档前等待四份 delta spec 同步选择；不将本地回归视为生产验收。

- 用户确认 FE-F3B 整包进入 apply。工作树 `/Users/mshengran/.codex/worktrees/fe-f3b-content-identity/AIContentStudio` 从 FE-F3A 提交 `1fa4520` 建立，分支 `codex/fe-f3b-content-identity`；来源目录仍留在主工作区，未修改。
- 已将来源 proposal/design/specs/tasks 纳入标准 `openspec/changes/fe-f3b-content-identity/`；新能力规格改为 ADDED delta，三份旧能力规格补全 MODIFIED 原要求，OpenSpec strict 通过。
- 审计补强：现有 BrandVoiceVersion 是无 owner 字段的全局版本资源；brandless 历史 Persona 不补造 Brand/修订；归档祖先不得参与新生产；重绑父级时不得悄然丢弃不兼容子级；旧裸 Workflow API 仍须保护 Account/Series 默认定义。
- 基线第一次后端全套 295/296：唯一失败是新工作树默认 worker SQLite 文件缺表，`test_task_queue` 的 Celery task 不使用测试内存库。使用独立临时 SQLite 并初始化后，296 passed、5 warnings；前端 build 通过，现有主包 1,060.65 kB 提醒。未改代码、未触及生产库。
- 模型已加 Brand/Persona/Account/Series 的稳定实体与修订、IdentitySnapshot、两类新默认绑定，并为 Persona/Unit/Run 添可空引用。定向模型结构测试先按缺表/缺列失败、实现后 2 passed。隔离空库迁移初次因新增外键无名称而失败；显式命名后 `f3a→f3b→f3a→f3b` 通过。带历史样本的迁移回读仍待做。
- 内容身份服务和新路由已接入：四级层级所有权、Pydantic override 字段校验、追加修订与 409、缺失/显式 null/整体替换解析、全局 published BrandVoice 检查、快照构造与所有者读取。第一批 API 定向测试先 404 后 3 passed；Unit/Run 接线和跨所有者/归档回归仍待完成。
- 新 Unit 已持久化 IdentitySnapshot，Run 启动时复制精确 snapshot ID，并在归档身份祖先时拒绝新运行，历史 Run 仍可读取。相关测试先因序列化缺字段失败、修正后通过；现有工作仅完成此纵切片，重绑/默认/前端仍待实现。
- 显式身份重绑已接入 Unit PATCH：无 Run/Snapshot/Output 历史时原地生成新快照；有历史时创建替代 Unit、归档旧 Unit，旧 Run 固定旧快照。父级变化而未显式处理子级时返回 422；定向 FE-F3B/FE-F2 回归 25 passed。层级默认工作流尚未接入，当前重绑仍仅解析角色默认。
- 账号/栏目默认工作流的 GET/POST、乐观修订冲突、可移植性校验和有效优先级已接入；新 Unit 固定 Series > Account > Persona，旧 Unit 不自动重绑。旧裸 Workflow API 的 owner 检查覆盖账号/栏目 scope；定向 FE-F3B/FE-F2 回归 26 passed。
- FE-F3A 读模型已接入真实快照条目及 legacy 状态，Overview 对活动单元的缺失/空身份给 `identity_unready`；新 Brief 版本里的结构化身份 ID 会校验 owner 与层级，旧字符串标签保留。定向 FE-F3B/FE-F2 回归 27 passed。
- `/identities` 已换为后端持久层级工作区：树、四级修订字段、继承/覆盖/清空、历史、账号/栏目、工作流偏好和诚实的内容记忆空态；前端构建通过。项目版本页也显示真实身份快照及 Legacy 条目。浏览器交互与项目/生产上下文仍待验收。
- 在独立临时 SQLite 上，先由 FE-F3A 原代码建真实旧 schema 并插入 owner/Persona/Project/Unit/Workflow/Run，再由 FE-F3B 执行 upgrade→downgrade→upgrade；旧 Run checksum 原样、Unit/Run 快照仍 NULL、IdentitySnapshot 0 行，`foreign_key_check` 空。迁移有既存 workflow parent FK 的 SQLAlchemy 警告，非失败；未碰项目数据库或生产库。
- 项目矩阵账号/栏目选择、有效默认预览、显式身份刷新和生产页四级 Context Header/只读快照已接入；最新前端 build 通过，现有主 bundle >500 kB 提醒仍在。浏览器端到端验收尚未做。
- 全量后端首次 303 passed / 1 failed：旧 FE-F3A Overview 测试假设唯一风险为 `unit_blocked`，与 FE-F3B 新 `identity_unready` 合同冲突。按新合同加入确定性的身份下一步并更新该断言后，全量 304 passed / 5 既有 warnings。该调整仅涉及风险读模型与既有回归预期，不抹掉真实风险。
- 追加 FE-F3B 定向回归：身份归档后 project-scoped 与 legacy Run rerun、项目覆盖保存均拒绝；发布 BrandVoice 可入快照、草稿版本不可引用；身份新修订不改旧快照，显式重绑生成新 checksum。FE-F3B 定向 9 passed，最新前端改动后 build 通过；后续需重跑全量。
- 最新本地门禁：后端全量 305 passed / 5 warnings；前端 TypeScript/Vite build 通过（主包 1,078.53 kB 提醒）；OpenSpec strict、`git diff --check`、涉及后端文件 Ruff F 检查通过。独立代码审阅已发起，尚未归档/提交。
- 补充 Snapshot `readiness`/原因元数据，以及 Unit 创建、原地重绑、替换事件的结构化旧/新 snapshot ID。定向测试最初误把 Activity 分页对象当数组，按既有 `items` 契约修正测试后 9 passed；全量门禁需在审阅修订后再次运行。
- 扩充 FE-F3B 定向测试至 12 passed：跨层级/跨所有者、归档祖先、唯一键竞态回滚、数组/对象整体替换、BrandVoice 覆盖和账号默认模板可移植性。隔离浏览器与 API 共同验收：四级身份创建/刷新、栏目默认 v1 保存后旧 Unit 未自动改绑、新 Unit 固定 v1、品牌修订 v2 后旧快照仍 v1、无历史原地刷新到新快照、真实 Human Run 固定快照、再刷新创建替代 Unit 并归档旧 Unit。临时库读回旧 Run checksum 不变。
- 最新完整门禁：后端 308 passed / 5 warnings，前端 build 通过（主包 1,078.53 kB 警告），OpenSpec strict、diff-check、Ruff F 通过。独立审阅结论仍待回，未归档/提交。

## 2026-09-27：FE-F3A apply 起点

- 用户已明确授权进入 apply；使用标准变更 `fe-f3a-content-project-core-completion`，spec-driven 产物 4/4，任务 2/54 完成。
- 当前分支 `codex/fe-f3a-project-core-completion` 基于 FE-F2 `734990c`，存在上一轮尚未提交的规格/README/记录改动和用户原始 FE-F3A 包；这些均保留，不新建丢失规格的工作树。
- 实施顺序记录于 `docs/superpowers/plans/2026-09-27-fe-f3a-project-core.md`。尚未运行生产迁移，也不推送/合并。
- 1.1/1.2：五个模型和增量迁移文件已加入；FE-F3A 表结构测试先因缺表失败，新增模型后单测通过。下一步在隔离库验证迁移 up/down/up，并实施事件/归档语义。
- 1.3 部分：隔离临时 SQLite 已完成 `e5fef2000001 → f3a000000001 → e5fef2000001 → f3a000000001`；仓库初始迁移会按当前模型预建新表，因此 FE-F3A 迁移使用既有的表/索引存在性防御。尚未在该迁移链路里插入并回读 FE-F2 历史行。
- 2.x 部分：项目创建/编辑/归档、单元创建/编辑/替换/删除、项目工作流保存、项目来源角色默认保存、快照与关联产物写入 ProjectEvent；当前事件/项目及 FE-F2 Data/Output 定向测试 11 passed。项目归档后新旧 Run 修改权限加了保护，后续仍需更完整回归。`project_events.py` 的稳定常量与 2.5 全路径验证尚未完成。
- 3.1/3.2：Brief 已有当前/历史/详情/追加版本 API；保存按 expected_revision 对比，唯一键并发冲突回滚为 409，事件同事务写入。先验证无路由 404，再实现后定向 4 passed；前端尚未接入，完整字段校验和并发双会话验证待做。
- 4.1/4.2/4.4：项目 Source 引用可附加、幂等重复、解除并重新激活，旧全局 Source 保持可读；Fact Boundary 可读取当前/历史并只绑定有 checksum 的冻结 FactPack，revision 冲突返回 409。相关测试先 404 失败后定向 6 passed。项目级 Clone/Freeze-and-bind、全局 FactPack 服务共用规则、前端 Evidence 仍待实现。
- 4.3/4.5：全局与项目级 FactPack Clone/Freeze 现复用 `factpack_service`，项目级 freeze-and-bind 要求当前边界的直接草稿子版本，冻结、审计和边界修订同一数据库事务。克隆→冻结→新边界→旧历史可读的定向测试先失败后通过；FE-F3A+FE-F2 项目定向 13 passed。前端 Evidence 仍未接入。
- 后续实现已接入 Brief、Evidence、Assets、Overview、Versions、Activity 后端与项目七标签前端；此前后端全套 289 passed、前端 build 通过，最终门禁待重跑。新归档项目回归证明历史 Run 可读、旧裸 Run mutation 与项目 mutation 均拒绝。
- 收尾修正：项目 PATCH 不允许绕过专用归档接口直接设置 archived；生产工作台共享素材按项目上传/系统引用/工作流产物区分，图文与视频“已生成”列表只显示工作流产物。
- 定向补测通过：项目 PATCH 直接归档返回 422；注入上传事务内事件失败时 Material、MaterialRevision、项目引用均回滚，预先存在的同哈希共享字节保持不删。FE-F3A 定向测试 12 passed；此前全套 290 passed，最终变更后需再跑。
- Evidence 返回项目页后可从 FactPack 列表恢复当前边界的最新草稿，避免“编辑后无法冻结并绑定”；Matrix 已提取为独立 Tab 组件并隐藏已归档项目的矩阵写入按钮。前端构建再次通过（主 bundle 1,057.94 kB，原有体积提醒）。
- 隔离迁移库带真实 FE-F2 ContentProject、ContentUnit、WorkflowRun(checksum) 完成 e5→f3a→e5→f3a；三条历史行与 checksum 回读一致。未触及生产库。
- 隔离浏览器验收：创建项目、Brief v1/v2、文本 Source 创建并关联、冻结 FactPack 绑定、项目边界 Clone→跳转编辑→返回恢复草稿→冻结并绑定、PNG 项目上传、同版本再次引用幂等、Overview/Versions/Activity 真读模型、七标签逐一刷新均成功。验收使用独立临时 SQLite 与 127.0.0.1:18081/15174。
- 归档状态的普通 PATCH 旁路已同步堵住：Project 必须走 DELETE→archive，ContentUnit 必须走已有删除/归档语义；避免写成通用 updated 事件或绕过历史保护。
- 新定向用例先发现 Overview 把 `waiting_human` 单元误归为普通生产；已补待人工聚合，并区分最新 Run 的 stale/failed/waiting_input 节点状态。Brief 同内容显式保存会形成新修订、checksum 相同。FE-F3A 定向现为 13 passed。
- Overview 前端将风险/人工状态代码翻成用户可读中文，并显示待处理项对应单元；不在 React 重算阶段。
- 新增跨所有项目核心读模型的归档/跨所有者回归：归档后 Brief、Boundary、Assets、Versions、Activity、Overview 可读，Source 解绑不改已冻结边界；另一用户均 404，归档项目的新写入均 409。FE-F3A 定向现为 14 passed。
- 当前最终本地门禁：后端全套 293 passed / 5 warnings；前端 `npm run build`（含 TypeScript）通过，主 JS 1,058.31 kB 非阻塞提醒；OpenSpec strict、`git diff --check`、本次后端文件 Ruff F 检查通过。独立代码复核已发起，OpenSpec 归档与提交保持等待。
- 定向回归进一步验证 Clone 后编辑草稿再冻结会产生不同 checksum 且旧 FactPack item 数不变；重复 Source/Material 关联不重复写项目事件。新增断言后 FE-F3A 定向 14 passed；全套门禁仍需最终复跑。
- 在 FE-F2 素材真实字节/Attempt 回归上增加 FE-F3A 并集断言：同一 MaterialRevision 同时由 workflow 与 system_reference 合法展示，两个稳定 key，数据库仍只有一条 Revision；定向测试通过。
- 独立审阅首次结论为不准归档/提交，指出 5 个重要缺口。已逐项修：新哈希上传失败单独记录可核对的 `material.upload_orphan_candidate` AuditLog，不删除共享字节；归档 Evidence 隐藏创建/绑定并在全局 Source 创建前再次核对项目状态；项目 PATCH 不能修改 objective；显式素材回传 MaterialRevision 来源信息；Evidence 增加当前冻结 FactPack 条目区，Brief 历史可展开全文。定向单测与前端 build 已针对相关修改通过，最终全套和复审待跑。
- 隔离浏览器归档后复验：Evidence 的 Source 创建/解绑和边界绑定控件均不出现，事实条目和边界历史仍可读；Brief/Assets/Matrix 的项目级写入控件不出现。
- 二次复审又发现 orphan candidate 的 `AuditLog.entity_id` 超过 PostgreSQL 的 50 字符限制、且未被清理消费。现只在该列存 50 字符哈希前缀，完整哈希留在 detail；既有 `run_retention` 以一日宽限、每批上限处理候选，先检验路径与已提交 MaterialRevision/DraftMedia/AssetMedia 引用，再删除无引用字节或保留共享字节。未处理候选不受普通 90 天 AuditLog 清理影响。新增新文件删除/共享文件保留/过期候选保留测试均通过，复审待重跑。
- 最新本地门禁：后端全套 294 passed / 5 warnings，前端 TypeScript/Vite build 通过（主包 1,060.65 kB 非阻塞提醒），OpenSpec strict、`git diff --check`、涉及后端文件 Ruff F 检查通过。独立审阅正在复核最后两个上传清理边界，9.6 尚未完成。
- 第三轮审阅指出清理任务未注册、同哈希上传与清理可能竞态。已注册现有 beat 配置的 `retention_sweep`；MaterialRevision 写入持有哈希分片文件锁到外层事务结束，保留流程在引用检查与 unlink 期间持同锁，并逐候选提交。新增任务注册与跨线程锁释放回归；清除本机异常 `NO_PROXY/no_proxy` 后后端全套 296 passed / 5 warnings，前端 build、OpenSpec strict、diff-check、Ruff F 通过。最终独立复核进行中，仍未归档/提交。
- 独立复核最终 PASS、无剩余 blocker；9.6 已勾选。用户确认同步主规格后，OpenSpec 已归档至 `openspec/changes/archive/2026-09-27-fe-f3a-content-project-core-completion/`，同步两项旧能力规格并新增 FE-F3A 主规格（9 added / 3 modified）；三份主规格 strict 均通过。待核对暂存快照并提交本地分支；不推送、合并或部署。

## 2026-09-27：FE-F3A 规格复核与归位（仅文档）

- 以 `734990c` 为基线创建 `codex/fe-f3a-project-core-completion`，把用户提供的结构化 FE-F3A proposal/design/tasks/三份 spec 归入 `openspec/changes/fe-f3a-content-project-core-completion/`。原始目录、ZIP 与合并文档保持原状，便于追溯。
- 对照 FE-F2 实际项目、单元、Source、FactPack、MaterialRevision 和迁移头复核；旧 Source/FactPack/Material 为全局资源，项目引用不等于获得资源所有权。现有项目 DELETE 可物理删除无单元项目，与新增 append-only 活动/子表冲突，已在规范中改为归档语义。
- 已补强事件同库事务、Brief/Fact Boundary 并发冲突转 409、Source/Material 唯一绑定重新激活、素材字节写入后的失败清理边界。业务代码和数据库未改动；`openspec validate fe-f3a-content-project-core-completion --strict` 通过，纳入新增规格文件后的 `git diff --check` 通过。
- `tasks.md` 仅将分支/规格门禁 0.1–0.2 标记完成；所有实施任务仍待明确 apply 授权，不因 4/4 规格产物齐全而视为功能已完成。

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
