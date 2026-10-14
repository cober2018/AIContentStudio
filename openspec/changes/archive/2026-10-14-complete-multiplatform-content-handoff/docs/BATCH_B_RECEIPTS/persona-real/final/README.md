# 两 Persona 最终来源、图卡与完整检查

当前阶段：**Text/Graphic 来源、成品绑定、完整检查与用户委托的 Codex 质量评审通过；无阻断，保留准确 coverage warning。** Audio 原件和初轮技术 QC 保全，整模态声音评审由 owner 的独立委托回执承接。

## PRD / 需求背景

用户明确委托补齐事实边界、图文检查并由 Codex 评审质量。沿用已成功的两篇文章、两个三卡计划和两份 WAV，不再调用文章/TTS 生成。原始观点与假想简报不得伪装成 verified 新闻或事实。

## 代码与成果目录

产品代码版本由 owner README/index 统一记录；本工作者只修改隔离数据与此需求成果。副本位于 `/private/tmp/aics-persona-series-20261014.ane8u3as`；补边界前完整 DB 备份为 `before-final-boundary-20261014-181454.db`，SHA-256 `5331e4baae9e408a7a4cba13a209a2229c614bf246a7eb868fb7b5b3699267e6`。

- [manifest.json](manifest.json)：最终 source/boundary、身份转换、全部当前检查、语义调用、权利依据、精确 hashes 与历史关联。
- [review.md](review.md)：Codex 受托固定 rubric 与 warning 处置。
- `tech/`、`lifestyle/`：原字节 `article.md`、`audio.wav`、`audio-qc.json`，最终 `graphic-1.png` 至 `graphic-3.png`，两个 Master、两个 checks、`source-boundary.json` 和标记私有的 `source-excerpt.md`。
- [初轮入口](../README.md)及初轮 manifest/样本保持历史，未覆盖。

## 已完成

| 项目 | 科技 Persona 2 / Series 1 | 生活 Persona 3 / Series 2 |
|---|---|---|
| 真实原始来源 | 已批准 design 摘录＋原始创作 brief，Source 1 | 原始手机离身假想场景 brief，Source 2 |
| 真实类型 | 两项 `author_opinion`，FactPack 2 | 两项 `author_opinion`，FactPack 3 |
| 冻结边界 | Project 3，boundary revision 1 | Project 4，boundary revision 1 |
| 最终文章 | Unit 7 / Master 21 / Snapshot 7 | Unit 8 / Master 22 / Snapshot 8 |
| 原文保全 | 与接受 Master 11 的 payload hash 完全相同 | 与接受 Master 12 完全相同 |
| 显式图文 identity | Series Graphic Profile revision 1；新 Unit 11 / Snapshot 11 | Series revision 1；新 Unit 12 / Snapshot 12 |
| 最终图文 | layout Master 17 → 完整成品 Master 18 | layout Master 19 → 成品 Master 20 |
| 精确三卡成品 | Materials 23–25，完整 render refs＋manual attestation | Materials 26–28，同左 |
| 当前 readiness | Text/Graphic 均 current | Text/Graphic 均 current |
| 完整机器检查 | schema/evidence/rights/render/fact/identity/platform 无阻断 | 同左 |

重新绑定采用产品已有路径：含历史执行的旧 Graphic Unit 9/10 被 archive，replacement Unit 11/12 继续同一 Series；旧 snapshots、Stage 接受回执、Master 与 local-only PNG 全部保留。Persona 默认没有改变，生活默认照片封面链没有冒称通过。

新 identity/boundary 改变 render input hash，所以在当前上下文用现有本地 renderer 重渲并明确接受六张 PNG。这不调用图像生成 Provider；六张像素文件与初轮对应 PNG 的 SHA-256 完全相同。最终成品通过真实字节/尺寸/当前绑定、完整 canvas 覆盖与确认的 render input hash。

## 调用与权限

本增量只执行四个完整 checks API，各自 fact/identity 两次：**Gemini 8 次全部 succeeded，零 Unknown、零重试。** 原批 11 次＋本增量 8 次，累计 19 次真实 Provider（Chat 17 / TTS 2）。没有新 Text/TTS/外部图片生成。临时脚本两次在接受前发生本地错误，废弃预览未接受；后续六个当前 renderer 输出按 exact input/output 正常接受，不影响生成 Provider 计数。

Source 全文 metadata/locator 为 `public_disclosure_allowed=false`、`verified_external_fact=false`。冻结的作者观点/虚构边界摘要获本轮明确委托，可用于内容和模型核对；这不是原文公开许可或 verified 事实认证。

图卡只包含本机文字与形状，没有第三方 input image；依据真实 renderer input/output 和用户明确委托，创建新的成品权限版本：public=true、model=false、commercial=false。旧 local-only 图卡、未知 Provider 权利和两段 WAV 权利未改；未进行任何平台公开发布。

## 关键设计与评审结论

作者观点边界、文章正文、图卡派生与声音历史分别保留准确关联。新增 user_edit Master 只记录对旧 accepted Master/hash 的引用，不复制或伪造 trusted `stage_provenance`。文章 cover 来自同角色当前真实图卡，满足 article 合同；没有为消除 warning 插入重复正文照片。

所有 fact/identity 语义覆盖均为 verified、issues 为空，四个检查集合全部 current。Text warning 为合法独立封面的 declared_asset_unused，以及既有 legacy SEO description/pre/post 未执行；Graphic identity 仍保留 visual_semantics unavailable 提示，实际六张 PNG 已由 Codex逐张审阅。准确处置见 review，不把 warning 改写成系统 pass。

## 待完成 / TODO 与依赖

本工作者不操作主 Git、任务勾选、正式库/服务或归档；owner 统一收口。Audio 整模态质量由 owner 的独立委托评审承接，不能把本文件说成人类亲自试听。外部公开发布没有执行。

沿用既有 API venv、模型配置和本地 renderer，无新增依赖。文件可直接打开；不要复跑带真实 Provider 的临时脚本。全量 schema/integrity/foreign keys 与旧行/旧原件保全回验在 manifest。

本轮实际 skill：using-superpowers（subagent 规则）、writing-plans/同一 owner 计划、executing-plans、openspec-apply-change、systematic-debugging。
