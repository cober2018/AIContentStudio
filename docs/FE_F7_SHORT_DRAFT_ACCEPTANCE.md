# F7 官方公众号有界短稿验收

## 2026-10-02 用户确认本次实验结束

- 用户明确：成功草稿不要求额外回读，到此结束。产品 Candidate6 / Account1 / Target6 / Attempt6 已完成 token、封面上传、draft/add，保存有效 media_id，状态 succeeded，用户后台已确认；本次草稿创建验收 PASS。
- 对照本机 WeWrite 4.2.1：toolkit/cli.py 正常 publish 在 create_draft 返回后报告 media_id，不自动执行 get_draft。独立查询函数存在，不代表正常发布要求回读。
- 取消拟议的成功草稿只读回读入口与补测；readback_hash 为空如实保留，不标回读 PASS，不重复上传/create、不公开发布。原 Unknown 对账边界保持不变。
- 本轮仅更新验收/计划文档；不改业务代码、数据库、凭据或规格，不新增 CapabilityVerification/Receipt，不将本次接受扩大成整个 F7 完成或授权归档。

## 2026-10-02 产品成功草稿回读预检（零网络）

- 用户本轮确认验证 AIContentStudio 产品链路。只读原私有库得到：Candidate6 / Account1 / Target6 / Attempt6；Attempt=succeeded，Target=awaiting_manual_receipt，completed_steps=[token, asset_0, create]，remote_id hash=`61bbf2b1b617cb31befa0cb656ac4e4ff5558f07479cee60d5fa8ea47f3c34f9`，readback_hash=null，Receipt/CapabilityVerification均0。
- 原实验授权已过期。当前 `POST /delivery-targets/{id}/official-readback` 调用的 service 仅允许 unknown / reconciliation_needed，不允许这篇已成功的草稿。没有发起该端点/微信请求，不把本地预检描述为远端失败。
- 未修改成功状态、旧Unknown、授权或数据库；未重复上传/create，不以WeWrite/底层直接调用替代产品验收。成功草稿的显式只读回读与新授权契约需要单独规格/实施授权；本轮只更新证据，未勾选一般合同/终验/归档任务。
- 无业务代码、依赖、迁移或启动方式改变；未重跑后端/构建，不引用旧门禁作为本轮结果。

## 2026-10-02 指定完整 HTML 草稿测试（独立 WeWrite API，非产品全链验收）

- 用户指定原文件 `/Users/mshengran/Project/new_media/content/articles/drafts/公众号HTML输出/2026-09-03-量化数据平台数据接入实践下篇-公众号文章_stripe_StripeDocs_微信公众号版.html`，并确认短标题“决定 AI 量化成败的四根数据支柱”、首图封面、仅压缩副本、保留原HTML、同一公众号草稿箱一次。未授权公开发布。
- 原HTML SHA256=`9601ab512fa2d4ea1fabb0fc0ac6826a44b706157189dc5796fa62c78727cf70`；正文约6366字、8张图、216个style。JPEG90副本全部保持3840×2160，722623–902156字节；原HTML与PNG不改。
- 本地预览 `/private/tmp/aics-wechat-rich-html-frk1uV/preview.html`；approved-inputs冻结标题、正文hash、图hash与首图封面。直接复用本机WeWrite `wechat_api.upload_image/upload_thumb`、`publisher.create_draft/get_draft`，没有将HTML转Markdown，body外包装转section保留原style，正文图只替换上传URL。
- 实际一次token、8个inline上传、1个cover上传、1个draft/add；提交HTML47577字节。创建返回media_id=`TrHZ7fvz9Q_Wyx8cuHKbyX1_UlOmy4fFYq3U8bSjgil9hjSn-RSrDDBicTqI9MX_`，SHA256=`99dc66f3acf62d0c7f8e9044629cec6b54dff8a30db68e2e82da258d53da7b6e`。
- 初次draft/get已确认标题，但微信用img[data-src]返回图片，临时核对器取src发生KeyError；创建已成功，不是微信拒绝。后续仅只读获取同一个media_id，不上传/新建/重发。
- 最终回读：标题一致、去空白正文一致、216个style逐项完全相同；8张图资源路径及排列一致。微信将HTTP转HTTPS、资源URL末段0转640，所以URL字符串和HTML字节不是原样相同，未下载远端图验证字节，未假称公众号后台视觉验收。远端正文hash=`b5598f2a0d94db6ebe6767c857851a0b4ddba7da08607185fe93aaabf837426a`。
- 安全记录 `/private/tmp/aics-wechat-rich-html-frk1uV/evidence.json`、回读 `readback.html`/`readback-fragment.html`，私有目录/文件，不保存凭据或原始账号API响应。只执行create一次，claim保留，后续不再执行发送脚本。
- 这是指定HTML文件的独立上传测试，不是产品Candidate/Approval/Delivery落库，也不建立CapabilityVerification。产品短稿一般gate、F7计数131/152、公众号19/22及剩余任务均不因此改变；无公开发布、历史Unknown重试、正式库/配置修改、业务代码/测试/迁移、commit/push/deploy/archive。


