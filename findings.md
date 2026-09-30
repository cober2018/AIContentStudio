# 配置记录

## 2026-09-30 F6E 最终复核决策

- v5 按 `(unit_id, variant_key)` 判当前，旧 v3/v4 按不含 v5 的 Unit legacy 系列判当前；否则冻结任一 v5 会意外阻断旧 v4 的新审批/授权。Project Versions 和 Review UI 必须与服务端采用同一系列边界。
- Review Overview 不可仅取最后冻结渠道的审批/授权作为整个 Unit 的结论。多系列投影逐一展示审批/目标，任一系列待审核时整体保持 `waiting_review`；`unknown` 对账仍优先。
- 模型辅助适配会接触完整冻结 FactPack，上游 `model_use_allowed=false` 即使没有显式 citation，也必须在 Provider 调用之前阻断。安全摘要/LLMRun 本身不能代替输入权利检查。
- 候选初次读取与授权后刷新是两条独立异步路径；两者在每个 awaited 响应后均需核当前选中项。隔离浏览器以迟到响应注入证明不会覆盖新选择。

## 2026-09-30 F6E 前端与数据库边界

- `ContentUnit` 没有持久 `content_form` 字段；Matrix 的 form 是非持久规划建议，确认仅创建现有 Unit。相同渠道的多个 form 可在该 Unit 下继续建立不同 `ChannelVariant` 系列，不能把 Unit title 当 durable form 真源。
- 旧 Review UI 以 Unit 最新 Candidate 和 Unit.channel_id 授权；v5 的当前性与渠道目标必须分别取 `variantSeries` 与冻结 manifest.target，否则 X Single 会误伤 X Thread/公众号，channel-neutral Unit 会无法授权。交付目标列表也必须按所选 Candidate 读取，不能复用 Unit 最新候选的 targets。
- Variant/Matrix 已拆成 lazy chunk；构建脚本现在验证 import graph，Channel Variants 不引入 TipTap/XYFlow。数据库对 Variant 历史采用 RESTRICT/no cascade，项目归档与 Unit 执行历史保护保留历史关系；已在隔离 SQLite 迁移测试核对约束，PostgreSQL 仍待独立验证。

## 2026-09-30 F6E 历史包与声明边界

- 历史 v5 Candidate 的冻结 warning 快照只证明当时有人处置，不证明同一 Master 后来追加的检查仍安全。包回读现在核最新适用来源检查及 warning 集合；`text_platform` 等 channel-neutral 目标检查、抖音脚本不需要的最终视频 render 检查仍按 Variant 来源门槛排除，避免误拦正常历史包。
- 受控 Variant 的披露声明是独立元数据。若正文及 exact citation/evidence refs 与来源投影逐一相同，新增声明不应使事实覆盖从 `source_equivalent` 降为 `unknown`；当前只对这种可证明的等价子集通过，不放宽改写正文后的语义检查。
- 五形态本地包都从冻结清单输出，不调用远端 Publisher；对同一个 Candidate，`ContentAccount` 是稳定账号身份，`account_ref` 只是快照别名。两个账号共享别名时仍须各自授权、各自保留状态；一个 unknown 不得让另一个已授权本地包失效，但项目 Overview 必须继续提示对账。

## 2026-09-30 F6E v5 来源 warning 的处置门槛

- v5 Variant 可在来源 Master 存在 current warning 时就绪，但原 v5 Candidate 未冻结这些提示；审批与包回读因此会丢失人工确认义务。现在 Candidate 清单冻结来源 Master 最新适用 warning，审批要求 check ID/input hash 对应的非空理由，已批准历史取包重验 Review 中的处置；缺失或篡改 fail closed。只有无 warning 的旧 v5 清单允许缺少新字段。

## 2026-09-30 F6E 脚本交付与视频成片的来源门槛

- `video.master.v2` 的 `render` 检查要求真实成片，适合直接冻结 Video v4；但 `douyin.spoken_script.v1` 的受控目标是脚本和估算 SRT。原 `_source_gate` 将前者硬性套在后者上，使脚本 v5 永远无法 ready。仅对这一准确来源/目标组合豁免成片检查，其余来源上下文、结构、时间线、身份、事实、素材权利与 Variant 自身检查不变。
- 两种 v5 形态已实测本地包：Graphic→小红书的真实图片、Video→抖音的脚本/SRT/B-roll。抖音 ZIP 不含未生产的 MP4；直接 Video v4 冻结仍拒绝无成片源。B-roll 撤权后取包返回 `variant_b_roll_unready`，未修改已批准历史。
- 三个 Text 目标已新增真实 API 集成回归：带原稿 Citation 的 Text v2→公众号/X Thread/X Single 都能冻结准确 FactPackItem、checksum、位置并生成本地包；公众号同时带真实封面字节。按当前 `_evidence_check` 的精确来源投影比较逻辑，新增手工声明会使证据覆盖变为 `incomplete`；这条声明场景尚未实测闭环，6.6 继续待办，不将空声明清单冒充完整能力。
- 同一已发布 Profile 的 RuleSet 原地变化会改变目标能力快照；回读必须把旧 Variant 检查标为 stale，而不是沿用此前 pass。新增定向测试已确认 `profile_or_adapter_changed` 且所有检查 stale；测试来源未建 Brief/Fact Boundary，因此原 `source_gate` 先前并不 ready，本例只验证规则漂移，不声称可冻结。

## 2026-09-30 F6E Text 引用的保守继承

- 之前 Text Adapter 遇任何原稿 Citation 都拒绝，虽有 FactPackItem 也不能进入 Variant。现在仅支持无格式的段落且文字不变：服务端比对原 Master 的 citation ID、block/range、selected-text hash 与 ContentMasterEvidenceRef，映射成目标 location/range。X Single 的 location 固定为 `single`，公众号/X Thread 保持原 block ID。
- 目标 Variant 不能漏掉原稿 citation；检查只把完全同源的确定性投影判为 `source_equivalent`。手工或模型改写后的证据语义仍未知；模型建议带引用来源暂不可用，不把可能移动的引用当已验证。事实撤权继续令旧检查 stale。
- 并发同幂等键请求可能两者先读到不存在，再由数据库唯一键选出赢家；失败方不能一律报泛化冲突，应回读胜出行并比较请求指纹。此路径已加恢复逻辑，仍需双连接事务回归证明实际数据库行为。

## 2026-09-30 F6E 模型建议与来源权限

- Variant 的模型辅助入口复用现有 `LLMRun`，但建议并非 Variant 写入。输入锚定当前 Master 和已发布目标 Profile/Adapter；Provider 输出先在服务端 canonicalize，过大输出不进入运行记录，失败运行不能成为可信血缘。
- 显式保存只接受服务端签出的同项目/单元/操作者 `LLMRun`，核对输入、输出和当前目标能力；Variant/v5 仅保存安全摘要，不复制 raw output、错误或 Secret。改写产生的新事实若没有可证明的精确证据，现有 evidence check 保持 incomplete，不能冻结 Candidate。
- 归档单元先前还能拿到适配预览；现在预览和模型建议都拒绝，历史 Variant 仍可只读。Matrix 在无 Brief 身份范围时优先当前项目已选身份，不把其他作者扩成建议。
- Variant 直接保存时的安全摘要并不足以保证 v5 冻结时仍可信；现在候选输入装载会回查 `LLMRun` 的成功状态、原始服务端 receipt 与当前 Variant 绑定，运行变为 failed 后不能再冻结。Variant 版本差异使用同一系列上一修订及稳定块 ID，区分移动和改文；不拿不同渠道版本作前版。

## 2026-09-30 F6E 多渠道读模型与只读 Matrix

- 旧 Versions/Overview 把同 Unit 最大 Candidate ID 当唯一当前结果，导致其他渠道系列被误标过期，甚至漏掉待对账 unknown。v5 必须用 `(unit_id, variant_key)` 系列投影，未知回执继续高于内容建议。
- 旧 Review 媒体预览仅认 v4 render outputs，v5 封面虽能进入 ZIP 却无法查看；v5 预览应从冻结 manifest 的 exact asset ref 找版本，实时校验撤权、hash、MIME，不按任意 revision ID 取文件。
- Matrix 仅取同渠道同形态 PublishedContentRecord 与实际 PerformanceObservation 的指标 namespace/key 覆盖，`known/missing/unknown` 分开；不聚合跨平台分数，不用缺失数据补零。成本/价值模型仍不存在，`estimatedCost/estimatedValue/confidence=unknown` 尚未满足完整估计要求，不能伪造排序。

## 2026-09-30 F6E 批量交付决策

- 100 个条目是 OpenSpec 验收粒度，不应等同 100 个实施批次。剩余工作改为后端闭环、前端与终验两批；原规格、失败关闭边界和测试覆盖不因此缩小。未提交的 v5 Review 实现纳入第一批，集中验证后再提交。

## 2026-09-30 F6E v5 审批与历史包

- 旧 Unit-wide `latest ContentAsset.id` 判定会把同一 Master 的 X single 和 thread 互相误判为历史候选；v5 必须以 `(content_unit_id, variant_key)` 查本系列 Candidate head，v3/v4 原行为不动。
- v5 历史已授权包不能调用“当前 Variant”校验，否则新修订会错误废止已有本地授权；历史包须核 frozen Variant→Master→Profile/Identity/Brief/Boundary/refs/checks 血缘，并重新核实时素材字节和公开权利。历史可读不代表历史候选可新建授权。
- `channel_variant_revision_id` 为 v5 唯一 Candidate 来源 FK；五个旧来源/Workflow 字段任一非空，即使已批准和已有授权，授权与包仍拒绝，不能退回 v4/v3。公众号精确封面字节已进入本地 ZIP，撤权后取包被拦截；远端动作仍属于 F7 未验证能力。

## 2026-09-30 F6E v5 实时冻结

- 旧 Freeze API 仅允许 Draft 或 Master，RED 回归得到 422；新增 Variant 显式分派后，只有服务端读取的当前且 `ready` 的 Variant 能成为 v5 来源。v5 的来源 Master 渠道/形态与目标渠道/形态必须分开冻结，不能用 Unit 的源渠道冒充目标。
- Candidate v5 `content_master_revision_id` 与 `workflow_run_id` 均不写；来源 Master/Workflow 仅在 manifest 中追溯。只读预览先按 schema 识别 v5，再拒绝五个旧来源/工作流字段污染及目标投影列不符。
- 现有 Variant `ready` 检查已覆盖部分实时素材/证据/渲染；冻结前与提交前双次重算可捕获一般漂移。审批/授权/包的 v5 live validator 已在后续切片接入，但冻结全面并发锁与跨形态验收仍未完成；不得把冻结成功等同已获审批或可交付。

## 2026-09-30 F6E v5 清单边界

- v4 manifest builder 依赖源 Master 的 channel/form，不能直接服务 channel-neutral v5；v5 改为 `source_master` 与 `target` 分离，目标 Profile/Adapter/Rule 不覆盖源渠道血缘。
- `ContentAsset.channel_variant_revision_id` 已存在，但仅有 FK 不构成 v5 冻结闭环。先完成纯、确定性、拒绝 raw LLM 输出的清单契约，再由后续服务加载真实 DB 当前状态并写 Candidate；不能以纯 builder 的通过声称 Freeze 已可用。

## 2026-09-30 F6E Variant 来源与成品投影

- 原 `ready` 只聚合 Variant 自身检查；来源 Master 即使 Brief/Boundary 不全或自身检查缺席，也没有独立门槛。现在以项目级授权后对精确 Master 的只读投影核对，避免把 Variant 局部 pass 当成内容可冻结。
- Adapter `package_projection` 当前是确定性结构/文本投影，不是 ZIP 字节包。新增检查只存安全的 projection hash 和 coverage；Profile/Evidence/Rights/Render 任一未就绪时，package 只能 incomplete。真实本地包和远端副作用需后续明确分开验收。

## 2026-09-30 F6E 公众号封面引用

- 已发布 WeChat article Profile 要求封面；此前 Text Variant 无法携带任何素材，因此正文适配即使成功也永远过不了 Profile 闸门。现只开放一个有界 `cover` sidecar，锚定项目可见的精确 MaterialRevision、内容哈希、文件字节/MIME 与实时公开权利；其它 Text/X 素材仍 fail closed。
- Text Master 已有同形封面时，预览显式继承这一个 exact ref，保存不可静默丢弃；新封面可从项目共享素材池显式选取。不复制图片字节，也不把本地包或远端发布冒充已完成。正文里复杂 inline media、证据继承、封面替换与 v5 package 仍是后续任务。

## 2026-09-30 F6E Profile 与安全检查覆盖边界

- 精确发布 Profile 可以确定目标形态和必要封面/内图；X 单条的纯文字无需媒体，小红书图文的首张真实卡片可满足封面，公众号文章在当前 Text Variant 不支持封面引用时必须明确 `cover_required`，不可因正文结构合法就可冻结。
- `variant_profile` 只把已知的素材规则当作可执行的确定性配置；未知或畸形 RuleSet 返回 incomplete，远端 Publisher 始终显示 unverified。`variant_rights` 复用项目可见、live public-use、字节/hash/MIME 检查；零媒体显示 not_applicable，不伪称实际验证了媒体。
- `variant_evidence` 对精确引用做 scope/checksum/撤权核对，但引用与文字的语义支持关系没有被确定性算法证明时保持 incomplete；手工改写若偏离可证明的来源适配且无引用，也保持 incomplete。简单来源等价改写可通过结构覆盖，但不冒充模型语义审查。
- 现阶段没有完整 byte-exact 本地包检查，因此 `variant_package` 明确保持 incomplete；即使其它已实现检查通过，Variant 整体 `ready=false`。Candidate v5 和最终交付仍待实施。

## 2026-09-29 F6E Variant live drift

- 冻结输入 hash 单独比较只能发现 Variant 行自身变动；同系列新版本、源 Master 新 head、Profile 退役、Evidence 撤权后，旧 schema pass 仍可能显示 current。本轮改为读取时核对真实 head、Master 上下文、当前 published Profile/Adapter/rules、精确证据和 Graphic/Video 素材/渲染；旧 CheckRun 不修改，只投影 `stale` 和具体原因。
- 这只是历史检查的保守失效边界，不代表 `variant_evidence`、`variant_rights`、`variant_profile`、`variant_render` 检查已可执行，更不代表 Candidate v5 可冻结；这些未实现项仍为 incomplete。

## 2026-09-29 F6E 首个 Variant 写入边界

- Variant schema/content 检查必须只说明这一类检查的结果，不能用“结构通过”推断 Profile、权利、证据或渲染已验证。检查投影对每个 required kind 取最新记录；同输入的晚到 blocker 高于旧 pass，输入漂移时旧 pass 变 stale。其余闸门未实施前整体 `ready=false`。
- Video v2 的 `shot_source` 可作为口播脚本 B-roll 的可证明来源：Variant 必须显式保存 shot→MaterialRevision/hash/位置，实时校验项目可见、素材字节和公开权利，并在提交前重复检查。估算 SRT 仅取镜头计划时长，标 `estimated=true`；真实字幕 cue、音轨、最终成片在当前受控适配中不静默丢弃，而是 typed no-write。
- 抖音 `spoken_script` 的目标 `artifact_kind=script`。Video v2 只有 shot 与 script block 能无损对应、且不含未映射媒体/定时字幕时才可确定性预览/保存；没有视频成片或真实时码就不产生 `estimated_srt`。B-roll/音轨/字幕来源未来必须按 exact ref/时间映射，不可静默丢弃或冒充发布成片。
- 小红书图文不能由 canvas prompt 推断已产图：F6C Graphic Master 的 `render_input_hash` attestation、逐画布输出与当前素材字节/哈希/权利同时成立，才能预览/保存 `image_note`。Variant 卡片 `image_ref_key` 和冻结 `ChannelVariantAssetRef.sort_order` 必须同序；显式重排两者合法，只改一边拒绝。提交前撤权会回滚 Variant、Refs、Event。
- 预览与保存是两个动作：`adapt-preview` 只对当前精确 Master 和 published Profile 生成 canonical Text 建议，不创建 Variant、ProjectEvent 或 DeliveryTarget；不支持的目标和来源 refs 明确不可执行。远端 Publisher 仍为后续 F7 范围。
- Text Variant 新增的 citation 只能绑定当前 source Master 所冻结项目 Fact Boundary 内的 exact FactPackItem/checksum，且该 item 仍须可公开使用、未撤权；正文 range 与 EvidenceRef locator 由 canonical payload 同步校验。提交前撤权会回滚 Variant、引用和 ProjectEvent。畸形 ref 在数据库查询前转成 422，不让任意 JSON 引发 500。
- 公众号文章、X 推串及单条仅实现无素材/证据引用的简单 Text v2 确定性子集；复杂结构、citation、exact refs 不能被静默丢弃，当前服务对其 fail closed。注册的 published Profile 不等于 Graphic/Video Adapter 已可执行。
- Variant 写入按项目/Unit 授权、精确 Master/Identity/Profile、稳定系列 CAS、幂等键与不可改目标验证；Profile 在事务提交前改变时回滚 Variant 和 ProjectEvent。当前仍需处理素材 refs、来源 Master 已有 refs 的显式映射、完整 live rights/evidence、AI receipt、检查与 v5 Candidate，不能把已保存 Variant 等同可冻结/发布。

## 2026-09-29 F6E 独立规格结论

