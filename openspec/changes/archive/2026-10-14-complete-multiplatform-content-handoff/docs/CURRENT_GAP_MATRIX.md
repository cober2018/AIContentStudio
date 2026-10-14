> 当前结果见 E4：Batch B已实施33/43；下方E1/E2为历史缺口，不代表当前状态。

# Current Gap Matrix — v2（2026-10-14 Phase 0 实测）

> 依据：2026-10-13 `AUDITED` 回执 + 2026-10-14 本轮实时代码核对（`main@4646ad3` 工作区）。
> 本矩阵区分 `contract-complete`（实现/测试完成）与 `quality-accepted`（真实成品人审通过）两种状态。

## E1. 子系统完成度

| 子系统 | 审计值 | 本轮实测核实 | v2 缺口/验收关键 |
|---|---|---|---|
| Persona Creative Studio | 151/156 | 任务文件实测 151/156（156 个复选框） | 余 5 项真实人工质量/听测；不能声称已经最终开箱质量通过 |
| Creation Recipe Stage Control | 141/144 | 任务文件实测 141/144 | 余 3 项持久回归/生命周期收尾；复用真实 `stage.variant.adapt@1` |
| Multiplatform Handoff（本 change） | 2/13 | 原批 2/13；v2 拆归后新增第 4/5/6/7 节任务 | 大部分 12/17 业务尚未 apply；不能把部分后端 schema 当作产品完成 |
| 17 形态 adapter catalog | 部分实现 | `FIRST_BATCH` 17 个 (channel,form) 中仅 **14 个**属约定 17 形态：缺 `bilibili/image_note`、`x/long_post`、`x/articles`；`xueqiu`×2、`juejin` 为范围外既有登记 | 任务 6.1 逐项补齐或核对；不以清单宣称代替实现 |
| 17 形态 canonical validators | 部分实现 | `ARTICLE_SCHEMAS` 11 篇章 schema + `SINGLE_TEXT_SCHEMAS` 2；无 long_post/articles/bilibili.image_note 的 canonical 分支（落入 `unsupported_variant_schema`） | 任务 1.2 |
| 17 形态前端编辑 | 部分实现 | `ChannelVariantForm.tsx` `fieldsFor` 仅硬编码 5 schema，其余显示“此正文版本暂不支持编辑” | 任务 6.2/6.3 Descriptor 驱动 |
| Account 公开标识登记 | 部分实现 | API+测试在位（`register_public_channel_account`）；UI 独立一级导航 `/accounts`（`App.tsx` NAV 第 50 行），偏离北极星九入口 | 任务 5.7 统一入口 |
| Series 跨平台归属 | 未完成 | `ContentSeries.account_id` NOT NULL；`hierarchy()` 强制栏目挂账号（实测 422 路径在位） | 任务 5.1–5.3 + ADR |
| v5 多账号授权 | 有 409 断点 | `delivery.py:173-174` 等值锁实测在位；账号多行与 `authorization_account_key` 幂等键本身已支持多账号 | 任务 5.5/5.6 |
| 第三方浏览器上传 | 参考项目已审阅 | 无浏览器自动发布运行时（`browser_automation` 仅为 capability kind 字符串） | **不在本次开发范围**；默认人工交付 |

## E2. 阻断类测试（必须有负向覆盖；对应任务 5.8/6.6）

1. 不同 Persona 的账号不得成为该栏目默认 target 或交付目标。
2. 同平台 Account A/B 不得被 `platform_channel` 字符串折叠成同一个身份。
3. v5 跨渠道、同渠道不同账号合法授权不得再因为 origin `unit.account_id` 而 409。
4. legacy fixed-account Candidate 不得因此改成可随意换号。
5. 冻结 Candidate 不得被通过改 request body/URL 换成未经审核的另一个账号。
6. Target Account 撤销/失效、rights revoked/unknown、citation 不完整或媒体缺字节均应 blocked，不可静默 fallback。
7. 已可能触发外部副作用后的异常必须是 `unknown`（按既有契约），不得自动重发。
8. 新 Persona Series 不需要 Account；旧 Account Series 原有规则、快照和外键保持可用。
9. 17 form 的可见 UI 字段都被 Executor/Validator 消费；字段未知时不会丢失；保存重开 hash 一致。
10. 导出包并不代表 Publication succeeded；微信草稿箱也不能被记录为公开发布。
11. Brand 写入 `*_creative_profile` 被拒绝，两个 Persona 共享 Brand 约束但不共享创作默认。
12. 不存在目标账号自动登录、cookie 泄露、未审批自动发布或 Agent 绕过 Delivery 的隐藏路径。

## E3. Definition of Done（状态分层）

