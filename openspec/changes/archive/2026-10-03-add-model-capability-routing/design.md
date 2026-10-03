## Context

基线main@da73bbb及已批准dirty F7工作区。ModelProfile只有mock/openai_compatible与enabled；models.routes按文本purpose选择Profile。image单独持久化；image.openai只接受明确OpenAI协议，不能用更换品牌名替代适配。Video/TTS/ASR已有typed协议但无真实注册。SystemSetting/runtime配置、Registry、LLMRun、provider_calls、provider_media、Workflow Attempt是真源，必须复用。

用户确认缺能力时自动调用预配置插件，无需每次另问；仅在配置授权预算内。Commons暂缓。此前已验证图像/视频/证据/审批安全边界不可削弱。

## Goals / Non-Goals

**Current account acceptance scope (2026-10-03):** 用户明确排除 MiniMax 视频生成及 H3 原 job 下载验收，停止其请求/查询/重试，不作为本轮 F7 blocker，也不记为 verified。用户所述套餐限制视为账号范围决策，不能推断所有 MiniMax API/模型均无视频能力。保留原任务与协议/Unknown 安全历史，不新增默认或静默 fallback。MiniMax 后续验收为文字转语音、语音转文字、已有视频→已验证音轨→ASR；最后一项只转写声音，不生成视频或理解画面。新真实调用须先明确输入、次数和时长上限；配置/密钥和 generic video 运行机制不因本记录而被修改。

**Goals:** 任意模型可配置并手动声明能力；受支持协议能真实执行；模型与生成插件统一路由；Settings配置完整、执行选择可解释、费用与Unknown受控。

**Non-Goals:** 自动下载执行任意插件、默认相信模型自报能力、接通所有世界供应商、免凭据真实调用、跨品牌伪兼容、生成新闻证据、发布后改稿、生产部署、多租户改造、自动重发微信。

## Decisions

### 1. One configuration truth, three independent facts

扩展SystemSetting models配置为版本化envelope（schema_version、revision、profiles、routes、media_plugins、policies），通过既有服务原子CAS保存并刷新缓存。Profile保留稳定ID/name、enabled及既有文本字段，新增declared_capabilities及capability_bindings。能力首批chat/image_generation/video_generation/tts/asr；理解图像/视频与生成严格分开。每个binding显式指定adapter_key/version、model_id、connection/secret引用、参数约束；同一品牌可有多个模型/端点。

effective能力是管理员声明、已加载adapter支持、完整配置、输入参数与授权策略的交集；声明/配置/实测验证三列独立，不能把勾选当verified。配置GET与启动不探测供应商。保留mock仅开发夹具，不把它列为真实生成能力。

替代方案“按模型名称猜能力”不可维护且不诚实；替代方案新Model/Asset表与现有真源重复。2026-10-01用户同意修订持久任务方案：仅放宽一个ProviderGenerationTask任务表，配置/资产/Workflow真源不变；额外持久对象仍需另行确认。

### 2. Plugins are explicit registered execution bindings

media_plugin有稳定ID、enabled、declared能力、Registry key/version、model_profile_id/capability binding、参数上限。Plugin描述符实际支持能力必须来自加载Registry；配置不是任意代码执行许可。插件可以调用不同供应商，也可以指向MiniMax等同一模型Profile的专用生成binding；不能要求聊天模型本身具备生图才允许它调用生图插件。禁止环形插件路由、悬空引用、未知协议和任意URL返回后无校验下载。

### 3. Deterministic routing and frozen plan

任务携带purpose、required_capability、所选Profile、输入类型/来源refs、参数和权限；Workflow节点可显式固定binding，不可被全局默认覆盖。顺序：显式节点binding（缺能力则阻塞）→所选Profile可执行的同能力binding→该能力预配置的有序plugin fallback/default。selected Profile无法执行时生成route_reason，不静默丢弃用户选择。fallback仅允许配置中已授权候选，不能遍历全部模型。