- `x/thread` 与 `x/single` 的 published Profile 都存在，但注册配置本身不证明 Adapter 已实现；现公众号文章、X 推串和单条的无引用 Text v2 子集、小红书已验证 render 图文以及抖音无媒体口播脚本子集可执行，其余来源内容仍需显式映射。所有目标均未验证远端能力；旧 `x_thread/thread` 不在 v5 矩阵内。
- 五种 Variant canonical payload 在服务端限制字段、稳定 ID/顺序与长度；引用了图片槽位或 citation 却缺少对应精确素材 hash / FactPackItem checksum+locator 时拒绝。纯校验通过不代表当前项目素材可见、live rights 或真实字节已核验；这些还要在项目级保存与冻结闸门完成。
- Variant 只读 API 必须先核项目 owner 和 Unit 归属，再查行；只判断 `variant_id` 存在会造成跨项目历史泄漏。当前 list/current/detail 均复用 `owned_unit()`，detail 再确认行的 project/unit，foreign raw-ID 回归为 404。
- 当前 Registry 的 published Profile 真源是 `ChannelTemplateVersion`，所以 Variant 除 channel/form/hash 外还须精确保存 `profile_template_version_id` 外键；只存字符串版本会丢掉不可变配置来源。此字段已加入计划内 Variant 表。
- 降级安全不能只看 Variant FK：历史 v5 Candidate 的链接若被置空，也必须拒绝删表。SQLite 与临时 PostgreSQL 均证实 manifest `schema_version=5` 可阻断降级，并保持版本/表/历史不变。
- 外部复核确认 v5 `channel_variant_revision_id` 是唯一 Candidate 来源 FK；`draft_id`、`topic_brief_id`、`mother_revision_id`、`content_master_revision_id`、`workflow_run_id` 均须为空。工作流血缘只能经 Variant→精确 source Master→冻结 manifest 追溯。
- `(unit_id, variant_key)` 是 v5 当前性的系列边界，不以 Unit 下最大 Candidate ID 替代；v3/v4 的分派与当前性保持原语义。
- F6E 可开始计划内四表、一列的加法迁移；若出现破坏性迁移、额外持久业务对象或安全闸门放宽，先停下修订规格。

## 2026-09-29 F6E 前置门槛与独立规格复核分离

- F6C `tasks.md` 74 项全勾，`progress.md` 记录后端、SPEC、前端独立复核 APPROVE；F6D `tasks.md` 79 项全勾，外部独立实施复核 APPROVE。F6E 0.1 可以作为历史依赖确认完成。
- F6E 0.2 是不同门槛：当前 source-pointer 修订尚未收到独立 SPEC PASS。不能用 F6C/F6D 的审批替代 F6E 规格审批，也不能因为 0.1 完成就启动 v5 迁移/业务代码。

## 2026-09-29 F6D 独立结论与 F6E v5 source-pointer

- 独立复核 `main@a51efe0` 明确 F6D 实施 `APPROVE`；复核方看了 D1–D3 实现、回归代码和浏览器证据，但未重跑报告中的 1026 项后端测试或 12 个浏览器 gate。8.4 可据复核结论关闭，F7 Provider/真实远端发布不因此变成已验证。
- 当前 `ContentAsset` 实有 `draft_id`、`topic_brief_id`、`mother_revision_id`、`content_master_revision_id` 和 `workflow_run_id`；之前 F6E 只列了其中三列为空，与“Variant 是唯一来源 FK”矛盾。`ContentMasterRevision.origin_workflow_run_id` 已能承载准确工作流来源，因此 v5 选择五列全部为空，工作流血缘随精确 source Master 与冻结 manifest 保存。v3/v4 的 Candidate workflow 投影不变。
- F6E design、主 delta、FE-F4 delta 与任务 8.7/11.14 已列明污染字段逐项拒绝及 Review/Approval/Authorization/Package fail closed。此为规格修订，不表示 v5 代码或独立 SPEC re-review 已通过。

## 2026-09-29 F8 身份映射与发布学习链路

- `deps.get_current_user()` 目前由 `X-Studio-User`/默认 email 查询且可能自动建 User；`User` 仅有唯一 email、role、is_active，没有 `issuer/sub` 字段。F8 生产 token 校验若仅按 email 映射，即使签名有效也缺少明确稳定主体绑定。规格现将映射方案列为实施前审定项；如果必须新增持久结构，属于原计划未定义的 schema 变化，须停下修订 OpenSpec/迁移方案。
- F5B `published_history.sync_receipt()` 仅对 `human_confirmed` 且有 `delivered_at` 的 Receipt 建 Studio PublishedContentRecord，并核 Candidate/Target/hash 与 unresolved Unknown。F8 9.4 本地包与 9.7 发布/学习并非自动相邻步骤：没有真实人工确认时，全链路只能证明到 handoff，不能把 ZIP、授权或 attempt 冒充已发布/学习成功。已在 F8 spec/design/tasks 增加正反场景。

## 2026-09-29 F7 source_url 双用途歧义

- F7 tasks 4.5 原写“Persist source URL/ref/license/provenance”，但 design/spec 同时禁止签名或凭据化抓取地址进入既有 `MaterialRevision.source_url`。`materials.create_revision()` 当前仅透传 `source_url`，因此不修规格容易让实施者把 provider fetch URL 当公开来源引用持久化。
- F7 active spec 现区分 stable public citation URL 与 temporary fetch/preview URL：前者经正向安全验证后可保存；后者不得存储或回显。仅有歧义地址时以有界来源 ID 和单向哈希替代，不伪装成公开引用。实施时还须验证成功与失败路径的 MaterialRevision/审计/事件/API 脱敏；本次没有验证真实 Provider。

## 2026-09-29 F6D 独立复核缺口与 F6E 多系列当前性

- D1 属消费契约错位：后端 frozen Video v2 已有 `script_blocks/timeline/voice/subtitles/overlays/music/cover`，Review UI 仍按 v1 `script/timeline_present` 渲染。前端按 v2 字段存在性分派、只读冻结结构，隔离浏览器实测历史 Candidate 在当前 Master 升版后保持原样。
- D2 源于每条轨道只校验自身 item ID，而 `timeline_media.slot_key=item.id`；两个轨道同名媒体 item 可共享 role/slot。保存前从 canonical 文档导出 expected refs 并校验全局 `(role, slot_key)` 唯一，负向 API 422/无 Master 或 ProjectEvent，正向同一素材在不同 slot 可复用。
- D3 四处枚举 membership 对数组/对象可抛 TypeError；统一先检查字符串类型，16 组非法类型 API 均返回 422，无部分写入。未扩大权利或 Provider 范围。
- E1 不能复用旧 Unit 最大 Candidate ID：同一 Master 先冻结公众号、X thread、X single 后，旧闸门会错误拒绝先冻结的两条。规格现要求 v5 每个稳定 Variant 系列独立当前性、同系列替代；源 Master/context/profile/rights/check 真漂移仍 fail closed，v3/v4 的原路径不放宽。此为需求修订，不是 v5 实施或独立 SPEC 通过。

## 2026-09-29 F7 既有持久字段脱敏缺口

- 现有 `MaterialRevision` 明确包含 `prompt_text`、`source_url`、`source_metadata_json`、`metadata_json`，`ConnectorEndpoint` 包含 `last_pull_error`；现有自动交付 `execute_attempt()` 还允许旧 `allow_unverified_auto_draft` 在未验证时执行。F7 已要求关掉后者，但外部素材/Connector 对前五个字段的写入仍需安全投影约束，不能只依赖 Settings 页脱敏。
- 修订后的 F7 要求使用安全来源标识、请求/输入哈希和有界错误码；不把原始 prompt、签名媒体链接、请求头、远端响应或异常字串写进既有字段。成功接受媒体与失败 Connector 拉取都要做嵌套 secret 负向校验。该修订不建新表、不替代 F7 真实 Provider/Publisher 验证，也不跨过 F6D/F6E 门禁。

## 2026-09-29 F6E 六份 delta 本地保留性复核

- FE-F4 canonical 的 Delivery Authorization 将 ContentAccount 的活动状态/身份归属与平台能力区分：账号名称和自由格式 profile 不能充作已验证的远端能力；缺验证时自动动作 unavailable。F6E 主规格/design 同样允许明确标记的手工本地包，并要求远端动作精确验证。
- F6E 的 FE-F4 delta 原句“new Delivery Authorization SHALL validate current Variant and account/channel/form/action capability”未区分本地/远端，实施时可能错误地用未来 F7 远端验证阻断 `copy_package`/`manual_handoff`。现只将该句细化为：本地仍验证冻结目标与账号活动/归属/单元绑定并标为人工；远端效果额外要求精确的账号 × 渠道 × 形态 × 动作验证。该本地审计不等于独立 SPEC re-review，也不满足 F6E 0.2。

## 2026-09-29 F6E apply 前基线与旧 V1 验收保留审计

- 当前基线 `main@c295174`；tracked tree 在本次审计前 clean，仅用户原始规格包仍未跟踪。Alembic `heads` 为 `f6a000000001`。`ContentUnit.channel_id`、`ContentMasterRevision.channel_id/content_form` 可空；`ContentAsset` 有 Draft/Topic/Master source FK、channel/content_form/artifact_kind 查询列，但没有 Variant FK 或 ChannelVariant 模型。`delivery.authorize_target()` 仍会用 Master FK 判定 v4 并按 Unit 渠道限制项目目标；`project_review.decide_candidate()` 当前只分派 v3/v4。因此 F6E 的 v5 source-pointer/schema-first 校验是必要新增，不是现有功能。
- 当前代码基线新跑：从 `apps/api` 执行 pytest，1009 passed / 2 skipped / 5 warnings；`apps/web` 的 TypeScript/Vite/FE-P1 构建通过，`/projects` 224.75 kB raw / 72.89 kB gzip，通用 Production 276.96 kB raw / 88.24 kB gzip。此为 F6E 实施前对照，不证明任何 Variant/v5 功能。
- `complete-prd-v1-channel-deliverables` 的 `.openspec.yaml` 已标记 `superseded_by: align-v1-prd2-content-harness`。下表只审计其七个 Scenario 的保留落点，不重新激活旧 change，也不把映射写成通过验收：

| 原 Scenario | 保留落点 | 尚需的真实证据 |
| --- | --- | --- |
| 旧稿缺少新审批证据 | F6E `Legacy histories` / F4 Candidate 审批边界 | 历史 Douyin/XHS 草稿回读且显示未就绪 |
| 下载已批准脚本 | F6E controlled `douyin/spoken_script`、v5 Review/Package | 批准 hash 一致的脚本/分镜/B-roll/引文/estimated SRT 本地包；不标已发布 |
| 图片缺失 | F6E canonical `image_note`、素材检查 | 只有 Prompt、无合格图片字节时冻结/交付阻断 |
| 图片顺序或字节变化 | F6E ordered refs、v5 frozen manifest/Package | 改顺序或改实际字节后旧包拒绝、须新 Variant/Candidate/Approval |
| 账号独立交付 | F6E v5 DeliveryTarget；F7 远端 Publisher | 两账号授权/包/尝试/回填相互隔离，一方失败不污染另一方 |
| 权限撤销 | F6E live rights/evidence gates | 已批准历史可读，未完成目标的下载/交付被阻断 |
| 本变更完成后查看 V1 状态 | F6E 11.8 与 PRD 总验收 | 仅报告已验本地路径，15 条与 30 Topic 不自动通过 |

PRD §15 的 15 条仍是独立验收单元。下面是证据入口，不是完成判定：

| §15 | 所需证据入口 / 后续责任 |
| --- | --- |
| 1 | 文本、URL、PDF/TXT/CSV 至少三类真实导入；以 SourceDocument 与导入 API 的实际样本证明 |
| 2 | SourceDocument 抽取候选 Facts；检查来源及候选血缘 |
| 3 | Fact 人工确认、拒绝、编辑三动作；核实际状态与审计 |
| 4 | FactPack 冻结并产生不可变版本；核版本与 checksum |
| 5 | 真实 Topic 绑定 frozen FactPack；不能以 Project Fact Boundary 自动代替旧 Topic 路径 |
| 6 | 同一真实 Topic 的抖音/XHS/公众号三渠道生成；F6E 三种 Variant 本地路径不能单独证明旧 Topic 条件 |
| 7 | 生成产物记录模型/Prompt/模板版本；检查 LLMRun、Workflow/产物冻结血缘 |
| 8 | 事实性句子能映射 Fact；检查 DraftClaim 或 Master/Variant EvidenceRef 的精确定位 |
| 9 | Fact Checker 阻止无来源数字；须用含无来源数字的负向样本证明阻断 |
| 10 | Reviewer 能退回及批准；核两种独立内容决定与历史 |
| 11 | 批准内容进入 ContentAsset；核 Candidate hash 与资产读回 |
| 12 | Markdown/TXT/JSON/SRT 对应格式真实导出；逐格式检查包内容，不以 ZIP 存在代替 |
| 13 | 生成失败可重试且不覆盖旧 Draft；核 Attempt/Draft 版本 |
| 14 | FactPack 历史升版不改旧稿证据；核旧 Candidate/引用 checksum |
| 15 | 外部系统不能直连产品数据库；由 F8 生产网络/认证/部署验收证明，非本地 API 测试可替代 |

PRD §16 的发布门槛另需 **30 个真实 Topic（抖音/XHS/公众号各 10）**，并对无来源数字率、Fact 覆盖率、人工事实错误率、格式通过率、Reviewer 返工率及同 FactPack 三渠道一致性逐一统计；还需 Blocker 事实错误不可自动通过、FactPack 版本不可变、Draft 历史不丢、全流程审计可追溯及部署/恢复/备份文档。当前本地 fixture、F6E 未来的四渠道包、F5B Performance 数据和 F8 规格都不能充作这组真实发布验收。

## 2026-09-29 F6D 4.5 与 F7 真实能力边界

- F6D 设计第 5 项及 Video Studio/Review delta 已把真实 Video/TTS/ASR 输出、接受字节/许可/血缘/权利和响应脱敏列为 F7 义务；F7 标准 change 的真实能力规格、5.1–5.11、6.1–6.7 与安全结果要求可逐项承接。
- 因此 F6D 4.5 是已完成的规格移交，不是 F6D 中实现 Provider，也不是 F7 测试通过。F6D 8.4 独立实施复核仍是当前实质门禁；不能以本地全绿或移交勾选代替该外部结论。

## 2026-09-29 F6E 独立 SPEC 反馈核验

- 旧 `complete-prd-v1-channel-deliverables/.openspec.yaml` 已有 `superseded_by: align-v1-prd2-content-harness`；`openspec list` 仍按未勾任务显示 in-progress，这不是重新激活的依据。七个 Scenario 标题和 PRD §15/§16 验收义务保留，标准 F6E 不再称其 active。
- 真实 Registry 种子对首批五形态给出 `wechat/article=text`、`x/thread=text`、`x/single=text`、`xiaohongshu/image_note=image`、`douyin/spoken_script=script`。旧 fallback 的 Xiaohongshu 为 text，但不应覆盖 exact published profile；旧 `x_thread` 不成为 v5 目标。F6E 现把 v2 Master→form 与 artifact_kind 匹配写成实施闸门，v1 须显式 fork。
- `ContentAsset` 现有 Draft/Topic/Master 可空 source FK，Delivery 仍用 `content_master_revision_id is not None` 作为部分 v4 判断，项目授权还按 Unit 渠道校验；v5 若同时写 Master FK 会被误分派。修订要求 v5 仅 Variant FK，缓存 channel/form/artifact_kind 与冻结目标一致，Review/Approval/Delivery/Package 先按 manifest schema 分派。
- 现有 `LLMRun` 记录 provider/model/prompt/purpose/input hash、parsed output、raw output/error；后两者可能含敏感内容。F6E 必须验证成功运行与 exact 输入/接受输出 hash，只把安全投影写入 Variant/v5，而不是新增 receipt 表或复制原始输出。
- 当前修订只动标准 F6E OpenSpec 与项目记录；F6D 4.5 是 F7 Provider/rights/redaction 移交，8.4 独立实施复核仍未通过。F7 真 Provider 不反向阻塞 F6E，但 F6D 独立复核仍阻塞 F6E business apply。

## 2026-09-29 F6D WAV 拒绝根因

- 证据：同一有效 RIFF/WAVE 字节 `sniff_mime(bytes, "audio/wav")` 返回 `audio/wav`，`sniff_mime(bytes, None)` 返回 octet-stream；`content_masters.save_revision()` 因 `video_asset_bytes_or_mime_invalid` 返回 422。不是权限、项目可见性或文件哈希的问题。
- 修补在原有素材嗅探层识别精确 `RIFF....WAVE`；`RIFF....WEBP` 继续是 image/webp，其他 RIFF 仍 octet-stream。Video 保存、既有 live rights/byte gates 不降级。v4 ZIP 增加 `audio/wav`→`.wav`，包内字节逐 hash 验证。
- F6D 录音 WAV 已有隔离浏览器和后端端到端证据，但不能替代任务 8.4 的独立实施复核，也不能把 F7 真实 TTS/ASR/Video Provider 标为 verified。协作桥状态 green 不等于 ChatGPT 已调用连接器审阅。

## 2026-09-29 F6D 素材隔离根因与修复

- 根因是 `asset_media.MEDIA_ROOT` 写死为仓库路径，临时 `DATABASE_URL` 不会隔离内容寻址的文件字节；此前共享目录中的同 hash 文件不能安全清理，历史验收记录保留而不改写。
- 新的 `AI_STUDIO_MEDIA_ROOT` 只在显式绝对路径设置时覆盖默认值；新隔离 API 以临时 DB 的兄弟目录 `media` 启动。浏览器 fixture 先校验该环境变量，再实际回读临时目录中的 hash-addressed MP4/MP3 并核对 SHA-256；API 未使用相同根目录时验收会失败。
- 临时 Playwright 运行依赖未写入 package/lock 文件，而是复用本机已有缓存；本次不新增正式依赖。主规格同步/归档、推送/部署/生产迁移和 F6E 业务代码均未执行；F6D 独立实施复核仍待外部结论。

