# Findings — Twelve-platform local content handoff

## 需求与实际范围

- 原范围见根PRD §3.1、docs/AI_CONTENT_STUDIO_V1_ALIGNMENT_PLAN.md渠道表：十二平台，不能用首选三渠道或F6E首批五形态替代。
- 用户2026-10-06确认本阶段先做平台稿件/素材包；公众号既有草稿箱保留，其他人工发布。该回答没有授予新的发文、正式profile写入或business apply权限。
- B站专栏/图文、知乎文章/回答、X single/thread/long_post/articles独立验收；因此十二个平台对应十七形态。抖音当前适配目标是脚本，不是视频成片；通用Video Master生产能力不被删除。

## 代码事实

- ChannelRegistry读取published ChannelTemplateVersion.profile_json并提供legacy fallback；不是缺少平台字符串枚举。
- seed_v1_channel_profiles有十四平台定义，但X仅single/thread、B站仅article；没有现代长帖/Articles/B站图文合同。seed还包含管理员/BrandVoice/Prompt等其它初始化，不能在正式库整体运行来补渠道。
- channel_adapters.FIRST_BATCH/可执行注册、channel_variant_documents与前端ChannelVariantsPanel.TARGETS当前五种形态硬编码；只更新目录会让新平台没有可执行adapter/编辑合同。
- production_packages已有v5受控本地包，但只生成generic guide/有限text/image/script投影；需要安全sources/declarations、平台HTML和形态结构文件，不能从live正文或Draft补内容。
- v5可复用append-only Variant、safe LLMRun、exact refs/checks/profile/currentness和单一source pointer；无需新增表、迁移或Candidate版本。
- 当前未暴露codebase-memory-mcp graph工具，仅对相关代码/字符串使用限定rg/read回退，不全仓扫描。

## 保留边界

既有五schema/hash、所有legacy/v1-v5历史、归档只读、project权限、live material/evidence、derived rights、safe provenance、profile CAS、Unknown不重发及公众号原文件名/字节/MIME契约不能削弱。Registry/profile≠executable adapter≠local package≠verified publisher≠published。

严格校验验证结构，不代表十七平台已实施；受控fixture不代表真实模型质量或平台发布效果。profile正式启用需单独明确授权及配套备份。
# 2026-10-08 Persona前置规格边界

当前真实适配Stage为`stage.variant.adapt@1`（stage_domain_integrations映射）；不存在`stage.variant.propose`可执行插件。计划已统一真实名称，持久参数化覆盖与集中十七形态冒烟均明确为后续义务，临时冒烟不能冒充持久覆盖；目前没有写入许可或新测试文件，不把Persona自动续行扩大成十二平台apply。

# 2026-10-14 v2 拆归轮实测（Phase 0 / SPEC_REVISED）

仓库事实：HEAD `4646ad3`；`git status --short` 73 条未提交/未追踪（含 untracked `AccountDesk.tsx`/`ChannelPluginPanel.tsx`/`channel_methods.py`/`test_channel_methods.py`/`test_minimax_video_submit.py` 与本 change v2 文件）；`git stash list` 3 条——全部保全未动。alembic head 实测 `idx000000001`（30 revisions，脚本遍历 down_revision 链计算）。`openspec` CLI 1.2.0；必须从仓库根运行（在 `apps/api` 下运行会误报 No items found）。

对 2026-10-13 AUDITED 回执的逐条核实与修正：