## 2026-10-02 统一收口记录（当前状态）

| 验收范围 | 状态 | 证据 / 剩余边界 |
|---|---|---|
| 精确账号、封面、一次创建草稿 | PASS（有界实验） | 产品Attempt6返回有效media_id；用户后台截图确认标题及封面；未公开发布 |
| 冻结审批内容不可改（F7 8.5） | PASS | 最新129项定向、1660项后端及独立逐任务复核；历史缺官方render拒绝远端效果 |
| 草稿正文API匹配回读 | 未执行 | 对已确认创建而言是可选增强；截图不证明正文相等，不重新create |
| 一般长文/普通账号verified（8.3、10.5、10.6、补充2.8） | PARTIAL | 一般合同gate仍false；实验不创建CapabilityVerification或扩大权限 |
| 整阶段终验及本地提交（2.9） | PARTIAL | 本轮定向/全量/build/budget/strict/Ruff/diff通过；原生PG和浏览器本轮未重跑，独立复核是逐任务范围，不是全阶段终审；未提交 |
| 主规格同步归档（2.10） | 未执行 | 不以本次短稿通过替代独立范围/归档授权 |

本轮只读原私有证据库：旧五条Attempt全字段未变，Receipt/PublishedContentRecord/CapabilityVerification均0，没有再次调用微信。准确当前进度为F7主切片98/105、模型路由14/25、公众号19/22，合计131/152。

另有一项实现/规格差异待处理：真实产品上传使用MIME派生的固定`media.png`/`media.jpg`，没有透传原文件名。素材字节/hash/MIME不变，不能因此否定已确认草稿；也不能声称完全保留原文件名。该差异保留给公众号终验，不静默改写原规格。

以下保留按时间发生的历史记录；其中“未创建”“待上传”等不是当前验收结果。

## 2026-10-02 响应兼容修正后的真实产品草稿创建（成功）

- 用户提供后台“近期草稿”截图并确认一致即通过：可见标题“响应兼容测试，请勿发布”、更新于14:31，黄色封面“系统联调测试 / 请勿发布”与本次已批准封面一致。人工后台可见性验收PASS，证据为用户附件`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/codex-clipboard-03793d47-a3e7-4dd0-a0a1-933255ccff85.png`。截图未打开正文，也未展示media_id；不冒充draft/get内容匹配回读，不生成数据库Receipt/CapabilityVerification或公开发布记录。
- 用户随后明确授权已展示的正文、封面发送到指定同一公众号草稿箱一次，解除上轮进程启动前的审批阻断。复核冻结输入/cover hash/五条旧Attempt后，零网络preflight再次通过；仅执行既有product runner一次，没有CLI fallback或第二次创建。
- Candidate6 / Account1 / Target6 / Attempt6；题为“响应兼容测试，请勿发布”。真实完成`token → asset_0 → create`，`status=succeeded`，Target=`awaiting_manual_receipt`，`create_confirmed=true`、`in_flight=null`，保存一个精确封面映射。微信draft/add返回media_id=`TrHZ7fvz9Q_Wyx8cuHKbyeLh4zoiuEs3uY3iKfLw_JlvAbK4XJbKtK5PArnlaPfZ`，SHA256=`61bbf2b1b617cb31befa0cb656ac4e4ff5558f07479cee60d5fa8ea47f3c34f9`；本地持久化回读一致。
- 本次仅按有效`media_id`确认创建，未追加微信draft/get；readback_hash为空，不声称远端正文匹配回读已通过。HTTP响应MIME/body未额外保存，不把本次成功倒推为旧Attempt成功。
- 五条旧Attempt全字段与源库一致；源库仍5条，新私有副本6条，Receipt/PublishedContentRecord均0。未公开发布、群发、修改正式库/配置、迁移、提交、部署或归档；一次授权已消费，不再重发。真实远端新建封面素材和草稿，仅限本次批准内容。
- 仅关闭task2.8a有界短稿创建验收，公众号19/22；2.8一般合同/完整平台范围、2.9全阶段终验/本地提交、2.10单独同步归档仍待完成。一般remote_contract_ready仍false，成功短稿不解除长文合同或整体F7/F8义务。此前“执行未启动”记录保留为历史，不是当前结果。