## 2026-09-29 F7 原包任务保留核对

- F7 源包 96 条任务与标准 `fe-f7-capability-integrations-delivery` 的 105 条任务以完整 checkbox 行逐字比较：源包没有任何缺失项，标准版新增九项。新增项覆盖 registration/runtime 精确可用性、typed Connector 映射限制、搜索接受后的项目引用、Provider 响应/错误脱敏与假成功拒绝、旧 auto-draft 绕过、执行时重新验证、WeWrite 结果脱敏和只读 Settings 不探测。此核对只覆盖任务文本，不替代独立规格审阅、代码执行或真实 Provider/Publisher 验证。

## 2026-09-29 F6E 原包保留审计

- 原始总包 `modules/03-fe-f6e-channel-variants-content-matrix/tasks.md` 的 6.2 是“X thread/single adapter where registered”。实际 seed 同时发布 `x/thread` 与 `x/single`，因此上轮标准 change 把 single 留待不确定未来适配器是错误收窄；F6E 实施/浏览器验收必须包括两种独立 X 形态。注册时不冒充可执行，完成的受控本地包也不冒充远端 Publisher verified。
- 原包 ChannelVariantRevision 推荐包含 `source_kind` 与 `edit_summary_json`；标准版先前仅泛称 request provenance，现具体补入设计、模型任务和长期契约。原包的 `regenerate` 是显式新预览/建议，不是隐式持久化；项目级 UI 任务已补明确边界。
- 原始任务总数 102、标准任务总数 96 的差额主要来自把 adapter 方法、候选清单字段与最终门禁合并成更可验收的工作项；任务数不同不等于范围可缩。后续实施仍须逐项映射原包要求，不能只凭标准任务计数宣称 North Star 完成。
- 原包分组与标准分组逐项复核：0→0、1→1、2→2、3→3、4→3/4、5→5、6→2/6、7→7、8→8、9→9、10→10、11→11。明确发现并补回的遗漏是 6.2 的 `x/single`、Variant 的 `source_kind/edit_summary`、UI 显式 regenerate 和归档就绪交接；其余原包分组在标准 change 中有对应任务与长期 Scenario。此映射仅证明规格保留，不证明任何业务代码已完成。

## 2026-09-29 F6E 规格与真实 Registry/授权差异

- `seed_v1_channel_profiles()` 已发布 `x/thread` 和 `x/single`；`x_thread/thread` 仅在 Channel Registry 的 legacy fallback 中存在，未携带 published profile。因此 F6E 原稿的“`x_thread/thread` 作为 exact published v5 目标”和“X single 尚未注册”均不符合当前代码。标准 F6E 应实现 `x/thread` 与 `x/single` 两种受控适配，旧 `x_thread` 的 v3/v4 兼容行为不变；在各自适配器完成前注册不等于可执行。
- 当前 `delivery.authorize_target()` 对项目候选检查 `unit.channel_id == payload.channel`。F6E 允许由 channel-bound Master 派生其他渠道 Variant，故 v5 必须按冻结 Variant 目标渠道/形态授权；v3/v4 原规则不变。`ContentAccountRevision.profile_json` 没有类型化渠道绑定，不能从自由文本推断平台所有权；本地包只表示人工交付，远端效果须 F7 精确账号/渠道/形态/动作验证。身份与 Unit 固定账号不可绕过。
- `ContentUnit.channel_id` 已可空、Master 保存也接受 null channel/form；F6E 的新增工作是明确 source-only neutral Master 与 v4 冻结阻断及 v5 适配链，不能把已有 nullable 字段或 Unit 创建误报为新实现。上述修正未触及业务代码或迁移，F6D 仍待实施独立复核。

## 2026-09-29 F6D 隔离浏览器验收

- 使用独立临时 SQLite、独立 API/前端端口及浏览器脚本，真实保存 Video v2 脚本、镜头、时间线、MP3 配音、字幕、叠字与同一 MP4 的不同精确位置。读取后的三条素材引用分别为 `shot_source`、`timeline_media`、`voice_audio`；修改输入立即清除旧 `render_output`，重新绑定后还须单独输入哈希确认。
- 双窗口旧版本保存返回 409 且保留本地输入；旧 Video v1 预览明确暴露不可推断的画幅/时长/时间线，人工确认后追加 v2，旧 Master hash 和脚本/镜头 ID 不变。显式画幅转换产生 `derived_video` 子修订，浏览器可读稳定版本差异，归档后保存/检查禁用。
- 已冻结 Candidate v4 在 Review 播放真实 MP4；warning 经明确说明后才能审批，交付只授权人工本地包。ZIP 内同一 revision 因不同用途存在多个 MP4 条目，逐条字节 SHA-256 均匹配；公开使用权撤销后再次下载被服务端阻断，无远端发布。Video/TTS/ASR 仍显示未验证/不可执行。
- WAV 上传可持久化为 `audio/wav`，但 Video v2 保存的字节复核无法无声明识别其魔数，因此被 `video_asset_bytes_or_mime_invalid` 正确拒绝。验收改用含 ID3 魔数的 MP3；这不是无凭据 TTS，也未放宽后端类型闸门。此限制应在真实音频接入阶段单独处理。
- 专用 ChatGPT 复核浏览器控制工具在本会话不可用，`codex-with-chatgpt` skill 明确不允许通用电脑操作替代。因此当前仅有既往独立 SPEC 审阅，F6D 实施的独立复核不能虚报为通过。
- 隔离验收只隔离 SQLite 与端口，`MaterialRevision` 上传仍写到应用共用的内容寻址 `apps/api/app/media/material/`。现有 `store_bytes` 对相同 hash 不覆盖；未删测试文件，以免误删其他本地数据库可能引用的字节。后续验收应将媒体根目录也隔离，不能把本轮称作完整文件系统隔离。

## 2026-09-29 F6D 专业检查边界

- Video v2 前端原来仍由 raw JSON textarea 驱动，并默认以 v1 schema 保存；这会让已实现的后端 v2 契约无法被普通用户可靠使用。现改为 typed Video draft 与 Video-only lazy shell，旧 v1 留在显式升级边界。编辑脚本或镜头会撤销旧 `render_asset_ref`/`render_output`，不能沿用过期成片。当前 shell 只实现脚本/镜头基础操作，不能把结构预览或未验证 Provider 称为成片；完整 Video Studio 仍在做。
- 镜头重排若只改变 payload 的 `order` 而不重排 `shot_source` 引用，后端 exact-ref 校验会拒绝保存；镜头删除也不能留下旧 `sort_order`。模型回归先发现该问题，再统一按镜头顺序重建素材引用。
- Video v2 的结构化时间线既允许空 audio/music 轨道供编辑，也禁止无精确音频版本的已放置片段。前端模型统一由 payload 构建 `shot_source → timeline_media → voice/music/cover` canonical 引用顺序，trim/volume 进入 placement；字幕 SRT 仅作为有界本地导入，不赋予 ASR provenance，也不自动保存 Master。
- 最终视频的“可播放”与“已证实属于当前 Master”是两层事实。Video UI 现在只在主动预览时读取项目可见 MP4、校验 SHA-256 并播放字节；绑定和播放不生成 attestation，必须再经当前 render-input hash 的显式人工确认及服务端闸门。
- 旧 Video v1 未核画幅/时长/时间线，升级预览返回 `payload:null` 和可证字段，因此不能像 Text/Graphic 那样直接拿 preview payload 提交。Video UI 用单独的升级草稿并锁定旧脚本和镜头身份，要求用户显式确认占位值和全部 warning；服务端仍验证完整 canonical v2、CAS 与旧数据保留。尚待隔离浏览器验证该 UI，不把接口连线等同验收。

- 真实重复下载测试发现 v4 ZIP 即使 approved Candidate/媒体完全相同，`zipfile.writestr` 默认当前时间也会让归档头变化。根因在 ZIP 条目元数据而非内容哈希；现为 v4 包固定 ZIP 时间和权限，跨两个模拟年份构建字节相同，MP4 与清单仍按 frozen hash 校验。legacy ZIP 未在本切片改变；其确定性若属长期契约应另行审计。

- F6D 的 Video/TTS/ASR 是项目级能力状态而不是“插件存在即能用”：当前无经项目验证的 Provider，故 configured/executable/verified 均 false；生成、语音合成和识别请求均 fail closed 且无素材/Master/引用写入。真实 Provider 接收与许可证据继续留给 F7，不能用 generic Material 适配器冒充。

- 派生操作不能把“已请求转换”写成成功血缘。F6D 专用路径现要求具体 canonical Video v2 用户编辑结果；长转短/画幅转换分别验证实际 duration/ratio，镜头再生成的手工路径必须绑定新 exact MaterialRevision。`derived_video` 来源与完整来源哈希/context/结果哈希只由服务端写入；无可信 Provider 时返回 typed unavailable，不产生 Master、素材或成功回执。显式本地 deterministic transform 尚未实现，因此同样不可用，不冒充成功。

- F6D 5.6–5.10 的无 Draft Video v2 后端闭环已从真实 Project/Unit/Identity/Brief/Boundary 与精确 PNG+MP4 字节运行，不只是假 manifest：撤权在 freeze/approve/authorize/package 各层被拒绝，MP4 字节损坏、候选 manifest 篡改和新 Master 后旧候选再授权也被拒绝；同一 package 两次构建字节一致，未创建 DeliveryAttempt。此结论仅限本地成品包，不代表远程发布或浏览器 Video Studio 验收。

- 原通用 Master diff 路由把 Video v2 误送到 Text diff，返回 `unsupported_text_master_schema`；专用 v2 分派现在按脚本/镜头/时间线等稳定 ID 比较，素材、渲染与上下文单独列示。Video v1 仍按旧行为保持不可跨 schema 暗中对比；Candidate Review 的冻结差异另在 5.5 验证。
- Review 的 Video v2 预览原先把结构化脚本压成 `{"structured": true}`，镜头也读取了不存在的 `duration` 字段，冻结 Candidate 的结构信息无法评审。现从已验证 manifest 的 canonical v2 内容直接投影全部关键结构，前后 Candidate 差异复用稳定 ID 比较；旧 Video v1 分支仍保持原样。
- Video v2 结构/时间线 CheckRun 原先完全缺失；现采用既有 Master append-only 检查记录。有效文档可做确定性结构与时间线验证，空草稿保持 incomplete。身份检查不能从文字推断画面或音频的品牌一致性：即使文字语义提供方返回 verified，整体仍是 warning；身份快照无有效 profile 时为 incomplete。渠道规则仅按 exact published video profile 执行，profile 变更使旧结果 stale。
- 5.3 已用隔离 API 证实：新 source ref 与新 Brief 分别进入新 Master 的 render-input hash；旧检查随 Brief head 变化 stale；source 撤权令 rights stale/冻结不可用。历史 Master 输入 hash 不随上游修改而回写，这正是 immutable 血缘要求；“失效”通过 currentness/live gate 实现，不篡改历史 hash。

## 2026-09-29 F6D 旧视频显式升级边界

- v1 只核镜头稳定 ID，不核画幅、时长、时间线或实际媒体位置。因此 preview 不自动生成 v2 payload；只返回已存脚本/镜头列表顺序和警告。专用提交必须显式供给完整 v2、精确 refs、确认当前警告；首个 child 保留脚本文本和镜头 ID/顺序，旧 render 不继承，内容调整须后续新修订。CAS/idempotency 的 request-hash 不在 edit_summary 重复持久化整份 v2 文档。
- 本轮证据覆盖旧 Master hash 不变、普通跨 schema save 拒绝、反向 schema/错误升级源拒绝、冲突与重试无额外修订。旧 Candidate hash 未单独建回归，2.7 暂不勾；独立浏览器升级路径亦未验收。最后反向 schema 断言加入后 API 全量重新运行 994 passed/2 skipped/5 warnings。

## 2026-09-29 F6D 音轨素材位置

- Video v2 原先允许 audio/music 时间线片段不声明 MaterialRevision，因而没有对应精确素材 ref 仍能保存。标准 change 现明确：空音轨合法，但已放置的音频片段必须指向精确素材；全片 voice/music 声明仍按原契约作为独立 source，不冒称 TTS/ASR 执行。字幕 cue 的顺序和不重叠既有服务端校验，补定向回归。后端全量 986 passed/2 skipped、strict 30/30、相关 Ruff/diff PASS；没有实际浏览器或成片验证。

## 2026-09-29 F6D 冻结 Candidate 读边界

- 原 `_verify_frozen_production()` 仅覆盖 Text/Graphic v2，Video v2 即使缺失最终成片 ref、输出 MIME 错误或人工 attestation 不一致，Review 仍可显示。现加入 Video v2 的冻结自洽校验，并冻结 published profile 供纯函数重算 render-input hash；输出仍只标记 `origin=manual`。Package、live rights 与浏览器端到端仍需后续单独验收，不能据此宣称 F6D 完成。
- 全量后端测试必须从 `apps/api` 运行：Alembic 配置和默认开发库路径相对当前工作目录。从仓库根运行产生 4 个环境性失败，正确目录实测 `976 passed / 2 skipped`。不得把根目录的失败归因于 Video 代码，也不能把正确目录的通过冒充浏览器/外部能力验证。

## 2026-09-29 F6D 规格复核发现

- 当前 Channel Registry 只有 `media_requirements`/`graphic_requirements`，没有 exact published Video 规则载体；Video v2 检查必须新增可选、有界 `video_requirements`，缺字段不凭空限制，畸形/未知规则不可 PASS。
- `ContentMasterAssetRef` 已有 role/slot_key/sort_order/placement_json，F6D 原草案未定义一处视频素材多次使用和最终输出的映射。标准规格现固定六种角色及稳定 slot，源引用进入 render-input hash；最终 render_output 因哈希循环单独验证。
- 当前 save_revision 仅支持 Text/Graphic 的 verified upgrade pair，并只信任 user_edit/explicit_upgrade/workflow_seed；Video 派生不能让客户端直接伪造 source_kind/edit_summary。Review 的 frozen v4 校验目前仅覆盖 Text/Graphic v2，必须扩到 Video v2 才能防篡改与 legacy fallback。

## 2026-09-29 F6C 最终独立复核

- 原 ChatGPT 对话和同项目新对话最初都在 `workspace_info` 报内部错误；本地 doctor 当时一度显示正常，但公网实际返回 HTTP 521，Cloudflare 连接日志有 TLS EOF。只重建 AIContentStudio 工作区连接后，公网 `/mcp` 返回预期 401、HTTP/2 HA=2，ChatGPT 才实际读取到 `main@2891bac`。因此本地 doctor/401 仍不能单独代替 ChatGPT 侧读取证据。
- 独立定向复核确认三项已修：F7 active spec/task 明确 Provider 响应/错误/血缘与嵌套 secret 的脱敏和负向测试；`GraphicStudioModel` 仅 Graphic 条件动态加载，bundle gate 检查通用 Production/Text/Video 静态闭包；画布和图层按钮暴露 `aria-pressed`。SPEC 与 frontend 均 APPROVE；后端前轮 APPROVE 且本轮未改后端业务代码。真实 F7 Provider 能力仍是后续工作。
- 最终门禁补充发现：F6C 范围内 Python 文件 Ruff PASS，但全库 Ruff 有 23 个既有问题，主要是非 F6C 文件的导入排序。保持范围边界，不因本阶段收尾批量改写无关代码。

## 2026-09-29 FE-F8 规格校准发现

- F8 源稿十条 Requirement 没有 WHEN/THEN，原任务 91 项；标准化需补实际验收场景与现状门禁，不等于已经达到 production readiness。现有 `deps.py` 信任可伪造的 `X-Studio-User`，缺省本地身份并自动创建 User；生产模式必须彻底拒绝这条路径，而不是仅在代理层隐藏 Header。
- `main.lifespan()` 当前会 `init_db()`、同步 Prompt/模板、加载覆盖配置、seed profiles；这些开发便利不应在生产服务启动时静默建表/改配置。F8 标准方案要求生产只读预检和显式迁移/变更流程。
- `/api/v1/health` 已存在，`check_health()` 的 DB 异常字符串可进入响应且降级仍由路由返回默认 200；`/metrics` 直接以原始 request path 作为 label，会暴露动态 ID 并扩大时序数。应原位改为可区分 liveness/readiness、安全 reason code、真实非成功状态及有界路由标签，不再造一个冲突的第二健康真源。
- MaterialRevision 是现有素材业务真源且会校验 hash，但 `MaterialRevision.file_path`、DraftMedia、项目/工作流/Review/Delivery/retention 多处直连 `MEDIA_ROOT`。已有 MinIO 服务主要用于导出，不意味着全部不可变媒体具备可替换存储。F8 存储切换必须先清点所有读写者、完成引用字节复制校验与可恢复回退；不能只改一个 `read_bytes_checked()`。
- `SystemSetting` 可能持久化明文 Secret；Settings 脱敏不等于静态存储与日志安全。生产启用前必须清点、明确迁移或禁用，并避免把值打印到审计报告。

## 2026-09-29 FE-F7 规格校准发现

