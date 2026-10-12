# 本批发现与决策

## R1 / R2 post-enable收尾（2026-10-05）

R1实读确认：正式aco/integrity ok，7个User身份两列全null；代码默认f7d与当前schema不一致。新增default回归先失败，再只改常量到aco通过。F8-owned的8份当前schema/运维文档（含根README）允许窄修，根task_plan/progress/findings及其他5份F8文件不动；历史f7d验收保留，不将f8a ancestry当JWT启用。R2实读未找到三核心域持久测试，新增测试均用临时SQLite/素材、实际服务/路由，不访问正式库或供应商。原147/147不再代表closeout全部完成，新收尾7项单独记录。

四永久测试文件共108项，全量从1660增为1768 passed、仍28 skipped；72条warnings来自既有库/service API被新用例覆盖，并非零警告。迁移初始版本用当前metadata，必须先在一次性库降至f7d并检查新表/身份列缺失，再验证真实ancestry升级；否则仅换version_num可能是假旧schema。Mendel独立复跑108项并APPROVE。扩大Ruff到全scripts时发现无关seed脚本原HEAD三条错误；本轮app/四新测试通过，保留原脚本不扩大修复范围。153/154只剩最终closeout复核，不把内部定向复核代替15.7。

## 整体执行回执口径（2026-10-05）

147/147只代表本change批准范围全部实施/验收，不代表整个产品未来蓝图或专业工具pilot全部完成。正式启用已另行完成，但main HEAD仍是原基线加未提交实现，不能写成“已提交/已归档”。strict/健康/任务数本轮重新验证；全量suite/build与独立复核引用已有对应证据，不混为本轮重跑。回执复用既有最终验收文件，避免再造一套最终状态真源；F8十三文件继续保留原字节。

## 本机正式启用（2026-10-05，当前运行状态）

- 用户明确授权正式schema升级和原服务重启，已完成；以下“不改正式库”是实施/隔离验收时的历史边界，不再代表当前运行状态。
- 继续使用原SQLite、本地媒体根、development_header及原launchd Worker/beat。`REQUIRED_SCHEMA_HEAD=aco000000001`放在现有私有runtime.env，避免改变APP_ENV或代码默认head来强推JWT/MinIO。
- 备份前确认真实Worker无active/reserved/scheduled；既有3条queued ContentJob与97条外键异常原样保留，不自动重发或借启用修数据。正式升级及重启后，83张历史表5145行原始列哈希一致，素材7引用/5字节文件一致。
- MCP身份绑定原有激活admin用户1；随机token仅在ignored/0600私有配置。真实Codex客户端的正式连接是临时子进程配置，不表示本聊天或所有客户端全局自动注册了新工具。
- 正式页面现有Video上下文stale、Text素材权利/身份/check阻断是真实业务状态，不是部署失败；不能通过更新上下文、改权利或重跑模型来伪造启用通过。
- 本轮只验证正式联通、数据保全和页面读取，不重复创建示例或发送模型/公众号任务。完整输出接受/Master/Candidate/包写链证据继续来自既有隔离验收；专业工具pilot仍不在第一版范围。


## 最终结论（2026-10-05）

三类最终独立复核全部 APPROVE，六处原发现、文件恢复的追加边界与偏好表单 dirty 均闭合。13.7 在完整承接/复核通过之后实施：仅去除日常旧侧栏，保留全部旧实体路由和 Settings 十五个兼容入口；独立导航窄复核、实际只读浏览器及历史全表 hash 再验通过。当前147/147，下面未完成描述均为当时的历史，不代表当前状态。

实现验收与正式启用必须分开：SQLite仍f7d000000001，精确六表未存在；不通过重启正式进程触发 schema 变化。诊断最初用creative_%误含旧CreativeBrief；换成迁移中精确六表后确认，不改用户数据库。OpenSpec可选遥测连接错误不等于规格校验失败，实际strict35/35、exit0。

## 偏好表单 dirty 闭合（2026-10-05）