- `ContentSeries.account_id` NOT NULL FK（models.py:1579）、`hierarchy()` 选栏目强制账号（content_identity.py:121-122）、`delivery.py:173-174` v5 `unit.account_id` 等值 409——全部实测在位。
- 修正：`channel_adapters.FIRST_BATCH` 实有 17 个 (channel,form)，但仅 **14 个**属约定 17 形态——缺 `bilibili/image_note`、`x/long_post`、`x/articles`；多出的 `xueqiu/quant_research`、`xueqiu/market_recap`、`juejin/tech_article` 是范围外既有登记（原批已声明不计入完成义务）。审计回执"后端部分 schema/adapter 已有实现"成立，但 14/17 差异必须在批次 B 逐项补齐。
- `channel_variant_documents.canonical_payload` 无 `x.long_post.v1`/`x.articles.v1`/`bilibili.image_note.v1` 分支（落入 `unsupported_variant_schema`）；`ARTICLE_SCHEMAS` 11 项 + `SINGLE_TEXT_SCHEMAS` 2 项为现有可校验新增 schema。
- `ChannelVariantForm.tsx` `fieldsFor` 仅 5 schema 硬编码，其余显示"此正文版本暂不支持编辑"——与审计一致。
- `App.tsx` NAV 第 50 行 `/accounts` 一级导航实测在位。
- 账号多行并存能力现 schema 已支持：`(platform_channel, platform_account_id)` 唯一约束允许同平台多账号；`uq_delivery_target_authorization` 含 `authorization_account_key`（`content-account:{id}`），逐账号授权/幂等键无需迁移。v2 断点仅在栏目归属与投放绑定真源（见 ADR）。

Delta 语义落位说明（相对 v2 文稿的修正）：

- C4（fe-f3b-content-identity）与 C6（fe-f0-f1-project-experience）的 requirement 名在 canonical `openspec/specs/` 中不存在，C2 的两条新 requirement 亦然 → 均按 **ADDED** 落位（v2 文稿标注的 MODIFIED 指 capability 层级被修改，非 requirement 层级）。
- C3 的"Default manual handoff..."与既有 `Manual delivery is separate from remote draft and public publication` 语义重叠 → 仅把 `social-auto-upload` 参考场景合并进该既有 requirement，未新建重复 requirement；"Per-form real media requirements"场景并入 `Complete platform local package...` requirement。
- C5（creation-recipe-stage-control-loop）capability 尚未 canonical（由同名 active change 与 add-persona change 以 ADDED 持有）；本 change 按 ADDED 落位。**归档时三个 change 对同一 capability 的 ADD 需合并去重**，此为生命周期义务，已列入 3.1 注意项。
- 跨 change 需求名冲突排查：本 change 全部 requirement 名与 `add-persona-creative-studio`、`creation-recipe-stage-control-loop` 两个 active change 的既有 delta 无重名。

验证回执：`openspec validate --all --strict` → 38 passed / 0 failed（与拆归前基线一致，均为 canonical specs + 各 change）；`openspec validate complete-multiplatform-content-handoff --type change --strict` → valid；`git diff --check` → clean（exit 0）。无业务代码/测试/正式库改动，无模型/账号/发布调用。

# 2026-10-14 独立代码级规格复核（SPEC review 回执，回应 REVIEW_PENDING 六项）

方式：全部本地只读（rg/sed/sqlite3 mode=ro），未改业务代码；发现的规格缺口以 spec 文档修订承载（design D-v2.2 补充表、ADR §6、tasks 4.7）。逐项结论：