- 用户 F7 源稿十条新增要求未包含 WHEN/THEN 场景，直接放进标准 OpenSpec 会缺可验收契约；标准版新增场景并保留原意，四份受影响 canonical 能力仅写 ADDED delta，不覆盖旧块。
- 现有 `content_harness.registry` 按 kind/key/version 精确解析，但 `data_source_plugins` 只允许 Studio Source，`ConnectorEndpoint` 已另有真实拉取/Fact 路径。F7 必须显式映射一个 typed plugin/endpoint，不能靠 generic Connector 配置使 Notion/API/SQL 自动可执行。映射计划先放在已规划 CapabilityRegistration 安全字段；若真实实施需要第三个长期业务对象，按总目标停下来重订规格。
- `DeliveryTarget`/`DeliveryAttempt` 已保留批准哈希与 unknown 对账，但旧 `allow_unverified_auto_draft` 可放行 `WechatWewritePublisher.verified()==False` 的执行；这和“未验证远端动作不可执行”冲突。标准 F7 将关闭新远端效果的绕过并明确为兼容性行为变更，历史记录仍可读，本地包不受影响。
- `WechatWewritePublisher` 的失败结果可能把 subprocess 尾部输出写入 error；仅 Settings 脱敏不足以保护执行路径。F7 的注册/验证、API、Material、AuditLog、ProjectEvent、Attempt/Receipt 都要安全白名单；嵌套 secret、带凭据 URL、签名 URL 和本地路径需负向验证。Provider 成功但无真实字节/明确许可也不能入 MaterialRevision 或产生 Master/Render 血缘。

## 2026-09-29 North Star 总包校准 / F6C 规格发现

- F6E 源包的新增规格没有 WHEN/THEN 场景，不能直接通过 OpenSpec strict；现已补可验收场景和五份主能力 delta。现有 `ContentUnit.channel_id`、`ContentMasterRevision.channel_id/content_form` 可空，但 `content_masters.save_revision()` 将 Master 绑定到 Unit 渠道，v4 仍按旧候选路径；必须把无渠道 Master 设为显式 source-only，而非偷改 v4。源包“选择 target”不得提前建 FE-F4 DeliveryTarget，因它需要 exact approved Candidate。active V1 change 的七场景已做保留映射，未声称已通过。
- F6D 衍生操作原草案只要求来源和转换意图，可能被实现为无实际内容变化却记录“转换成功”；现已要求具体、有效的 v2 结果，未验证 Provider 时无写入。F6C 独立复核仍受 ChatGPT 模型加载错误影响，本地连接器可读不能代替 ChatGPT 实际独立读取。
- F6D 源包原第 4 组同时要求 F6D“接受 Provider 输出为 MaterialRevision”和 F7“真实 Provider 验证”，与 F6C 已纠正的阶段边界相同。标准 F6D 草案仅定义 Video/TTS/ASR 的能力状态和未验证请求无写入；真实输出的字节/许可/血缘/响应脱敏由 F7 承接，F6D 不假造 Provider 产物。原始用户包保持不变。
- 独立 F6C 复核发现：F7 原包 1.4 只约束持久化不存 secret，9.6 只约束 Settings 脱敏，均未明确约束 Provider 执行/结果/错误/血缘响应。F6C 设计与 delta 已留下 F7 标准化必须新增的规范及负向测试，不修改用户原包。另发现通用 ContentMasterPanel 静态导入 GraphicStudioModel，虽然 Graphic Shell lazy，但模型仍进通用 Production；已改为 Graphic 条件动态导入并在 bundle gate 验证静态闭包隔离。画布按钮此前只靠颜色显示选中，现加 aria-pressed。
- 总目标与 F6C active change 审计发现一处阶段归属冲突：F6C proposal/design 明确真实 Provider 验证归 F7，F7 源包 4.3–4.8、5.3–5.9 已包含外部素材下载/字节/许可/MaterialRevision/显式接收，但 F6C tasks 5.4–5.7 和一条 Scenario 仍要求当期“实际接受 Provider 结果”。已机械校准 F6C 为只验断连 fail-closed 与项目已有精确素材，移交真实结果接受到 F7；F7 标准归位时还须补精确 Project 关联及返回脱敏的显式任务/场景，防止原要求丢失。未验证能力继续不可执行，未放宽权限。
- F6C 自动渲染能力未经过项目级验证，先前能力投影仅覆盖搜索/生图/变体。现在自动渲染也显式返回 `configured/executable/verified=false`；客户端试图把保存声明冒充 `verified_renderer` 会得到类型化 422 且无新 Master。人工声明继续由服务端记录 `origin=manual`。这只关闭未验证来源的旁路，不等于已接入真实 Renderer。
- 第二个 Graphic v2 Candidate 历史回归发现 Review 检查摘要只读取旧 `check_kind`，而 v4 冻结清单使用 `kind`，导致 UI 丢失检查名称。已兼容读取两种冻结格式；旧 Candidate 继续展示首版文字与检查输入哈希，新 Candidate 展示新正文及独立检查，结构化差异不制造文本相似度。
- 隔离浏览器发现两项只靠单元 happy path 不会显露的问题：真实上传的 `MaterialRevision.status` 是 `candidate`，旧 Graphic v2 图层保存误要求不存在的 `active`；修复后仍拒绝 revoked/archived 和未授权字节。第二项是同一 revision 既为 `graphic_layer` 又为 `render_output` 时，v4 ZIP 循环按 revision ID 多次写同名 `render-2.png`；修复为先写冻结 media，再按 adapter 给定的画布顺序单独写每个 render，并用失败回归锁住文件名唯一性、顺序和哈希。
- 隔离浏览器已证实 Brief/Boundary 新增后旧 Master 显式 stale，接纳上下文才可保存；文字层的 Unicode 选区绑定 exact FactPackItem 会使旧 render 引用失效，需重新绑定并显式人工确认输入哈希。检查中的 fact/identity 是 `warning`（模型使用受限、身份语义不可用），审批须逐条写处置；`awaiting_manual_receipt` 不是已发布。验收图片为真实上传字节及人工渲染声明，不证明图层预览与最终图片视觉同一，也不证明自动 Renderer 可执行。
- 浏览器额外核实了归档只读与 CAS：有 Master/Candidate 的隔离 Unit 经 API 移除变为 archived，Graphic 标题、加画布、保存、检查、冻结、渲染确认全部禁用；另一个单元让页面保留本地修改后通过 API 写入下一版，旧页面保存显示 409，服务端历史只有初版和外部并发版。本地编辑没有被静默覆盖或伪装成已保存。
- 本机环境的 `NO_PROXY/no_proxy` 含不合法端口片段，导致无关设置测试在 httpx URL 解析时出现 12 个失败；不改业务代码，使用 `env -u NO_PROXY -u no_proxy` 重跑同一全后端后 951 passed/2 skipped/5 warnings。F6C 定向加 F6A v4 包回归为 83 passed，前端模型 20/20，TypeScript/Vite/FE-P1、OpenSpec strict 26/26、相关 Ruff 与 diff-check 通过。
- Graphic 每画布最终图与嵌入图片是不同角色：本地图层/内容变更立即移除旧 render_output，显式绑定则只创建 canonical 顺序的精确声明/引用，不制造 attestation。用户需先保存，再对服务端返回的当前 render-input hash 确认；浏览器未完成该两步闭环，不能提前算通过。阶段画布上的前 12 个可见媒体层现在经 Header 鉴权取字节，并比对 MaterialRevision SHA256 后才用 blob 预览；仍不可被当作最终渲染。
- Graphic 文字证据与 Text 同样只从当前 Project Fact Boundary 的 FactPackItem 列表选，选区从浏览器 UTF-16 转 Unicode code-point locator。纯模型将 claim 与 EvidenceRef 同步增删；过期边界/撤权证据不允许在 UI 绑定，服务端保存时仍原子校验。真实浏览器的选择/保存/回读尚未通过，不提前勾最终验收。
- 新 Graphic UI 只读取 `GET /channels/{channel}` 返回的 published exact image form；`graphic_requirements.presets` 通过用户确认才改变当前画布尺寸，未配置/旧 text-classified form 保持不可直接冻结。几何、裁剪、样式与锁定操作先在本地模型按服务端相同范围阻断；服务端保存仍是最终真源。
- Graphic 编辑若只更新画布而保留旧 `render_asset_ref`/`render_output`，虽然服务端输入哈希会阻断假 attestation，UI 草稿仍会展示误导性“旧最终图”。现在所有内容变更从本地 draft 移除旧最终输出；同文本 no-op 保留现有 claim/evidence。画布复制保留 exact MaterialRevision 但新建 placement、清空需要人工重新确认的 claim；项目素材列表仅为选择体验，服务端继续在保存/冻结/包阶段检查 live rights。
- 旧 `/materials/generate` 会在通用生成路径直接给 `public_use_allowed=true`，并不能证明 F6C 的项目级 provider、版权/商用许可或结果核验。F6C 新 Project Graphic 能力边界因此 fail-closed 暴露 unavailable；真实 provider 接收/授权仍待 F7 验证，不将“接口可调用”包装成“生图可用”。新 Graphic UI 原先只提交未指定 schema 的 JSON，因此默认落历史 v1；现在显式提交 v2 typed draft，旧 v1 需单独升级。
- Graphic v2 不应继续走 Text Master diff：原路由会返回 `unsupported_text_master_schema`。已按目标 Master schema 分派到只读 Graphic 差异，历史 v1 可以有界比较；稳定 layer ID 跨画布移动需要去重成单个 move，不能呈现为误导性的 remove+add。Review v2 从冻结 manifest 显示文字、卡片、exact render/checks；篡改的 manifest/hash 不可继续展示。真实两画布本地包已核实字节/顺序及撤权后 fail-closed；这只证明本地交付，不证明外部平台发布。
- F6C 专业检查发现旧格式 FactPackItem.snapshot_json 可能是列表，直接按字典读取会 500；现在这种条目显式降低 semantic coverage，不能假称完整事实审查。Graphic 的文字层身份语义即使由 provider 验证，也不覆盖视觉身份，状态仍是 warning。已发布 exact image form 的版本/hash 应影响 platform check freshness，但未声明的尺寸/张数/封面规则不得臆造。
- F6C 第一批实现发现：若全局将 `default_payload_schema("graphic")` 改成 v2，既有省略 schema 的 F6A 调用会被意外重解释。已将契约明确为“新 Graphic Studio 显式发送 v2；legacy 无 schema 仍是 v1”。变体引用只要求同文档无环，不与展示顺序绑定；否则用户重排画布会无故失败。两项均用失败→通过测试固定。
- F6C render 复核发现：F6A 只按 canvas ID 集合验证覆盖，不按顺序或 render_output ref 的 slot/placement 验证。v2 adapter 已额外对 canonical 顺序、slot、placement、sort_order 做 fail-closed；v1 路径未改。全量测试的首次 12 个 `httpx.InvalidURL` 是继承的代理环境变量所致，去掉 `NO_PROXY/no_proxy` 后同一全量套件 935 passed/2 skipped。

- 总包旧基线 `main@ca52aa5`/F6B 131/162 已过时；当前本地 `main@670dd49`/F6B 162/162，源包与 ZIP 保留未跟踪。后续规划任务数必须按当前代码重新校准，不能照旧勾选。
- F6A 的 `MediaMasterAdapter` 已支持按 canvas ID 的 render-output 覆盖和手工输入哈希证明，但只比较 ID 集合，不保证 Canonical 画布顺序；F6C 必须冻结明确顺序并验证包字节排列。当前 Graphic 仍是 JSON 壳且默认 `graphic.master.v1`，普通保存禁止 v1→v2；需要独立升级路径。
- 现有 `ContentMasterAssetRef` 可用 `slot_key`/placement 表示同一 MaterialRevision 的不同 layer，目标零新表可行。`MaterialRevision` 已有 provider/version/prompt/source/rights 字段，但旧通用生图 API 的 provider 成功不可自动证明公开/商用权利；F6C 的 project-scoped hook 不能沿用假授权。
- Channel Registry 的历史小红书 `image_note` artifact_kind 为 `text`；F6C 不将其隐式改成 `image`。真正图文渠道适配留 F6E，F6C 用已发布的 exact image-classified profile 做直接 Graphic 闭环。

## 2026-09-29 FE-F6B FINAL-CLOSE 审计起点

- 23.9 收尾只纳入标准 active change、F6B 源码/回归与本次记录；用户原始规格包/ZIP 不进提交，canonical specs 不更新，active change 暂不归档。Backend 本轮新跑 913 passed/2 skipped/5 warnings；前端修复后构建/预算复跑；最终归档是下一授权边界。
- 修复后的独立前端复核 APPROVE；SPEC/backend 的先前 APPROVE 保持有效。三类独立审查完成，剩本地提交与最终记录，不能把暂存或 active change 误称为已归档。
- 独立 SPEC 与后端复核均 APPROVE。前端复核发现格式控件未暴露按选择变化的活动态；原 `role=toolbar` 又隐含未实现的方向键导航。最小修复为 `role=group` + 原生 Tab 顺序，四个格式操作增加 `aria-pressed` 与视觉活动态，并监听编辑事务更新；浏览器已验证选择→加粗状态 0→1、Tab 前进，最终前端复核仍待返回。
- 最终浏览器已补齐：Text v2 的图文/图表 exact refs、同 FactPackItem 多处 citation、解除引用、AI 本地接受、显式升级、真实 Draft seed、结构化 diff、百家号 Candidate→Approval→本地 ZIP。微信 article `cover` 缺失仍保持 blocker，不以 inline 资源绕过。ZIP 下载事件在浏览器自动化中超时，但同一隔离后端 GET 包字节已逐项核验，并不表示发布成功。
- 工作流草稿和 Text Master 同时编辑时分别显示各自 dirty；将有 Run 历史的测试 Unit 归档后重新打开，所有保存/运行/编辑控件禁用，历史 Run 仍可见。新建 Graphic/Video Unit 的 F6A JSON 壳可正常加载且没有专业 Text 编辑器。隔离 CDP 故意阻断 TextStudioShell 动态模块，错误边界给出重载入口；解除后点击重载恢复，常规标签页无 console error，故障模拟标签页预期有 import error。
- 全量后端 913 passed/2 skipped、F6A/F6B 三形态定向 130 passed、前端模型 9/9、TypeScript/Vite、FE-P1、OpenSpec strict 25/25、相关 Python Ruff、diff-check 均通过；全仓 Ruff 的 23 个问题位于本次未改文件，不写成全仓质量通过。`apps/api/alembic` 无改动。当前独立 SPEC/backend/frontend 审阅尚待结果，不可用主 Agent 自审替代。
- 微信文章 Registry 要求 `cover` 角色；Text Studio 当前“插入图片”产生 `inline` 角色，专业平台检查正确报 `missing_required_media:cover`，不可为验收绕过。Candidate→ZIP 浏览器闭环使用 Registry 中无封面必需项的百家号 article；不修改渠道规则或虚构封面。隔离浏览器操作时有外部输入混入测试目标的人工账号引用，已在可变审批说明中清除误入文本，但授权目标快照的 `account_ref` 带额外非测试字句；只影响临时 SQLite 测试夹具，不可作为精确账号映射的验收证据。
- 隔离真实浏览器与同一临时 SQLite 上，v2 Master 的结构化 document、图片/图表引用、Unicode 列表 citation 与 `ContentMasterEvidenceRef` 一次保存一致；同一个 FactPackItem 可在段落和列表分别使用而不合并 locator。解除引用/移除图表只影响新 Master 修订，系统库底层资源保留。上述结果已用 project-scoped Master detail API 逐字段回读，不仅凭页面成功提示。
- OpenSpec 剩余 31 项分布为跨层 5.6/6.1/6.3、旧版与跨模态 21.x、浏览器 22.x、最终门禁 23.x；本轮先沿现有 F6A 验收夹具补真实数据，再按可观察行为逐条确认，不把 API 单元测试冒充浏览器接受。
- 当前代码图 MCP 工具未暴露；相关代码发现仅用定向 `rg` 与明确路径读取。评审工具若不可用，将保留未完成状态而不写“独立 APPROVE”。

## 2026-09-29 FE-F6B 前端阶段性发现

- 隔离浏览器发现 TipTap 初始化/可编辑状态同步会发出与当前 runs 等价的 update，导致 Master 保存后仍假标 dirty 并禁用检查/AI；现在先规范化比较 runs，等价更新不触发 `onChange`。刷新后可见“内容已同步”，AI 和检查恢复可用。
- 双窗口并发测试确认旧 revision 保存返回 409 且不覆盖新版本；旧版 UI 原显示 `409 · [object Object]`，现改为明确提示版本/上下文变化，保留本地编辑供人工核对。独立第二窗口刷新后浏览器 console 无错误。
- 隔离夹具中项目无共享素材或冻结 Fact Boundary，且 WeChat profile 要求封面；不能把“Master 检查已运行”冒充 Candidate-ready，更不能以此勾选精确素材/证据/Review/package 的浏览器验收。
- 新 Studio Document 不可从旧 `markdown` JSON 状态隐式推断；当前 v1 Master 只能只读，必须显式 upgrade。新的 Text 保存请求已明确带 `text.master.v2`，不会修改 Graphic/Video 的 F6A 保存路径。
- Vite 在 Text-only TipTap 动态块引用共用 typed model 后，将 Production 动态入口映射为 `_PersistentProductionPage-*.js`；路由仍是真正 lazy，静态闭包无 TipTap/XYFlow。旧预算脚本只匹配源码 key 导致误报，现按唯一动态入口别名解析后继续执行原预算和重依赖门禁。
- 浏览器选择范围使用 UTF-16，服务端 citation locator 使用 Unicode code point；本地模型必须明确转换并在文本变化时重定位唯一匹配或使引用失效。图片/图表和证据引用须与区块/citation 同步更新，最终权限/权利仍以服务端为准。

## 2026-09-29 FE-F6B Backend Milestone B 审计边界