最终产品 reviewer 通过此前修订/范围保护与其他面，独立发现偏好捕获有名称/正文/来源选择时仍无离开提示。真实 Chrome RED 后，仅把该表单接入既有 baseline/dirty 聚合；成功创建后解除，busy/409 与 exact 来源选择保留。父层定向 GREEN 与构建通过；模拟 409/200 不冒充 durable API 验收，也不替代待返回的最终窄复审。

## 最终恢复缺口与 MCP 结论（2026-10-05）

post-link 复审已通过，另两种边界先 RED 后修：中途未完成写入需精确目标/内容 hash 的 pending 身份，不能按任意 prefix 文件猜测；合法输出数由原 500-row 合同限定，不可被 200-directory-entry 扫描预算截断。现在只恢复 exact-bound、uid/600/regular/singlelink、expected bytes prefix 的零/半字节临时副本，未记录或错误内容仍拒绝；预算不放宽原输出合同。

最终 MCP reviewer 已 APPROVE（441 项独立内存断言）；14.9 可关闭。后端 reviewer 发现文件 link 成功、pending unlink 中断后会留下双硬链接，普通重试和接受都会拒绝。真实临时文件 RED 证实；修正仅允许锁内恢复归属/精确字节/inode 可证明的私有 pending 文件，仍拒绝未知输入/任意硬链接/符号链接，不删除累计 manifest。父层 GREEN 不替代 14.7 独立复审。

## 最终独立复核窄修（2026-10-05）

三类最终 reviewer 均返回 REVIEW_NEEDS_FIX，而非批准。具体为：MCP 编码令牌回显、QuickTime 误识别、通过新 package hash 绕过 unknown、文件暴露早于 manifest commit、复用外部派生素材未重验祖先撤权、方法详情/设置切换丢弃编辑。编码令牌与 MOV 已先用纯合成数据复现再窄修；其余继续处理。重新验证及独立复核前，不关闭 14.7–14.9 或旧导航。

## 最终复核证据口径（2026-10-05）

- Reviewer 的流程提问、not_found 或 usage limit 都不是复核通过；最终 14.7–14.9 仍须各自的实质源码结论。父层的只读自查不能充当独立批准。
- 当前正式 SQLite head 和新表缺失均经 sqlite3 的 readonly 模式确认；隔离迁移/suite 通过不等于正式库已启用。
- 新鲜门禁与跨批浏览器证据分开记载：本轮重跑既有全量后端 1660/28、构建/预算、strict35、Ruff/空白/F8哈希；没有重新生成媒体、发送公众号或声明专业工具自动化已验收。

## 第七批：Legacy parity（进行中）

- 最终独立复核的六路 agent 因账户额度终止；不能记为 APPROVE，旧导航保持可见。父层继续可执行的隔离验证，不反复重试 agent。
- 证据包内嵌编辑器缺少逐条公开权利入口，导致 Source→Fact→Pack 正常冻结后仍被 Master evidence gate 拦截。先复现缺失控件，再接既有 exact-item PATCH；默认不授权、明确确认、冻结只读，模型使用权利不猜测。
- 旧素材详情的撤权提示取消仍提交默认原因。临时浏览器已复现一条错误写请求（拦截，未实际撤权）；窄修后取消零请求。空原因不提交，错误可见，刷新精确版本/清单。
- 浏览器的受控 checkbox 不应使用立即断言本地 checked 的操作；等待后端回读。冻结也等待 query invalidate 完成，不能把回读中的草稿 UI 当成冻结契约失败。
- 日常 Text 链路已走通 v4 审阅/明确处置 coverage warning/批准/本地授权/ZIP，精确 payload hash 与正文一致，Master 不变。隔离未配置模型的 semantic coverage 仍 unavailable，绝不把 deterministic pass 冒充语义检查。
- 端点周期原来选中即 PATCH，与明确保存契约不符。临时 RED 后改为本地选择＋保存周期；真实回读通过，失败不丢选值，不触发 pull。旧 Connector/模板/素材/证据入口的角色未知/失败均禁止写操作。
- BrandVoice 草稿归档已有 API，内嵌工具缺控件；补入口后已验证 Clone→归档→确认删除隔离克隆记录。published 不直接归档，仍沿用 immutable/clone/新版本发布下线旧版本规则，没有新增状态 API。
- Settings Advanced 兼容目录覆盖 15 个既有入口，目录打开零写入、不加载本机运行配置工具；旧日常菜单没有隐藏。
- admin@studio.local 在隔离副本实际是 editor，不能因邮箱名称猜权限。新管理员 fixture 与旧正文 owner 分开，查看者和无授权身份仍 fail-closed。只在 `/tmp` 新增测试身份，不改正式用户行为。
- 历史读取使用专门创建的 synthetic Topic/Mother/Draft/v2 Candidate/Target/Receipt，不伪装成用户真实发布历史。审批页须选“已批准”；字段 label 包含 options；配置清单和操作面板须分别定位，等待回读后再操作新版本，避免测试夹具误读而去修改产品契约。

