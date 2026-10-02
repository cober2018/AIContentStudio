# Model capability routing

2026-10-02 真实 H3 探针：本机 MiniMax CLI 单次 5 秒任务 `448101822222777` 远端 `succeeded`，证明账号可提交/完成 H3；产品安全下载因当前 VPN 将成品 CDN 解析成 `198.18.4.255` 而拒绝，MP4 字节/正式素材/权利未验收。CPA 三模型在本地已登记且 Gemini 为默认，但 `/models` 当前仍鉴权失败；不调用 Gemini/Grok 代替视频。现有目录、依赖、启动方式不变，任务仍 15/23，后续只恢复原任务，不重发。

## 2026-10-02 本批任务与外部证据边界

持久任务的安全只读视图与前端历史现明确显示 frozen route reason：模型自身、显式工作流模型、显式插件或已授权自动插件。既有 Plugin/Model Registry 和计划仍是真源，没有新持久对象；Workflow/ASR/浏览器端到端尚需单独验收，因此不提前勾 2.6。

task 2.5 的遗留“native”范围字样已与当前 CPA 决策对齐：只对已实证的精确操作合同和固定 MiniMax CLI 做 dispatch；Google/xAI 官方专用适配器不再被暗中加回验收条件。

同步 CLI 若已发出请求但本地退出非零、输出缺失/空白/超限，现保留 `unknown` 而不是标成可再次提交的 `failed`；已提交的一次性 claim 不重置。三个无供应商离线分支探针已通过，完整并发、真实视频、ASR、权利和浏览器复核仍开放。这是现有 Unknown 契约内的安全修正，不扩产品功能或新增表。当前 15/23，余 8 项。

MiniMax ASR 的 CLI 非零退出保守返回 Unknown；通用 provider 异常仍保留现有 502 脱敏契约，不能把它说成已统一防重复。其建议收据非 durable task，后续安全/并发验收仍开放。

九项剩余任务按已批准范围继续处理。本机 `mmx 1.0.27` 的 image/video task/TTS/ASR 帮助与当前固定参数一致；现有路由及 F7 持久化回归 83 项通过。这些是本地操作合同和回归，不是 CPA 的真实聊天 ID/媒体协议、MiniMax 视频原任务、许可或浏览器验收。第三方 CPA 此前 `/models` 返回 401，仍只作为登记/聊天兼容配置，不因 Gemini/Grok 名字赋予媒体能力；Google/xAI 官方直连不是当前要求。已同步 [适配契约](../../../docs/FE_F7_PROVIDER_ADAPTER_CONTRACTS.md) 与 [F7 能力矩阵](../../../docs/FE_F7_CAPABILITY_MATRIX.md) 的当前状态；F7 一般账号范围和 F8 生产身份/存储门槛均未因此解除。本批未调用收费供应商、不重发 Unknown、未改默认配置、未推送/部署或执行正式迁移。

## 2026-10-02 CPA 范围校准

用户确认 Gemini 与 `grok-4.7` 均由第三方 CPA 网关提供。本变更不再要求 Google/xAI 官方专用适配器；原 task 2.2/2.3 从范围移除，不计已实现。复用现有可配置 OpenAI-compatible 厂商/模型登记和聊天路径；生图、视频、TTS、ASR 必须按网关实际逐操作协议验证，不支持时仅可在发送前选择已配置且可执行的对应插件，或显示不可用。MiniMax CLI 原任务、私有字节、显式接受与 Unknown 不重发边界不变。当前 15/23，余 8 项；并无新的 CPA 媒体或 Google/xAI 官方能力验收。

目录仍由 proposal/design/tasks、`specs/model-capability-routing/spec.md` 组成；依赖和启动方式见下方“依赖与使用”，无新迁移或默认路由变更。待完成：CPA 实际聊天/媒体契约证明、MiniMax 可靠性与产品验收、最终门禁；不把范围删除计为功能通过。

## 2026-10-02 本轮验收与修复