- 旧实现曾允许客户端通过普通 `edit_summary.ai_provenance` 写入伪造的“已验证”血缘；保存端必须拒绝该保留字段，只从成功且精确匹配的 LLMRun 生成 compact provenance。相同 run ID 不得在链内重复；`issued`/`subsequently_modified` 不等于明确 Accept。
- Review 原来直接展示 v2 `manifest.render.body_markdown`，即使数据库内冻结清单被改写；现在先验证 Candidate canonical hash、render 内容哈希与 ready 状态，失败保持 409，不回退到 Draft/当前 Master。
- 改写引用之前的文字会改变后续引文位置。引用与编辑区域重叠时，建议响应明确列出失效 citation 并返回删除该 locator 的本地 evidence refs；完全位于之后且文本未变时精确平移 citation 与 evidence start/end。不能把旧 EvidenceRef 自动绑定到改写后的新 claim。FactPackItem 的正文来自冻结 `snapshot_json`，不存在 `statement` ORM 属性；只有 live `model_use_allowed=true` 的条目可进入建议上下文。
- 每次 Master 追加版本都会产生新的 asset/evidence ref 数据库行 ID；diff 比较这些 ID 会错误报告内容变更。结构化 diff 排除存储行 ID，保留 exact revision/checksum/locator/排序/权利语义。
- v2→v2 Candidate 可展示 stable-ID 结构化变更；v1→v2 只给有界渲染文本比较，不把旧版缺失的结构块伪装为“新增”。本地 ZIP 已直接打开验证冻结 `content.md`，不止校验 package preview JSON。

## 2026-09-29 FE-F6B 检查层与历史包边界

- v1/Graphic/Video 保留原全局检查输入哈希；`text.master.v2` 使用按 check_kind 的冻结 requirement 元数据与哈希。精确 SEO profile 的后来变更只过期可发现性检查，不让结构等无关检查一并过期。
- v4 当前 Freeze/Approval/新授权重算当前要求；已授权历史包从冻结 manifest 的 check/report 取原要求集，同时重新校验 live rights、完整性、同输入最新结果。冻结集必须含 v2 所有必需检查，新增默认 profile 不倒灌历史。
- Fact 的确定性审查可用公开证据；只要 FactPack 中存在不可供模型使用或已撤销条目，就不把可能引用它们的正文送给语义 provider。禁用、mock、失败、截断和不合法模型输出均显式标 coverage，不能升级成 `pass`。
- Identity 检查读取 Master 固定的 IdentitySnapshot，不跟随后续 Persona 新修订；可机器执行的显式禁用词独立检查，其他语义约束在模型不可用时保持 warning，不修改身份。
- 渠道检查使用精确 Channel Registry 内容形态和规则描述；未支持的规则返回 incomplete。可发现性只用同时匹配 channel+content_form 的 published profile；旧通配 resolver 未改。旧 SEO profile 的 description/pre/post 字段当前 Text Master 无真源可执行，明确 partial warning 交由审批逐条处置，不制造假完整，也不让默认历史 profile 永久阻断 v2 Freeze。

## 2026-09-29 FE-F6B 转换/升级/seed 批次

- 升级和新 Draft seed 只调用 text_documents.convert_legacy_text；canonical 文档/hash、exact refs 相同，入口血缘仅放 edit_summary。旧 Markdown/body 保持权威，只有文字逐段精确相同的 composition 才能用来安排已声明媒体，比较不得 strip 缩进。
- 不实现第二套旧编辑器 parser；支持有限可证明的 Markdown 语法，其余保留有界字面文本并返回 warning。Setext、plus-list、嵌套/转义链接、复杂强调、实体/硬换行/容器布局等不能无警告改文。规则核对参考 [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/)，并以定向回归锁定本切片的保守转换行为，不声称全量 CommonMark parser。
- 重叠选文也算多处匹配；第二个匹配即停止并标记 unmapped，不把 Python 非重叠 finditer 当唯一性证明。Unicode U+2028/U+2029 不当成换行替换。只有 unique claim text + 已证明 FactPackItem/checksum 才转换为 citation/locator。
- 旧素材同 exact revision/hash 可合并一份声明，重复 placement/role 有显式归一警告；冲突 hash 拒绝。多个 media block 仍引用原 revision，不复制资源或字节。
- latest v1 不等于非 stale v1。上游 Brief/Identity/Boundary 已变动时首次 upgrade commit 必须拒绝，不能用刚读的 current context hash 把旧内容洗成 current；preview 可读历史，已提交 replay 优先返回既有结果。
- Generic save 的跨 schema gate 保留，reserved upgrade provenance 不能由客户端伪造；trusted upgrade 走同一 save transaction，不另造持久化模型。新 Draft seed 保留全部冻结定义/最新成功 Attempt/最新 Draft/身份及渠道验证；历史 v1 seed 的重放及 Candidate v4 冻结继续兼容。
- 有界JSON还不足以防整数解析异常：4301位列表序号在Python int转换时会报错。只转换ASCII 1–9位列表标记，其余保留字面并warning；不调整解释器安全限制。真实升级预览与纯转换回归均通过。
- 下一阶段从任务9/10开始：精确 published channel+content_form discoverability，schema/profile/provider/live model-use currentness 和真实专业 checks；A/B 未绿前不做 TipTap 前端。现有专业 handler 不可用仍 honest incomplete。

## 2026-09-29 FE-F6B apply 授权

- 用户明确授权标准校准包 apply；真实 HEAD ca52aa5，单 Agent 主写、main 直接开发仍为执行方式。
- 未提交的上轮审计文档和标准包是本任务输入，不视作可删除的 dirty tree。原始八文件/ZIP、canonical 与 migration 保持不改。
- 当前 JSON 模型可承接计划，若新增持久化结构必要必须停止修订；本轮不借 apply 自动获得 push/生产/归档授权。
- 本批确认旧调用不都带Markdown：F6A存在只发旧document的合法保存请求，必须保留v1/renderer-incomplete，不能根据“含document”就重解释成v2。无显式schema时只有Studio schema文档进入v2；新Studio会明确发v2。
- Ref校验须独立拒绝bool/float整数替身；不能只用Python字典相等。一个FactPackItem多次引用仍各存独立locator row。
- Markdown citation标记必须转义成字面量，避免与随后括号正文组成链接；实体字符、强调边界空白、inline-code换行和padding均可能让渲染正文与真源不一致。
- 同素材ID重复使用可去重字节，但必须逐block检查image/chart类别；不能让最后一个block覆盖前面的冲突。
- 现有RBAC取持久化User.role，不读取X-Studio-Role。测试必须设置真实数据库角色，不能把不存在的Header当权限契约。
- 阶段安全出口：v2四类专业检查尚未实现时显式incomplete，AI回执尚未验证时拒绝保存；不是虚构成功，也不是完整F6B验收。
- CommonMark强调符号在中文标点/不同marked runs邻接时不能可靠表达格式；投影仅在这些边界用固定服务端strong/em inline tags，所有用户文本继续转义。不增加HTML导出产物或raw-HTML输入，不用加空格改变正文。

## 2026-09-29 FE-F6B 初始审计证据

- 真实基线 main@ca52aa5；新增 text-production-studio 尚无 canonical 是预期，不是基线缺失。其余 Production Core/F4/FE-P1 canonical 已读。
- 现有 Master payload/edit_summary、asset placement、evidence locator、check report、LLMRun parsed_output 均有 JSON 容器，支持目标零新表/零迁移；不是已实现 v2。
- adapter 当前只按 modality；Review v4 Text 当前读取 content.markdown；包使用 frozen render 并验证匹配，需 schema-aware 调度，不能默默改 v1。
- 原稿 MODIFIED 三份仅新场景，缺少旧场景；标准包需保留旧要求场景。v1/Draft 的 markdown 是旧真源，转换优先级不得用过期 document 覆盖正文。
- 引用范围尚缺 Unicode 单位、列表项定位、同一 FactPackItem 多次引用、编辑后的引用失效处理；LLMRun 没有 owner FK，必须以服务端 JSON provenance 与 Project 授权验证，不可信任模型返回的 owner 信息。
- codebase-memory graph 工具本轮不可用，使用限定相关目录的 rg/定点源码读取，没有全仓扫描。
- 最终 SPEC_READY：三位只读 reviewer 均 APPROVE；校准采用签发时服务端应用补丁、保存时比较 after/final hash 或连续链的更短方案。不存整份 before，也不声称证明浏览器 Accept 点击；retention 清理后未提交 receipt 不可验证，已提交紧凑 receipt 冻结在 edit_summary。
- 现有 warning disposition 在 project_review.py Approval，不在 Freeze；discoverability.py legacy resolver 允许空 channel/form fallback，v2 必须另行 exact matching；candidates_v4.py 当前只取顶层/structured citations，v2 必须从 document.citations 映射。三个实际边界都已补设计/任务/规格。
- 保留审计：Production Core 修改4块/保留9旧场景，F4 1/3，FE-P1 2/4；三份完整 canonical 仍35要求/86场景且逐文件不变；源包八文件逐文件不变。strict25/25与新旧文档 diff-check 通过，实施0/162。

## 2026-09-29 FE-F6A 归档授权与边界

- 用户确认授权覆盖五份主规格同步、archive、strict/diff及本地main commit；原21.9等待授权条件已满足。
- 归档是规格生命周期收尾，不是新apply；只使用已验收delta，保留旧要求/场景、原始包及业务代码。
- F6B及以后仍未授权；本轮不写下一阶段方案，不push/deploy/生产迁移。
- 同步后核对全部主规格而非仅MODIFIED块：F2保留8要求/33旧场景，F3A9/45，F3B12/41，F4 11/30；所有29个delta要求块与已验收文本一致，未涉及旧要求不变。
- 归档工具生成的production-content-master Purpose TBD已补为长期契约说明；CLI按UTC日期命名后校正为本项目本地归档日期09-29，不改9份归档内容。
- active移除F6A，全量strict24/24、diff-check通过；归档与源包各9文件hash一致，业务代码不变。F6A正式状态ARCHIVED，后续仍须单独方案确认。

## 2026-09-28 FE-F6A 最终收尾边界

- 本轮用户明确禁止F6B及以后实施，未来切片必须先有具体方案；这里只关闭F6A的214项，不主动开始下一份proposal。
- final backend753通过（206项F6A）；SQLite/真实PG往返与两会话撤权约束通过，不能把本地验证叫生产验收。
- 三独立评审最终APPROVE；归档UI遗漏已用真实浏览器先复现后修复，统一project或unit readOnly，不仅依赖后端拒绝。
- 最终浏览器完整闭环13 gates且无pageerror，包含v3/Draft/debugger；AI provider明确mock、manual render明确人工确认，未启用真实Connector/Publisher。
- canonical/原始包保持不变，标准change任务21.9禁止未经单独授权同步/归档；本轮达到ARCHIVE_READY，本地main提交后停止。

## 2026-09-28 FE-F6A FINAL-CLOSE

- 独立后端复核指出Project事务锁不能覆盖system-shared撤权；gate现在以确定顺序锁Material/Revision及FactPack/Item，真实PostgreSQL第二会话撤权被锁阻断。SQLite green不能替代该证据。
- 嵌入素材/证据必须属于明确ref集合，基础设施路径不可进入payload；标题与ref字段受真实PG列bounds约束。审批warning按准确check-id/input-hash明确处置，不改写warning为pass。
- 显式content_form编辑应校验用户读到的旧form live context，再冻结新form context；不能拿新form hash拒绝正常编辑，也不能省掉Brief/Boundary漂移CAS。
- Preview先按schema分派，旧v3 graphic/video仍是冻结正文，不得套用v4 canvases/shots导致历史消失。当前检查不对stale Master执行；已授权历史包按冻结输入取最新检查，同输入新blocker仍拒绝，不同上下文stale检查不能污染历史。
- project_outputs目前按既有plugin白名单识别Draft/Material/Candidate，没有content_master_revision分支；新支持必须验证成功Attempt/冻结输出及同Unit/Run实际来源，不能因为任意节点报告ID就关联。
- 已批准设计约束三种最小开发壳而非专业编辑器；保留现有Workflow保存/Run/debugger，Master独立请求/dirty/CAS冲突状态。最终任务勾选须有具体测试或浏览器证据，不按剩余数量机械勾满。

## 2026-09-28 FE-F6A v4 live gate

- 共享校验不能简单重建manifest再比整个hash：项目展示名称可能变化，重新检查产生新ID；冻结Candidate和原审批hash不能被回写。需分别检验冻结Master/context/refs/render、冻结Check行与最新可用结果，维持不可变Candidate。
- 新Approval/Authorization要求最新Master/当前context和Candidate；已授权历史本地包按design第26段保留冻结target语义，只检查冻结来源和live rights/checks，不改绑最新Master。historical与current校验要显式区分。
- frozen_context必须从Master固定的Identity/Brief/Boundary重建并验证context_hash；历史包的check_input_hash使用这些固定引用，而不是项目最新heads。最新必需检查仍需pass，冻结check行/report也要匹配；重新检查不回写Candidate。
- 按schema分派同时以content_master_revision_id防降级：即使攻击性测试同时重算Candidate/批准hash，把v4改成v3仍不能穿过旧适配器。Publisher入口明确拒绝v4，失败不产生Attempt。
- 审批/授权flush后刷新并复核，注入提交前撤权时Review/Target/Event原子回滚；包从冻结content/render/精确素材输出，不读legacy final_body。单Agent检查清单复核，不标记独立review通过。

## 2026-09-28 FE-F6A Adapter边界

- descriptor/validator只是结构草稿；Graphic/Video现固定final_render_required，未验证具体Master输入。人工render确认须是显式API输入，由服务端绑定actor及exact输入hash，不信任edit_summary冒充确认。
- render_input_hash必须排除最终render引用，覆盖payload/context及非render素材/证据；全canvas都要有exact输出。ChannelRegistry未注册组合不能因素材存在而被推断支持。
- 初始确认只实现manual，不冒充verified renderer；媒体存在不是确认。API追加保存时服务端绑定actor及输出hash，旧Master不变；改payload/context/非render素材/evidence refs会使旧确认失效。实际MIME、字节和实时权利变化使检查stale。
- Draft引用不能只检查Fact ID：source job必须有与当前Boundary一致的FactPack ID/version/checksum，且条目唯一/typed；DraftMedia必须有精确hash、字节、项目可见性与使用权限。无法证明的引用保留unmapped并阻止检查pass，幂等重试回放已有冻结Master。
- manifest-v4取快照与纯builder分开；identity冻结真实snapshot/checksum而非readiness。提交冻结候选前再次刷新版本/context/检查及live gates，并对manifest hash复核。复核发现旧证据checksum变化后重新检查会错误pass，已补exact MasterEvidenceRef与当前边界item匹配回归。
- 现有Approval仍Draft-only、copy package仍仅project schema v3，不能把v4 Freeze通过等同完整闭环；下一阶段必须独立schema dispatch，禁止v4回退。

## 2026-09-28 FE-F6A 后端复核

- ProjectWorkflowOutput是项目共享素材的血缘，Master引用不可额外限定当前unit_id；仍需验证成功Attempt、生成插件及内容哈希，防裸ID绕过。
- Channel Registry已有resolve_content_form，应复用其真实注册能力；不能把unknown组合默认为可执行，也不能以单Agent替代事务一致性。
- 锁不能只放在Master端：复用mutable_project入口使Brief/Boundary/Unit写入共享同一Project行锁，项目归档也参与。no-op UPDATE不改updated_at；提交刷新context仍是必要的防御。SQLite真实双连接已测，不能据此宣称PostgreSQL实库竞态验收。
- 检查input hash必须包含整个边界包的live权限/快照状态，而非仅Master显式引用的item；素材状态应包含父Material归档和实际字节结果。否则撤权和文件替换后旧pass仍会被错误认作current。
- 新增可选context期望时，不携带此期望的旧请求必须保留原fingerprint算法，避免破坏已成功请求的幂等重放。

## 2026-09-28 FE-F6A 本地main阶段整合授权

- 用户明确要求将当前阶段代码合入本地main，并因当前仅一个开发Agent，后续直接在main实施；此授权覆盖必要的本地提交与整合，不包含push/deploy/生产迁移。
- main与隔离分支共同基线661e30a；main重叠审计文档、标准change和计划已逐项核对，无main独有业务改动。限定路径可恢复备份后整合，原始规格目录/ZIP保持未跟踪。
- 当前F6A仅44/214；分支整合技能在本轮只用于阶段代码整合，不执行完成声明、归档或工作树/分支删除。
- 结果：661e30a→7c2be75本地快进，main合入后574测试、build/预算、strict24/24与Ruff/diff通过；历史审计备份stash cbee2d1保留。后续直接在main开发，不自动恢复旧隔离文档覆盖主工作区。

## 2026-09-28 FE-F6A 基础实现复核与安全收紧

- 早期任务勾选与实现不一致，已撤销完整CAS/适配器/生成素材权限/完整检查/候选v4等过早完成标记；完整change仍为214项，不修改产品范围。
- downgrade必须在任何DDL前检查四类Master历史与NULL-body/Master-linked Candidate；不通过删除历史或伪造正文强行回退。四类历史和两类不兼容Candidate拒绝测试通过。
- request fingerprint应记录用户请求意图而非重试时的新上下文；否则响应丢失后Brief/渠道变化会把相同请求误判为新请求。相同请求重放保留原版本，读取投影如实显示stale。
- 检查每次显式执行追加新记录；当前投影按各kind最新记录、live输入和profile版本判定，旧pass不遮蔽新blocker。未连接renderer/缺内容不能显示render pass。
- Seed必须验证Unit/Run/Step/最新Attempt、成功状态/输出一致性与精确Draft修订；失败/过期/替换Attempt不能沿用旧历史成功。不能证明的素材/claims保持unmapped记录而不自动成为引用。
- code graph MCP未提供，代码发现仅在相关Master、Project、Review服务和既有测试范围回退搜索。