## 第六批：恢复、偏好、客户端与秘密边界（2026-10-05）

- 支持 checkpoint/revert/recover 是 executor 声明，不是 Runtime 证明；旧 partial metadata 可读但不能冒充完整声明。恢复必须保留原 checkpoint/binding，重复相同 ref 也不能覆盖既有观察证据。
- 偏好来源是重复已保存人工正文编辑，不是两份 accepted 成果。比较排除 render binding、仅 context/intent/attestation；exact parent/hash/actor/冻结 context/AI receipts 都重新验证。candidate-only 去重避免新捕获返回已有 saved/pinned 方法，晋升始终单独人工确认。
- 秘密格式校验要贯穿 execution/recovery/MCP，不只保护方法库。独立复核发现 Google/Stripe/percent-encoded assignment/签名 URL 缺口；扫描副本 NFKC/最多三次解码，不改存储正文和 canonical hash，整体拒绝，不静默清洗。MCP 先拒绝敏感 ID 再赋值/dispatch，固定错误不回显凭据。
- 实际客户端证据使用安装的 Codex app-server，不用 Test Agent 冒充。只连接/读取可不发模型 turn，也不需要改全局用户配置；runtimeStatus=null 不解释成已有状态投影。
- 既有 SQLite `.backup` 已覆盖新表，无需第二个备份器；恢复核对全部 90 表/schema/约束与精确 accepted Material bytes，缺 disposable staging 的历史仍可读。对比在后续 UI 测试写入前完成。
- read-only inventory 需要确认真实 SQL 与 effect entrypoints，不只数 HTTP 方法；29 surfaces/89 ORM 表、零 provider/native/external/protool/network/process，五个浏览器入口零写请求。现有外部字体被拦截，不扩展为本批重构。
- 定向恢复 28、偏好负向 33、shared secret 57、真实 MCP 10、独立 source 23/全安全 325 通过；完整后端 1660 passed / 28 skipped，最终独立复核 APPROVE。正式库/F8/Worker 不动，专业 pilot/质量/正式启用与最终全 change 收尾不提前宣称完成。

## 第五批：导演入口、正文修订与成果回接（2026-10-05）