- **SPEC_APPROVE**：设计允许开发，不等于业务完成。
- **CONTRACT_COMPLETE**：实现/测试完成，不等于默认创作质量已被人验收。
- **QUALITY_ACCEPTED**：有真实文章、图文、音频的人审与 QC 证据，不等于它们已公开发布。
- **DELIVERY_HANDED_OFF / WECHAT_DRAFT_CONFIRMED**：仅证明对应交付动作，不等于其他渠道自动发布成功。

## E4. 2026-10-14 Batch B 当前17形态完成矩阵

本段为当前代码/受控验收事实，E1–E2保留Phase0历史实测。Batch A已实施；Batch B现33/43。CONTRACT_COMPLETE不包含正式Profile启用（2.5）、真实模型质量或公开发布。source/schema目录17完整，范围外xueqiu×2/juejin继续保全。

| Requirement / 形态 | 当前代码 | 持久测试 | UI | 包 / 阻断原因 | 状态 |
|---|---|---|---|---|---|
| exact baijia/article / baijia.article.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[baijia/article]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/baijia-article.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact bilibili/article / bilibili.article.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[bilibili/article]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/bilibili-article.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact bilibili/image_note / bilibili.image_note.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[bilibili/image_note]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/bilibili-image_note.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact douyin/spoken_script / douyin.spoken_script.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[douyin/spoken_script]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/douyin-spoken_script.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact netease/article / netease.article.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[netease/article]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/netease-article.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact penguin/article / penguin.article.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[penguin/article]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/penguin-article.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact sohu/article / sohu.article.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[sohu/article]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/sohu-article.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact toutiao/article / toutiao.article.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[toutiao/article]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/toutiao-article.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact wechat/article / wechat.article.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[wechat/article]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/wechat-article.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact weibo/single / weibo.single.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[weibo/single]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/weibo-single.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact x/articles / x.articles.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[x/articles]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/x-articles.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact x/long_post / x.long_post.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[x/long_post]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/x-long_post.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact x/single / x.single.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[x/single]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/x-single.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact x/thread / x.thread.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[x/thread]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/x-thread.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact xiaohongshu/image_note / xiaohongshu.image_note.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[xiaohongshu/image_note]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/xiaohongshu-image_note.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact zhihu/answer / zhihu.answer.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[zhihu/answer]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/zhihu-answer.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |
| exact zhihu/article / zhihu.article.v1 | channel_variant_documents + channel_adapters + candidates_v5 + production_packages | test_multiplatform_contracts / pipeline[zhihu/article]，target_accounts与exports负向覆盖共享边界 | Descriptor Form +17生产/Review浏览器独立行 | [冻结ZIP与hash](BATCH_B_RECEIPTS/zhihu-article.json)，无占位素材；正式profile另待授权 | CONTRACT_COMPLETE |

共享产品路径：`ChannelVariantForm/Model`读取server Descriptor（未知字段只读+阻断）；`ChannelVariantsPanel`与`StageContractControls`读取目录/账号/问题；`CandidatePreview/ProjectReviewCenter`读取冻结正文/diff/checks并分别展示本地包和公众号草稿。共享安全路径：v5 sole FK/currentness/hash、live rights/tamper、target account、public export hash、required真实媒体和Unknown无重发。两图文复用已有真实4PNG，公众号真实封面，脚本无最终视频要求；文本为受控合同样稿。不存在以一个样本代表其它形态，完整逐形态回执位于progress。

## E5. 全权授权后的正式启用与最终验收（2026-10-14）

当前40/43，授权已充分；仅7.1/7.2真实成品人工评审与3.1全验收后生命周期未关闭。E4的17形态CONTRACT_COMPLETE与独立证据保留，不把生成/QC写成QUALITY_ACCEPTED。

