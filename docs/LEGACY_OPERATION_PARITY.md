# 日常入口与旧操作承接清单

## 需求背景与判断原则

本轮依据已批准的北斗星及 `align-creative-orchestration-product`。新产品负责创作决策、统一版本与结果回传，不再把工作流编辑器当普通用户的创作起点。旧功能按操作承接，不以隐藏菜单代替迁移。

基线：`main@341ead8`，正式环境是本机 SQLite＋本地素材库＋loopback API/Web。F8 的既有 13 个未提交文件由 F8 拥有，本清单不覆盖它们。现有 F6E 功能任务已完成，change 仍 active；本批不做 canonical sync/archive。

分类：`move_to_new_surface` 移到新日常入口；`advanced_compatibility` 继续显式提供兼容操作；`historical_read_only` 历史读取；`obsolete_after_parity` 只有承接验收与产品复核均完成才可退出日常入口。

2026-10-05当前状态：53/53操作清单承接及三类核心独立复核已通过；原147项实施通过，新增R1/R2收尾另行跟踪。仅移除日常 `LEGACY_NAV` 侧栏，九个主入口统一使用；Settings十五个兼容入口、全部旧URL和实体深链接仍在，没有删除操作/页面或隐式迁移旧记录。正式SQLite已另行获准升级为aco000000001，API/Web/原Worker/MCP保持启用；f8a身份祖先列全空/inert，不启用JWT。原历史行/素材hash保全；当前归档待R1/R2与最终closeout复核，完整证据见 `ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md` 和 `ALIGN_CREATIVE_LOCAL_ENABLEMENT.md`。

## 路由盘点

| 现有地址 | 本轮目标 | 历史与兼容承诺 |
| --- | --- | --- |
| `/`、`/home` | `/` 进入今日工作台 | 旧 Landing 另在 `/legacy/landing`，`/dashboard` 仍保留 |
| `/production` | 创作与执行投影：项目/单元＋原生生成任务 | 只读不 dispatch；外部执行尚未接入时明确说明 |
| `/projects`、`/projects/:id` | 项目业务根；矩阵、渠道变体、执行以及既有项目页 | 原 Brief/Evidence/Assets/Versions/Activity 及 `tab=matrix` 不变 |
| `/projects/:id/units/:unit/production` | Master 创作＋精确单元的渠道变体入口 | Workflow、历史 Master、归档只读保留 |
| `/opportunities`、`/opportunities/:id` | 显式转换为 Project | 建议不是事实边界，转换不自动批准 |
| `/review`、`/identities`、`/learning` | 既有真实工作区 | 本批不改审批/身份/学习业务规则 |
| `/assets` | Source/Fact/FactPack/Material/Collection 日常操作 | 同一数据真源，不复制为新 Asset 表 |
| `/settings` | 既有注册表投影＋按需打开 Connector/模板操作 | 读清单不拉取；高级运行工具仍显式打开 |
| `/sources` | 兼容来源页 | 原 URL 保留，新页面复用相同 import/drawer 组件 |
| `/fact-packs`、`/fact-packs/:id` | 兼容证据包页 | ID、版本、冻结 checksum 不变 |
| `/materials` | 兼容全局素材页 | 同一 MaterialRevision；旧 Draft 挂载仍可用 |
| `/connectors`、`/templates` | 兼容配置页 | 配置/拉取/版本操作 API 不另建 |
| `/topics`、`/workspace`、`/workspace/:topicId` | 高级旧 Topic/Draft 路径 | 不隐式升级或把 Topic 映射成无关 Project |
| `/review-publish`、`/review-publish/:topicId`、`/legacy/review` | 高级旧审核路径 | 旧 Draft/Candidate/Receipt 身份保留 |
| `/legacy/assets`、`/handoff` | 高级历史交付路径 | 原 Mother/ContentAsset/DeliveryTarget/Receipt 可回读 |
| `/workflows` | 高级独立 Workflow 调试 | FE-F2 Run/Attempt/rerun 安全规则不变 |
| `/legacy/settings` | 管理员高级工具 | 保留模型、图片、skills/MCP/dsh 操作；不能自动写本机 Skills |
| `/projects/demo`、非数字 demo project/unit 地址 | 旧 Mock 演示 | 不作为持久化/真实执行验收证据 |

