## Context

### 2026-10-02 文件名收口（用户明确批准先补实现）

上传素材必须保留既有 MaterialRevision.metadata_json.filename 中的原文件名，不能从标题、存储哈希路径或 MIME 编造名称。缺少原文件名、路径/控制字符/引号等不安全名称，或不支持的 MIME，官方投影明确 unavailable；不改变历史素材/清单。新冻结的 official_render 使用 renderer_version=2，素材槽同时冻结原 filename 和 mime_type，二者参与 render_hash/Candidate hash；每个远端步骤在发送前与 exact MaterialRevision 再验证，原样传给 multipart。版本1历史预览、本地包和既有 hash 保留，新官方远端效果必须重新冻结审批到版本2；不得审批后补字段。无需新表/迁移，不调用公众号真实接口。本轮仅修订既有文件名要求的实施细节，不扩展功能。

### 2026-10-01 已批准的有界短稿实验

用户批准正文限额冲突下的独立实验例外，不撤销一般远端拒绝规则。授权仅绑定指定账号/AppID、精确Candidate ID/hash、DeliveryTarget及本次Attempt，限wechat/article/auto_draft和短期有效的显式操作者实验授权。实现须在产品中识别此scope，而不是将remote_contract_ready设为true、修改全局环境开关或monkeypatch。库存不得因实验模式显示一般合同已验证；普通验证/授权及其他账号继续拒绝。

token/上传前验证冻结HTML及按既有URL边界计算的替换后字节上界严格小于2048；真实资源URL替换后在create前再次检查最终content UTF-8字节数严格小于2048，不能以字符数或含占位符模板代替。不截断、不压缩、不改稿。过大拒绝，已上传的partial证据保留，无create。只允许一次创建，unknown保留且无自动重试；known ID可显式回读，结果不匹配继续对账，不放宽规范化。

复用existing Target/Attempt安全metadata和短期scope，不增加业务对象或migration。实验成功只形成exact受限实验记录，不生成一般verified、公开Receipt或PublishedContentRecord，不解除长文合同冲突或F7/F8剩余义务。下面远端默认拒绝、真实动作未授权和DNS失败描述保留为历史；仅本段批准的例外优先，所有账号/审批/权利/网络/并发门槛仍有效。

实施出口为内部明确`prepare_short_draft_experiment`，无公开HTTP实验参数。active owned管理员的exact account/AppID/Candidate/hash/actor/expiry输入在普通authorize的live检查后，原子生成Target+Attempt并在既有snapshot签入最多15分钟HMAC权限；一般available/verified/remote_verified保持false。每步从DB真源重建scope、保留exact scope撤销优先及live锁。worker开始也在Target锁下commit不可自动重领标记；token及所有请求在DNS/TLS完成后、HTTP字节发送前再验expiry。实验Target不允许第二Attempt，known-ID回读沿用本次未过期权限且不create；到期需要独立明确后续授权，不能自动续签。

真实验收脚本只对私有临时目录内已存在的隔离 SQLite 库执行，不创建/迁移真实库，不伪造 Candidate/CheckRun/Verification。输入明确 Candidate/hash、Account、actor、expiry，复用上述内部出口。默认仅 preflight 并 rollback（零 Target/Attempt、零 transport）；显式 execute 才 prepare/execute。固定批准的 WeWrite/new_media 两份配置须账号及 secret 一致，凭据仅短时注入当前进程精确账号环境引用，身份 HMAC key 仍须显式配置。已有官方 Target 时拒绝第二次运行，不自行 reconcile/renew/retry；safe 输出不复制正文、token、secret、claim、签名或原始错误。测试稿/封面确认前不执行远端写入。

2026-10-01执行授权更新：用户允许使用new_media/WeWrite已有公众号凭据测试token、素材上传、草稿创建与回读，明确不公开发布。此授权解除此前“真实动作未授权”条件，仅限用户指定同一账号；不是平台验证或通用runtime放行。配置预检确认账号一致，官方DNS返回198.18.1.55被现有公网校验拒绝；body-size合同仍未闭合，因此尚未向账号发送任何请求。真实API前须满足现有exact账号/scope/冻结审批和合同/网络门槛，禁止旧WeWrite命令fallback。下文Non-Goals及旧证据中的未授权真实动作描述为历史范围，不撤销现行安全要求。