| Requirement | 当前代码 / 产品路径 | 持久覆盖 / 验证 | UI / 实际产物 | 当前结果 |
|---|---|---|---|---|
| 2.5 正式Profile | multiplatform_profiles + templates/apply；同事务新增+旧published归档 | dry-run副本演练、CAS/幂等旧payload/hash、singleton回归 | profile-activation-20261014.json；版本19–30，正式17capability配置且可执行、17页面可选 | 正式启用完成；APIready/schema/FK正常 |
| 合法旧source cover | channel_variants._text_source_cover_refs | test_legacy_master_cover_maps_without_changing_source_refs；先红后绿，不同placement仍拒绝 | 原Master6不改，目标cover/inline字典精确 | 修复，target/rights/bytes校验不放宽 |
| Persona-owned Series | content_identity.hierarchy / content-personas/series | test_series_targets（含不存在Series404与无Unit回归） | accounts-real：Series1/Project3，新Unit来源身份，无账号创作 | CONTRACT_COMPLETE |
| 7.3 跨平台/同平台多账号 | target-specific Variant→v5→Review→Delivery | target_accounts与series_targets及真实clone四链；swap4次409 | accounts-real：微信3/知乎4/小红书5与6，各4图ZIP/独立export/hash/授权/Review；原文媒体向量一致 | 本地交接完成；bound_unverified非真实远端认证 |
| 7.4 legacy/历史保全 | 原Account分支、旧Snapshot/Candidate/Attempt引用 | 470旧行的两备份独立比对；非空legacy持久案例；SQLiteintegrity ok/FK0 | 原正式Series/Receipt=0，不假造非空正式历史；Profile仅12个旧状态归档 | 通过 |
| 7.5 全量机器门禁 | 当前工作区/approveda3series00000001 | 2626passed/28skipped/1已豁免断链环境fail；134聚焦；Web/FE-P1/Ruff/strict38/38/diff | backend-closeout-final.log、closeout-green-final.log、web-post-enable.log、formal-runtime-20261014.json | 通过并保留已知环境例外 |
| 正式复杂Master的确定性边界 | 服务端Adapter保守subset + Source/Target refs | 不放宽结构或精确media规则 | formal17-browser.json：17可选、3媒体/脚本preview成功，11结构/3素材阻断；显式源排版revision后账号文章链通过 | 明确边界，不混称原Master全17自动preview |
| 7.6 相邻change独立核对 | 同一真实产物索引与各自tasks | 独立code-reviewer核对，人审与Stage持久/收尾条件分别保留 | Persona151/156、Stage141/144原计数保持；未自动归档或勾选 | 核对完成；相邻事项未冒称关闭 |
| 7.1/7.2 两Persona质量 | 真实Stage→Text/Graphic/Audio明确接受 | 本轮11实际调用；Audio QC pass，Graphic geometry/structure pass；evidence_missing/inline媒体blocked，固定humanrubric/listening未通过 | [persona-real成品与hash](BATCH_B_RECEIPTS/persona-real/README.md)：2文章、6PNG、2WAV；原耐久六样本亦未冒称人听 | QUALITY_ACCEPTED尚未成立，复合任务开放 |
| 7.8/3.1 授权/生命周期 | 同一change规范与Git范围 | 用户全权授权已记录；不是再次请求权限 | 未canonical同步/归档/commit/push；3.1要求全部验收通过 | 授权条件完成，生命周期等待质量验收结果 |

安全公开发布边界沿用原产品范围：非公众号人工交付、无新自动发布driver。本轮无需额外迁移或凭据/运行配置改动；没有重启用户Vite或worker。

## E6. 最终委托验收（当前）

E1–E5均保留对应阶段历史。当前42/43，质量已验收，最后规范/Git生命周期执行中。

| Requirement | 代码/持久证据 | 真实验收 | 当前结论 |
|---|---|---|---|
| 图文平台输出卡合同 | graphic_master_checks + 13新回归，227相关通过，独立code/Python批准 | 两角色当前3卡完整render/rights/checks；原PNGhash保全 | 通过；不替代照片样式门槛 |
| 7.1科技整模态 | 同一Stage/Series/身份；Text21/Graphic18 | author_opinion设计边界，2种完整checks；真实文章/3PNG/107秒WAV，固定AIrubric | QUALITY_ACCEPTED（明确委托AI范围） |
| 7.2生活整模态 | Text22/Graphic20；明确lifestyle-cards非照片样式 | 假想brief边界；真实文章/3PNG/84秒WAV，固定AIrubric | QUALITY_ACCEPTED（明确委托AI范围） |
| 完整音频审阅 | 原签名TTS/QC + 全文offlineASR/声学 | 对齐97.93%/99.10%，LUFS与时序见quality-review | 未直接试听，不声称主观听感通过 |
| 7.5新鲜工作区验证 | backend2639通过/28跳过/1既有环境豁免；Web/FE-P1 | 原17受控UI/API/ZIP及正式17可选/3复杂来源preview保留 | 通过并记录环境/来源subset边界 |
| 实际提交候选 | 46代码路径，排除相邻插件扩展 | 368后端通过/1跳过，Web/FE-P1、8Node通过 | 提交内容已验证 |
| 相邻change | tasks hash不改 | Persona151/156、Stage141/144 | 未自动关闭/归档 |
| 3.1生命周期 | 七capability增量与原canonical比较 | 待执行同步/归档/本地commit | 最后收尾中，未push/公开发布 |

E6最终生命周期已完成：七capability23新增/2修改/0删除同步并归档本change；43/43。旧规范/相邻tasks原样保全，实际本地Git提交版本见HEAD，未push/公开发布。