## 2026-09-28 FE-F6A 规格审计

- F6A原稿的四份MODIFIED规格为片段；标准归位必须基于post-F5C canonical完整要求块合并，不能日后归档丢掉F2/F3A/F3B/F4旧契约。
- 规格审计和业务apply授权分离；本轮不实施，外部connector可见性仍需独立证据。
- 真实本地基线661e30a，Alembic只读heads返回f5c000000001；未执行upgrade或连接生产库。
- 代码证据：ContentAsset.final_body目前NOT NULL，ArtifactKind无video；project_review.freeze仅Draft/v3，decide_candidate拒绝无Draft来源，delivery.build_copy_package只接project-v3。因此v4需从serializer→approval→authorization→package明确schema dispatch，不能只改Freeze。
- content_projects._has_execution_history只查Run/Snapshot/WorkflowOutput，手工Master无Run会落入物理删除/原地重绑；须把Master/Candidate历史纳入原闸门。
- IdentitySnapshot由显式create_snapshot固定，旧Unit不会随Persona新修订更换snapshot；原稿“层级更新自动stale”的场景已校准为层级drift提示与实际unit-pinned context stale分离。
- 原子save需规范key请求fingerprint、lost-response重试顺序和head CAS；render需input hash绑定/显式manual attestation，非“有MP4即可”；check新blocker不能被旧pass覆盖；Draft seed需检查attempt当前性。
- 保留核验实际通过：23个原稿要求标题、203条原任务保留；10个完整MODIFIED canonical块及33旧场景保留，四处旧schema/source文字仅为v4兼容明确调整。canonical及业务代码无改动。
- 独立复核指出冻结总契约仍强制Draft/Run，已仅对实际workflow来源要求该血缘，手工Master无Run按Master自身上下文/引用/检查/渲染校验；专门验收场景和任务22.11已补齐，当前214项实施任务。

## 2026-09-28 FE-F5C 归档边界

- 两份新增与三份更新delta均为长期契约；须全部同步canonical再归档，不能仅移动change。
- 旧主规格以ac6d4dc为比较基线；新增/修改块逐项与归档delta对比，未修改旧块逐字保留，不以原始包覆盖canonical。
- 复用OpenSpec CLI同步归档，业务代码、数据库和原始包不变。
- 结果：20项新增、4项更新、0项删除；24项delta逐块匹配，22项旧要求/92旧场景保留。新增Purpose与三处EOF空行已规范化，归档后全量strict23/23和diff-check通过。

## 2026-09-28 FE-F5C 本地整合核对

- main49d6c4b与F5C分支共同基线一致；重叠的README/progress/findings/task_plan、标准规格和实施计划内容完全一致，无main独有段落需要合并。
- 只保存和提交本轮白名单，原始包/ZIP不进入提交；本地main整合不包含canonical同步归档或生产操作。
- 已快进49d6c4b→7956273；合入前后547测试、build/bundle、strict22/22、Ruff/diff均通过。可恢复stash fcbbd3e保留，原始包/ZIP未纳入提交；待独立授权同步五份canonical及归档。

## 2026-09-28 FE-F5C 最终复核闭环

- 系统资源仍system_shared；Usage的私有Project/Opportunity计数、标题与链接必须授权过滤，unsupported不能补零。
- Collection成员写入绑定所读snapshot revision，不能用新版父token提交旧成员值；409显式刷新，归档保留历史而禁写。
- MaterialRevision固定ID但授权需精确回读，变化清确认；后端引用拒绝revoked/archived而保留历史。Source真实校验和是sha256。
- 安全Settings读不运行外网/目录诊断；旧危险库存admin显式打开。Provider URL只允许受限version/api-version查询，隐藏地址必须重新输入，不能保存掩码/空地址。
- 最终547测试、build/bundle、strict22/22及独立SPEC/QUALITY通过；PG DDL不等于实库并发，真实Connector/租户隔离/生产准入不在本切片范围。

## 2026-09-28：FE-F5C SPEC审计

- 源包两份新增为主规格格式，三个MODIFIED为片段；标准归位必须保留完整既有块，避免归档时丢掉F2快照stale或F3A素材/证据历史场景。
- system_shared资源可读不代表Project/Opportunity使用情况可读；usage数量和链接均按所有权过滤，不能泄露外人存在计数。
- Collection只组织Source/FactPack，created_by不是owner；归档/排序/重激活加expected_revision与条件写闸门，引用不复制、不授予Fact Boundary。
- Source权利不由trust推断；MaterialRevision与FactPackItem区分false/NULL/撤销，冻结不等于允许公开。列表用SQL有界轻量列，不先读全库再截断。
- Settings必须以safe allowlist投影，保留既有真实角色和mutation边界，不能直接透传SystemSetting/connector配置/带密钥URL/本地路径。

## 2026-09-28：FE-F5B 归档契约

- 两份新增与四份更新 delta 都是长期契约，必须全部同步 canonical，不能只移动 change。
- 更新块保留原有产品入口、项目历史、Home优先级与身份边界；Identity旧 Memory 占位场景明确限定为 pre-F5 历史行为，不再描述当前系统。
- 使用 OpenSpec 内置 archive 同步主规格；归档前保存 requirement 块用于归档后逐块比较，不触碰业务代码、原始包或数据库。

## 2026-09-28：FE-F5B 本地main整合边界

- 最终本地整合为dd71a14→9e0ce04快进；主工作区合入后只剩用户原始包/ZIP未跟踪，无业务或暂存差异。可恢复审计备份stash756ed20保留，四份文档已有审计及实施历史，不需要恢复旧版覆盖新进度。

- main和实现分支同在dd71a14，主工作区仅四份本任务文档及标准change/计划重叠，用户原始包与ZIP是无关未跟踪资料。
- 已将主工作区独有SPEC审计/发现/计划段落补入实现分支；重叠工作区改动以限定路径stash可恢复备份，不删除原始资料，不使用reset/强制切换。
- 用户本次只授权代码并入本地main，隐含必要本地commit，不授权主规格同步/归档、推送、部署或生产数据库写入。

## 2026-09-28：FE-F5B apply边界

- 四份MODIFIED delta已逐块对照canonical：Product shell保留九工作区及F3B/F4/F5A入口；Memory旧占位场景明确限于pre-F5；项目事件原有事务约束保留；Home原有七级优先级及稳定去重保留。尚未同步canonical，避免未授权归档。
- 恢复声明幂等凭据存入PublishedContentRecord永久provenance，不依赖90天AuditLog留存；观察新增用owner+active条件写锁，归档竞态拒绝。generic context识别的scalar/list引用严格正整数校验，坏输入422而不是500。
- 服务端冻结promotable_claim和Memory写闸门共用推导；旧可信accepted读时派生且标记derived，不改变原checksum。声明、范围、局限不得借任意accepted候选扩张；不同声明需匹配的新accepted候选。

- 发布回收是同一事务：项目事件未注册会使Receipt/History全部回滚，不能只用legacy无Project夹具替代项目链路验收。已增加project-bound重复回收仅一条事件回归。
- 恢复幂等不是绕过当前约束的通行证：返回历史前仍核对unknown、冻结哈希及Receipt有效性。计算上限代表结果未知，不代表指标不存在。
- 晋升表单只能使用服务端冻结可提升声明；前后端字段契约必须一起验证，否则服务端限制正确也可能使浏览器无法提交。

- 持久化采用七个独立业务资源，共用现有用户、身份、Receipt、Candidate及AuditLog，不新增第二套Home/Delivery状态。
- 现有隔离工作树已包含可复用node_modules；Python运行使用主工作区虚拟环境，但代码和测试从隔离cwd导入。只使用临时数据库，避免访问正式开发/生产数据库。
- SQLite读取DateTime会省略时区，指标窗口口径比较必须统一UTC；旧Receipt delivered_at代表人工回填发生时间，默认保留published_at未知。
- 不可证明Candidate哈希的legacy Receipt不能伪造Studio血缘，应跳过历史回收并在同步结果显式报告；已证明但不一致的哈希拒绝写入。
- 指标超过安全分析界限时不能截断再称最新值，当前返回computed=false和明确缩小范围说明；正常分析的指标Coverage与cutoff/metric/key/unit/有效观察保持一致。
- 当前Memory需防止仅检查accepted状态就支持任意改写；冻结命题、适用范围和限制必须与实际新记忆匹配，锁顺序也需跨promotion/revision一致。独立SPEC复核正在关闭这些缺口。

## 2026-09-28：FE-F5B SPEC review发现

- 标准源包两份新增规格使用主规格格式，四份MODIFIED均为替换片段；已按OpenSpec delta格式归位并保留完整旧块，Identity旧占位场景标为pre-F5历史行为。
- `routers/delivery.py:add_receipt`和`routers/article_handoff.py:add_receipt`都将`delivered_at`写为回填时`utcnow()`；不能视为真实历史发布日期。保留确认真源，仅显式已核实时间进入published_at，否则未知。
- `services/delivery.py:reconcile_attempt`只改Target/Attempt并记录AuditLog/ProjectEvent，不创建Receipt；不能凭human_confirmed Target合成已发布历史或悄改对账语义。
- 同名metric也可能有不同unit/window或重复累计读数；补snapshot/interval粒度、effective correction、cutoff和不可直接求和规则。
- 原包直接POST Memory及revision缺验证门槛，accepted证据未冻结、晋升幂等未说明数据库约束；补服务端共用gate、冻结验证快照、candidate/revision冲突409和promotion唯一来源。
- 图谱MCP工具未提供，本轮仅按已知路径定向读取相关模型、Receipt入口、Identity/Home集成，不全仓代码扫描。
- 独立复核补充：不生成receipt是正确边界，但需可执行的人工恢复入口。已定义confirm-reconciled独立发布确认，原Receipt API状态闸门与reconciliation语义保持不变；需要人工确认真实发布，而非草稿创建。

## 2026-09-28：FE-F5A 主规格同步归档检查

- 六份同步结果：新增 Opportunity 7 条、Home 4 条要求；更新 FE-F0/F1 2 条、FE-F3A 4 条、FE-F3B 2 条、FE-F4 2 条。全部21个 delta requirement blocks 与归档逐块一致，四份既有主规格37个旧 requirement blocks（含场景正文）全部保留。
- 已替换两份新增主规格的 Purpose TBD；归档工具在四份旧主规格末尾增加空行，已去除。没有业务代码、API、依赖或迁移变更，因此收尾门禁限定为规格完整性、全量 strict 与 diff-check，不重复业务测试/浏览器验收。

## 2026-09-28：FE-F5A 本地 main 整合边界

- main 与 FE-F5A 分支共同基线为 `2f52053`，无需冲突合并或获取远端提交；主工作区未跟踪内容为用户原始规格包，不加入本次提交。
- 本次授权仅覆盖本地 main 整合；六份 delta 同步与归档保留待确认，不删除仍需用于归档的隔离工作树。
- 本地快进成功：`2f52053` → 功能提交 `3012fe5`；main 上重新验证 346 后端测试、前端构建与预算、OpenSpec strict 18/18。未跟踪的原始规格包未变，未访问生产数据库或更改远端。

## 2026-09-28：FE-F5A apply 验收发现

- 独立复核后的最终修正：Brief identity_scope 不能用数字 ID join/map(Number) 读写层级对象；改为 JSON 保留 ID/层级对象，同时转换去除 null 键，兼容既有 Brand-only Brief 校验。浏览器和 API 回归通过。
- 普通 HTTP LAN 上不能假设 crypto.randomUUID 存在；使用功能探测和 getRandomValues v4 回退，幂等 key 按用户/机会/评估版本保存在 sessionStorage。实际 LAN 部署不在本次验收范围。
- 四份 MODIFIED delta 原本是片段，且 FE-F4 的 Unknown 标题与主规格不一致；已补为保留原契约与场景的完整 requirement blocks，尚未执行主规格同步或归档。

- SQLite 与 PostgreSQL 的评估/转换竞争共用机会行写锁，失败路径必须显式 rollback；否则复用 Session 时失败锁的 updated_at 可被后续 commit 写入。回归已验证。
- Opportunity 转换 scope 必须使用 typed schema，不能依赖现有 Brief 的任意数组；非法形态与字典元素返回 422，而不是 500 或生成项目。
- Home 必须先按 priority / sensitivity / expiry / recency / id 排序再 LIMIT；待决策扫描与近期项目卡片的 LIMIT 分离，避免老项目 unknown 被隐去。
- Home 回包不含 review 完整历史；近期活动来自 ProjectEvent，不以项目 updated_at 伪装排期。
- 全量 pytest 需使用隔离且已迁移 DATABASE_URL，worker.apply 使用独立 SessionLocal，不受 TestClient 内存 session override 影响；默认空数据库失败不能误判成 F5A 业务回归。

## 2026-09-28：FE-F5A-SPEC-R1 review 处理

- Review 指出的状态旁路确实存在：原规格允许普通 PATCH 直接写 `converted/archived`；现已限定为转换事务/归档路径专属状态，并拒绝非法回退。
- Assessment 原规格没有写明 `expected_revision`、409 和数据库竞争处理；现已补成 append-only 并发契约，要求失败不留下部分 revision/audit。
- Opportunity 预 Project 阶段不能使用 ProjectEvent；现采用已有 `AuditLog` 记录 Opportunity 生命周期，ProjectEvent 只从成功 conversion 开始，不新增 OpportunityEvent 表。
- 已删除单一 Opportunity `source_type` 作为真源，来源由 Signal 类型派生；转换只允许明确选择的 SourceDocument 进入普通 ProjectSourceBinding。
- Home 已固化 Today 排序、待决策优先级和稳定实体去重；核心投影失败不得伪装为空，需返回错误或 `incomplete=true` + `section_errors`。
- tasks 已改为要求 F5A 定向自动化回归，包括权限、状态旁路、并发、转换原子性/幂等/回滚、Fact Boundary 禁止、Home 优先级/去重和性能预算。

## 2026-09-28：FE-F5A Home + Opportunity 规格审计补充

- 源包包含 `proposal.md`、`design.md`、`tasks.md`、F5A 新规格，以及 FE-F0/F1、FE-F3A、FE-F3B、FE-F4 四份 delta；已放入标准 `openspec/changes/fe-f5a-home-opportunity/`。
- 不能直接用四份 delta 覆盖 canonical specs：它们是 MODIFIED 片段。归档时必须与现有完整主规格合并，否则会丢失既有项目、身份和审核契约。
- 源包的转换语义已采用：Opportunity → Project 可绑定用户明确选择的 SourceDocument；但不创建 FactPack、不冻结/绑定 Fact Boundary、不创建 IdentitySnapshot；新项目仍由 Overview 派生为 evidence-needed。
- Signal 只保存受控引用与版本/checksum/注释，不复制 SourceDocument、DataSnapshot 或 DeliveryFeedback 真源；权限在创建和转换时重新校验。
- Home 只做 Projection；没有排期实体时 `upcoming=[]`、`schedule=false`，不能从时间戳推导发布日期。
- 规格门禁：strict validation PASS；diff-check PASS。connector 基线在本地无法独立证明已从旧 main 刷新，故 apply 仍受外部 workspace reconciliation 前置约束。

## 2026-09-28：FE-F5A 规格审计

- `/home` 与 `/opportunities` 当前只是占位页；`project_overview()` 已经是可复用的确定性项目状态来源，Review/Delivery/Identity readiness 也已有项目投影，适合由 Home 聚合而不是再造状态表。
- F5A 的稳定边界是 `ContentOpportunity`（为什么现在做）、`ContentOpportunitySignal`（依据快照）和 `ContentOpportunityAssessment`（可追溯评估版本）。TopicBrief 仍是生产输入，不应接管 Opportunity。
- Opportunity 转 Project 必须显式、幂等、可回溯；建议值只能进入可编辑 Brief 草稿；只有用户明确选择的 SourceDocument signal 才能创建普通 ProjectSourceBinding，仍不能自动创建 Fact Boundary、IdentitySnapshot、Candidate 或 DeliveryTarget。
- 当前没有排期实体，因此 Home 的“近期计划”不能由更新时间伪装；规格将其收敛为近期项目活动/更新项目，等调度契约另开变更。

## 2026-09-28：FE-P1 前端加载边界审计

- 归档 CLI 使用宿主机日期 `2026-09-27` 命名，尽管当前任务日期是 2026-09-28；FE-P1 实际归档目录须以命令回执为准。五条 ADDED Requirement 已同步到新的主规格，无旧要求被替换；自动生成的 Purpose TBD 已修成正式描述。