plan固定configuration revision、Profile/Plugin IDs、adapter版本/runtime identity、model、参数、input_hash、source refs和预算授权；dispatch前CAS/live revalidate，历史Attempt保持原plan，不被配置变更重写。文本purpose路由继续兼容；聊天、媒体、Workflow和Production复用同一resolver而非各自维护合法能力表。

纯SHA只证明内容校验，不证明服务端原始计划。当前开发进程使用服务端HMAC签名固定plan摘要；客户端重新计算SHA仍不能伪造授权意图。进程重启/跨worker签名验证失败必须显式重新规划，历史计划只读保留，不静默改写。当前消费者尚未dispatch；生产多worker接入时需明确受控共享签名key/rotation配置，并仍从实际任务派生输入/来源与actor授权，不能把客户端自报hash或签名当事实/权限证明。

```text
Task capability → explicit binding / selected model
                                  ├─ executable → pinned plan
                                  └─ unavailable → configured plugin → pinned plan
pinned plan → budget/live gate → adapter → actual bytes/transcript
                                         → preview → explicit acceptance/save
```

替代方案“模型自主决定插件”无法保证预算和审计；模型可建议，但服务端确定执行计划。

### 4. Budget is authorization, not an invented billing ledger

用户在配置中明确allow_automatic_fallback与每次请求的数量/图片尺寸/视频或语音时长/token上限、超时、可选币种金额上限。未设置安全上限不得无限执行。金额上限必须基于明确的版本化计价/可证明最坏成本，无法估价时拒绝无人值守付费执行而非按0计算；只配置结构上限时UI不得承诺货币总额可控。应用硬限制与供应商账单区分；不声称现有系统已有每日共享预算账本。若要求累计/跨worker额度，必须补事务性预留与持久化规格，不能只用进程内计数。

自动fallback是能力缺失/发送前不可执行的选择，不是错误重试。发送后timeout/connection uncertain等Unknown保留现有Attempt/claim；不换模型重发。异步video只轮询原job ID，bounded polling、显式取消语义，不创建第二个job。付费真实验收另需额度授权；本次规格确认不发送请求。

### 5. Configurable CPA compatibility and bounded MiniMax, not brand-specific adapters

用户确认 Gemini 与 `grok-4.7` 均走第三方 CPA 网关。首批复用现有 OpenAI-compatible 厂商登记、密钥/模型配置与聊天路由；不开发、不要求验证 Google/xAI 官方专用生成适配器。已存在的无网络 Google/xAI descriptor 不表示可执行，不能自动启用或作为验收证据。CPA 按配置的 endpoint、实际协议和模型 ID 验证，而非按 Gemini/Grok 品牌推断能力。聊天兼容不意味着图片、视频、TTS、ASR 兼容；每种媒体操作只有在 CPA 提供精确且已验证的 endpoint/request/response/async-job/下载/授权契约时才能绑定通用版本化适配器，否则选择已经配置且可执行的对应插件（当前优先核 MiniMax CLI），或返回 typed unavailable。不得把聊天文本/URL当作生成媒体，也不得在请求已发送且 Unknown 后换插件重发。图/视频/TTS实际字节仍经有界TLS/SSRF/redirect/size/MIME/解码/hash验证；ASR保持显式接受。MiniMax 本地 CLI 仍按独立受控协议验证，不能因为 CPA scope 缩减而省略其真实验收。

复用provider_media：预览仅临时，用户接受后才写MaterialRevision与Project精确引用。Workflow生成是否自动入项目池沿已批准节点契约，不用本变更扩大授权。来源generated、真实provider/model/runtime/input/output hashes可查，rights/license需明确证据；生成内容不能作为现实事件拍摄证明或进入Fact Boundary。

### 5.1 Local MiniMax CLI is an explicit, bounded provider

本机官方mmx-cli 1.0.27源码核对：video generate --async返回JSON taskId；video task get --output json不加quiet才能保留task_id/model/status/url/file_id结构。H3提交显式duration4–15秒及7000个UTF-16 code units输入上限，且不同时等待/下载；查询传原model区分V2与V1。CLI下载默认5GiB、重试及自动redirect不能当系统安全门禁；H3短期URL仅在内存交给已有pinned_transport的30MiB/总deadline/HTTPS同源redirect、无认证header下载，校验结果字节后入任务。下载在独立spawn进程内进行，父进程按绝对deadline终止并回收，覆盖DNS阻塞/慢速响应而非只限制单次socket等待。expired保持unknown和原job，不当确认失败；V1 file_id下载没有安全元数据接口时显式unavailable，保留原file/job，不调用CLI默认下载绕过约束。身份连续性仍按5.2阻断，不因为接口代码存在就标verified。

