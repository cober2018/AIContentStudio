# FE-F7 capability implementation and evidence matrix

2026-10-03最新：F7为107/110，8.3/10.5已按精确有界公众号草稿范围通过。当前实现真实Attempt7成功、原账号用户可见确认、Receipt1/Verification1持久化及新进程幂等回读完成；不同账号/形态/动作/版本/runtime不复用。仅私有验收库，未搬入正式库，未公开发布/成功草稿回读或重发，不放开一般长文合同。剩10.2 Commons用户暂缓、10.11本地提交、10.12主规格同步归档。模型路由23/23不变，详见[真实公众号证据](FE_F7_SHORT_DRAFT_ACCEPTANCE.md)；下方105/110及缺口描述均为本轮前的历史。

2026-10-03主清单最新：10.3按当前真实模型范围及限定证据复核关闭，F7为105/110、剩5条；模型路由仍23/23。8.3/10.5仍需补成功Attempt与当前指纹的显式绑定，并获得当前版本单次草稿授权/同账号确认，不能从旧真实草稿或夹具推定verified；Commons10.2用户暂缓，10.11本地提交与10.12同步归档未执行。当前模型表保持以下真实/接受/权利边界，不新增模型或微信调用。详见[主任务](../openspec/changes/fe-f7-capability-integrations-delivery/tasks.md)。

## 2026-10-03 当前范围与证据（下方旧计数/未接入状态均为历史）

模型路由当前23/23，最后五项实施与限定独立复核已完成；最终门禁为1660后端通过/28跳过、177定向、Web/FE-P1/state、strict34/34、Ruff/diff。canonical同步/归档未执行，整个F7/F8仍以各自任务为准。具体真实/夹具/排除范围如下，不从计数推导额外供应商能力或许可。

| 能力 | 当前实际证据 | 当前边界 |
|---|---|---|
| CPA通用聊天 | 三个exact模型的产品chat200、模型发现、用途路由与Gemini结构化消费者已实测 | 不要求Google/xAI原生适配；CPA媒体未证实，不能因模型名执行 |
| MiniMax图像 | image-01真实JPEG33997bytes、result_ready | 未接受正式素材、公开/商业许可未证实；隔离UI接受是合成结果，不混淆 |
| MiniMax TTS | 真实task→人工接受→正式MaterialRevision6→Project1引用→Unit3 Master9及浏览器刷新 | 公开/模型/商业权利false，不能冻结为可发布音频 |
| MiniMax云ASR | 真实WAV及测试MP4音轨准确转写 | 固定SRT/时间戳、来源hash；不是视频生成/画面理解 |
| 本机MLX ASR | 用户视频→43字幕→明确接受/保存Video Master5→刷新/重启回读 | 本地离线，原素材/运行收据固定；不替代事实证据 |
| generic持久任务 | 并发/崩溃/重启、key/credential/job/bytes篡改、撤权/回滚、Unknown不重发已隔离验收 | 夹具不是供应商视频或许可PASS |
| MiniMax真实视频/H3 | excluded_by_user_scope | 停止调用，不是PASS或全品牌无能力，不阻断当前范围 |
| 路由页面 | 合成image插件/native TTS预览接受、Unknown、unsupported零发送、限额CAS实际浏览器已验收 | 原真实验收不重复计费，本change计数以tasks.md当前为准 |

当前协议、限额、权利界限见[契约](FE_F7_PROVIDER_ADAPTER_CONTRACTS.md)，真实/夹具证据见[模型验收](FE_F7_MODEL_VALIDATION.md)。已有正式本地f7d启用不等于F8身份/租户/部署验收；本批不更改正式配置、数据库、额度或公众号。以下历史矩阵保留追溯，不作为当前TODO清单。