基线main@da73bbb。ContentAccount已有非空persona_id；身份解析拒绝不匹配的Persona/Account/Series。用户明确不允许同账号跨角色共享。Delivery已有exact account、publisher版本、批准hash与Attempt/Receipt；F7旧publisher_runtime_fingerprint恒None，不能将新HTTP实现冒充WeWrite。

## Goals / Non-Goals

**Goals:** 保留一对多并防真实账号重复绑定；账号隔离的官方草稿适配器；审批前冻结可交付表示；可审计的创建、回读与unknown处理。

**Non-Goals:** 多对多、账号跨角色转移、公开发布/群发/排期、微信第三方平台代授权、任意平台自动发布、真实账号副作用、F8跳级或生产迁移。

## Decisions

### 1. 单父级与真实身份分开

保留ContentAccount.persona_id。在既有Account追加可空platform_channel和platform_account_id（微信以AppID作连接身份），成对非空CHECK及非空组合全局唯一约束；同一真实账号不能以两个本地Account绕过单父级限制。重复绑定返回不泄漏另一个角色/用户信息的固定冲突。绑定只能是已有active owned Persona下的账号，首次绑定后不得原地改平台/真实身份/父级；先归档不释放真实账号独占性。历史空绑定账号仅保留读取/本地交付。名称或自由文本profile不是平台身份。

替代：junction多对多违反用户决定；仅检查persona_id不能防同AppID重复建号。平台身份字段不存token/secret；显示身份不证明操作者拥有微信账号，真实精确验证仍独立。

### 2. 新Publisher与账号配置

新key为publisher.wechat.official@1，kind沿用publisher。不继承publisher.wechat.wewrite验证；旧实现历史兼容且新远端效果继续拒绝。一个implementation registration可有多个account scope，最终指纹函数接收account而非只接收plugin key。registration.config_fingerprint只绑定新实现代码/合同，verification.config_fingerprint绑定该实现加AppID、safe credential identity/version和账号配置版本。当前append_verification/is_verified_for_scope对非Renderer只接受registration同一fingerprint，必须仅为精确新official key增加server-derived account-scope校验分支，不放宽旧Publisher/Connector规则、不接受客户端任意hash。每次验证/执行核对registration实现指纹与event账号指纹；账号A轮换只使A scope无效，不能修改单一registration字段覆盖B。复用既有CapabilityVerification，不创建Publisher状态表。

复用已有SystemSetting只存每账号安全connection配置和secret引用/版本，实际secret由显式进程环境/批准resolver获取，不能写入IdentityProfile、manifest、浏览器或AuditLog。token缓存以publisher/account/AppID/credential/runtime版本为键，启动后未配置为unavailable，不能使用全局“当前账号”、另账号token或fallback。F8可替换secret实现，此处不声称生产Secrets已完成。

### 3. 审批前的官方内容投影

实施载体为v5 manifest内可选`official_render`，只为新冻结的wechat/article生成；旧清单不补字段、不改hash。build对存在的表示重新确定性验证canonical content、exact refs和render hash，Review API直接返回冻结值。正文block/cover/inline槽均在冻结前确定，实时权利和字节校验复用现有gate；远端上传/映射/回读另属Batch B，不能从本地render成功推导平台已验证。

Review 前端直接展示冻结 HTML，放在无权限 sandbox iframe，首部固定 CSP 禁止脚本、外部资源、表单和 base URL；不把 HTML 注入产品主 DOM。独立显示冻结标题、摘要、作者、render hash、exact 素材槽及不可用原因，不发账号请求或提供远端操作。没有 official_render 的旧候选保留原预览；槽位清单不冒充正文内图片已定位或真实上传结果。

图片预览按精确Candidate render endpoint读取当前授权字节，SHA-256与冻结slot比对后仅在局部展示HTML替换对应占位符；PNG/JPEG转为内嵌data URI，CSP只为图片允许data，不开放脚本/同源/外部网络权限。不得变更manifest或render hash。HTTP LAN缺WebCrypto时使用与标准SHA-256一致的无依赖fallback；累计8MiB与20秒为本地预览资源预算，不作为微信真实大小合同。切换actor/候选取消旧请求，超时/权利/哈希失败显示明确不可预览。