官方协议优先于CLI帮助中的系列简称：TTS仅接受官方完整model ID，文本严格小于10000字符；ASR声明上限及实际WAV帧数/采样率时长均须不超过500秒，实际音频不得超过请求授权上限。只修改固定子命令发送前校验，不因官方文档列出型号就标记账号verified；认证版本、完整dispatch和真实验收仍待闭合。协议证据见 `docs/FE_F7_PROVIDER_ADAPTER_CONTRACTS.md`。

图片CLI没有独立model选择flag时，不凭型号声明猜测执行：固定prompt的本地 `--dry-run --output json` 只读取白名单 `request.model`，不投影原始request/headers。binding及发送前必须匹配同一实际型号，图片runtime hash包含该型号；缺失/变化/不匹配则不发送。2026-10-01本机dry-run为image-01，不代表image-01-live已接通，也不证明认证版本/实际账号/额度或生成成功。

ASR本地适配使用明确的 `asr-1.0`、`response-format=srt`、`timestamp-level=sentence`，CLI写入受控结果文件；按官方SRT协议把实际时间段严格映射为现有 `status/transcript/cues` 契约。无时间段、格式错误、重叠/越界、超长文本或输出超限均拒绝；不能从纯文本估算字幕时间，不能回填身份/证据或直接修改Master。当前只接受经既有解码门禁验证的WAV输入；视频音频提取仍待既定完整适配，不偷偷把MP4冒充音频传入。

本地输入闭合实施：复用Video Studio既有精确MaterialRevision及live model-use/hash证明；MiniMax适配器可在受控临时目录把经真实解码验证的MP4首音轨提取为16kHz/mono PCM WAV，再以实际WAV帧数验证请求限额和500秒上限。固定ffmpeg参数、file-only协议、单线程、30MiB输出界限和剩余deadline；不得裁剪超限来源、估计字幕时间或回写新的素材版本。缺音轨/工具/非法时长/超限时发送前拒绝，原MP4来源hash继续进入既有ASR receipt，成功仍只产生显式接受/Save Master所需建议，不自动改Master。真实转录/账号验证仍另行验收。

ASR执行指纹同时固定CLI runtime和受控credential epoch；缺失连续性证明时不可执行，原建议接受/提交前通过既有runtime复核拒绝凭据漂移。该读取只在明确ASR操作发生，静态ModelAdapter库存不读凭据。共享音频解码要求实际帧数大于零，不能将只有WAV头的文件作为成功结果。

media.generate 的输出别名不能覆盖服务端派生的 generation_task_id、generation_started_attempt_id、generation_state、reason、generated、material_revision_id、content_hash 或 media_kind；只有映射到自身的同字段保持兼容。定义保存、执行和 resume 共享校验，必须在任何供应商调用/恢复前拒绝冲突，避免 accepted 被别名替换后继续等待或精确素材血缘被覆盖。

新MP4输入路径先以真实字节MIME校验容器，再固定file-only ffprobe/视频帧解码/音轨提取；不复用旧MP4预校验的无界capture_output。媒体诊断stdout+stderr合计4096字节，所有命令与最终CLI共用同一remaining deadline及超时进程组回收。模型绑定投影保留已加载的合法runtime hash，但CLI缺认证连续性证明时reason为credential_continuity_unverified、executable/verified为false；共享resolver不得把这个理由抹成“未加载”或显示可执行。

本地个人生产环境可使用已安装的 `mmx` CLI，但它必须作为版本化、受控的 Registry Provider 接入，而不是允许配置任意命令或脚本。适配器只调用固定的 `mmx` 子命令，使用参数数组、非交互模式、输出/超时/文件大小边界。经用户明确授权后，适配器可以只读官方固定路径的 MiniMax CLI 认证配置，用于固定调用与检测认证上下文变化；读取必须限于受控本地进程和已知配置结构，不接受用户任意路径或任意字段透传。