2026-10-03 real speech acceptance: three authorized operations succeeded, no retries/video generation. TTS speech-2.8-hd returned a 3.41334375s WAV through isolated durable-task APIs; a new process verified task/result HMAC, CLI credential epoch and exact bytes. Existing asr-1.0 adapter accurately transcribed both WAV and locally constructed H.264/AAC test-video audio. These are real supplier proofs, not synthetic responses; ASR Production API/browser, formal schema/config/material acceptance and public/commercial rights remain separate/unverified. Existing regressions54 passed, strict33/33, diff-check PASS; routing remains15/23. See [current evidence](FE_F7_MODEL_VALIDATION.md).

2026-10-03 latest user scope: MiniMax video generation/original-H3 download is excluded for this account/package, not PASS and no longer a current F7 blocker; stop further video requests/queries. Prior H3/DNS evidence remains historical. MiniMax live focus is TTS, ASR and extraction of existing video audio for ASR (not video generation or visual understanding). No configuration was mutated and no speech operation was performed by this scope update.

2026-10-03 actual model evidence: CPA product chat tests PASS for gemini-3.8-flash-high, claude-opus-4-6-thinking and grok-4.7; discovery contains all three; seven purpose resolutions and real Gemini JSON consumer PASS. Revision/default/routes unchanged. Original MiniMax-H3 job is remotely succeeded, but product download returns zero bytes because the OSS host resolves to VPN Fake-IP198.18.4.255. No replacement generation or media acceptance. Prior401 is historical, and CPA chat is not CPA media or F7 full acceptance. See [current evidence](FE_F7_MODEL_VALIDATION.md).

## 2026-10-02 最新范围决议（下方旧计数为历史快照）

主 F7 成功草稿 API 回读不再是验收条件：精确 Attempt 的有效 `media_id` 加同账号后台人工确认已满足本次有界草稿创建，10.6 按新口径关闭；一般账号/形态/动作的 CapabilityVerification 仍属 8.3/10.5，不能由一次草稿推定。Gemini 和 `grok-4.7` 都通过第三方 CPA 网关接入；模型路由变更取消 Google/xAI 官方专用适配器任务 2.2/2.3，改按已配置的 OpenAI-compatible 接口和真实逐操作协议验证。现有模型聊天注册不证明 CPA 生图/视频/TTS/ASR 可用，MiniMax CLI 的独立任务与可靠性验收不变。当前未新发微信草稿或模型付费请求，未创建一般能力验证，也未更改默认路由。准确计数以两份 active `tasks.md` 为准；本文件以下旧复合计数与文件名差异叙述是历史记录。

## 2026-10-02 MiniMax 单次真实图片/语音证据

在私有隔离 SQLite 副本中各执行一次 MiniMax CLI：`image-01` 任务 `cc6f9c535ac94ab296916aff9b990d8f` 返回 `image/jpeg`、33997 bytes、SHA256 `1e18a7be540f091ac7d71510a3aebe68a24ca57413f99b2e00667857c0db7298`；`speech-2.8-hd` 任务 `90a0d78b4fbd4d0e97bafbc922a5e25d` 返回 `audio/wav`、180980 bytes、SHA256 `5e6c663fb225d07c8db2b0609294966b3a452e791160ef351443c05a39cbcb7b`。两项均为 `result_ready/rev3`，未接受为 `MaterialRevision`。新进程完成 DB/文件字节回读，但本轮临时 receipt key 未持久化，HMAC 跨进程验签未完成；这不是正式可信素材、权限接受或重启恢复证明。旧 image Unknown 不变，不重试。

## 2026-10-02 consolidated current evidence

Authoritative checkout: local main@da73bbb plus the existing dirty F7 tree. Counts: core98/105 + routing14/25 + official supplement19/22 =131/152, 21 remaining. Google/Grok and Commons remain deferred, not PASS. No production migration, configuration mutation, push, archive or F8 activation occurred.