- Video 日常入口不需要新的 video.master.v3：导演包可从无最终 render 的 v2 生成；接受 MP4 后显式绑定/保存，再按原 attestation/checks/v4 门禁推进。原时间线/叠字/渲染控件保留在高级入口。
- Variant 正文和 creative intent 必须一起走原 manual_edit CAS；本地表单保留稳定 ID/order/refs/citations/declarations。浏览器先 GET current 检查也不替代提交边界 CAS，实际拦住 POST 后制造竞争，证明 409 留住本地草稿。
- Material 是 system_shared：外部成果的 source project/unit 是原执行血缘，不是禁止其他项目显式引用的 owner 边界。消费项目必须已有 exact ProjectMaterialReference 或 WorkflowOutput，再验证 accepted output/package/Material 字节；保留原来源，不能把来源改成消费项目。真实 v4/v5 跨项目冻结通过。
- 清理审计不能按最后 event ID 当最新操作：旧请求 A 的失败可能晚于新请求 B 的成功写入。每个 key 的权威结果按不可变 intent_revision 再 event ID 排序，旧记录 fallback 原 revision_no；旧失败继续留审计，但不能覆盖新成功或导致重复删除。
- 清理先约束 exact staging key 的全部 output/attempt 引用；unknown/未解决 blocked/待接受共享引用不丢字节。已接受副本清理先重验正式 Material bytes，不删除 Material storage/output 行。临时 32 项断言及实际页面删除三个隔离副本通过。
- Review 只展示从 source Master/Variant 精确引用中冻结的安全 provenance，不能拿 result_ready 充 Candidate；历史无新字段时不 backfill 或改 hash。跨项目 provenance 仍指向原项目/单元，读取权限由原服务检查。
- Home 继续 projection：unknown 风险不因成果或学习条目而降低；读取无 dispatch，缺新表明确 unavailable。外来/归档 Execution 不泄露。
- 临时 harness 的按钮名称含“未保存”、预览实际使用 /content 而非 /raw、角色/Fact Boundary/cover order 等按真实契约修正；不为夹具误用放宽权限、证据或顺序规则。Workflow/Master 两份 dirty state 与独立保存控件实际通过，开合不丢草稿。
- 本批是受控 Test Agent、ffmpeg 可读 MP4/WAV/PNG 的产品链路验收，不证明专业剪辑器自动化、语义生成质量或真实模型能力。正式库/运行环境、F8 13 文件和旧导航不动。

## 第四批边界与验收结论（2026-10-05）

- Capability 三表已存在于已演练迁移；本批服务/API/UI/MCP 复用已完成，无需新增 durable 对象。
- Installed Skills 是外部 inventory，不由方法库导入/安装/启用；同名不等价。
- Learning 已有 trusted_frozen_decision，可验证 accepted 和冻结支持证据；桥接仅写 candidate，不走 ContentMemory promotion。
- 11.5 的重复接受编辑不能用执行成果接受替代；证据不足则保留后续。
- Unicode 必须保存规范化结果，而不只是扫描 NFC/NFKC：嵌套文本/键 NFC 后参与 hash，等价文档相同 hash，规范化键冲突拒绝。
- 字符串上限与 JSON 总量分别校验；8192 字节合法正文不能因包装开销成为不可用方法，渲染文档总量保持 64 KiB 并在 Use 提交前验证。
- 秘密格式不能只依赖字段名：可识别 Google/Stripe 凭据在正文、参数描述与渲染参数中整体拒绝。
- 方法生命周期不等于已有使用生命周期：归档/追加修订禁止新使用，原 Use 结果仍可明确回填。409 回读同记录后人工确认新的 CAS 基线；回执绑定 use/revision，读取期间禁止新 Use。
- 去重包含精确来源 FK/provenance，不因不同执行有相同方法 hash 就共享无关历史；实际 API 负向通过。
- 先复制 `.backup` 才有 SQLite WAL 一致快照；临时并行验收应按 exact execution/source 计数，不用整个库的全局行数推断单操作原子性。
- 独立 SPEC/后端安全/TypeScript 最终 APPROVE；修正后完整 suite 与 API/页面/MCP 重新执行。正式启用、真实专业工具及全 change 验收并未随本批完成。

## 第三批页面与 MCP