1. **Series scope 约束与旧查询**——发现真实缺口并已补入规格。`account_id` 可空化影响六处站点，原 design 仅覆盖 `hierarchy()`/`effective()` 两处。新增实测：`project_authorization.py:123-131` 工作流默认解析 join `ContentSeries.account_id == ContentAccount.id`（persona_editorial 栏目不可达）；`project_matrix.py:76` 以 `series.account_id != account.id` 判非法（NULL 误判）；`owned_entity`（content_identity.py:146-151）None account 即 404；series 路由仅有账号作用域（content_identities.py:277/285）；`IdentityWorkspace.tsx:87-88/135/189` 前端经 account 链反查。六处已列为批次 A（5.2/5.4/5.7）逐处义务。正式库 `content_series` 实测 0 行，本机 backfill 为空操作；legacy 分支义务不因此免除。
2. **series_account_target 唯一性与跨 Persona**——通过。`ContentAccount.persona_id` NOT NULL FK；`delivery.py:177` 已有跨 Persona fail-closed 先例；绑定唯一键 unique(series_id, account_id, content_form)；账号平台不可变（`platform_identity_immutable`）保证绑定兼容性稳定；启用校验须另过 `resolve_content_form`（delta C1 已覆盖）。
3. **v5 每目标账号授权/快照/幂等**——通过。幂等键含 `authorization_account_key`（uq 约束 + delivery.py:253/317 双回查）；同平台 A/B 账号各自独立 target/attempt/receipt 结构已就绪；409（173-174 行）是唯一需移除的锁；目标账号 revision 冻结由 5.4 承担（现 capability 快照在授权时冻结于 277 行，账号版本未冻——已在任务范围内）。
4. **SQLite 迁移与历史兼容**——通过（附执行条件）。正式库 head 实测 `idx000000001` 与报告一致；`account_id` NOT NULL 经 PRAGMA 确认；`batch_alter_table` 为本仓既有模式（f8a/f6e/f6a/g31/f7b 五处先例）；ADR fail-closed downgrade/备份策略维持；执行时须重验实况 head（ADR §6 已写入该条件）。
5. **17 形态 Descriptor 与 canonical validator**——通过（维持 14/17 事实）。FIRST_BATCH 17 键全量枚举比对：约定 17 形态交集 14，缺 bilibili/image_note、x/long_post、x/articles（全库 grep 无相关实现）；`canonical_payload` 无对应分支，落入 `unsupported_variant_schema`（channel_variant_documents.py:278-279）。xueqiu×2/juejin 为范围外既有登记，批次 B 不得删除（任务 1.2 注记已含）。
6. **Active change ADD delta 归档冲突**——通过（零需求名冲突）。本 change 六份 delta 的全部 requirement 名与 `add-persona-creative-studio`（13 项）、`creation-recipe-stage-control-loop`（12 项）delta 及 canonical（fe-f3b 12 项、fe-f0-f1 5 项、delivery-router 4 项）逐一比对无重名；冲突仅发生在 capability 层归档合并（creation-recipe-stage-control-loop 尚未 canonical），义务已在 3.1 记录。

**结论：SPEC_APPROVE（有两条规格强化修订已就地合入：design D-v2.2 站点表、ADR §6 证据）**。新 blocker 0。BUSINESS_APPLY 仍未授权——批次 A/B 与正式库迁移等待集中授权；正式迁移执行前必须按 ADR §6 重新确认实况 head 与备份。

# 2026-10-14 Batch B 开始

当前没有暴露 codebase-memory-mcp 图谱工具，按约定回退到仅任务相关文件。历史源稿 OPENSPEC_ONLY 不覆盖用户本轮 SPEC_APPROVED + BUSINESS_APPLY 授权；不得重复 propose 或创建重叠 change。

## Batch B 实际集成发现

1. 目标账号公开登记合法地没有 AccountRevision：空 profile 以账户 ID/平台公开标识和空 profile hash 冻结；后续创建修订即使版本从无到有，也导致目标上下文 stale。没有虚造修订行。
2. 新正文合同需要扩展 `_text_source_evidence_refs` 的多自然段 Unicode 偏移和列表条目全局 ID；原五映射保持。知乎问题必须显式 confirmed，来源等价检查消费同一用户问题，不从标题猜。
3. 新 B站图文的服务 checks 已有 render，但 v5 builder 原先仅按 xiaohongshu schema 要求 render，集中 smoke 揭示冻结时 missing/duplicate。现统一依据 image artifact 合同。
4. ZIP 内部 manifest 原来复制 identity/brief/production；现新导出为 `studio.channel-export.v1` 公开投影，Candidate 原 hash仍为内部记录引用，单独 export_hash 与 per-file sha256。所有新包有来源/声明/指南及形态结构，旧内部 Candidate/已交付文件未改。
5. 普通 provider 建立前失败仍 unavailable；已可能提交后异常为 unknown，记录精确 binding并阻断同 binding 再提交，不重试。没有真实 provider调用。

## Batch B 独立复核后的关键修正与决策