正文图片采用兼容加法契约：wechat.article.v1 新增显式 image block，字段为稳定 id/order、kind=image、image_ref_key、text(图注)、alt_text。旧纯文本 block 的 canonical 结果和 hash 不增加默认字段。image_ref_key 必须一对一对应 inline_image ref，placement={usage:inline,block_id:精确block id}，按正文出现次序连续排序：有封面从1开始、无封面从0开始；封面仍为 cover/cover/order0，互不混用。缺封面仍按真实Profile和official render的cover_required阻断就绪，不伪造封面。后续明确选择封面仅允许原inline refs按顺序后移一位。不得出现孤儿/重复槽或自称 URL。冻结 HTML 只写固定 `aics-resource:槽位` 占位符，slot 同时冻结 block id、revision/hash。确定性来源映射只接受已有 text v2 的无 marks 段落和精确 image block；保留 block ID/顺序/图注/alt，不能证明的格式仍 typed unavailable，不能放宽 Evidence semantic gate。

公众号接口不能以Markdown当最终正文。新增版本化wechat.official.article.v1冻结render contract：title、digest、author、HTML模板、允许的固定媒体槽（MaterialRevision ID/hash/用途）、正文结构hash、renderer版本与render hash。由服务端确定性render在Candidate freeze前生成，Review显示同一冻结表示；不改Variant内容、不调用模型。现有v5历史缺该contract时不得远端上传，也不得审批后补render，必须重新freeze/review/approve；v1–v4和本地包保持旧路径。

正文槽只允许平台上传返回值替换固定img src占位符；每次替换必须对应冻结槽/精确字节hash及当前目标账号，保存到既有Attempt的安全执行metadata映射。任何正文/标题/摘要/声明变更或新资源均拒绝，必须回到新Candidate审批。禁止发布阶段markdown→HTML、摘要截断、自动封面、临时加声明。平台不能接受原批准素材格式/大小时拒绝，不临时压缩或转码。第一版只接受官方契约已验证的有界HTML与PNG/JPEG资源。

### 4. 创建与回读

### 4.1 WeWrite HTTP wire parity

2026-10-02用户授权仅本地修正响应兼容：固定官方接口的HTTP200响应允许`application/json`或`text/plain`（含charset参数），两者都必须经过同一有界严格JSON解析和具体操作字段校验；拒绝重复key、非有限常量、非对象、非法/非零errcode，以及缺失/非法media_id等。HTML、缺失或其他MIME、压缩、非200、预算/期限超限继续拒绝。此前诊断记录“不放宽JSON MIME”是上一轮授权范围，不阻止此次明确批准的text/plain兼容修正；本轮不新增真实请求、不重试旧Unknown、不改变一般合同未就绪状态。

本次移植以本机已安装WeWrite的实际HTTP实现为协议参考，不再维护一套行为不同的公众号请求实现。产品仍使用自己的账号解析、权限、Attempt/CAS、冻结内容和安全诊断边界；只移植请求线上行为：

- token使用`GET /cgi-bin/token`，query包含`grant_type=client_credential`、精确AppID和secret；secret不得进入日志、Attempt、审计或响应。产品可以继续使用固定host/SNI、无重定向、无自动重试和有界读取，但不能再把`stable_token` POST JSON当作WeWrite兼容实现。
- 图片上传使用`multipart/form-data`字段`media`，保留冻结资源的文件名和MIME；正文图片调用`/cgi-bin/media/uploadimg?access_token=...`并只接受响应中的`url`，封面调用`/cgi-bin/material/add_material?type=image&access_token=...`并只接受响应中的`media_id`。不在发布阶段压缩、转码、改名或生成替代素材。
- `draft/add`使用UTF-8 JSON字节（等价于`json.dumps(..., ensure_ascii=False).encode("utf-8")`）和`Content-Type: application/json; charset=utf-8`。article至少包含WeWrite实际发送的`title`、`author`、`digest`、`content`、`show_cover_pic: 0`、`thumb_media_id`；产品已有且已批准的评论字段只有在契约要求时追加，不得删掉WeWrite字段或用Markdown替代HTML。
- 成功只以HTTP JSON中存在合法非空`media_id`为准；仅有HTTP 200、空对象、`errcode`为0但缺少`media_id`、或解析不确定都不能收口为成功。成功后写入现有Attempt的安全remote_id，状态仍是草稿交付，不是公开发布；回读仍是可选增强核验，不得再次create。

“完整移植”不等于复制WeWrite的全局`_token_cache`、环境凭据、CLI入口或其自动重试行为。token缓存必须继续按ContentAccount/AppID/credential/runtime版本隔离，所有外部步骤继续沿用本变更的claim、live revalidation和unknown不自动重试规则。