- Official product WeChat draft creation and human draft-box visibility are PASS for the exact bounded experiment: Candidate6/Target6/Attempt6, validmedia_id, succeeded/awaiting_manual_receipt. F7 8.5 immutable package implementation independently passes. No further WeChat request, Receipt, PublishedContentRecord or CapabilityVerification was created; the general long-form/runtime gate remains false. Optional body readback was not executed. Original filename preservation is not established: product multipart uses the MIME-derived media.png/media.jpg, while exact bytes/MIME remain preserved.
- MiniMax read-only reconciliation confirms original TTS result_ready/rev3, WAV126738bytes, original hash and decoded1.96209375seconds; image remains unknown/rev3 with no original job. MaterialRevision0/accepted links null. This process lacks the original receipt key, so byte/hash inspection is NOT a new signed receipt verification or acceptance. There is no original video job in this acceptance database to poll; do not create one under the label recovery.
- Fresh local gates: WeChat129 targeted, backend1660 passed/28 skipped/8warnings, TypeScript/Vite/FE-P1 PASS, all strict33/33, scoped Ruff and diff-check PASS. Native PG/browser were not rerun this turn. Independent reviewer approved8.5 and bounded2.8a only, not whole F7 or general account verification.

The dated sections and matrix below retain historical evidence; statements such as "no real TTS" or "no product draft" describe earlier snapshots, not this current record. Actual remaining scopes are in the three active task lists.

## 2026-10-02 product browser preview increment

Settings now includes the loaded minimax.cli binding option and correct local address/auth-reference labels; two existing isolated bindings read back unchanged. The original real TTS task opens in the product Assets panel after signature/bytes/hash checks; browser audio reports duration1.962094, readyState4 and no media error. No acceptance/rights confirmation was performed: isolated MaterialRevision count remains0 and both task accepted FKs remain null. Original image remains unknown rev3 without resubmission. This is preview evidence, not license, full provider/Workflow, WeChat or F8 acceptance. Build/bundle/state regression and strict33/33 pass; no fresh backend suite claimed for this UI-only patch. Composite remains125/150.

## 2026-10-02 authoritative incremental evidence

Scope remains F7 on local main@da73bbb plus the existing dirty tree. Google/Grok and Commons are user-deferred, not passed. F8 remains unaccepted/not activated. No default configuration, production database, remote publication or archive was changed.

- MiniMax image/TTS now expose fixed durable `submit_task` entry points. Image uses a single base64 response, no CLI CDN downloader, and explicit 8-aligned square dimensions within the frozen pixel ceiling (512–2048 per side). TTS uses the existing WAV generation/decode/duration gate.
- Actual product service acceptance in private isolated SQLite: chat-only selected profile → configured MiniMax TTS plugin → prepared task → committed one-send claim → real `speech-2.8-hd` → result_ready. Task `fcb16a09f4fa406fa84e1df4b520d4a5`; output WAV 126738 bytes, 1.96209375 seconds, SHA256 `8375eaa19d0f33870f4a220c21ab068a88c32add4fd0c8c528544eaf2c715d6e`. Fresh-process receipt/bytes readback passed; no MaterialRevision was created and inventory `verified` remains false.
- The separate image task `34836024ec1443bcac3572febd496f39` exceeded its 25-second deadline. It is persisted as unknown/revision 3 with no original job ID; there is no usable image evidence. Fresh-process readback and rejection of another execution passed. It was not resubmitted or replaced. Do not infer that the supplier did not process/charge it.
- Independent WeWrite CLI test previously created a draft (see short-draft acceptance document). This proves CLI/account connectivity, not the account-bound product Publisher's create/readback gate. The original official product Attempt remains unknown and is not retried.
- Isolated schema was created from current metadata for service acceptance only; this is not an Alembic migration test or F8 acceptance. Receipt key is an explicitly selected isolated-only reproducible test key, never a production credential. Production still needs explicitly provisioned stable secret keys/schema.

Missing: accepted media/project/Workflow and browser closure, actual image/video/ASR evidence, durable safety review, and official product draft readback. Full composite F7 tasks remain 125/150; partial real TTS evidence does not justify completing multi-capability tasks.

## Scope and interpretation

Current refresh: local `main@da73bbb` plus approved uncommitted F7/official Publisher changes, 2026-10-01. F7 remains 97/105; the supplement is 17/20. The original audit input `main@707fc34` and its 94/105 gate record below are historical, not the latest implementation state. This is a repository/acceptance matrix, not a claim about live deployment or every database's configuration. No credential values or real account identifiers were inspected or printed in the Commons continuation.