- 实际 `useProductionWorkflow.readOnly` 原来只有归档判断，不能把它当成 viewer 权限。补 `/users/me` 角色读取并在未知/失败时关闭编辑，与已有后端 require_editor 一致。
- MCP 不新增审计真源：执行服务和 UI/API 共用原子 ProjectEvent/AuditLog；幂等 prepare 只读重放不再增加记录。
- Checkpoint JSON 保留现有安全 metadata 投影，绑定字段由服务端记录到同一 JSON 的独立 envelope；客户端不能声明或伪造 binding。未领取执行不能保存真实 checkpoint。
- 无会话 JSON Streamable HTTP 可以复用 FastAPI；本批先验证限定协议 2025-11-25，不新增 SDK/daemon。Capability 服务和真实 Codex/Claude 客户端不以模拟清单冒充完成。
- 重复选择当前 Package/Execution/Variant 不应清空已读详情；但显式确认重新读取必须真正重置 dirty state。这两种行为分开处理，并由隔离浏览器验证。
- Claim 是持久领域证据，不能只依赖可按保留策略清理的 AuditLog。共用 ProjectEvent 记录 exact execution/package 领取，保留日志清理后仍能合法继续。
- Recovery 的 verified/succeeded 与 checkpoint 一样必须携带观察证据；更换 checkpoint_ref 后原 observation/readback 不再适用，除非本请求给出对应新证据。
- 所有 unknown reconciliation 都要匹配已冻结 executor kind/key/version；blocked 或 failed_before_dispatch 不应成为忽略执行者身份的旁路。
- 有界长度不等于正则耗时有界。URL scheme 搜索和 key 后重复空白的回溯已用最小模式修正；保留 secret 拒绝，解析放入线程池，并以 254 KiB 真实 MCP ping 验证。
- 第三批页面/受限 MCP 通过不等于 accepted 素材已经绑定 Master，也不等于真实 Codex/Claude 或专业编辑器接入。相关未终验任务继续保持未勾选。

## 2026-10-04

1. **测试启动口径**：直接 `.venv/bin/pytest` 会导致脚本模块找不到；默认 development 环境下的 memory DB health fixture 也不具完整 schema head。使用 `APP_ENV=test .venv/bin/python -m pytest` 后验证通过，不为测试启动方式去改业务代码。
2. **Evidence locator 不是纯文本**：冻结证据的 `source_locator` 可以是对象，Project Evidence 直接作为 React child 会报错。改用已有 `readableValue` 安全显示；未改变快照或事实。
3. **精确引用表单不应随详情回读重建**：使用完整 revision JSON 作组件 key 会在精确版本 fetch 时清空本地表单。现在 key 只使用资源类型/ID/所选 revision ID；回读未完成时仍不允许写入。
4. **模板清单只读不等于管理工具不可用**：当前 page 的 inventory 没有可编辑项时，不应隐藏管理员的既有版本工具入口。规则仍只读，具体模板操作仍由原 API 授权/版本约束检查。
5. **原生任务 ID 是字符串**：队列至素材页的 deep link 保留字符串 task ID，不按数字解析；读取不 recover/re-dispatch。
6. **确定性入口与真实供应商分开验收**：本批验证 staging→人工接受→精确素材版本，用隔离固定图片 Provider；没有宣称真实图片模型已通过本批验收。
7. **现有静态网络资源**：旧 Landing 和现有全局字体会尝试读取外部字体/演示视频。最终隔离浏览器显式阻断这些请求；不为入口整合重构既存字体/演示资源，不把它们误报为模型/发布调用。
8. **进度文件所有权**：根 README/task_plan/progress/findings 已有 F8 未提交工作，本批使用 change 独立记录与阶段验收文档，不覆盖根文件。
9. **Worker 测试需要已初始化的独立库**：最终复跑换为全新临时目录时，一个既有 Worker 测试报 `no such table: content_job`；该任务使用模块级 SessionLocal，而不是内存 fixture session。在临时库执行现有 Alembic head 后，定向队列测试 4/4 通过。正式库不动，测试逻辑与后端业务代码不改。
10. **原生接受的项目语义取决于冻结任务上下文**：既有 `ProviderGenerationTask.project_id` 不为空时，接受会原子创建 `MaterialRevision + ProjectMaterialReference`；旧全局临时预览只入库。不能把它们统一写成“接受只入库”，也不能靠前端重复添加项目引用。Project 素材接受回调现在回读 shared-assets，提示与按钮展示实际冻结的项目 ID。
11. **操作控件必须同时体现角色与归档边界**：viewer 仍能读取自己拥有的活跃项目，不代表可操作 Source/Fact/Pack/Material。Project Evidence/Assets 先读取角色，未核实或非 editor/admin 时只读；task deep link 读取绑定项目状态，归档或无法核实时禁止接受/恢复，但保留原任务与已接受字节读取。
12. **任务 deep link 不能成为操作死胡同**：单个任务入口新增只读刷新与显式 recover；recover 只查询原任务，不提供重新提交。Project Source 的文本/URL/文件统一传递已有 as_of 元数据；没有新增数据模型。