## 2026-10-02 响应兼容修正后的新测试（已预检，执行未启动）

- 用户授权一次新草稿测试。私有副本`/private/tmp/aics-wechat-plain-json-6R6sO5/acceptance.sqlite`保留五条旧Unknown；产品API创建Unit6/Master7/Variant7/Candidate6及Approval，标题“响应兼容测试，请勿发布”，正文“这是一次公众号草稿箱响应兼容测试，请勿公开发布。”，预览`preview.html`同目录。
- Candidate hash=`9b22b3132e4229061a252df29366b225f1114c1bdf92d93412145631bd8937d5`，render hash=`55f66f3f0e5435c6ab8d68938a4017190756a1b85ab2174f0d4199051c0f96eb`，HTML118字节，沿用精确cover revision1、19723字节、hash=`5f83fabcec23ee495c34e51b043a627a5673a577767c7bc11066848ecd02163f`。四条语义warning有明确测试稿人工处置，不伪造CheckRun/Verification。
- 账号是既有WeWrite/new_media配置对应的同一公众号，隔离Account1/Persona1，本地名称“已批准公众号草稿箱联调”。零网络preflight通过、rollback后Target/Attempt均5条，五条旧Attempt全字段未变化。
- 本机执行auto-review在进程创建前拒绝，要求明确本轮具体目标账号、正文和封面的外发授权。无新网络/上传/draft/add，未生成Attempt6或新的Unknown；不绕过或切换CLI。保留预览和库，等待用户确认这些精确输入。2.8/2.8a/2.9/2.10均保持未完成，不能称此次微信接口失败或平台成功。

## 2026-10-02 WeWrite响应兼容修正（仅本地）

- 用户明确授权本地修正。先更新现有design/spec/tasks，transport仅将接受MIME从application/json扩为application/json或text/plain（charset参数可有）；两者都走同一有界严格JSON解析及具体操作字段验证。WeWrite作为协议参考，不执行CLI fallback。
- RED离线复现合法plain JSON因content_type拒绝；GREEN用既有内存wire fixture覆盖15个端点组合成功和16个拒绝场景。HTML/缺失或其他MIME/压缩/非200、畸形/重复key/NaN/非对象/非法errcode、缺失或非法media_id、超预算仍拒绝；每个拒绝只发一个fixture请求，零网络。
- 新鲜门禁：129定向passed/1既有warning（14.09秒），全后端1660 passed/28 skipped/8既有warnings（77.68秒），strict33/33、Ruff、tracked/untracked diff通过。独立单一MIME条件静态只读复核APPROVE，无阻断；不是其重跑测试或真实微信通过。本轮无前端改动或构建验收。
- 未读取凭据、未调用微信、未修改私有验收库或旧Unknown，未提交/推送/部署/迁移/归档。本地兼容通过不证明Attempt5上传成功，不关闭2.8/2.8a或一般长文合同；下次新的真实草稿测试仍需独立明确授权。

## 2026-10-02 诊断补丁后的单次授权验收（已定位拒绝分支，未创建草稿）