认证配置只在进程内短暂解析：原始密钥、OAuth token、完整配置、CLI 原始输出和错误诊断不得写入数据库、日志、任务 receipt、前端响应或素材元数据。当前已知认证投影覆盖 `api_key` 以及官方配置可能提供的 OAuth access/refresh token、account identity、认证版本和过期信息；存在 OAuth 认证上下文时，所有已知凭据字段一并参与指纹，不能因残留旧 `api_key` 而漏检轮换。持久化的 `credential_epoch` 只能是由现有受控 receipt key 计算的不可逆 HMAC 指纹；没有稳定 receipt key、配置权限不安全、配置结构未知、认证字段缺失或认证上下文变化时，必须返回 `credential_continuity_unverified`，保留原任务且禁止恢复、接受、查询或重发。CLI help、masked key、quota 和模型名称仍不能替代认证连续性证明。

当前 CLI help 已确认的能力为 `text chat`、`image generate`、`video generate/task get/download`、`speech synthesize` 和 `speech transcribe`。帮助信息只能证明命令协议存在，不能证明账号额度、模型可用或一次真实生成成功；Settings 仍分别显示已加载、可执行、已验证。真实生成仍复用 `provider_calls`、原任务 Unknown/不重发、provider_media 的字节/MIME/解码/hash/rights、预览→人工接受链路。

CLI Provider 只允许本地 `mmx` 可执行文件，禁止用户输入的可执行路径、shell 字符串、任意参数透传和自动安装。图片/音频直接读取受控临时文件；视频只能等待或轮询同一原始 task/file ID，下载后的字节必须经过现有验证。文字 CLI 可作为可选文本路由，不替换现有 CPA 默认；生成媒体不能替代真实截图、新闻照片或事实证据。

### 5.2 Durable local generation tasks — revised proposal

用户已于2026-10-01确认修订稿并授权apply；以下为实施契约，不是已完成能力。本地就是用户正式使用环境，重启恢复不能依赖内存Preview、配置表、审计日志或虚构WorkflowRun。

当前切片仅使用local私有存储，MinIO任务输出明确unavailable，避免网络存储持有DB事务锁；以后扩远端存储需先完成传输与短事务分离。迁移目标显式为f7d000000001（F7c后），未启用F8草案只把down_revision后移以保持单head，不执行其身份升级。初始历史迁移按当前metadata建表，任务迁移仅对匹配形状幂等跳过；development init_db也不自动创建任务表。

结果实现边界：视频先复用真实decode，再以同一MP4字节的首视频流/容器实际duration核对冻结秒数上限；缺失、非法或超过限额均不入库。generation命名空间固定任务ID/hash路径；0700目录、0600临时文件fsync后原子无覆盖链接，并同步文件目录及新目录父项，重复写不同字节拒绝。现有普通素材存储语义保持。

产品准备与执行分开：读取配置不生成；显式选择模型/能力/单份尺寸或时长上限后只写prepared，再独立确认一次执行。同输入准备保留幂等键，unknown/submitting/running不能通过结束准备清键创建替代任务；重启显式选择已有prepared任务，不自动发送。列表显示安全冻结路由与限额，不把当前配置替换原任务。

first-send检查冻结configuration revision；恢复/接受不因无关配置的全局revision变化失效，而验证原provider/model/protocol及认证、实际runtime。收到原claim返回的job/结果先存证，来源撤权/项目归档/配置变动只阻塞后续使用，不丢弃已知job。CAS须同时匹配所读revision、state与lease token，不能仅使用客户端提供的未来revision。

