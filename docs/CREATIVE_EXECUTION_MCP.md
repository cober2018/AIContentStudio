# Creative Execution 本机 MCP

## 范围与状态

本机 Agent 从已冻结的 CreativeExecutionPackage 领取已准备的执行，读入精确输入、回报状态、提交文件，再请求人工审阅。结果暂存不等于接受，接受仍须由普通 UI/API 的授权用户逐项决定；绑定 Master/Variant、冻结 Candidate、审批和交付各有独立步骤。

Group3 提供同一 FastAPI 进程的 `POST /api/v1/creative-mcp`，没有新依赖或第二个 daemon。2026-10-05用户另行授权后，正式SQLite已升级到aco000000001，原API/Worker恢复；正式入口为 `http://127.0.0.1:8000/api/v1/creative-mcp`。稳定随机token与原用户1绑定只保存在既有ignored/0600 runtime.env；正式HTTP握手及真实Codex客户端读取通过。以下各批“不启用正式库”是当时的历史，详见 `ALIGN_CREATIVE_LOCAL_ENABLEMENT.md`。

文件分工：

| 文件 | 责任 |
|---|---|
| `apps/api/app/services/creative_mcp.py` | 工具白名单、严格参数、受限投影、既有领域服务委托 |
| `apps/api/app/routers/creative_mcp.py` | loopback/Host/Origin/token、JSON-RPC、初始化及 HTTP 约束 |
| `docs/CREATIVE_EXECUTION_MCP.md` | 接入边界、协议、验证状态及主线待办 |

## 配置与接入

仅在获准的隔离运行环境或后续明确授权的正式接入中，由操作者把 `AICS_CREATIVE_MCP_TOKEN` 和 `AICS_CREATIVE_MCP_OWNER_USER_ID` 加入既有 ignored runtime 配置。token 应是随机生成的 32–512 个 ASCII 字符，允许字母、数字及 `._~+/-`；owner ID 必须是数据库中已经存在、激活且角色为 editor/admin 的用户。缺配置返回 503，身份不可用返回 403。每次 POST 都重新查询 owner，不建号、不采信 `X-Studio-User`、email 或 role 声明，不使用默认身份。

Agent 使用 Bearer 请求头；不要将真实 token 放入本文、Settings、SystemSetting、日志、截图、导出的诊断或版本库。认证使用固定长度 SHA-256 摘要的 constant-time 比较。

入口验证实际 ASGI peer 是 loopback；Host 只接受 `localhost`、`127.0.0.1` 或 `[::1]`，必须显式带当前 socket 的端口。Origin 可以缺省；若存在，必须是相同三个精确主机之一，HTTP/HTTPS，端口为当前 API socket 或既有 Web 5173，无路径、查询、fragment 或 credentials。端口须在 1–65535 内；不接受域名后缀、尾点、无端口、`null` 或其他本机端口。拒绝重复关键请求头及 Forwarded、X-Forwarded-*、X-Real-IP。

主线已在 `main.py` 注册此 router；运行仍须仅绑定 loopback，入口拒绝所有转发身份头。不建立新启动脚本或代理。正式schema/token接入已完成，不表示所有Agent客户端已经全局注册；正式验收的Codex配置仅作用于子进程，不改全局配置或本聊天工具清单。

## 协议