当前14/25；routing3.5旧复合证据不足，先重新开放再补本轮门禁并关闭。精确f7d在隔离SQLite/原生PG往返、非法记录/retained downgrade、同名CHECK/UNIQUE/type/PK/index漂移，以及literal空格/NOT VALID/partial index负向验证通过。accepted重放重新验证live/source/receipt/private bytes/精确素材与父Material/库中实际字节。所有补丁后全量1661 passed/28 skipped，实际前端build/预算、strict33/33、范围Ruff/diff通过；限定独立复核APPROVE（主agent实际PG与复核员metadata/SQLite验证分开记录）。目录/依赖/启动不变，无新迁移版本/持久测试文件、真实Provider调用、生产迁移或默认变更。原job/幂等/回滚等合成探针不替代3.4完整并发接受/崩溃和真实供应商验收。

## 2026-10-02 实际产品任务增量（仍11/25）

固定image/TTS submit_task已接；图片明确预算内512–2048、8倍数正方形尺寸，base64避免CLI CDN下载/重试。真实隔离TTS经chat-only→plugin→持久claim→实际WAV→result_ready、新进程验签/hash回读通过；图片25秒截止unknown、无job、不重发。没有接受入正式素材库，也没有新浏览器或独立复核；2.4/2.5/3.2等包含多能力完整契约，不能仅因单条语音成功就勾完。Google/Grok用户暂缓不计PASS；既有依赖/启动/显式生产key与schema前置不变，不改默认配置、不运行生产迁移。

## 2026-10-01 认证连续性规格修订

用户已授权本机受控读取 MiniMax CLI 官方认证配置。实现仍必须只读官方固定路径、只解析已知认证字段；原始凭据不得进入数据库、日志、任务 receipt、前端或素材，仅允许持久化受控 receipt key 生成的不可逆 HMAC `credential_epoch`。缺少安全读取条件时继续 `credential_continuity_unverified` 阻塞；本次只完成规格修订，未读取实际配置或发起真实生成。

实现状态：已加入固定配置路径的权限/字段检查与 HMAC 指纹计算；本机当前缺少稳定 receipt key，因此实际仍安全阻断，未发起真实生成。相关完整测试受环境缺少 `pypdf` 影响，定向路由回归可通过。

## 2026-10-01 Video ASR输入续批（仍11/25）

minimax_cli_provider.py已补精确MP4→首音轨16kHz/mono PCM WAV，固定file-only probe/decode/extract共用4096字节诊断上限和剩余deadline/进程组回收；真实来源/音轨时长不得超过请求或500秒，不裁剪补造。既有建议/接受/Save Master仍独立；不创建新素材或直接修改Master。下方“仅WAV/MP4待接”为历史，本批仍缺真实转录/完整路由/Workflow/认证连续性验收，不勾完整2.4/2.6/3.3。依赖及启动沿用ffmpeg/ffprobe和现有API；无新测试代码/真实供应商/生产迁移/默认改变。

独立复核发现并修复预校验deadline/诊断界限及字节MIME缺口；最终限定源码APPROVE。共享模型库存还保留credential_continuity_unverified与合法loaded runtime，明确executable/verified为false，不抹成未加载。现有回归不是新输入边界全覆盖，真实账号/转录/浏览器及整体F7/F8门禁仍未完成。

## 2026-10-01 MiniMax原任务协议续批（仍11/25）

本机官方CLI源码/帮助核对后，新增H3 async taskId提交、固定model/protocol原任务query（不加quiet），H3内存URL经HTTPS公网DNS固定/同源redirect/无环境代理/无凭据header/30MiB限额下载；旧V1只保存原file_id并明确下载unavailable。没有安全credential-version证明时仍blocked，3.2不提前完成。目录/依赖/启动仍沿用上述service与已有API，未运行真实供应商、生产迁移、默认改动或新测试代码；完整Workflow/ASR/外部验收TODO。

独立初审三项修复后，下载用spawn隔离进程硬截止DNS/慢速响应，H3输入限制7000 UTF-16单位，expired保持unknown+原job。修订后既有全量1661 passed/28 skipped（8 warnings）、Ruff/strict33/33/diff通过，限定源码复审APPROVE；无前端改动或本批build/浏览器结果，不把现有测试等同新增协议全覆盖。

## 2026-10-01 结果与前端消费者续批（仍11/25）

generation_tasks新增同MP4字节ffprobe真实时长限额，私有generation存储补0600/0700、fsync及原子无覆盖落盘。现有ProviderMediaPanel补登记模型/能力/单份限额→仅prepared→独立确认一次execute，并展示冻结路由、可重选原prepared；Unknown保留幂等键，不通过结束准备创建替代任务。完整Provider身份/submit/query及Workflow/ASR、浏览器尚未完成，3.2/3.3不提前勾选。未新增测试代码、调用生成、改变默认或迁移生产库。