跨重启信任与此前process-local规划签名分开：持久任务保存task_receipt_key_id及服务端HMAC receipt，绑定任务ID、owner、request_hash、原plan/runtime/credential_epoch。密钥来自显式受控本地secret配置，启动不得自动创建/轮换；只保存key ID与签名，不保存密钥。缺少稳定key时新持久任务在发送前blocked；重启只验原receipt，不重新规划已发送任务，缺key/验签失败仅允许安全状态读取、禁止恢复/接受。轮换保留只验旧key，撤销旧key则历史仍可读但不得执行。MiniMax历史credential epoch也必须用任务原receipt_key_id派生，不能因活动key轮换而误报凭据变更；新任务用当前活动key，实际API/OAuth变化仍阻塞原任务。原process-local计划仍按既有规则仅用于发送前规划，不能替代持久receipt。

credential_epoch由现有连接配置服务在受控认证更新时生成并随SystemSetting CAS持久化。对于CLI，本次授权的受控认证读取可以补足这一证明：适配器通过当前 OS 用户的官方固定配置路径解析已知认证字段，并以 `O_NOFOLLOW` 文件描述符读取后，在进程内组成规范投影，再用现有受控 receipt key 计算不可逆 HMAC；任何原始凭据都不得离开进程内存。该指纹必须纳入runtime/receipt且每次查询/接受复核。若配置无法安全读取、字段不完整、receipt key不可用或指纹变化，明确返回credential_continuity_unverified，保留原job与本地只读结果、不查询、不重发、不接受；支持这一blocked状态，不伪称MiniMax自动恢复已经成立。后续若改用官方安全身份接口，仍需锁定官方契约并保持相同的无密钥落库边界。

仅新增 `ProviderGenerationTask`，适用于独立素材生成及真实Workflow节点生成：稳定ID、owner_user_id、可空project_id、可空真实workflow_step_attempt_id、idempotency_key、request_hash、state、revision、固定plan及plan_hash、capability、provider/adapter/model/protocol版本、runtime_hash、credential_epoch（非凭据）、input_hash、精确source refs、规范化有界输入/参数及授权限额、安全provider_job_id/file_id、结果私有storage key/MIME/bytes/hash、安全rights/provenance摘要、接受后的MaterialRevision ID、lease token/expiry、timestamps及安全reason code。禁止保存密钥、原始响应/错误/签名下载URL或完整CLI配置。文本/提示词仅存本地受访问控制的有界请求；不在日志或公开列表暴露。ASR结果存有界文本/cues，不伪造成Material。

DB约束：owner+idempotency_key唯一；同key不同request_hash返回409；状态枚举/正revision/合法大小、可空关联FK及owner/project/state索引。request_hash包括输入、来源、模型/插件/runtime、参数、授权限额与任务作用域；重启不得修改原plan。配置凭据轮换用受控epoch显式标记；CLI只允许读取官方固定配置路径的已知认证字段并生成不可逆HMAC指纹，无法证明同一认证上下文则恢复阻塞，不猜账号。这里只保证单任务数量/大小/时长授权，不实现累计计费账本。

状态为 prepared → submitting → running → result_ready → accepted；failed/cancelled为确认终态，unknown为不确定态。发送前事务创建prepared并原子claim为submitting，事务提交后才调用供应商，绝不跨网络持有数据库锁。claim commit是dispatch授权线性化点：来源撤权先提交则不允许取得claim；claim先提交则允许该已冻结授权发送一次，撤权不追撤此claim，但阻止之后的新claim以及结果接受/复用。并发只能一个claim发送；进程在submitting退出后视为unknown，不能凭lease到期再次提交。仅确知从未进入发送claim的prepared可继续首次提交。已知job立即持久化再返回running；发送成功但job保存失败也是unknown，不重发。用户明确取消/远端查询确认失败才记录相应终态，杀本地进程不等于远端取消；已知job查询返回adapter unavailable不证明远端失败，必须保留unknown及原job，不授权重发。

恢复只读取原provider/protocol/model/job：MiniMax CLI H3查询显式原model，V1 file与V2 URL严格分派；无job的unknown要求人工对账，不自动新建或跨供应商fallback。查询有deadline、间隔、次数和并发上限；所有lease更新用CAS/claim token，旧worker晚返回不得覆盖新revision。任务/job不属于当前actor或项目、认证epoch变化、协议不支持或job过期均安全阻塞；不以过期证明未生成。所有输出均核对返回的job/file类型及既有身份，不能只在running分支检查；已知job的成功或确认终态必须回传同一job，成功字节还必须匹配已知file。缺失/foreign身份不得入result_ready、签成功结果或判定确认终态。