本实现提供 MCP 2025-11-25 最小 JSON Streamable HTTP 子集。按官方 [传输规范](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)、[生命周期](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)、[工具](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) 与 [资源](https://modelcontextprotocol.io/specification/2025-11-25/server/resources) 核对：

- POST 使用 `Content-Type: application/json`，Accept 同时包含 `application/json` 和 `text/event-stream`；请求响应为 JSON，无 SSE。
- 先发送 `initialize`，包含 protocolVersion、capabilities、clientInfo.name/version；服务端协商唯一支持的 2025-11-25。随后 `notifications/initialized` 返回空体 202，才允许普通操作；ping 可在初始化前使用。
- initialize 之后的请求须携带 `MCP-Protocol-Version: 2025-11-25`。不支持的版本返回 400。
- 无 MCP-Session-Id、连接专属会话或事件回放。初始化就绪门槛只在本进程内按单一 token/owner 绑定共享，不隔离同凭据的多个客户端；更换 token/owner 或重启隔离进程须重新初始化。每个客户端仍应完成自己的握手。
- 支持 ping、tools/list、tools/call、resources/list、resources/templates/list、resources/read；固定目录一页，无 cursor。没有服务端请求或采样。只接收 initialized/cancelled 通知；通知不能调用工具或写业务数据。
- GET/DELETE/HEAD/OPTIONS 返回 405 和 `Allow: POST`，安全验证在此之前执行。

请求上限 256 KiB，参数 64 KiB，JSON 深度 24，单个字符串 8192 字符（超界拒绝，不截断），响应 2 MiB，请求头总量 8 KiB，读取 body 最长 10 秒。长度检查先于共享脱敏正则；共享模式消除重复扫描/空白回溯，解析和检查在线程池完成。拒绝 batch、重复 JSON key、非有限数字、异常 ID、额外顶层字段。业务参数 strict/extra=forbid，领域服务继续校验 metadata、scope、currentness、executor、CAS、权利、终态和数量合同。

响应携带服务端生成的 `X-Creative-MCP-Trace`；错误只有固定 code/category/trace_id 和安全状态，不输出原始异常、输入校验内容或凭据。工具领域错误用 `isError=true` 和相同 text/structuredContent。返回超界或被脱敏拒绝时，已成功的领域写入可能已提交；若返回 `read_execution_before_retry=true`，先读原 execution，不重发外部执行。

共享输入扫描覆盖 Google/Stripe 凭据、编码赋值和云存储签名 URL；最多三层解码与 NFKC 仅用于扫描，不改正文/hash。敏感 RPC ID 在响应 ID 赋值及业务 dispatch 前被整体拒绝，错误使用 null ID，不回显原值。普通非秘密 URL/ID 保持正常语义。

当前配置的 MCP bearer 另做精确扫描：覆盖 JSON 的键和值，先限制字符串大小，再 NFKC＋最多 24 轮百分号解码；达到界限仍未收敛直接拒绝，不把编码 token 当普通 ID/metadata 保存或回显。解码只用于检查，正常输入和内容/hash 不改写。

## 工具与资源

| 工具 | 边界 |
|---|---|
| get_context / get_package / get_execution | 显式 project_id/unit_id，加精确 package_id/execution_id；context 只返回当前元信息、Brief 摘要和 Identity/Fact Boundary 指针，不读原始 Source；冻结包可返回该包明确包含的内容 |
| find_capabilities | 先验证真实 project/unit/context，返回所有适用 saved/pinned 方法的 exact revision/scope/hash；不隐藏合并，不自动选赢家 |
| use_capability | 明确选择 artifact_id/revision_id 与有界参数；共用方法库服务，返回确定性内容并记录 CapabilityUse，不执行方法代码、不改正文或业务配置 |
| claim_execution / start_execution | 只操作已准备的当前执行；expected_revision 和完整 executor kind/key/version 必填 |
| materialize_inputs | 原领域服务返回私有 work_root 和精确输入相对路径/hash；不开放任意读文件 |
| report_progress / report_blocker / report_checkpoint | 只通过原 transition/CAS；不开放任意 action/state/recovery 字段 |
| submit_output | 仅 `outputs/<filename>` 相对路径；原服务校验 regular file、无 symlink/traversal、MIME/大小/hash/role/index/attempt |
| mark_unknown / reconcile_unknown | Unknown 不重试；对账必须有 observation_hash、summary、明确 resolution/dispatch certainty |
| request_human_review | 只在 result_ready 写入持久的安全 summary；不接受输出、不改内容、不审批 |

资源 URI 使用 `aics://projects/{project_id}/units/{unit_id}/context`、`packages/{package_id}`、`executions/{execution_id}` 或 `capabilities`（后三者同一 project/unit 前缀）。资源委托同一读取接口；URI 不能表示本地文件。`aics://creative-mcp/status` 按当前数据库是否具备三张方法库表报告 availability；代码已接线不等于正式旧库已启用。

`use_capability` 只记录使用事实，不批准方法、成果或内容。普通 Capability promotion 仍是人的 UI/API 动作；MCP 没有 promote/import/enable Skill 工具。使用失败不自动重试；若响应提示 `read_capability_use_before_retry`，先核对使用记录，不把它当执行已成功或重新 dispatch 的依据。

不提供 package prepare/create、execution prepare、accept/decide output、Master/Variant save、Candidate approval、Delivery、发布、SQL、安装插件或任意文件读写工具。MCP inventory 不探测 provider，不调用专业工具。

## 输入落盘与恢复边界

精确输入先完成所属关系、当前包、live rights 与字节/hash 检查，然后 CAS 提交累计输入 manifest 和审计，最后才开放私有输入文件。写入失败不会删除已记录的派生权利边界，子集重试也不能缩小它：

`检查 → 累计 manifest/Audit commit → 私有文件写入 → executor 使用 → 接受时再次 live 检查`

文件发布由目录 descriptor 锁保护。pending 名绑定精确目标和内容 hash；显式重试同一文件时，只有 uid/私有模式/regular file/单链接及预期字节前缀可证明的零字节或半写副本才清理。link 后中断留下双链接时还必须是目标的相同 inode 和完整字节；清理后 fsync。不会覆盖不同字节，也不清除未知输入或外部硬链接。扫描预算兼容既有 500-output 历史上限，不改变原合同。接受时检查输入目录与累计 manifest 一致，未记录的文件/符号链接继续阻断。正式素材和累计数据库记录不由这条恢复路径删除。

已经接受的外部派生素材再次作为输入或进入 Candidate 时，也递归核对原输入的 exact revision/hash、live rights、归因和许可义务；加工后的新文件不能绕过祖先撤权。

## 整合待办与验证记录

主 Agent 已接入 router，并在原 `creative_executions.py` 补齐共同 ProjectEvent/AuditLog 原子审计及 checkpoint 精确 execution/package/executor/revision 绑定；prepare 不允许未 claim 的实际 checkpoint_ref。Claim 证据保留于 ProjectEvent，不依赖可清理的 AuditLog；更换 checkpoint 清除过时观察，所有对账都匹配原执行者。MCP 直接调用这些服务并返回 checkpoint_binding，不建立第二套审计或 checkpoint 真源。

2026-10-04 本组验证：新建独立临时 SQLite，TestClient 仅挂载本 router；初轮 73 项传输/安全断言通过（初始化、202/405、Host/Origin/peer/token/owner、白名单、严格参数、请求大小/深度和无自动建号）。新增字符串前置限制后，新鲜 63 项传输、实际所属单元读取、外来 ID、明确 Capability unavailable、委托参数/CAS/owner、错误脱敏与输入/响应长度断言通过；Ruff 和两文件 AST 解析通过。业务写操作采用领域函数替身检查参数委托，不能写成已完成实际 CAS/成果接受链路。未生成永久测试，未访问主 Agent 的 `/tmp/aics-align-ui-mcp.cVc6Qr/studio.db` 或正式库，也未向真实 API、Provider 或专业工具发送请求。

主线随后用真实隔离 HTTP/数据库/存储完成 Test Agent：claim→精确 input materialize→checkpoint/start→output staging→页面人工接受为 MaterialRevision/明确项目引用。多必需输出拒绝后可同槽位重提新 attempt，旧行保留，全部必需输出接受后才整单 accepted；正文未自动修改。实际安全负向及浏览器证据见 `ALIGN_CREATIVE_UI_MCP_ACCEPTANCE.md`。

敏感文本正则的 scheme 搜索和重复空白回溯均已修正，敏感内容拒绝语义保持；254119 字节认证 MCP ping 为 0.1458 秒。共同审计/checkpoint 与 UI/领域路径实际复核已完成，独立 SPEC/Python/TypeScript/安全均 APPROVE，范围见阶段验收文档。

2026-10-05 第四批 Capability Memory phase 10 已通过隔离实测：initialize/initialized 后真实 HTTP `find_capabilities` / `use_capability` 返回适用精确版本/范围/hash 并记录使用；外来范围拒绝。方法只渲染返回，不自动执行、保存正文、批准或发布。owned `GET /api/v1/capability-memory/uses/{id}` 可核对已有使用结果，foreign 404；不以未知响应自动重试。最终校验及限制见 `ALIGN_CREATIVE_CAPABILITY_MEMORY_ACCEPTANCE.md`，正式旧库仍未启用。

2026-10-05 第六批实际 Codex 客户端验证：已安装 `codex-cli 0.160.0 app-server` 通过隔离子进程参数连接 `127.0.0.1:15431`；initialize/initialized、15 个工具目录、资源清单及 owned Project 1 / Unit 4 context 的 `mcpServer/resource/read` 均成功。没有创建聊天或模型 turn，没有执行领域写操作，没有修改用户全局配置；不是 Test Agent 替代真实客户端。CLI 的 runtimeStatus 返回 null，仅记录已实际完成的握手/目录/资源读取，不推断未返回的运行状态。

同批 descriptor/recovery 输入复用原服务与 CAS/checkpoint 绑定：能力只代表声明，revert/recover 还需精确原 checkpoint、观察 hash 和 executor readback，Unknown 不自动重发。两条受控实际文件恢复及新进程 hash 读取通过。安全窄修后真实 Codex 读取复验、325 项临时边界检查与完整后端通过，独立安全/SPEC APPROVE；本批隔离 API/Web 已停止，证据保留。

最终状态（2026-10-05）：整个change实施验收147/147、三类独立复核APPROVE，日常导航完成收敛；详见 `ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md`。真实专业工具恢复/自动化pilot在第一版范围之外；受控文件checkpoint/recover的通过不等于专业工具已验收。正式启用、schema升级、canonical sync/archive、提交/push/deploy均未执行。第六批详情见 `ALIGN_CREATIVE_RECOVERY_PREFERENCES_ACCEPTANCE.md`。

2026-10-05 最终 MCP 独立只读复核 APPROVE：441 项合成内存断言通过；父层实际 HTTP 另确认 encoded ID/metadata 在账号读取与工具调用前拒绝、错误 ID 为 null，普通 ping 正常。实际 MOV `ftyp qt  ` 优先识别 QuickTime，普通 MP4/M4A/WAV 检查保持。全 change 的后端/前端最终复核单独记录，MCP 通过不替代它们。