本批最终门禁：既有全量1661 passed/28 skipped/8 warnings，TS/Vite/FE-P1、Ruff、strict33/33和diff通过；限定目录持久性/最终UI独立复审APPROVE。不是新状态机全部覆盖或真实供应商证明，整体任务仍11/25，无生产迁移/提交/推送/归档。

## 2026-10-01 持久任务apply首批（11/25）

3.1单表/加法迁移及部分3.2/3.3框架已实现：签名、owner/idempotency/CAS/claim、原job查询、私有结果、人工原子接受；materials generation-tasks API与前端回读/查询/预览已接。MiniMax安全身份/真实dispatch、视频时长、Workflow/ASR和创建执行UI仍待完成，不提前勾Batch B或3.2–3.5。

本轮现有全量1661 passed/28 skipped，TS/Vite/预算、Ruff、strict33/33、diff通过；隔离SQLite up/down/up及PG兼容DDL编译通过，独立最终复核仅APPROVE底座。无新测试代码，未覆盖所有新状态机验收。运行需local存储、显式稳定AICS_GENERATION_RECEIPT_KEYS/AICS_GENERATION_RECEIPT_KEY_ID及另行授权的f7d迁移；启动不自动建表，缺key/schema或CLI身份证明fail closed。无额度消耗/默认变化/生产迁移/提交/推送/归档。下方待确认/无模型/API文字为历史阶段记录。

## 2026-10-01 持久任务修订（待实施确认）

用户同意先补持久生成任务方案，现proposal/design/spec/tasks已同步：只新增一个ProviderGenerationTask表，原job恢复不重发，私有字节结果可重启回读，人工接受原子写既有MaterialRevision。计划3.1–3.5按两大批执行；配置/Registry/Workflow/资产真源不复制。下方“无新增迁移”描述已完成代码，不代表修订实施后仍零表。尚未新增模型/迁移/API，不调用收费生成、不改默认、生产库不自动升级。依赖及启动方式保持现状。

## 需求背景
用户要求平台适配模型与生成插件，手动标注聊天/生图/生视频/语音等能力，并在选定模型缺能力时自动路由到配置插件。自动调用仅限预授权范围和硬上限。

## 目录结构
- proposal.md：范围、动机与F7补充关系。
- design.md：配置/能力/插件/预算/执行冻结与供应商协议设计。
- specs/model-capability-routing/spec.md：新增运行契约。
- specs/product-settings/spec.md：Settings增量，原主规格保持不变。
- tasks.md：原两大批20项及已授权持久任务增量5项，共25项。

## 已完成

图片CLI新增实际型号证明：固定prompt本地dry-run只解析白名单request.model，当前安装结果image-01；binding和发送前精确校验，图片runtime hash纳入实际型号。不展示/复制原始request/headers；image-01-live并未因名称合法而获得执行资格。缺失/不匹配返回unavailable，不发生成请求。认证版本与完整供应商链路仍未闭合，Batch B不提前勾选。