2026-10-01真实实验暴露诊断丢失：token成功而asset_0未确认，execute_prepared捕获传输异常后仅传error=True，固定code/dispatch hint未进入Attempt。沿用2.4安全metadata契约，失败结束只保存明确allowlist transport code及严格bool提示；未知/任意异常不转存detail/str/raw body。不得为过去Attempt补猜测诊断，不改变unknown或重发门槛，不发新远端请求。

2026-10-02用户批准仅本地补充脱敏诊断，不授权新接口调用。未来失败Attempt可额外保存allowlist phase（dns/connect/send/response_headers/response_body/response_json/response_contract）、reason（io_failure/deadline/tls/protocol/http_status/header_limit/content_type/content_encoding/body_limit/invalid_json/invalid_response/api_rejected）、严格整数100–599的http_status、response_type分类（json/text/html/missing/other）。原始header、正文、URL、token、provider message和异常文本一律不保存；字段在持久化边界再次过滤，非法值省略，没有附加信息的历史调用保持原两字段契约。分类仅描述拒绝分支，不放宽JSON MIME/状态码/响应预算，也不证明远端副作用未发生；不回填旧Attempt。

官方HTTP传输使用stdlib HTTPSConnection，TCP只连接本次验证的公网DNS sockaddr，TLS校验证书/SNI与Host仍固定api.weixin.qq.com:443。每步骤新连接，无代理、重定向或重试，也不使用会记录含token URL的httpx日志。DNS任务有界并发/期限，连接、TLS、header/body读取共用单次截止时间；JSON响应、HTTP头、上传与本地请求资源预算显式有界。所有传输错误只暴露固定code和是否可能已dispatch，不保留raw响应或异常。该资源预算不解决官方正文限额冲突；真实门槛仍默认false，隔离fixture不能使生产verified。

只开放article/auto_draft，沿用DeliveryRouter的授权/Attempt/unknown语义。准备Attempt和稳定idempotency key在token/上传/创建前提交；锁定精确账号/批准Candidate与当前live gates。token获取、封面/正文素材上传、草稿创建、草稿回读各自有边界：HTTPS官方host allowlist、连接IP/TLS绑定、禁重定向/环境代理、有限响应/时间、无自动副作用重试、secret-bearing query与返回内容不入日志。

复用Attempt.metadata安全保存步骤完成状态、resource mapping摘要、draft ID及回读hash，不保存正文raw response/token。草稿创建返回官方成功响应且包含精确`media_id`时，按WeWrite同等规则确认“草稿已创建”，立即把Attempt收口为`awaiting_manual_receipt`；这不是公开发布，也不创建PublishedContentRecord。显式回读保留为可选的增强核验路径。草稿创建timeout、连接断开、响应缺少`media_id`或含糊结果仍为unknown，原Attempt留存，不自动重新创建。已知draft ID且回读失败仍保留ID等待显式回读/对账，不能用第二次创建代替回读。素材阶段部分成功如实记录，不自动删除远端素材；本地回滚不能声称外部上传撤销。

当前execute_attempt并没有reconcile的目标写锁，不能声称自动继承完整串行机制。新官方路径必须在目标写锁内CAS核对可执行状态/当前Attempt后准备唯一Attempt并commit；并发请求发现已prepared/in-flight/unknown的Attempt时不再次dispatch。每个新token/upload/create步骤前，重新取得确定顺序的target/account/registration/source权限锁，核验该Attempt仍持有执行权、scope/expiry/runtime/账号活动和exact source rights；锁持至该有界步骤结果完成，safe步骤结果写既有Attempt后commit。prepare commit释放锁不证明后续授权持续有效。撤销先获得锁则阻止下一次dispatch，已发送步骤不能声称撤销可取消；失去响应/进程崩溃的in-flight步骤转入显式对账，不按超时自动收回执行权并重发。不得为了执行lease新增业务表；若现有Attempt列/安全metadata和事务CAS不能满足需停下修订。独立PG/双连接竞态验证，而非仅唯一约束或进程mutex断言exactly-once。

成功回读须按有界schema检查title/digest/author/正文及冻结资源映射。平台规范化只允许有官方证据的版本化转换白名单；不一致或无法证明时保持reconciliation_needed，不伪称成功。草稿不是已发布，不能创建PublishedContentRecord或假delivered_at公开时间。