- 私有证据库：`/private/tmp/aics-wechat-diagnostic-7OrCjk/acceptance.sqlite`；从上一轮库只读备份，保留四条旧Unknown。通过现有API建立Unit 5 / Master 6 / Variant 6 / Candidate 5及Approval，非手填CheckRun/Verification；标题“诊断联调测试，请勿发布”，本地预览同目录`preview.html`。
- Candidate hash=`0c860a851a16c2b184ab09307c32ecf729ea87f8ee4f1d2f3cf5f33e36c2942d`，render hash=`b78e5dd0c8c48b08221a896927910df9b9842fdce792f49e8c8e138df8b65b28`，冻结HTML118字节，原精确封面19723字节；四项语义warning明确按原创测试稿人工处置，不冒充全覆盖。
- 零网络preflight通过且rollback后无新Target/Attempt；用户新授权仅执行一次。新增Target 5 / Attempt 5完成token，停在asset_0：`official_response_unconfirmed`，dispatch_hint=true，phase=response_headers，reason=content_type，http_status=200，response_type=text。状态unknown/reconciliation_needed，remote_id/readback_hash为空；未调用draft/add/read，未公开发布，授权已消费、不重试。
- 此次确认产品在收到HTTP200/text/plain后、解析正文前拒绝。未保留原响应，不能断言上传成功或响应正文一定是合法JSON；更不能将该分支倒推给四条旧Attempt。HTTP响应已到达，不能归为本次DNS无法访问。
- 只读核对本机WeWrite源码：`toolkit/wechat_api.py`的`upload_thumb()`/`upload_image()`直接调用`resp.json()`，没有Content-Type必须为application/json的前置条件；`toolkit/publisher.py`创建草稿同样直接解析JSON。因此产品响应接受条件尚未完整兼容WeWrite。建议下一轮修订为限定官方接口允许text/plain中严格合法JSON，仍需exact media_id/errcode、状态/预算/TLS/无重试检查；本轮不修改业务契约或代码、不追加真实请求。
- 四条旧Attempt全字段与源库相同；源库4条、副本5条；Receipt和PublishedContentRecord均0。源配置/正式库/旧记录未变，不使用CLI fallback、不修改VPN。2.8/2.8a/2.9/2.10继续未完成。

## 2026-10-02 上传诊断细化（仅本地，无新平台验收）

- 用户批准只补本地脱敏诊断，不授权新真实请求。transport记录固定phase/reason、有界整数HTTP状态和响应类型分类，delivery再次过滤；不保存原始header/body/error/URL/token/provider message。
- 无网络probe覆盖16拒绝分支、缺media_id与真实_finish合成DB路径，既有129项公众号回归通过。旧两字段诊断保持兼容，Unknown与partial安全记录不变；不新增持久测试代码或迁移。
- 私有验收库及历史Attempt不修改、不回填；Attempt 4的真实原因依然未知，本轮不尝试上传/create/readback，不把分类补丁当作2.8平台通过。最终全后端1660 passed/28 skipped/8既有warnings（74.80秒）、strict33/33、Ruff/diff、独立诊断窄复核APPROVE；不是公众号全阶段/归档通过。

## 2026-10-02 token 修正后的新授权验收（未通过）

- 权威证据库：`/private/tmp/aics-wechat-token-fixed-vlhp68/acceptance.sqlite`，私有副本保留此前三个 Unknown。通过产品 API 完成 Unit 4 / Master 5 / Variant 5 / Candidate 4 / Approval，不手填 Candidate/CheckRun/Verification；本地冻结预览位于同目录 `preview.html`。
- 标题“接口修正测试，请勿发布”；Candidate hash=`0d92e7a9123b004bba85ac626dc4991f85486b19d9ea8babb2c1623f424ab391`；冻结 HTML 112 UTF-8 字节，封面 19723 字节。身份 key 仅显式保存在该私有验收目录，供本次验收进程读取；不得复制进仓库或正式配置。
- 零网络预检通过后按用户授权只执行一次，Account=1、Target=4、Attempt=4。实际完成 `token`，停在 `asset_0`；safe code=`official_response_unconfirmed`、dispatch_hint=true，status=unknown、target=reconciliation_needed，无 remote_id/readback_hash。draft/add/read 均未执行，未取得 media_id，不公开发布。
- 只读全字段比较确认原 Attempt 1/2/3 未变化；源库仍3条、副本仅新增1条；无 Receipt/PublishedContentRecord。新旧 Unknown 都不重试，预览/证据保留，不删除远端或猜测素材是否已上传。
- 当前错误类别无法定位具体 HTTP/响应解析分支，需要先细化安全诊断；不把失败归因 DNS/VPN、不盲改协议。2.8/2.8a/2.9/2.10 继续未完成；本轮没有新业务代码/测试或正式迁移。