## 操作级承接矩阵

下表 API 路径均以 `/api/v1` 为前缀。每行的多个动词仍需逐项验证；“复用”只表示已接入口，不表示全量真实外部验收通过。

| 编号 | 旧操作 | API / 数据真源 | 分类与新入口 | 历史行为 / 验收要求 |
| --- | --- | --- | --- | --- |
| S01 | 导入文本 | POST `/sources/text` → SourceDocument | move_to_new_surface：Assets 导入、Project Evidence 创建并引用 | 原文/hash 不复制；新建不授予公开权利 |
| S02 | 抓取 URL | POST `/sources/url` | move_to_new_surface：同上 | 明确点击才联网；抓取失败不可伪装成功 |
| S03 | 导入文件、资料日期 | POST `/sources/upload?as_of=...` | move_to_new_surface：同上 | 使用原解析器与 query 元数据；保留文件来源 |
| S04 | 提取候选事实 | POST `/sources/:id/extract-facts` → Fact | move_to_new_surface：Assets/Project 来源 Drawer | 候选不自动 confirmed、不自动进边界 |
| S05 | 编辑事实陈述 | PATCH `/facts/:id` | move_to_new_surface：同 Drawer | 只改真实 Fact，不回填已冻结快照 |
| S06 | 单条确认/拒绝 | POST `/facts/:id/confirm`、`/reject` | move_to_new_surface：同 Drawer | 逐项回读真实状态 |
| S07 | 批量确认/拒绝 | POST `/facts/bulk-status` | move_to_new_surface：同 Drawer，100 条/页 | 翻页清选择；不把未加载事实隐式提交 |
| S08 | 查看原文/解析/日期/事实 | GET `/sources/:id` | move_to_new_surface：Assets/Project | 归档来源仍可读，不可改 |
| S09 | 归档来源 | PATCH `/sources/:id` is_archived | move_to_new_surface：Assets | 明确确认，不删除历史引用 |
| F01 | 创建空证据包 / 选择事实建包 | POST `/fact-packs`，可带 fact_ids | move_to_new_surface：Assets/Project；新页空包后逐项添加 | 同一 FactPack；不伪造第二套快照 |
| F02 | 添加/移除事实 | POST `/fact-packs/:id/items`、DELETE `/items/:fact_id` | move_to_new_surface：内嵌 PackBuilder | 仅 draft 可改，exact Fact 选择 |
| F03 | 冻结 | POST `/fact-packs/:id/freeze` | move_to_new_surface：内嵌编辑器 | 明确确认；空/冲突仍后端阻断 |
| F04 | 克隆新版本 | POST `/fact-packs/:id/clone` | move_to_new_surface：同上 | 旧 frozen checksum 保留，新 ID/版本 |
| F05 | 回读历史 frozen 包 | GET `/fact-packs/:id` | historical_read_only：Assets/Project/兼容 URL | 不改旧快照、权利与来源 |
| F06 | 绑定 frozen 包 | POST `/content-projects/:id/fact-boundary` | move_to_new_surface：Assets 精确复用、Project Evidence | expected_revision CAS；Collection 不构成边界 |
| F07 | 克隆边界、冻结并绑定 | POST `/content-projects/:id/fact-boundary/clone`、`/:pack/freeze-and-bind` | move_to_new_surface：Project Evidence 内嵌编辑器 | 原边界仍可读；409 不自动重试 |
| F08 | Project Source 引用/解除 | POST `/content-projects/:id/sources`、DELETE `/sources/:source` | move_to_new_surface：Project Evidence/Assets | 引用而非复制，解除不改历史边界 |
| F09 | 逐条公开使用授权 | PATCH `/fact-packs/:id/items/:item` | move_to_new_surface：Assets/Project 的内嵌 PackBuilder | 默认不授权；明确确认、exact item 回读；仅 draft 可改，冻结只读。来源 trust 不授予公开许可，模型使用权利不猜测 |
| M01 | 上传、类型、来源和权利登记 | POST `/materials/upload` | move_to_new_surface：Assets 上传弹窗 | query 传现有元数据；精确 bytes/hash/MIME |
| M02 | 原生预览生成/人工接受 | Provider preview + accept、ProviderGenerationTask prepare/execute/accept | move_to_new_surface：Assets/Project 按需 ProviderMediaPanel | 全局/旧临时预览接受只入库；绑定项目的持久任务接受同时建立该项目精确引用；均不自动改 Master |
| M02a | 原持久任务状态与已接受结果读取 | GET `/generation-tasks/:id`、`/:id/raw` | move_to_new_surface：Production → Assets task deep link | 刷新只读；已接受原字节仍校验；viewer/归档不开放写操作 |
| M02b | 查询/恢复原供应商任务 | POST `/generation-tasks/:id/recover` | move_to_new_surface：原任务列表或 task deep link | 显式点击；先核对项目是否归档；unknown 不重发，无原 job 时保持未知 |
| M03 | 公共素材搜索/接受 | 现有 provider search/stage/accept | move_to_new_surface：Assets/Project 按需搜索 | 权利、归因与 safe fetch 原规则保留；真实网络验收不在本批 |
| M04 | 版本/媒体/权利/使用情况读取 | `/materials/:id/revisions/:revision/raw`、SystemLibrary projections | move_to_new_surface：Assets | 认证读取 exact revision，缺失 coverage 不补零 |
| M05 | 撤销公开使用 | POST `/materials/:id/revisions/:revision/revoke-public-use` | move_to_new_surface：Assets 精确版本＋原因＋确认 | 旧字节/hash不变，live rights 继续约束下游 |
| M06 | 项目上传/精确引用/解除 | POST `/content-projects/:id/materials/upload`、`/materials/references`、DELETE reference | move_to_new_surface：Project Assets/Assets | 不复制真源；旧临时预览需另行引用；项目绑定持久任务的明确接受包含引用，并立即回读共享素材 |
| M07 | 挂载旧 Draft 媒体 | 旧 DraftMedia(use) API | advanced_compatibility：`/materials`/旧 Workspace | 不改成 Master 引用；保留旧稿件 |
| C01 | 新建 Connector/鉴权引用 | POST `/connectors` | move_to_new_surface：Settings 数据源内嵌操作 | 管理员；只存环境变量引用，不存 Key |
| C02 | 添加 endpoint/mapping | POST `/connectors/:id/endpoints` | move_to_new_surface：同上 | 使用原 ConnectorEndpoint，配置不等于 plugin 可执行 |
| C03 | 修改拉取周期 | PATCH `/endpoints/:id` | move_to_new_surface：同上 | 管理员、显式保存；不自动拉取一次 |
| C04 | 显式拉取 | POST `/endpoints/:id/pull` | move_to_new_surface：同上 | editor/admin＋单次确认，生成候选 Fact 不批准 |
| C05 | capability registration/probe | 既有 `/data-source-capabilities` API | move_to_new_surface：Settings CapabilitySettings | exact scope，不以 Generic Connector 代替真实验证 |
| T01 | ChannelTemplate 克隆/发布/下线/删除 | `/templates/channel-templates/clone`、`/:id/status`、DELETE `/:id` | move_to_new_surface：Settings 规则与模板按需工具 | 发布版本规则、删除保护保持 |
| T02 | BrandVoice 克隆/发布/下线/删除 | `/templates/brand-voices/clone`、`/:id/status`、DELETE `/:id` | move_to_new_surface：同上 | 草稿可明确归档；published 原地修改仍禁止，新版本发布下线旧版；不静默改 Persona/IdentitySnapshot |
| T03 | Prompt 读取/删除 | `/templates/prompts`、DELETE `/:id` | move_to_new_surface：同上 | Prompt ≠ deterministic Rule；无不存在的编辑 API |
| O01 | Topic 模型建议/新建 | POST `/topics/suggest`、`/topics` | advanced_compatibility：`/topics` | 新日常入口用 Opportunity/Project，不复写 Topic |
| W01 | Topic 生成/Job 重生成 | POST `/topics/:id/generate`、`/content-jobs/:id/regenerate` | advanced_compatibility：旧 Workspace | 旧生成 history 不迁成 CreativeExecution |
| W02 | Draft 正文保存/选区 AI | PATCH `/drafts/:id`、POST `/rewrite-selection` | advanced_compatibility：旧 Workspace | 旧 Draft 是原真源；新 Master 编辑有自身版本 |
| W03 | Draft FactCheck/提交审核 | POST `/drafts/:id/fact-check`、`/submit-review` | advanced_compatibility：旧 Workspace/Handoff | 不以新 Master checks 替换旧结果 |
| R01 | 旧 Draft 批准/退回 | POST `/reviews/drafts/:id/approve`、`/request-changes` | advanced_compatibility：旧 Review/Handoff | 原 Review、Candidate hash 与 RBAC 保留 |
| R02 | 平台/discoverability 检查/标题建议接受 | POST Draft `/checks/platform`、`/discoverability/post`、`/discoverability/:report/apply` | advanced_compatibility：旧 ReviewPublish | 旧 fallback 只留 legacy，不污染新 exact profiles |
| R03 | 已授权 target 执行 | POST `/delivery-targets/:id/execute` | advanced_compatibility：旧 ReviewPublish；新 `/review` 保持 | unknown 不自动重发；本批不做实际发布 |
| H01 | MotherRevision 保存/从 Mother 建 Draft | POST `/article-handoff/topics/:id/mother-revisions`、`/mother-revisions/:id/drafts` | advanced_compatibility：Handoff | 旧版本只读，不隐式 fork Master |
| H02 | Handoff 封面上传/撤权 | POST Draft `/media`、`/media/:id/revoke-public-use` | advanced_compatibility：Handoff | 历史 DraftMedia 权利原样保留 |
| A01 | 旧资产 target 授权/包生成 | POST `/article-handoff/assets/:id/targets`、`/targets/:id/package` | advanced_compatibility：旧 Assets | 不绕过 approval hash；包不等于公开发布 |
| A02 | 人工 receipt/feedback | POST `/article-handoff/targets/:id/receipt`、`/feedback` | advanced_compatibility：旧 Assets | receipt 仍指 exact target；不自动造发布事实 |
| A03 | 旧媒体 slot 上传/资产导出 | `/assets/:id/media/:slot/upload`、POST `/assets/:id/export` | advanced_compatibility：旧 Assets | 旧 Candidate source/schema 语义不变 |
| WF01 | Workflow 定义新版本/Run 启动 | POST `/workflows`、`/workflow-runs` | advanced_compatibility：Workflows/Production | 现有冻结 checksum；不重造 engine |
| WF02 | 人工 complete/单节点 rerun/从节点 rerun/retry | POST Run `/nodes/:id/complete`、`/rerun`、`/rerun-from-here`、`/retry` | advanced_compatibility：同上 | 原 Project auth/Attempt/stale/side-effect gates 保留 |
| ST01 | 旧模型路由/LLM/图片配置保存、LLM清除/测试 | PUT `/settings/models`、`/llm`、`/image`；DELETE `/llm`；POST `/llm/test` | advanced_compatibility：Settings 高级工具；日常模型注册保持 | 只在明确保存/测试执行；不写秘密到文档 |
| ST02 | Installed Skills/MCP 配置/启用 | PUT `/settings/plugins` | advanced_compatibility：Settings 高级工具 | 与未来 Capability Memory 分真源；promotion 不碰目录/skills_enabled |
| ST03 | dsh 配置/写入 | PUT `/settings/dsh` | advanced_compatibility：Settings 高级工具 | 明确打开＋明确本机写入，不在 inventory 时运行 |
| RD01 | Landing/Dashboard/历史稿/Run/Attempt/资产/receipt 读取 | 各自既有 GET APIs | historical_read_only：原 URL | 无泛化重定向、无历史覆盖 |