- FE-F4 `2f3ced2` 的实际 Vite 产物只有一个 1,095.28 kB JS 文件，不能把“分成多个文件”或消除 500 kB 警告等同于首屏收益；预算应关注入口与默认路由的静态依赖闭包，并验证重型依赖不在其中。
- `App.tsx` 静态导入当前与旧页面；`Workspace` 静态引用 TipTap 编辑器，`Workflows` 静态引用 XYFlow。`PersistentProjectPages.tsx` 静态引用 `ProductionDesigner`、七个 Tab；因此仅将整个项目模块变为 lazy，不能隔离 `/projects` 与生产设计器。
- `vite.config.ts` 尚无分包配置，web package 只有 dev/build/preview，CI 当前只运行 build。首次切片优先路由级 lazy 与项目/生产边界；Tab 深拆、manualChunks、缓存策略和分页须以构建/运行数据再决定，不作为本次承诺。
- FE-P1 apply 的最新实测静态闭包为 214.45 kB raw / 69.98 kB gzip；旧 1,095.28 kB 单文件降幅 80.4%，但全站产物仍为 1,138.41 kB raw / 375.65 kB gzip。不能据此宣称所有页面更快或总 JS 更小；性能收益是按需加载边界，不是内容减少。Workspace 自身仍有 442.36 kB JS，Workflows 197.52 kB JS，仅在相应路由加载。Rollup module 归属表证实 TipTap 在 Workspace chunk、XYFlow 在 Workflows chunk，不依赖 chunk 名称猜测。
- Vite preview 不代理 `/api`，会显示 404，不能用 preview 的数字项目页证明真实操作。隔离 Vite dev + 临时 API 验证了真实项目、身份、内容单元、生产页保存项目覆盖 v1、Run succeeded 和刷新回读，随后清理唯一临时数据库；这仍不是生产环境时延或部署验收。
- Route error boundary 在加载失败时保留侧栏并支持重载；导航到另一条路由会重置错误。模拟慢网与 chunk 阻断的浏览器验收已观察到两种状态，未新增自动化测试框架。
- 独立复核指出以 `location.key` 重置错误边界会在同一路径 query 参数变化时重挂载页面，导致未保存 UI 状态丢失；根因是 React key 随每次 history entry 变化。已改用 `location.pathname`，仅实际路径变化才重置错误；需保留 query-only 导航的状态回归检查。

## 2026-09-28：FE-F4 apply 起点

- FE-F4 归档器采用宿主机日期 `2026-09-27` 生成目录，虽然当前任务日期显示 2026-09-28；README 必须引用实际路径。归档命令成功同步四份旧能力规格并新增 FE-F4 主规格（11 added / 9 modified），且自动生成的 FE-F4 Purpose 为 `TBD`，已修成正式说明。
- 独立复核把此前“项目 Draft 来源裸接口可能泄漏”的风险证实为实际旁路：`article_handoff` 的原始媒体可被其他用户读取/修改。当前已经使用 Project Run 所有权助手覆盖稿件、任务、素材、检查、文档与 Discoverability 入口；跨项目裸 ID 定向回归通过。Unknown 的普通回执与对账是两条不同路径，前者现在不能解除后者；项目历史 Candidate 也不能新建交付目标。
- FE-F4 旧裸 ID 审计发现，项目 Candidate 的大多数 Asset/Target 别名已共用所有者检查，但两个旧授权入口先返回资产状态再鉴权，可形成状态探测；现已把鉴权前置。通用 Draft/ContentJob 裸接口仍是 FE-F2 既有来源表面，需与 FE-F4 Candidate 边界分开评估，不把项目 Candidate 保密性等同于其来源 Draft 已完全隔离。
- 当前 `ProjectWorkflowOutput` 自动关联的可发布内容形态主要是 `draft`；纯媒体 `material_revision` 不构成完整可发布 Candidate。FE-F4 冻结适配器须基于持久化 Run/Output/Draft 链验证，不能把素材生成成功视为内容成品。
- FE-F3B `ContentAccount` 不包含已验证渠道、凭据或远端发布能力。自动交付必须依赖真实验证映射；没有映射时只允许明确标注能力未验证的人工包/复制交付，并拒绝远端自动动作。

## 2026-09-28：FE-F4 规格审计发现

- 后续主工作区本地 `main` 已快进至 FE-F3B `55eba02`；直接核实了四份 canonical 主规格、`ContentAccount`、`IdentitySnapshot`、身份 API 和 Alembic head `f3b000000001`。这解决了本地 apply 基线缺失；连接器端到端回读仍未单独验证。
- 初审时主工作区基线 `1fa4520` 与 FE-F3B 已归档提交 `55eba02` 分离；FE-F4 因而先在后者的隔离工作树做规格审计。该本地基线差异已由后续 `main` 快进解决。
- 来源包四份 `MODIFIED Requirements` 只有新增句子，没有主规格要求原文及既有场景。OpenSpec 归档会用 delta 替换同名 Requirement，必须把原约束和场景补全后才可标记 `SPEC_READY`。
- OpenSpec 的 delta JSON 读取只把同名 Requirement 的首段作为 `requirement.text`；把新增规范写成第二段虽然 strict 可通过，但合并后可能不成为规范正文。九个 MODIFIED 要求已将新增句子并入首段，并用 `openspec change show --json --deltas-only` 验证解析结果。
- 当前 `ContentAsset` 的 `draft_id`、`topic_brief_id`、`fact_pack_id/version`、`approved_revision` 非空，状态默认 `approved`；`Review.draft_id/revision_no` 非空。项目 Candidate 允许先冻结后批准，且 FE-F2 Unit 输出不保证有 TopicBrief/Draft；FE-F4 必须明确项目候选的真实来源与哪些旧必填列需变可空，禁止造假旧 Topic/Draft ID。
- `ContentAccount` 当前只有 Persona、名称和状态，没有渠道或平台凭据字段。新 DeliveryTarget 可以引用稳定账号 ID，但不能据此声称平台能力/渠道已验证；需界定显式账号映射与能力检查，保留 `account_ref` 历史快照。
- 独立规格审阅指出旧 `article_handoff` 手工包强依赖 Draft/v1 媒体字段；非 Draft 的 v3 Candidate 若沿用此路径会在交付时失败。已规定 v3 schema-aware 本地成品包适配器和真实字节/权利校验，v1 builder 仅处理真实 v1 资产。
- 现有 DeliveryTarget 唯一约束仅按 `account_ref`，两个不同 ContentAccount 若引用同一字符串会冲突。FE-F4 规格改为新增不可变 `authorization_account_key`：项目稳定 Account ID / 旧目标原 account_ref，替换唯一约束并统一幂等查询；不伪造旧行 ContentAccount 关联。

## 2026-09-27：FE-F3B 规格审计发现

- FE-F3B 归档 CLI 使用宿主机日期生成 `2026-09-27-fe-f3b-content-identity`，尽管任务环境日期显示 2026-09-28；文档须引用实际目录。归档自动同步四份主规格：三份 MODIFIED、一份 ADDED。FE-F2、FE-F3A、FE-F3B 主规格原有或新生的 `Purpose: TBD` 及 FE-F0/F1 已过时的 mock Purpose 均需改为当前长期契约描述。

- 来源 `fe-f3b-content-identity/` 的新能力规格采用完整主规格格式，不能原样作为 OpenSpec change delta；三份 MODIFIED 规格也只写增量、会在归档时丢失原有场景。已改成 ADDED delta 并补回被修改主要求的完整旧场景。
- `BrandVoiceVersion` 当前没有 owner_user_id；FE-F3B 只能复用现有全局 published 版本，不能声称“按 owner 验证”却没有所有权字段。历史引用不因未来归档而被重写。
- 现有 `ContentPersona` 可能无 Brand、无身份修订。迁移不回填；显式新建单位可冻结真实 Persona ID 与空 profile/null revision，并显示身份资料不完整，而不是编造品牌、定位。
- Unit 变更父级时，省略 Account/Series 不能被解释为悄然清空不兼容子级；需要明确替换/清空，否则 422。归档祖先拒绝新单位、默认工作流和 Run。
- `test_worker_task_function_executes_locally` 的模块级 `SessionLocal` 依赖默认 SQLite 文件，和测试 fixture 的内存库不同。新工作树默认文件缺表导致基线失败；独立临时文件库初始化后全套 296 通过，未改测试或业务逻辑。

## 2026-09-27：FE-F3A 规格复核发现

- 用户提供的结构化包与合并 Markdown 内容属于同一 FE-F3A 草案；标准活跃变更采用 `fe-f3a-content-project-core-completion` 作为 change 名，能力名保留 `fe-f3a-content-project-core`。原始资料未删除或覆盖。
- FE-F2 基线 `734990c` 的 `ContentProject` 已有 `status` 和所有者；`DELETE /content-projects/{id}` 在无单元时物理删除。一旦 FE-F3A 为项目写入 append-only `ProjectEvent` 和 Brief 等子记录，原行为会丢失历史或触发 FK 错误。因此提案明确改为归档项目、历史可读、项目级写操作（含 legacy run）拒绝。
- `SourceDocument`、`FactPack`、`MaterialRevision` 没有项目所有权；项目绑定只能在现有全局资源权限内引用，不应把项目拥有者视为全局资源拥有者。Source/Material 引用表的唯一键要求 detach 后 reattach 复用原记录。
- `materials_service.create_revision` 在数据库提交前写入内容哈希字节；项目上传的数据库原子性不能自动涵盖文件系统。规范须要求失败后清理或跟踪未引用字节，不可误删已共享哈希对象。
- 修订表 `(project_id, revision_no)` 唯一约束能阻止重复版本，但并发抢写若不捕获完整性错误会 500；规范要求回滚并返回 409，且事件同一数据库事务提交。
- 这轮只复核/校准 OpenSpec，不声称 FE-F3A 功能已实现；源包中要求定向回归测试为未来 apply 范围，本轮没有生成测试代码。

## 2026-09-27：FE-F3A apply 核对

- 五表在隔离库可逆迁移；带 FE-F2 项目、单元、Run 和 checksum 的 e5→f3a→e5→f3a 均能回读历史。生产迁移未执行。
- Browser 端使用独立 SQLite 验证七标签刷新、Brief 两版、Source 绑定、事实边界 Clone 后返回并冻结、素材上传和版本/活动聚合；项目上传与系统引用同一 revision 仍由唯一项目引用幂等处理，不复制字节。工作流关联可另列为独立来源。
- 现有素材存储为哈希寻址。项目上传事务失败时回滚 Material/Revision/Reference 与事件；不删除可能被其他资源共享的同哈希文件。新哈希失败写 `material.upload_orphan_candidate` AuditLog（相对路径/哈希/项目，`entity_id` 只存 50 字符前缀以兼容 PostgreSQL）。已有 `run_retention` 现消费该候选：一日宽限、每批上限、路径验证、查询已提交的 MaterialRevision/DraftMedia/AssetMedia 引用，仅删无引用字节；未处理候选不受普通 90 天 AuditLog 过期清理影响。若数据库不可写导致记录也失败，则写错误日志，不掩盖原上传失败。保留流程按现有维护入口执行，不在请求或 API 启动时自动扫盘。
- 清理计划原来指向未注册的 `retention_sweep`，已补对应 Celery task。仅做“检查引用后 unlink”仍会与复用同哈希文件的未提交写入竞态；现在写入方持有按哈希前缀划分的跨进程文件锁直至提交/回滚，清理方在引用核查和 unlink 期间持同一把锁。清理每个候选立即提交，避免持数据库写锁再等待下一把文件锁。
- 普通 Project/Unit PATCH 若允许直接设置 archived，会绕过专用归档事件及单元历史语义；已改为拒绝，要求走专用归档/删除入口。
- 非阻塞债务：前端主包约 1,058 kB，仍有 >500 kB 构建提醒；旧全局 FactPack 页面关于冻结条件的提示与当前类型化观点条目规则不完全一致，未在本切片重做该页面。
- 独立审阅还验证了三个领域缺口：归档项目的项目页面创建 Source 会先在全局 Source 库写成功、随后关联失败；旧项目 PATCH 可绕过 Brief 修订改目标；显式素材未向共享读模型传来源字段。现分别通过归档只读/创建前状态检查、目标 PATCH 拒绝、MaterialRevision provenance 回传收口。Evidence 补独立冻结条目区，Brief 历史可展开全部字段。

## 2026-09-27：FE-F2-R1 最终复核边界

- 用户提供的外部复核只覆盖 R1 五项补丁，结论为 `REVIEW_PASSED`，允许归档及本地提交；连接器未保存 pytest/build 原始 execution artifact。本轮须直接复跑门禁，不把复核文字当作命令执行证据。
- 归档同步会把 FE-F0-F1 的内容矩阵修订写入主规格，并建立 FE-F2 主规格；不使用 `--skip-specs`。归档与本地 commit 不等于 push、merge、部署或生产数据迁移。

## 2026-09-27：FE-F2-R1 复核发现与决策

- `pinned_workflow_id` 决定 Run 的实际版本；设计器以前在无项目覆盖时读最新角色默认，形成所见与执行版本错位。新增按单元固定版本读取，不自动改绑旧单元。
- 单独存在 `ProjectWorkflowBinding` 不构成不可改写的执行历史；Run、DataSnapshot、ProjectWorkflowOutput 才构成。历史身份变化通过新单元与旧单元归档保留，而不是篡改旧行；归档历史可读、项目及旧裸 Run 入口都禁止再执行。
- `resolve_placeholders()` 只应用于节点 config；角色默认模板中其余字段的项目/单元绑定必须拒绝，不能存一个运行时不解析的占位符。
- 失败重跑开始前必须持久化清空 current output/hash；旧成功结果由不可变 Attempt 保留。六类节点的 `kind` 优先写入 Step.node_type。

## 2026-09-27：FE-F2 apply 起点

- 工作流定义缺少持久 owner/scope 时，旧绑定切走会让历史定义失去归属；本轮迁移补可空 `Workflow.owner_user_id/scope`，仅新项目/角色默认版本使用，旧 Topic 定义保持兼容。
- 现有引擎将完整节点输出哈希用于 stale；DataSnapshot 每次刷新都会生成新 ID，即使内容不变。Data Node 的 stale 判断现改按 `data_checksum`，仍保留每次快照和 Attempt 审计。
- 现有素材版本实体是 `MaterialRevision`，而非名为 `AssetRevision` 的表；项目共享素材需要对这个真实版本做引用，不能凭节点返回路径或成功状态伪造素材。
- FE-F2 隔离验收中的 `/outputs` 404 来自无 reload 的旧 API 进程；新进程中同一路由 200，之前保存的 Run 可读回。Provider/Model 当前由全局模型路由选择，节点配置不可独立切换，因此设计器只暴露当前真实组合，并在保存/启动时拒绝不匹配值，避免“可选但被执行器忽略”。
- `ProjectWorkflowOutput` 对媒体版本原仅检查数据库路径/哈希字段，文件丢失仍可进入素材池；现增加字节存在与哈希匹配检查。图文/视频壳层对未生成素材和片段保持空状态。
- 全量测试默认继承本机异常 `NO_PROXY/no_proxy` 时，旧 DSH 探测链路的 12 项在 httpx URL 解析处失败（非法端口 `:1`）；仅对测试命令移除这两个环境变量后 274 项全过，未改 DSH 代码或全局环境。前端主包约 1.04 MB 是既有性能债。
- 最终 UI 复核发现“另存为角色默认”原与未保存状态绑定，导致先保存项目覆盖后无法再显式另存；现只在定义为空或请求忙时禁用，已保存项目版本也能另存，两个保存出口继续互不改绑。
- 历史 Run 画布原误用当前项目覆盖定义：项目 v2 出现新节点而 Run #1 的 checksum/step 仍属 v1。现运行模式读取 `run.definition`，设计模式读取当前项目草稿；隔离库浏览器在同一页面切换两模式已分别显示旧/新节点。

- 本轮开始时 `main@c044085` 已干净；用户同意在当前目录创建 `codex/fe-f2-persistent-production-workflow` 分支，因此不使用缺少旧本地改动的独立 worktree。
- Alembic 当前唯一 head 为 `d4audit00004`；FE-F2 迁移应从该版本增量接续，验证只用隔离本地测试库。
- 现有 `User.role` 是鉴权角色，不能代替内容 Persona；需要单独持久化内容身份归属。项目权限不能仅依赖请求中的 project_id。

## 2026-09-27：FE-F2 正式 review 的代码核对

- `apps/api/app/routers/workflows.py` 的旧 run detail、complete、retry、rerun、rerun-from-here、attempts 与 cancel 仍按裸 `run_id` 读取；`list_runs` 列出运行记录，`list_workflows` 的序列化还嵌入最近运行。只保护新 project-scoped URL 会留下读写旁路。
- 同文件的 clone/publish 使用裸 Workflow ID，raw create-run 也按 workflow ID 启动；若 FE-F2 把项目版本写入现有 Workflow 表，这些定义入口亦须授权或明确拒绝。统一检查必须以持久化项目/单元归属为准，不能相信请求携带的项目 ID。
- `workflow_engine.advance` 根据 `definition_json.edges` 判断依赖，`ready[0]` 从待执行节点取下一项；因此视觉顺序可以作为独立节点的稳定排序，但拖拽不能隐式改写 edges 或映射。
- Persona 默认模板从项目流程派生时必须服务端只保留通用结构与可共享 profile；项目、运行、快照、素材、稿件、候选、attempt 和实际输出要参数化或拒绝，不能直接复制 definition/context。
- FE-F2 回归测试现经用户明确要求；测试旧 API 权限、模板隔离、冲突、快照 stale、断连插件、副作用重跑、素材归属和历史 checksum 是该变更本身的验收，不是额外功能。

## 2026-09-27：FE-F2 V5 校准依据

- `AIContentStudio_Frontend_Product_Contract_V1_2026-09-27.md` §10–11 明确六类节点、拖拽与键盘替代、项目覆盖和显式另存角色默认版本，以及可扩展 Data Source Plugin 的六类起始来源。
- 旧 FE-F2 proposal/design 把角色默认版本推至 F3，并将首个 Data Source Plugin 描述得过于接近 Studio Source 专用适配；用户已明确要求前者在 FE-F2 真实持久化。
- 当前 `Workflow` 已有 key/version/checksum，`WorkflowRun` 可冻结版本，`WorkflowStepAttempt` 记录审计；可扩展绑定和输出关联而不新造引擎。当前模型未见持久化的内容 Persona/Role，FE-F2 需最小身份归属；鉴权角色 editor/reviewer 不能代替内容角色。
- 插件“已注册”不等于“已连接/可执行”。Notion、Obsidian、媒体数据、API、SQL 可以先有描述符和配置体验，但执行结果必须由服务端真实连接能力决定；缺连接时不得生成成功 Attempt、Snapshot 或素材。
- 用户只确认了角色默认版本这一边界；完整校准后的 FE-F2 OpenSpec 尚未被批准 apply。