- 两个复核轮发现的真实遗漏全部回写持久回归：知乎确定性接受缺用户问题；Source可选署名忽略private标记；嵌套列表/概要/问题/标签未进既有规则；B站description/tags未进包；直接/Stage Unknown跨入口绕过；公开包未直接拦DeliveryTarget账号投影篡改；显式Profile schema/adapter与合同不一致。按对应最小路径修正，原五hash与历史Candidate不动。
- Stage“清空”与“继承”必须不同：config target_account_id=0明确表示本次不选目标，转换到request为None；undefined仍表示继承。没有放宽真实账号ID/platform/persona校验，也没有新建账号。
- 精确媒体字段不能新增空槽：Descriptor递归判别media_ref，操作前阻断并隐藏不可安全新增的控件；引用/真实素材/其他dirty编辑保持。不是新增素材绑定功能。
- 普通受控文本与真实媒体分开：17合同/API/页面已验，真实PNG按既有public权利复用；模型改写质量、账号资格、实际公开发布未验。正文UI编辑后恢复再保存证明canonical重开一致，不声称改写已通过语义质量。
- `_model_variant` unknown LLMRun在Stage异常外层由finalize_invocation事务提交保留（stage_invocations.py的exception→finalize→db.commit无中间rollback）；直接Unknown→Stage有持久防重试回归；Stage→直接的事务保全本轮代码级核对，未冒称独立实网对账。
- 唯一已知环境失败按原交接豁免；没有操作断链、旧workflow7–20、正式profile/库/素材/服务、其它active change或任何Git生命周期。

## 全权授权后的执行口径

前轮待授权清单已由用户明确全权授权覆盖，旧边界保留为历史。真实质量与人工评审仍按实际证据记录，未确认质量不自动勾选；正式启用保持append-only/CAS/幂等，不运行全库seed或改历史绑定。

正式启用后的版本状态：apply本身append-only并保持旧行；必要API加载触发现有normalize_template_publication，把12个旧生效版本published→archived以维持每渠道一个published。不恢复多published状态；该既有生命周期变更如实记入receipt，旧ID/profile/结构/校验hash等列精确保持，其余90张表旧行不变。此前“旧行精确”断言仅对应apply后、重启前，不混称重启后全列未变。

## 2026-10-14 任务7.3真实来源与逐账号交接发现

- 正式Master6具有真实文章、cover和三张inline图；Master10有原canvas和Material5–8四张PNG，cleared/public=true/model=false/commercial=false。正式来源先只读backup，在副本内保留全部旧row并用产品API接受到Persona2新栏目，不复制同名Account Series。
- 复杂heading/list结构超出原微信/现代文章确定性subset；manual_edit虽可save，当前variant_evidence仍要求source adapter等价，否则semantic_delta_requires_review/incomplete，不能虚作ready。已确认最短合法路径是显式追加仅排版归一的源Master revision，保留原样接受revision与原hash；原文每block字符、顺序、图片ID/字节/rights均等价。没有放宽adapter/semantic gate，原shape两个422及算法/hash在accounts-real中单独记录。
- 同一Series的微信/知乎/小红书A/B四个目标分别冻结具体AccountRevision、profile checksum和binding version，四个正常授权没有固定源账号409；尝试换号复用Candidate均准确409。小红书A/B的内容payload/图组可相同，但target context/Candidate/Review/Authorization/export/ZIP身份各自独立。
- 产品没有authorization_hash持久列，回执明确用授权安全投影的SHA-256做核验索引，不能将其叫产品存储hash。四个样本账号均bound_unverified，没有CapabilityVerification增加；本地交付成立不等于远端资格、真实发文或人类质量验收。91表482条全列历史保全仅指此链baseline副本，本工作者没有宣称并发正式库其他授权操作不发生。


## 2026-10-14 两Persona真实Series验收发现