本地实现统一锁序为project/source/profile → 身份祖先/account → target → registration，匹配既有authorize先锁source的路径；官方verification追加通过registration写锁与dispatch串行。每步在外部动作前独立commit in_flight，再重获上述授权锁并校验私有claim。prepared/running进程中断不按时间恢复；人工reconcile必须带exact expected_attempt_id和证据摘要，先失效旧claim并保留unknown/partial历史，再按显式决策处理。仅已确认not_delivered才允许新的递增Attempt，不能自动重发。

新增明确POST /delivery-targets/{id}/official-readback，输入仅expected_attempt_id，不接受客户提供draft ID/正文/token。仅最新unknown且已有安全remote_id、exact runtime及未占用readback claim可调用；token/read仍逐步重验。该入口只有读取，不调用create，不创建发布记录；成功清除原错误并回到awaiting_manual_receipt。再次中断/不匹配继续保留unknown，不能靠第二次create恢复。尚未完成的前端入口与独立PG竞态需后续验收，不以API夹具代替。

Review现已连接explicit readback按钮，必须用户确认、exact最新Attempt、unknown且有remote ID；prepared/running官方目标可进入有依据的人工对账，不能恢复执行或create。历史/归档禁操作。UI的fixture只证明请求边界，真实权限/runtime仍由服务端重验。官方auto_draft的人工作为草稿交付Receipt，不走PublishedContentRecord自动同步；普通legacy人工发布回填保留。PG竞争和完整远端门槛尚未关闭。

### 5. Settings/Identity与验证

Settings渠道分区复用同一AccountPublisherPanel和owned Persona/Account API，配置入口不依赖旧WeWrite验证可用性；viewer也可选择所属账号只读。面板按actor/account重新挂载，保留既有未保存输入恢复和明确保存。Account配置与Channel Registry只读投影分开，不另建设置真源、不开放真实probe或新增verified记录。

connection安全读模型的read_only由服务端根据角色和完整Brand→Persona→Account活动状态计算；两个前端入口均遵守此值，缺失状态也不能开放写入。它只是权限投影，不新增持久化状态，保存仍再次验证层级和CAS。

身份页展示Persona旗下多个账号；管理员按具体owned账号绑定连接，viewer只读无secret；另账号资料不泄漏。库存读不读凭据/不取token/不探测。绑定、配置、验证、创建草稿是独立明确动作。能力scope包括account ID/AppID/channel/form/action/new publisher version/runtime，真实readback/human evidence才可验证；人工输入配置不等于平台ownership。撤销/过期/轮换/账号归档阻断新动作，既有Attempt/Receipt只读保留。

## Risks / Trade-offs

- 官方文档已读但正文限制冲突 → 用户2026-09-30同意本地apply与远端执行分离；允许账号绑定、适配器和隔离测试开发，不根据第三方/经验选择真实上限。未核实合同只能是remote unavailable，不能发起真实token/上传/创建/回读或标verified。
- 新列及唯一约束 → 提案确认才允许生成加法迁移；不从历史自由文本猜AppID。保留绑定/引用史时拒绝破坏性降级。
- 远端没有已证明幂等能力 → unknown不自动重发，人工明确核验；不承诺绝对仅一次。
- token/账号secret错用 → runtime/account隔离及两个账号交叉负向回归；不因方便使用WeWrite全局配置。

## Migration Plan

先复核官方接口证据和新规格；用户确认后分两大批实施。SQLite/PostgreSQL隔离验证成对nullable字段、唯一竞态、历史保留和拒降级；正式库执行另需授权。旧Account/F7注册/验证/候选/本地交付不回填，不删除旧WeWrite身份。

## Open Questions

### 当前执行门槛（2026-09-30用户修订批准）

用户明确同意先完成本地账号绑定、适配器和隔离测试，将官方正文限制冲突留作远端执行门槛。下面此前“不能业务apply”的证据记录保留为历史，已被本条授权替代。接口五类官方文档和公众号权限用户确认满足本地开发前置；真实限额、精确账号scope/凭据/动作授权与实际回读匹配仍须在远端执行前核实。禁止默认采用2KB缩减产品或采用1MB伪称合同确定；本地实现保留固定合同版本/未核实原因，真实dispatch必须fail closed。

### 2026-09-30 授权后官方证据补录