## 2026-09-27：FE-F0-F1 复核补丁范围

- 反馈属实：`STATUS_EXPLANATION` 原先只在 ProductionShellPage 读出；项目默认总览和矩阵缺解释。
- 已在异常项目的总览/矩阵复用说明；非异常项目不增加图例。前端构建和浏览器观察通过，未新增测试代码。
- 本地 `main` 仍包含更早未提交的 API、迁移、Materials/ReviewPublish 路由等改动；提交必须精确暂存本切片，不能 `git add -A`。

## 2026-09-27：FE-F2 真实工作流提案核对

- `apps/api/app/models.py` 已有 Workflow、WorkflowRun、WorkflowStep、WorkflowStepAttempt；现有运行通过 `topic_id`/channel/content_form 追踪，尚无持久化 ContentProject/ContentUnit 归属。
- `apps/api/app/routers/workflows.py` 已提供版本 clone/publish、启动、人工节点完成、节点重跑、从节点重跑和 attempt 查询，但没有项目覆盖保存/设计编辑接口。
- `workflow_engine.rerun_node` 对 side-effect plugin 禁止泛化重跑，`rerun_from_here` 也检查受影响节点；FE-F2 必须沿用闸门，不能为 UI 绕过。
- FE-F0-F1 的项目模型还在 `apps/web/src/product/mockProjects.ts` 的 `localStorage`；要实现跨会话持久化，需要显式后端项目/单元迁移与 UI 切换，不能把浏览器 mock 当真实记录。
- 原变更提案把角色默认模板发布留给 F3；这一历史观察已由上面的用户确认和 V5 校准取代。

## 2026-09-27：FE-F0-F1 前端基线

- 当前 `apps/web/src/App.tsx` 以旧 Source/Topic/Workflow 导航为主，已存在用户未提交的 Materials 与 ReviewPublish 路由；实施时保留它们。
- 前端为 React Router + TanStack Query + Tailwind；已有 Button、StatusBadge、Modal、Drawer、EmptyState、Spinner、ErrorBanner 可复用；`apps/web/package.json` 仅提供 build，无独立 lint/test 脚本。
- FE-F0-F1 只做本地 mock 的 ContentProject/Unit/AssetRevision 视图与交互；FE-F2 工作流设计器和后端结构均不在本切片。
- 浏览器已核对项目列表、七标签、矩阵增删改、共享素材抽屉/筛选和选中单元生产入口；异常样本同时显示受阻、已过期、待核对，状态不合并成“失败”。
- `/review` 与 `/assets` 用作新一级工作区占位页；旧页面仍在 `/legacy/review` 与 `/legacy/assets`，其他旧路由保持不变。前端 mock 由 `localStorage` 保存；已存在的浏览器数据优先于最新初始样本，因此素材数可能与新会话初始值不同。
- `npm run build` 成功，Vite 提示主 JS 包约 1.0 MB、超过 500 kB 建议值；这是性能待办，不影响本切片构建。仓库前端没有独立 lint/test 脚本，未声称完整自动化测试通过。

## 2026-09-24：PRD 作为产品长期目标

- 用户确认 `03_ai_content_studio_PRD.md` 是指导项目开发的最终产品需求基线，并纠正“三渠道就是全部”的误解。PRD 原文称三项为“首选渠道”；原对话的 V1 目标包含 11 个文章/图文/社交平台，另保留抖音脚本。已把此范围以 §3.1 补入 PRD，避免文件本身继续遗漏完整目标。
- 当前静态核对：`models.py:Channel`、生成 renderer、工作台已有抖音/小红书/公众号；旧导出支持抖音 MD/TXT/JSON/SRT、小红书 MD/TXT/JSON。`article_handoff.py` 的新候选/交付目标只接受公众号与 X Thread；小红书 renderer 当前输出图片 Prompt，未证明有序实际图片组成品。
- PRD §15 的 15 项验收与 §16 的 30 个真实 Topic 门槛尚未在本轮完成运行核对；M1 成果不能直接等同整个 V1 达标。

- 当前工作区：`AIContentStudio`
- 连接方式：固定域名
- 连接器名称：`Codex with ChatGPT · AIContentStudio`
- 当前本地连接检查：通过
- 新账号连接状态：已授权，账号显示为 `Austin`
- 新账号项目状态：已绑定正确的 `AIContentStudio` 项目合集
- 工作区读取验证：通过

## 2026-09-22：V1 范围基线

- 指定原对话：自媒体平台对比总结（6ab23aa1-ce20-83e9-9acb-c6ffeda87191）。
- 用户最新明确需求：内容中心服务量化平台、媒体采集分析工具及其建设过程；V1 文章/图文，V2 视频。内容中心不重做上游量化与采集。
- 对话整理的 V1 渠道清单：公众号、头条、百家号、知乎、小红书、X、微博、B站专栏/图文、搜狐号、企鹅号、网易号。具体账号可用性和自动分发权限仍须核验。
- 本地 `docs/AI_CONTENT_STUDIO_REQUIREMENTS_REFINED.md` 仍以抖音、小红书、公众号三渠道为主，与最新文章全渠道目标存在差异，不可直接作为本轮实施基线。
- 页面旧架构回答和最新需求整理同时存在；以用户最后说明与三产品矩阵定位优先，不把未来架构全部塞入 V1。

### 本地源码核对（静态证据，非本轮运行验收）

- `models.py:Channel`、`routers/topics.py:VALID_CHANNELS`、`generation/renderers.py:render_body`、`pages/Topics.tsx` 均为抖音/小红书/公众号三渠道。不能仅加菜单便算全渠道完成。
- `generation/orchestrator.py:run_generation_for_job` 直接从 Topic + FactPack 各自生成平台 Draft；尚无中立母稿和平台稿之间的版本依赖。已有 TopicBrief、ContentJob、Draft、Review、ContentAsset 可复用，不宜重建一套同义实体。
- `routers/generate.py:update_draft` 新建 revision，但保留旧 `structured_json`；正文编辑后的结构、图片文案和引用可能脱节，需要定义统一内容真源及重校验机制。
- `routers/fact_packs.py:freeze_fact_pack` 只固化状态/checksum，FactPackItem 仍引用可变 Fact；`routers/facts.py:update_fact` 未检查冻结包引用；生成时读取当前 Fact。冻结事实包不等于冻结事实值，必须补不可变证据快照或等价保护。
- `routers/reviews.py:approve` 检查事实校验、包状态、最新稿件版本，复制批准正文至 ContentAsset；这是可复用的文字审批基线，尚非完整的账号/素材/规则/声明发布快照。
- `services/asset_media.py` 是图片说明占位及上传入口；上传追加数据库行却可能按原 media.id 写同一路径，不能把记录追加直接当成素材字节不可变保证。小红书最终图片组未见完整生产和打包链路。
- `workflow_templates.py:build_gen_export` 当前公众号封面节点位于批准之后；`workflow_engine.py:_h_publish_wechat` 还会截断标题、选择动态封面/占位封面，再调用 wewrite 建草稿。批准内容与最终交付内容必须先统一。
- `workflow_engine.py:advance` 保存步骤状态且可人工暂停，但自动节点在调用内串行推进；任一失败/人工等待均会返回整次运行。`retry_run` 将失败节点直接重置，因此对外建稿结果未知时存在重做风险。代码尚非持久化可靠的独立发布任务系统。
- `tasks/worker_tasks.py` 已有 Celery 生成与拉取任务，保留该技术栈；`dispatch_generation` 在外层生成请求 commit 前 `.delay()`，任务投递与数据库持久化需要可靠衔接，不能只把函数改成异步。
- `routers/external.py` 外部内容目前是独立 ExternalContent 汇聚入口，可直接人工改 published；它没有自动进入事实/母稿/审核链，不能等同候选池及可信发布回执。
- `services/writing_pipeline.py` 已有风格、润色和安全扫描薄封装，但依赖本机其他目录；缺失可降为黄词扫描。`routers/reviews.py:approve` 未统一强制安全扫描，所以不能声明已有全入口安全阻断。
- `routers/dashboard.py` 聚合生成/审核/导出内部计数，未实现平台效果与产品反馈闭环。`deps.py:get_current_user` 是开发身份头，不能用于对外商业服务验收。

### 讨论状态

- 第一轮 INIT（任务 c2c_a173）曾显示思考中，但刷新后消息未保存；不能视为实际完成讨论。恢复聊天模式后再次请求当前工作区及 README 读取，出现生成错误，单次重试仍报错。经已保存会话 → 项目列表 → 原蓝图对话重新进入，仍只保留旧对话内容。
- 本轮最后一次本地连接检查全部通过，无需重新授权/重建的指示；原聊天的新文件读取未得到成功答复，未证明端到端可用。未删除连接器、另开对话或向其他工作区发送请求。协作检查点已标记阻塞，需原会话恢复回复后继续。
- 后续恢复：用户确认能回复后，本轮在同一原对话点击发送最小读取核验，约 1 分 25 秒后返回 AIContentStudio 及 README 第 3、9–13 行两项具体事实；端到端读取验证现已通过，未重建连接器。此前报错的根因未查明。
- 第一轮 ChatGPT 完整 PLAN 已收到：认可保留现有栈与 Topic 聚合，建议首批缩为“已有满意文章 → 公众号 + 一个新增渠道 → 可核实交付”，独立目标、人工凭证和最小反馈必须提前；内容审批与目标交付授权分开记录，界面可一次确认。建议 X 线程作为新渠道样本，但尚非用户选定。
- 第一轮新增源码观察已由本地定点复核：REST 接入指纹只哈希排序后的 statement，需防日期/单位/来源版本变化被误去重；默认抽取器只提取数字及日期类候选，纯观点/建设经验需显式类型化入口；AssetMedia 强制关联批准后才创建的 ContentAsset，最终成品审批需补稿件期素材关系。
- 第二轮已提出设计挑战：不扩建通用证据平台；在现有冻结边界补值快照；保留 Markdown 主数据并失效派生物；明确非数值文章的证据门槛，以及内容审核/账号授权的分工。首批可用人工交付证明价值，自动草稿需独立准入，旧路径不得绕过新门槛。
- 第二轮完成：M1 采用类型化 FactPackItem（事实/事件、引述、作者观点）及冻结值，不把非数值文章伪造为数值事实；审核严重程度和是否完整覆盖分开。已定点复核 factchecker.py：只取前 50 条事实/前 4000 字，模型不可用或失败透传确定性结果；不能据此声称全篇语义审查完成。
- 已定点复核 assets.py：素材删除可直接移除关联记录；导出仅按渠道格式检查。后续需保护批准清单引用、区分存档下载与正式交付包，且不得把内部证据默认放进公开包。所有建议仍为规划，未修改这些源文件。
- 已在原对话文档预览中补读完整附件 `AI_Content_Center_Requirements_R2.md`。与摘要相比，还需显式保留版本比较/锁定、定时栏目数据就绪、来源公开及模型使用权限、排期首发冲突、发布后勘误、收益资格/收入状态和四类样本验收。已加入对齐草案的 A01–A64 分组追溯表，不把附件建议自动视作用户逐项确认。
- 第三轮已完成，工具输出确认方案全文读取且未截断、findings.md 全文读取；ChatGPT 判定规划 DONE，无严重修正，OpenSpec 未创建且实施 HOLD。提醒历史证据显式 legacy_untyped、可空 fact_id 的相关读取路径兼容，以及 M1 重复/中断/未知结果验收；这些是实施约束，不是现有功能结论。
- 本轮新版独立复审通过：X 单帖/线程/长帖/Articles 均保留 V1 成品适配，逐“平台 × 形态”验收；M1 仅取公众号 + X 线程作为建议样本。自动化下限和首批渠道尚待用户确认，账号分发能力未验收。
- ChatGPT 最终复核结论：规划 DONE，无严重修正。必须保留三类门槛：证据一致性、交付安全、失败/重复安全；内容审批与目标账号/动作授权分离；Markdown 是母稿真源，结构化内容、引用、检查和包均为可失效派生物。
- 用户已确认按该思路继续落地：首批接受“完整成品包 + 人工发布回填”，公众号自动进入草稿箱不作为同时完成条件。
- OpenSpec 已落地为 `openspec/changes/add-evidence-bound-article-handoff/`，严格校验通过。实现前提是新 M1 目标不调用远端平台 API，旧入口不能绕过新快照、审批和目标授权边界；历史记录保持可读，不通过迁移伪造新批准。
- 执行中新增 API：`/api/v1/article-handoff/...`，覆盖母稿导入、公众号/X Thread 适配、目标授权、本地成品包、人工回执和反馈；人工确认状态不会写成 `published` 或平台已验证。
- 迁移实测：`alembic upgrade head` 已成功到 `d31415926535`。第一次迁移尝试暴露 SQLite 不支持直接 `ALTER COLUMN`，已改为兼容增量迁移并复跑通过；仍需在 PostgreSQL 路径复核约束差异。
- 测试实测：虚拟环境 129 passed / 12 failed；失败共同原因为既有插件状态地址 `:1` 触发 `httpx.InvalidURL`，不属于本次链路。该问题未修复，避免扩大范围。

## 2026-09-22：M1 实施复核与验收

- 成品包不能只返回受登录保护的下载路径；现已提供受目标授权保护的 ZIP，包含 Markdown、HTML 或 Thread JSON、manifest、说明和按批准哈希复核的媒体字节。
- 已人工确认、失败或待核对的目标重新读取成品包时不再回退到等待回填。相同授权目标和相同回执请求在并发冲突后回读既有记录。
- 授权操作人是 M1 账号边界：非授权 editor 不能取包、下载 ZIP 或写回执。该边界不等同于未来的组织/多账号权限模型，后者须单独设计。
- 冻结快照、母稿、候选 manifest 与资产记录保留历史；公开使用权限撤销另存控制记录，并阻止未完成目标，而非篡改已批准历史。
- Alembic 迁移优先回填可从关联资产/目标恢复的 hash；无从恢复的旧记录保留为不具 M1 资格的 legacy 行，避免迁移伪造审批或丢失数据。
- 旧工作流边界已收口：`gen_export` 默认不再生成 `publish_wechat`，仅显式遗留配置才保留；执行器还要求节点带遗留开关，并继续拒绝绑定 `MotherRevision` 的 M1 资产。
- ChatGPT 对最终修复返回 `DONE`；OpenSpec 变更已归档，未同步 delta spec，因为当前仓库没有对应的主 specs 目录。
# 2026-09-27：连接器故障检查

- 用户提供四项独立调用均为 `internal error`。再次核验发现公开 MCP 返回 530、该工作区 cloudflared 的 HA 连接数为 0，虽然 `doctor` 显示绿灯且协议为 HTTP/2。
- 对 AIContentStudio 定向执行 `c2c restart --tunnel` 后，工作区 cloudflared 使用 HTTP/2，HA 连接数大于 0，公开未授权 MCP 请求返回 401；这确认传输链路现已恢复。
- ChatGPT 连接器的端到端调用尚未由当前会话复验；需要在 ChatGPT 中重试 `workspace_info`。未重建或重新授权连接器。
- 2026-09-27 后续复查：bridge、MCP、OAuth、named tunnel 均为 green；公开 MCP 返回 401、对应 cloudflared 使用 HTTP/2 且 HA 连接数大于 0。状态详情出现“no free edge addresses”警告，但不足以推翻当前健康探测，故未重启。ChatGPT 端如仍失败，需按具体工具错误继续定位。
# FE-F6A apply 基线补充（2026-09-28）

- 用户提供的ChatGPT连接器读取结果确认main@661e30a、FE-F5C两份canonical和f5c000000001迁移；本地隔离分支以相同commit为基线。
- 547测试在限定NO_PROXY后通过；未限定时12项设置相关测试因环境变量端口格式无效失败，不属于业务回归。
- Ruff基线有既存import排序告警：content_projects.py和project_review.py；不应把它们错误归因于F6A。
# 2026-09-30 F6E 同系列并发保存

- `owned_unit(..., mutate=True)` 通过 `lock_project_context` 在读 Variant head 前锁项目行；SQLite 实文件的两个独立连接会在这里串行。把同步屏障设在 head 查询处会制造测试超时，不代表业务死锁。
- 同时进入保存入口的回归证明：不同幂等键为一成功一 409；相同幂等键返回同一 revision；两种情况都只有一条 `channel_variant.saved` 事件。`ProjectEvent.entity_id` 是字符串，比较时须与 Revision ID 的字符串形式一致。
- v5 Freeze 对同一精确 Variant 的双连接并发请求只返回同一 Candidate ID，且只留一条 `candidate.frozen` 事件；数据库唯一约束与项目写锁形成最后防线，无需新增并行 Candidate 状态。
- v5 raw-ID 边界已从 Variant 一直验到包：归档项目保留历史读取，但涉及新写入或下载后推进 DeliveryTarget 状态的包入口必须拒绝；外部用户对这三层 ID 均不可探测。
- Variant 保存使用同一个数据库事务落 Revision、EvidenceRef/AssetRef 与 ProjectEvent；提交前 Evidence 撤权回归现明确断言三类写入都回滚，不留下孤立引用或事件。