## 三个直接起点与日常用语

| 起点 | 正常路径 | 禁止隐式动作 |
| --- | --- | --- |
| 想法 | 内容项目 → 明确创建 Project → Brief → 内容矩阵 → Master | 不强迫先创建 Workflow/Topic |
| 来源/素材 | Assets 导入或 Project 来源/素材 → exact 引用 → Fact 确认 → frozen FactPack → 明确绑定边界 | 来源可信/集合成员不等于公开权利或事实边界 |
| 机会 | Opportunity → assessment → 明确转换 Project → Evidence/Brief/Identity/Matrix | 推荐不自动创建事实、批准或修改身份 |

界面用语：今日工作台、创作与执行、内容项目、内容矩阵、渠道变体、来源与证据、项目素材、审阅与发布、原生成任务、高级工具。不向日常用户展示 F6/F7 阶段名；`unknown/stale/blocked` 等真实业务状态不被改成“成功”。Workflow dirty/save 与 Master dirty/save 仍分开。

## 已完成与待完成（阶段历史）

- 已盘点 App 全部路由与上述操作真源；新入口先复用现有 API/组件，旧 URL 与导航保留。
- 已接入的入口必须通过隔离页面/API回读与 FE-P1 检查，证据记录在阶段验收文档。
- 本清单已完成独立产品/UX review，首轮三项清单/入口反馈经定向复核闭合；尚未对每一个旧高级操作做浏览器终验。清单批准不等于全部操作已验收，不得据此隐藏旧菜单或删除页面。
- 截至第七批，Creative Intent / Execution / 受限 MCP / Capability Memory / Director-first Video，以及真实 Codex MCP 读取、受控恢复、日常 Text 到 ZIP 与旧历史读取均有隔离证据。真实专业工具自动化未验证；完整操作终验与最终独立复核仍待完成，不能据此隐藏旧导航。