结果下载复用现有transport/MIME/decode/hash/大小/rights校验，临时私有文件校验后原子转受控storage并记录result_ready；崩溃孤儿文件可安全回收，丢失/篡改文件不得呈现有效预览或重新生成。重启按任务读取验证结果，不依赖旧Preview token；URL只是瞬时下载入口，不是资产。网络来源和下载redirect仍受原SSRF/TLS门禁。

接受必须显式、owner/project授权及live来源/rights/runtime复核，锁任务并在同一事务写MaterialRevision、精确Project引用与accepted关联；重复接受返回同一revision，部分失败回滚。既有Workflow自动入池仅保留已批准节点契约，不扩大自动接受。ASR复用既有显式建议接受与Master CAS，不创建第二个建议库。历史任务只读，归档项目不可提交/恢复写入/接受。

产品入口复用素材生成面板：提交、任务列表/详情、查询原任务、预览、接受/拒绝与unknown原因；无自动重发按钮，读任务/刷新页面不提交任务。Settings仍区分loaded/configured/executable/verified，不修改CPA默认或媒体优先级。

```text
固定输入/授权 → 持久prepared → 一次claim/submit → 原job持久化
                                └─ 不确定 → unknown → 原job查询/人工对账（不重发）
原job结果 → 私有字节/哈希/权利验证 → result_ready → 人工接受 → 既有MaterialRevision
重启 → 读原任务/原plan → 有界恢复或明确阻塞
```

### 5.3 Workflow durable generation linkage — apply authorized

2026-10-02用户明确同意本节方案并授权apply。源码核查时`generation_tasks.prepare()`尚未绑定真实Workflow Attempt、cover仍为旧路径、Attempt仅终态创建；本节是实施契约，不是验收声明。

- 只对显式选用新能力路由的新Workflow版本启用持久生成节点，保留历史v1/旧节点读取及执行契约，不静默迁移默认流程。
- 真正发送前先在同一真实Run/Step下追加不可变`started` Attempt，冻结输入与配置；ProviderGenerationTask绑定该真实Attempt。该记录不伪称成功，不创建虚构Run，不修改任何旧Attempt。终态另追加succeeded/failed记录，输出保留原task及启动Attempt标识，不能把started当可用生成产物。
- pending/running/unknown生成任务使生成节点明确等待，不执行下游、泛化rerun或创建替代任务；显式恢复只查询原job。无job的unknown保留人工对账，不通过新Attempt换幂等键重发。
- 原任务result_ready且精确字节校验通过后才收口节点执行结果；媒体接受保持独立人工确认，只有真实MaterialRevision才能进入共享素材/后续引用。不能把task ID、URL或供应商已受理当MaterialRevision。
- 前端须展示等待原因、task/Attempt血缘、只查原任务操作和独立接受；Workflow dirty/save仍独立。所有关联由服务端真实上下文派生，不允许独立素材API由客户端任意指定Attempt ID。
- 切换任务立即撤销旧预览/确认/权利选择；异步回读只接受最新请求且task/result ID/hash相符。恢复接受后复用既有output_mapping，接受前才缺失的素材字段延后映射，未知字段仍拒绝；不重发生成。
- 必须复核现有Attempt读取/最新成功选择、Run等待/恢复、通用rerun、ProjectWorkflowOutput和归档权限；并发执行/恢复不得重复发送、覆盖started历史或生成两个终态产物。仍只使用现有Workflow和单一ProviderGenerationTask，不增加业务表或第二套引擎。

实现使用新`media.generate@1` AI节点，旧cover不静默改写。节点配置选capability、selected_profile、可选explicit_plugin、prompt、parameters与精确source_revision_ids；只将本节点受控生成副作用列入Project定义白名单，Publisher禁令不变。该节点禁止通用rerun/retry/skip；等待状态通过既有complete入口的refresh/recover/submit_prepared操作续进原任务，客户端不得选择task/Attempt替代。result_ready显示生成完成、等待独立人工接受；accepted后追加带exact MaterialRevision的终态并进入项目Workflow输出，未接受时不执行需素材的下游。