`Implemented` means a real loaded code path exists. `Externally unverified` means no qualifying real-platform evidence was established by this audit. Fixture scope and externally verified scope must never be conflated. The PRD remains the product goal; local manual packages do not replace remote draft-box requirements.

## Matrix

2026-10-01 user scope decision: Commons is deferred/optional; stop further network and import attempts. It remains externally unverified, not passed. Creative media may use generation providers, but real screenshots/news photos/factual evidence require authentic sources. Gemini/Grok/MiniMax generation endpoints/configuration are not yet established by this matrix; chat model names do not establish executable media capability. No F8 prerequisite or verification gate is silently waived.

| Capability | Actual implementation | Established evidence | Missing / safe behavior |
|---|---|---|---|
| Internal Studio Data Source | Existing typed plugin and snapshots | Backend/project regression | Does not connect arbitrary external plugins |
| Typed API Connector | Explicit exact registration/Endpoint mapping, bounded GET, probe and snapshots | Prior configured isolated endpoint acceptance; scoped persistence regressions | Real source-specific credentials/configuration/evidence still needed; generic Connector is not Notion/SQL |
| Wikimedia material search | `search.wikimedia.commons@1`, bounded metadata/download and explicit rights acceptance | Fixture decoded bytes/revision/cross-Unit browser consumption; real metadata search 200 with 7 candidates | Real stage returned 502, zero imported revisions/verification; subsequent search 502 and API DNS 198.18.0.15. Import unverified; no DNS/private-address bypass |
| Native OpenAI image | `image.openai@1`, exact existing KEY_IMAGE config and one bounded POST | 28 native HTTP transport regressions plus real PNG stage/database acceptance | Explicit supported configuration and separately authorized paid request needed; no source-image edit or fallback |
| Legacy WeWrite image | `asset_provider.wewrite_image@1` retained | Honest unavailable boundary | Mutable global config/internal retry cannot attest exact runtime; no typed execution promotion |
| Video generation | Existing accepted-byte gates plus opt-in fixed MiniMax CLI H3 async/original-job query; durable local task scaffold | MP4 decode and local synthetic original-job/recovery probes | No real video task/result acceptance or complete cross-restart/rights proof; V1 file download remains unavailable; Unknown never resubmits |
| TTS | Existing exact audio acceptance plus opt-in fixed MiniMax CLI speech/WAV implementation | Isolated real `speech-2.8-hd` reached signed `result_ready` with fresh-process byte/hash readback; separate later image/TTS outputs used an ephemeral key and had only file/hash readback | Neither real output was accepted into MaterialRevision; licensing and full recovery/rotation/browser scope remain unverified |
| ASR | Existing suggestion/receipt and explicit Video save; MiniMax opt-in fixed SRT adapter with exact MP4 first-audio preparation or WAV input | Fixture provider/backend/Video browser checks; scoped input/bounds source review | New MP4 preparation has no real transcription acceptance or new targeted tests; full configured model routing/identity evidence and cross-restart receipt integration pending |
| Text render | Production modality deterministic render and scoped verification path | Actual deterministic render/check/Candidate/local package regressions | Must check exact scope/runtime/current context per action; not remote publication |
| Graphic render | `graphic.chromium@1`, explicitly configured browser/font, real PNG and exact scoped verification | Real Chromium PNG and isolated scope/editor/browser acceptance | Local evidence is not external model verification; unsupported fonts/styles fail rather than substitute |
| Video final render | Existing manual exact asset attestation | Video v2/exact refs/render-input/hash/approval/package regressions | No installed automatic final Video renderer; cannot claim generated final video |
| Local delivery | `publisher.copy@1` / explicit manual handoff, v1–v5 dispatch | Frozen Candidate→Approval→Authorization→ZIP and browser acceptance | ZIP/package-ready does not establish publication |
| Official WeChat remote draft | `publisher.wechat.official@1` is loaded; exact account runtime, deterministic pre-approval HTML/slots, bounded official transport, durable Target/Attempt claim, step live locks, partial/readback/reconciliation are implemented | Actual local source→Variant→Candidate→Approval→Authorization→fixture Delivery/Receipt; fourteen native PG/connection guards, 41 isolated UI gates, legacy regressions; draft Receipt never creates public history | `remote_contract_ready()` is false. Conflicting official body limits, exact real account/action authority, deployment credentials and actual platform readback remain unverified; fixture success cannot enable a real scope |
| Legacy WeWrite draft | `publisher.wechat.wewrite@1` retained separately, never aliases the new key | Historical compatibility and fail-closed regression | Global account/converter runtime cannot prove account-bound immutable content; fingerprint unavailable and no inherited official verification |
| X/Douyin/Xiaohongshu remote effects | No verified installed Publisher scope | Fail-closed regressions | Controlled Variant/local package support is not remote publishing support |