## 2026-10-02 WeWrite parity 实验与 endpoint 纠正

- 已授权的新产品测试稿在私有副本 `/private/tmp/aics-wechat-short-parity-wZDZ1K/acceptance.sqlite`，Candidate=3、Target=3、Attempt=3；标题“协议一致性测试，请勿发布”，冻结正文 95 UTF-8 字节，精确封面 19723 字节。
- 唯一一次调用停在 token：`completed_steps=[]`、`in_flight=token`、`failure_diagnostic.code=official_api_rejected`、无 remote_id。Attempt 保持 unknown，Target 保持 reconciliation_needed；上传、draft/add 和回读均未执行，没有新草稿创建证据，旧 Attempt 1/2 未重试。
- 离线发现上一批虽改 GET/query，却遗漏 `_PATHS["token"]=/cgi-bin/stable_token`，既有 wire 断言也仍检查旧地址。本轮更正为 WeWrite 的 `/cgi-bin/token`；收到 API 拒绝时保持实际 `dispatched=True`，但不回填 Attempt 3 的历史 false 提示，不按它推断请求未发送。
- 已离线复现两处遗漏；110 项既有定向、全后端 1660 passed / 28 skipped / 8 existing warnings（81.27秒）、Ruff/公众号 change strict/diff 及独立窄复核通过。此次修复本身没有微信请求或凭据读取，不能替代真实验收；2.8/2.8a 保持未完成。

## 2026-10-02 独立 CLI 证据（不替代产品验收）

此前获授权的 WeWrite 独立测试稿“系统联调测试，请勿发布”已成功进入草稿箱，命令正常退出并返回 draft media ID `TrHZ7fvz9Q_Wyx8cuHKbySlJWYxkNZYzL69KVigMsODFbeDny-8uGE9z7qzCoY8A`。没有公开发布；尚未取得该草稿匹配内容的 API 回读。此调用不是下文产品 Candidate/Target/Attempt 链路，不能关闭官方 Publisher 的 2.8 或建立 CapabilityVerification。

此前对用户 VPN/DNS 的归因不成立：相同网络操作在工具沙箱内受限，提升到本机执行权限后微信直连与 MiniMax 连接成功。没有为本轮改动 VPN/DNS/系统代理；MiniMax 仅测试进程使用已有 127.0.0.1:7890 代理。下文原产品 Attempt=1 的上传 unknown 保持原样，不重新发送，也不另建 Candidate 绕过。

## 需求与边界

用户已批准指定 WeWrite/new_media 同一公众号的 token、精确封面上传、一次草稿创建和回读实验，并确认可以使用醒目标注“系统联调测试，请勿发布”的短稿和测试封面。最终 HTML 正文 UTF-8 必须严格小于 2048 字节，不改稿、不截断、不公开发布。**真实执行一次：token成功，封面上传未确认，未进入草稿创建/回读；完整验收未通过。**

## 2026-10-01 实际执行证据

后续离线诊断修正：发现execute_prepared原来丢弃固定transport错误分类，现只在未来失败Attempt保存`failure_diagnostic={code,dispatch_hint}`（code白名单，hint严格bool或null）。不存raw异常/URL/token/provider消息；不改unknown/自动重试门槛，不为本次历史Attempt补猜测。旧错误的具体原因仍不可恢复。

初次上传3项及回读1项RED→GREEN；初批110相关通过，最终全后端1629 passed/28 skipped/9 warnings，范围Ruff、strict31/31、diff及两次独立只读复核通过。首次full因未初始化临时worker库有1失败，随后仅seed隔离临时库重跑，不改业务代码来绕过测试。无新微信请求；全应用Ruff仍12既有项，前端/原生PG本批未重跑。