## 第七、八批实际承接与限制（2026-10-05历史快照）

141/147，前两批共新增 10 项闭合。日常 Source→Fact→逐条授权→冻结包→Project Boundary→Text Master→v4→批准→本地 ZIP，原 Topic/Draft/Mother/Candidate/Target/Receipt 及 Workflows 读取通过。历史使用明确 synthetic fixture，全部表 hash 不变，不能把它冒充用户真实发布复验。

C03 已验证本地选值不写入、明确保存后回读，未自动 pull；M05 取消撤权零请求；T02 新日常 Settings 的 Clone→草稿归档→确认删除仅作用于临时克隆；四个旧操作页在 viewer/角色读取失败时均禁止写入。Advanced 兼容目录覆盖 15 个既有入口，不自动执行。

第八批已完成 Assets/Settings 的全操作 parity，并汇总完成 14.6 浏览器场景：53/53 清单行均有对应页面、API 真源或明确历史兼容入口；隔离浏览器重新验证了新日常链路、撤权取消、Connector 周期保存、Settings 兼容目录/BrandVoice 生命周期、历史只读和权限 fail-closed。三类最终独立复核仍未完成；真实 Provider/公众号/专业工具仍不在本 change 验证范围。`LEGACY_NAV` 继续显示，所有深链接保留。具体记录见 `ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md`。

## 目录、依赖与启动

新日常页面位于 `apps/web/src/product/`，被复用操作保留在 `apps/web/src/pages/`，既有 API 在 `apps/api/app/routers/`。入口批次复用原表/API；第二批按批准范围新增执行/方法表及 additive `aco000000001`，后续批次无新依赖/迁移。正式SQLite已在另行授权的启用阶段升级至aco；沿用现有本机API、Worker与Vite启动方式，f8a身份祖先不代表认证启用。构建 `cd apps/web && npm run build`。阶段隔离验收仍必须使用临时SQLite/素材目录，不能向正式库或供应商发送测试请求。

关联：`docs/AI_CONTENT_STUDIO_NORTH_STAR.md`、`openspec/changes/align-creative-orchestration-product/`、`docs/superpowers/plans/2026-10-04-align-creative-orchestration-phase-0-2.md`。