MiniMax ASR：核对本机CLI help与[官方转录协议](https://platform.minimax.cn/docs/api-reference/speech-to-text)，固定SRT/句段时间戳，并转换为现有ASR建议格式；时间/长度/数量严格验证，不凭纯文本估算时间。仅WAV已接，MP4音频提取待完整实现。正常两句字幕与6类非法输入零网络探针通过；不新增测试文件，不直接持久化Master，不把转换器当真实账号verified，task2.4–2.6保持未完成。

MiniMax 输出边界修复：`minimax_cli_provider.py` 使用固定argv、有界pipe读取（stdout+stderr合计512 KiB）、单一deadline和超限/超时进程组回收；临时输出只读30 MiB+1并拒绝超限，超时/超限结果保持Unknown不重发。正常输出/单流及合计超限/超时零网络探针通过，现有路由+媒体+ASR回归93 passed；不新增测试文件。完整CLI dispatch、ASR cue、视频任务恢复、认证版本与真实额度验收仍未完成，task2.4/2.5不提前勾选。无需新增依赖或迁移。
用户“开始执行”已授权 apply。当前实现版本化能力声明/绑定、CAS 保存、Registry-based resolver、frozen plan/revalidate 和 Settings 按需加载编辑入口；Google/xAI/MiniMax native adapter descriptor 已加载，但实际 dispatch 尚未接入，因此真实配置仍 blocked，绝不以声明或测试fixture冒充可执行。未请求供应商生成、未新增迁移。

## 待完成

本地CLI参数纠正：Video/TTS对未实现的source bytes/refs和未知model在发送前拒绝，不让结果挂上未使用来源。纯文本Video已支持的CLI型号为MiniMax-H3/MiniMax-Hailuo-2.3，Fast/SEF/S2V的精确参考输入尚未接，不标可执行。model默认显式传argv；image精确型号选择在当前CLI schema里缺失，需解决后才算完成模型路由。零网络探针和现有定向回归通过，task2.4–2.6仍未完成，无新依赖/迁移。

MiniMax binding-state已关闭未实现chat/未知capability的假可执行状态，媒体allowlist保留；修复后零网络探针和93项现有回归通过。输出边界批全量1661 passed /28 skipped，其启动早于binding-state补丁，不能代替该补丁完整终验。Batch B仍未验收，不切换默认模型/插件优先级，不执行真实生成。
Batch A 已按 tasks.md 关闭 1.1–1.10；共享 resolver/计划冻结核心、Workflow/Production 规划消费者和 Settings 编辑均已实现。真实供应商媒体 dispatch、浏览器验收和付费额度仍不在本地配置验证之内。

## 官方协议核查（部分完成，task 2.1 仍未勾选）

2026-10-01增量：MiniMax image/TTS/ASR与旧video query/download公共契约已实际读取，下方“MiniMax图像读取失败/未取得协议”为此前记录。TTS使用完整hd/turbo模型ID，拒绝系列简称与>=10000字符；ASR声明/实际WAV均不超过500秒与请求限额。H3创建协议仍读取失败，license/认证版本/原task恢复与完整路由未闭合，不把旧video endpoint当H3协议；task2.1/2.4保持未完成。无新依赖/迁移/默认配置/生成请求。
2026-10-01 只读取公共文档，没有模型调用或账号探测。Google 当前图像文档列出 `/v1beta/interactions`、API-key header 与 base64 image 输出；需继续核对兼容 generateContent、响应界限和各模型参数，不能把品牌/用户口述版本直接当能力支持。[Google 图像官方文档](https://ai.google.dev/gemini-api/docs/image-generation)。xAI 图像支持 base64 响应；视频是 POST 建任务、按原 request_id GET 结果，不能拿 URL 或 job ID 冒充已生成字节。[xAI 图像](https://docs.x.ai/developers/model-capabilities/images/generation)、[xAI 视频](https://docs.x.ai/developers/rest-api-reference/inference/videos)。MiniMax 图像目标文档读取失败，尚未取得完整 image/video/TTS/ASR 契约；Google/xAI 其他能力与 license/下载安全也未核完，任务保持未勾选。

当前已落地 `native_model_adapters.py`：Google/xAI 的精确模型/端点/认证边界与 MiniMax 的显式 unavailable 已注册到既有 Registry；该批只构建无网络请求契约，不代表外部账号或付费操作已验证。完整记录见 `docs/FE_F7_PROVIDER_ADAPTER_CONTRACTS.md`。

## 关键设计决策
复用SystemSetting/Registry/Run/MaterialRevision；声明不等于verified；自动fallback不得绕过Unknown或预算；真实性素材不可由生成代替；Commons暂缓不算PASS。

## 依赖与使用
沿用现有OpenSpec/API/web依赖与启动方式。active User可读 `/api/v1/settings/model-capabilities` GET 与无网络 `/plan` POST；仅管理员可PUT，提交 expected_revision，冲突409保留编辑。内部冻结计划含HMAC签名，当前process-local：重启/跨worker旧签名fail closed需显式replan，不改历史；生产签名key/rotation与消费者授权仍待实现。`OPENSPEC_TELEMETRY=0 openspec validate add-model-capability-routing --strict` 检查规格。完整后端测试须从apps/api运行，私有临时数据库隔离；web纯状态回归 `node scripts/test-model-routing-state.mjs`，构建 `npm run build`，无新增依赖；无密钥或实际账号信息。