不得仅因本节获授权勾选2.6/3.3或启动F8，仍需实现与验收。真实素材许可、正式key/schema及F8身份列授权仍是各自独立边界。

### 6. Complete product configuration and compatibility

Models & AI新增能力勾选、逐能力binding、插件与默认路由/预算编辑；界面显示未连接/不支持/已配置未验证/可执行及原因，提供无网络执行计划预览。保留RBAC、mask/blank-secret retention、完整配置保留与409，禁止重发mask作为密钥。旧Profile无能力字段按legacy chat解释，image配置在未显式迁移前保留原路径；显式升级预览/确认，不启用新付费能力或回填历史。通用Production依赖保持lazy，TipTap不入Settings首包。

CLI 库存与路由预览仅运行静态配置/能力判断，不启动可能自动加载认证文件的 CLI，也不读取 credential epoch；因此只能显示认证连续性尚未核验，不冒称可执行。明确任务准备和执行前复核才通过内部执行入口检查所请求能力及其候选路由的实际 runtime/认证；该入口不是 Settings API 参数，客户端不能以自报 input hash 或额外字段启用。原任务恢复/接受仍按冻结 receipt 与当前 credential epoch 验证，不使用库存投影替代安全证明。

## Risks / Trade-offs

- 品牌不同协议/返回URL → 按版本adapter而非泛化透传；官方契约复核后实现。
- 声明支持但账号未开放 → 真实执行错误安全显示，verify单独授权，不伪造verified。
- fallback产生意外扣费 → 预授权范围、硬上限与明确解释；Unknown不重发。
- concurrent config/credentials changes → CAS与dispatch/accept live身份检查，缓存一致，历史冻结。
- 现有F7 dirty tree → 只改本范围、隔离验收，不commit整个dirty tree。

## Migration Plan

The approved local activation acceptance reuses already generated bytes through the existing upload API, without fabricating a formal ProviderGenerationTask receipt. Upload metadata (kind, title, source and explicit rights choices) MUST use the existing API query contract; multipart carries the file only. Unverified rights remain unknown, and a local import MUST NOT be presented as a new provider execution or public/commercial permission.

2026-10-03用户进一步明确授权当前本机正式使用库的MiniMax接入：先在线私有备份、在副本演练已批准迁移链并核对旧数据，再显式升级到准确f7d000000001，不运行f8a或自动upgrade head。稳定receipt key通过固定本地受控启动配置加载，不入Git/数据库/日志。只配置已验证image/TTS/ASR及有界插件策略，不改CPA默认/文本routes、不启用video。复用既有字节必须通过正式素材导入/引用流程并真实标记来源；不得跨库伪造原Task/actor/provenance或为补证据重复付费生成。下方“不生产迁移”描述保留此前阶段边界，本条是当前精确本地目标授权，不是远程生产部署授权。

不修改canonical或归档，不生产迁移。先验证旧settings读取和文本purpose路由，新增schema显式保存与回滚兼容；然后接resolver/官方adapters/UI。持久任务修订确认后先开发一个加法迁移并在隔离库SQLite往返/原生PostgreSQL约束验证，不启动时自动迁移用户本地生产库。大批次执行：任务模型/原job恢复/结果校验，然后消费者/UI/接受/整体验收；真实供应商验收仅精确已配置且单独授权额度，缺凭据未验证。F7现97/105和F8原门槛保持，不自动放行。

## Open Questions

- 自动fallback已获用户原则确认；真实测试的供应商额度/可用API模型与凭据仍在实施配置时确认，不阻塞本地开发。
- 当前只定义每次执行限额；累计额度如有需求需单独设计事务预留。
- Commons按2026-10-03用户授权的生命周期收尾决定继续暂缓，并行政关闭F7该验收项；保持unverified/未实测，不计为真实PASS，日后恢复实测需另行授权。