Earlier loaded-provider evidence (2026-10-01, before CLI opt-in implementation) used explicit media/publisher bootstrap and descriptor-only registry reads: search=[Commons], image=[legacy WeWrite, native OpenAI], video/TTS/ASR=[], publisher=[copy, official WeChat, legacy WeWrite], official_contract_ready=false. MiniMax registrations now exist behind AICS_ENABLE_MINIMAX_CLI=1; source existence does not prove they are enabled in the user's running process. The Graphic Chromium registration is present in the read bootstrap source; the earlier descriptor command did not enumerate renderer kinds. No new account/runtime probe was performed to update that historical command result.

## Database / deployment distinction

The original read-only inspection of the **existing default local file** `apps/api/content_studio.db` found Alembic version `d4audit00004` and no capability_registration / capability_verification tables. This historical sample was not re-read in the 2026-10-01 refresh. No schema, settings or data were changed. It is not proof of the effective DATABASE_URL of a running process or production. The application must not be described as ready against a deployment database solely because isolated F7 migrations/tests passed. Selecting/migrating that database is a separately authorized operational step; first identify the actual process/database.

## Acceptance debt / next decision

The original batch additionally closed bounded-reader defects: 11 RED→GREEN regressions, 84 targeted and 1446 full backend/2 skipped. Those numbers are historical. Latest official-supplement evidence is recorded in `progress.md`: 1564 backend/26 skipped, 14 PG/guard and 1 isolated account migration, 41 browser API-fixture gates, build/FE-P1 and strict31/31; independently reviewed local increments. These execution results belong to the prior implementation turn, not commands re-run by this descriptor-only refresh. No new business code, browser run, migration or dependency is claimed here.

- The official account-bound local implementation now exists; old claims that no replacement was implemented are superseded. No safe WeWrite runtime has been established, and official real-platform verification remains missing. F7 8.3/8.5 are not closed merely by local adapter tests.
- F7 10.2/10.3/10.5/10.6 actual external/account acceptance is not satisfied by fixtures. Credentials, chosen providers and exact account/action authority are required.
- F7 10.4/10.10: missing implementations/configuration/evidence are explicitly listed above. This matrix does not close 10.11 ARCHIVE_READY or F8 0.1.
- The user approved a separate account-bound official adapter and local implementation. Actual token/upload/create/readback remains separately authorized and contract-gated. Do not enable the old bypass or label the new HTTP adapter as a proven WeWrite scope.
- F8 production auth/stable subject binding, storage, health, recovery/Golden/end-to-end/runbook work remains unapplied; completing this audit is not completing F8.

No push, deploy, production migration, canonical sync or archive. The original Commons read attempt was refused by URL safety; it was not repeated during this refresh. No successful external read, paid model request, account effect or provider verification resulted. Validation was not disabled.
# MiniMax CLI local inventory update (2026-10-02)

`mmx 1.0.27` is present and, when explicitly enabled for the local process, registers fixed image/video/TTS/ASR providers. The fixed credential reader produced an opaque continuity fingerprint and image dry-run matched `image-01`. This is local executable inventory evidence only; it is not paid generation, accepted media, rights, or remote-platform verification.