- Product模型运行指纹复用routing进程随机continuity key。临时harness分进程运行后，known成功creative attempt无法跨进程accept，正确返回stage_adoption_context_changed。原成功tech38不改；明确获准的新Run9补一次spoken，其后在同一持续进程完成。该失败是验收脚本进程生命周期问题，不是ProviderUnknown或产品缺陷。
- 私有runtime.env具有shell语法，shlex/dotenv不是等价加载方式；错误加载使receiptJSON无效，TTSprepare在发送前credential_continuity_unverified。使用原startup的set-a/source/set+a后即可恢复，未写私有配置或重发TTS。
- architecture-diagram与明确批准的lifestyle-cards纯文字3卡可以经真实card-plan、compose、renderer和精确接受完成，geometry/structure均pass；但实际小红书Profile29 inline=required，graphic_platform只认canvas内部image/chart，因此graphic_inline_media_required阻断仍保留。真实rendereroutputs不自动等于平台检查通过。
- 本批观点与明确假想文章没有冻结事实边界；当前readiness仍evidence_missing。不得用生成内容作为独立事实证明。真实Audio QC的签名voice/rate、Provider、当前绑定与字节完整性全部通过，但没有人听/ASR/LUFS证明。
- 本轮全部10交付文件为新产物、零旧媒体复用；11次调用按2Text+2CardPlan+3Spoken+2Voice+2TTS逐项留回执。所有media权利保持本机验收限制；公开renderattestation/发布不存在。安全bundle只含成品、validatedpayload与hash/QC，不交付DB/env/rawProvider或credential。

## 最终质量委托

最新用户明确将质量评审交给Codex并允许通过后归档提交。事实边界须来自已批准设计/实际创作输入，技术意见与假想生活场景分别声明；没有正在发生的新闻，不制造fresh报道。图卡为本地排版图形输出，不因缺照片自动假造图片素材，先绑定真实成品再复核检查语义。


## 2026-10-14 最终author_opinion与渲染身份闭环

- 作者设计观点/假想brief是可核对的真实原始输入；snapshot不要求Fact，按author_opinion冻结，source_locator保留来源ID、excerpt/source hash和private/public_disclosure=false。观点摘要传播与模型使用授权不等于来源全文公开，也不等于verified现实事实。
- user_edit不允许复制trustedstage_provenance；合法补充以original_master_revision_id/hash引用历史。仅Series GraphicProfile新revision+显式rebind，产品在有历史时生成replacementUnit并归档旧Unit；旧Snap/Stage/acceptedMaster完整保存。不得靠伪造Stage证明或改Persona默认处理preset。
- 新identity/boundary改变render input hash，需要既有本地renderer在真实当前上下文重新出像；纯文字/形状输出无第三方图片。新owned输出权利依据实际input/output+本轮委托，旧private媒体/WAV权限不改。新6PNG与旧6PNG字节相同但metadata/attestation新版本独立保存。
- root修正image_note平台检查后，完整body图卡按body canvas满足inline形态，照片必需preset、source/rights/hashgate维持。实际platform/render全pass；currentchecks全部匹配输入。独立cover与旧SEO/视觉语义coverage warning依然按系统原状态记录，只由受托Codex评审接受限制，不修改系统severity。
- 本增量8语义请求均成功，不是8次生成；原11次生成+规划、最终8次检查累计19实际Provider。源正文/WAV完全复用成功原件，未新增Text/TTS生成、重发Unknown或发到外部平台。

## 最终质量与提交事实边界

ASR输出繁体，与简体脚本直接比较会误报低对齐；保留原审阅，并用macOS CoreFoundation Traditional-Simplified纯规范化生成派生指标，不改音频/脚本。科技峰值round0dBFS不意味着大量削波，原精确clipping_ratio2.9e-07应保留。不能由ASR证明主观听感；用户指定AI评审仅按实际覆盖验收。三卡整体已包含入口、机制、取舍；单张封面的可选例子不自动升级为新要求。

共享脏文件不能整文件暂存：models/nodes/delivery/channel_variants/registry选择性候选保留HEAD兼容发布逻辑，隔离相邻channel插件依赖；content_projects现有guard diff不属owner。必须验证实际staged树，而非只以工作区测试证明commit。

实际delta有七个capability（不是早期口径六份），归档新增23要求/修改2要求；所有原requirement和scenario名保全。相邻两个active change任务文件逐hash不变。归档命令42/43 warning只指生命周期自身，质量项已关闭、用户已明确直接授权归档；非验收遗漏。