- 现有产品API生成真实冻结审批链路，原创测试封面经视觉核对；预检HTML810字节，零Target/Attempt，随后只执行一次。
- Candidate=1，hash=`2ce5a670d9a2e3ba2097aff4f4bee59466db92f58abb9a1689d250b31b75c1f7`；render hash=`a53f21ec84188e71740c712aeb88fc50883fca921bdbb7b287bc209f8e9556c0`。
- Account=1，Target=1，Attempt=1；completed_steps=`[token]`，in_flight=`asset_0`，status=`unknown`，target_status=`reconciliation_needed`，safe error=`official_result_unconfirmed`。remote_id与readback_hash为空；create/read未执行。不能断言封面未写入远端，也不能归因为DNS。
- 私有权威数据库：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aics-wechat-short-real-a2_tdwvq/acceptance.sqlite`；保留用于对账，不自动重试/删除。身份key仅验收进程显式配置，凭据不落盘/日志，不生成CapabilityVerification。
- general_contract_ready=false，public_publication=false，retry_allowed=false。F7 96/105、补充17/20、F8未apply；无业务代码/迁移改动，无commit/push/deploy。

实验不是长文合同确认或一般账号验证，不关闭 F7/F8。正文图片 URL 的现有保守展开上界会拒绝 inline 实验，首个实验只允许精确封面和短正文；这不代表完整公众号内容能力已验收。

## 目录与真源

- `apps/api/scripts/accept_wechat_short_draft.py`：默认 rollback-only 预检；显式 `--execute` 才进入现有产品 Delivery。
- `apps/api/tests/test_f7_wechat_short_acceptance_runner.py`：离线范围与默认零请求回归，使用假凭据/隔离 transport，不是平台验收。
- `app/services/wechat_official_delivery.py`：现有 atomic prepare、Attempt claim、live gates、执行与 Unknown 真源。
- `openspec/changes/add-account-bound-wechat-draft-publisher/`：已批准的范围；2.8 仍未完成。

## 验收准备

通过现有产品 API，在独立临时目录建立验收库/素材，完成真实的 Persona/Account 精确绑定、connection 配置、Project/Brief/Frozen FactPack/Master/Variant/checks/Candidate/Approval。禁止手填假的 checksum、CheckRun、CapabilityVerification 或跳过 Evidence gate。测试稿本身只用于联调，事实/观点及封面权利必须明确。

入口只接受临时目录内已存在、当前用户所有、其他用户不可读的 SQLite 文件（文件 0600、父目录 0700）。它不创建表、不迁移、不复制默认开发库、不改生产数据。数据库保留真实 Target/Attempt/步骤/remote ID，是中断恢复的权威证据；不要在尚需对账时删除。

## 依赖与运行

沿用 API 虚拟环境、SQLAlchemy、PyYAML（当前环境已安装）；不安装新依赖。仅运行该入口不会调用模型或旧 WeWrite 发布 CLI。实际验收数据仍必须事先通过产品链路准备好。

从 `apps/api` 运行 `.venv/bin/python scripts/accept_wechat_short_draft.py --help` 查看参数。所有参数均必填：`--database`（绝对路径）、`--candidate-id`、`--candidate-hash`、`--account-id`、`--actor`、`--expires-at`（显式 Unix 秒，最多 15 分钟）。不带 `--execute` 时只预检并回滚，无 Target/Attempt 留存、无网络。

只有测试稿/封面得到确认后，才使用同一精确参数加 `--execute`。不能改用全局 enable、临时 monkeypatch 或另一发布器。已有该 Candidate 的官方 Target 会拒绝再次运行；失败/Unknown 不得通过重新启动脚本、另建 Candidate 或修改 DB 冒充重试权限。

HMAC 身份 key 必须显式存在于当前进程 `AICS_WECHAT_RUNTIME_IDENTITY_KEY`；脚本不会随机生成 fallback。保留同一身份/配置版本供授权期内显式回读，不将 key 写入仓库、命令参数、终端输出或验收记录。

凭据只读取已批准的 `/Users/mshengran/.wewrite/config.yaml` 与 `/Users/mshengran/Project/new_media/config/accounts.yaml`，两份 `wechat.appid` / `wechat.secret` 必须一致。脚本仅在当前进程临时设置精确 Account 的 secret 引用与版本，结束恢复原环境；不复制凭据到 DB/日志/manifest，不修改源配置。

## 结果与恢复

默认预检不生成/补齐缺失资源。所有 ownership、approval/currentness、live rights/evidence/check、注册状态、runtime、最终字节和发送点期限仍由现有产品服务验证。

JSON 结果只包含允许的状态、内部 ID、内容/身份/render/runtime/readback hash、完成步骤。不会打印 AppID、正文、token、AppSecret、claim、签名、原始 provider 响应或错误。外部步骤失败且没有完成证据时，`dispatched=null` 表示不能证明是否发送，不应理解为零请求。

成功必须由既有 Attempt 的 `draft/add` 合法非空 media_id 支持，与已批准 WeWrite 规则一致；matching readback 是可选增强核验，不要求第二次创建。`succeeded / awaiting_manual_receipt` 是草稿交付结果，不是公开发布，不自动生成 Receipt、PublishedContentRecord 或一般 verified。非零退出、`unconfirmed` 或 Unknown 时，先检查现有 Attempt；保留 partial 和已知 draft ID，禁止再 create。known-ID 回读只走现有显式接口及尚未过期的 exact authority；到期不能自动续签。

## 已完成 / TODO

- 已完成：入口、默认rollback及opt-in边界、固定配置一致性/敏感错误遮蔽、精确产品校验、同Candidate防重复；真实隔离产品数据准备、token/封面upload/draft/add、有效media_id记录及用户后台可见性确认。
- 已确认：本次准确标题“响应兼容测试，请勿发布”，同一黄色测试封面，仅进入草稿箱，不公开发布。
- 未执行：可选的精确草稿正文API回读；不影响已记录的创建成功，不代表匹配回读PASS。
- 待完成：一般长文官方合同/账号verified范围、原文件名契约差异、整阶段终验/提交、主规格同步归档。其他真实Provider/F8继续独立，不以本脚本或离线通过代替。
# 2026-10-02：公众号补充变更最终收口

本节取代下文同日历史计数。用户接受指定真实账号的产品草稿创建/media_id和后台确认；成功草稿额外回读为明确豁免，不记录成已执行。补充变更22/22，仅此变更获准同步主规格、归档和本地提交；整体F7/F8不因此关单，`remote_contract_ready=false`和Unknown禁止自动重发继续保留。

文件名缺口已经补齐：新official render版本2从exact MaterialRevision.metadata_json.filename冻结原名称及MIME，两者参与render/Candidate hash，上传前逐步live核对后原样透传。拒绝缺失/不安全名称，不伪造technical filename；v1历史hash/预览/本地包不改，新远端动作必须重新冻结审批，不审批后补值。没有新表/迁移或新的真实公众号请求。

最终新鲜证据：

| Gate | Result | Scope |
| --- | --- | --- |
| Full backend | 1660 passed / 28 skipped / 8 warnings | 当前完整工作区，74.79秒 |
| Commit-isolated backend | 1624 passed / 28 skipped / 8 warnings | 仅公众号拟提交快照，75.36秒；不依赖未提交MiniMax/F8 |
| Native PostgreSQL / migrations | 22 passed / 5 warnings | 完整工作区及公众号快照分别实跑；临时本机数据库，不是生产迁移 |
| TypeScript / Vite / FE-P1 | PASS | 两个范围分别构建；快照projects224.89kB/72.96gzip，commonProduction280.24/89.14 |
| Browser fixtures | 41 gates PASS / zero page errors | 账号20、冻结预览12、对账9；阻断外部请求，不是新的真实发送 |
| Ruff / diff-check | PASS | 公众号代码及拟提交快照 |
| OpenSpec all strict | 33 passed / 0 failed | 同步并归档之后的全部主规格及活动变更 |
| Independent review | APPROVE | 安全/交付、现有测试修正、原文件名与拆分提交范围；未冒充审查员重新运行测试 |

本轮修正了四处遗留PG测试自动read期望，以及完整性测试的同义错误提示/always-cleanup；409、无Attempt/禁止publisher调用、竞争/撤销/Unknown保护均保留。早期全量10失败含9项共享字节污染、私有快照漏枚举造成41失败等已重跑解决，不把失败记录删除或作为通过依据。

提交只包含公众号实现、账号f7c加法迁移、相关UI/回归/规格/证据；MiniMax/model routing/F8保持原工作区改动，不推送、部署、改正式配置/库或公开发布。

归档位置：`openspec/changes/archive/2026-10-02-add-account-bound-wechat-draft-publisher/`；长期主规格：`openspec/specs/account-bound-wechat-draft-publisher/spec.md`。22项任务全部完成，原requirement/scenario均保留，无Purpose TBD。测试PostgreSQL容器及匿名卷已清理，15391测试服务已无监听；私有验收文件保留用于追溯。