暂未发现必须新增持久化结构才能承接本批入口的情况；后续执行域表遵循已批准规格，正式库升级仍单独授权。

## 第二批：阶段 3–7 后端

1. **迁移与正式启用分开**：新 head 为 `aco000000001`，前置 `f8a000000001`；正式库仍是 `f7d000000001`。新增 ORM 列不会通过启动时的 `create_all` 补进正式库，不重启正式 API 来冒充已启用。迁移只在副本中演练。
2. **历史初始迁移使用当前 metadata**：fresh upgrade 会提前建出新表；新迁移严格比对已存在的列、CHECK、FK、unique/index，而不是悄悄跳过。首轮测试与并行修改交叠出现 CHECK mismatch；文件稳定后定向迁移测试通过，最终全量结果另行记录。
3. **源包与可发布成品不同**：Director 可以从没有最终 MP4 的 current Video v2 创建，冻结原有 script/shots/timeline/voice/subtitles/cover，并诚实标记需要最终 render；不宣称 Candidate-ready。
4. **数量合同不是单文件布尔值**：每个 role 按不同 `output_index` 的最新 attempt 计算 min/max count。必需槽位的最新输出被拒后，必须同槽位更高 attempt 替换，不能用额外文件数量绕过；optional 拒绝不阻塞。
5. **换 key 不是 unknown 的安全重试**：除当前 execution 状态外，准备/claim/start 还需要检查同一冻结包 hash 的未决 unknown；重复 Package ID、换执行者或版本也不能成为旁路。
6. **来源枚举不等于可信来源**：`external_execution` 是输出接受服务的保留来源，不能让普通上传自行声明或伪造 provenance。
7. **接受成果不改变正文**：隔离 API 验证接受只写 MaterialRevision/明确项目引用。Master/Variant/Candidate/Review/Delivery/Published 仍须各自显式动作。相同字节可共享存储，但不同执行输出必须保留各自的 provenance。
8. **权利必须沿派生链继承**：package/input rights 和实际 materialize 记录在接受时重验；public/model/commercial 不升级，归因和许可义务保留。接受失败零部分业务写入。
9. **隔离回归不新增永久测试**：本批运行现有 suite 和临时内联 API/并发/文件断言；既有迁移测试仅更新一处当前 head 断言，没有新增测试文件或新测试用例。
10. **首次接受后不能扩展派生输入**：即使整个 execution 还未 accepted，任一输出已接受就必须冻结实际 materialize 输入集合，否则后追加受限素材会与已入库输出的公开权利矛盾。已有输入可在精确快照重验后重新读取。
11. **checkpoint 的证据校验必须晚于 metadata 合并**：仅验证请求片段会漏掉已有 unknown 与新 verified 状态合并；prepare 和最终合并结果统一验证 verified/succeeded 所需 observation hash。
12. **总量预算必须限制读取本身**：逐文件读取前传入剩余预算，不等全部字节读入内存后才拒绝；重复物化同一输入不重复计费，全部验证后才写文件或提交 CAS。

独立 SPEC、Python、数据安全复核均 APPROVE，追加三处安全补丁后全量 1660 passed / 28 skipped。当前没有具体本批阻断；尚未实施的页面/MCP、cleanup、Capability 服务与正式启用不因此自动完成。

本批的最终门禁、独立复核与准确勾选状态以阶段验收记录为准；页面、MCP、Capability Memory 服务和正式库启用不在本批通过范围。