用户已批准本地实施、加法字段/迁移开发和新Publisher；不授权真实账号API动作或生产迁移。web reader失败后，直接HTTPS公开文档GET实际成功，旧Add_draft入口301指向service草稿指南，再从官方指南取得API链接。以下均为文档读取，不是账号接口执行：

| 合同 | 官方来源 | 已核实范围 |
| --- | --- | --- |
| stable token | https://developers.weixin.qq.com/doc/service/api/base/api_getstableaccesstoken | POST /cgi-bin/stable_token；client_credential、appid、secret、force_refresh=false；返回access_token/expires_in，最长7200秒；IP白名单/管理员确认可能阻断 |
| 正文图片 | https://developers.weixin.qq.com/doc/service/api/material/permanent/api_uploadimage | POST /cgi-bin/media/uploadimg；multipart media；jpg/png且小于1MB；返回url |
| 永久封面素材 | https://developers.weixin.qq.com/doc/service/api/material/permanent/api_addmaterial | POST /cgi-bin/material/add_material；type及multipart media；image列出10M、thumb列出64KB/JPG；返回永久media_id，不混用两类限制 |
| 创建草稿 | https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_draft_add | POST /cgi-bin/draft/add；articles/news、title<=32字、author<=16字、digest<=120字；news需要永久thumb_media_id；返回media_id<=128字符 |
| 草稿回读 | https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_getdraft | POST /cgi-bin/draft/get，精确media_id；news_item含title/author/digest/content/thumb_media_id等，草稿临时url不是公开发布证明 |

当前创建页content说明同时出现“不可超过2kb”和“少于2万字符、小于1M”，回读页仅后者；不能选择较宽值当已证明合同。官方还明确过滤JS和外部图片URL，未给出完整HTML等价规范化白名单；因此只允许严格匹配已批准字段/资源槽，任何未经证明变化都需对账。正文限制冲突和具体账号的权限证据尚未闭合，task0.1保留未完成，不能启动业务apply。适用范围表列公众号/服务号可调用，不证明用户具体账号已开权限、白名单或管理员授权。

当前真实账号类型/AppID及接口权限只读证据未提供；不要要求在聊天中提交AppSecret。原“页面不可读取”是此前web reader失败记录，已被本次直接官方读取更新，不再以网络不可读为阻断原因。

2026-09-30用户随后确认首批为微信公众号，草稿箱和素材管理权限“已开放”。记录为用户提供的开发背景，不再要求重复确认或强制截图；不是已读取具体AppID的后台权限、真实token验证或远端动作授权。当前仍待解决的开发合同问题是正文限制冲突，不能把此确认写成task0.1全部完成或CapabilityVerification通过。

进一步直接读取官方公众号版本 https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add ，同样同时出现2KB和1MB，未通过切换账号类型消除冲突。因此没有可用的权威澄清，也未收到具体账号权限证据；不能重复读取同一页面或重新跑本地测试来关闭0.1。

五份官方接口合同已读，待补具体账号权限、正文大小冲突的权威澄清和实际回读的严格匹配验收。真实账号AppID、凭据resolver和上传/回读授权尚未提供；不得把本地fixture当外部通过。

2026-09-30尝试读取的官方来源均由web reader返回无法打开：
- https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Get_access_token.html
- https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/Adding_Permanent_Assets.html
- https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html
- https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Get_draft.html
- https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_draft_add
- https://developers.weixin.qq.com/doc/service/api/material/permanent/api_uploadimage

上述仅为待读取入口，不作为成功核验的引用；未确认字段包括token获取/失效策略、article必填字段与上限、素材type/MIME/尺寸、API权限类别、草稿get响应以及正文规范化。

## Flow

Persona → owned Account → unique platform identity → account-scoped connection

Master → Variant → frozen official render → Candidate → Approval → exact DeliveryTarget → prepared Attempt → scoped upload/create(media_id confirmation) → optional readback/reconciliation

有界实验：explicit owned admin scope → existing source/Approval/live gates → atomic Target + Attempt + expiring signed scope → durable worker-start CAS → step in-flight commit → live/expiry/byte revalidation → pinned DNS/TLS → final expiry check → exact upload/one create(media_id) → optional readback → bounded evidence only（no general verified / no public publish）。

本地runtime：exact Account/AppID → account setting revision + credential VERSION → stable environment HMAC identity → account fingerprint → scoped verification/token cache。部署身份key必须跨worker一致，缺失直接unavailable；库存不解析secret。远端合同仍未核实，只有上述本地隔离路径已验证。
