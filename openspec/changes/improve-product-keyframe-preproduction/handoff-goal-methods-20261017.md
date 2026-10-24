# 第9节批次交接文档（2026-10-17，开发中途停手交接）

用户已将第9节（目标与受众方法辅助）的实施改交原项目Agent继续。本文档是中断时点的完整交接：接手Agent持原始需求提示词＋本文档即可继续，不需要重新探索或重新确认方案。tasks.md 9.1–9.7 全部保持未勾选（本会话未产出可勾选的完整验收证据）；无提交、无push；正式数据、数据库、模型配置零改动。

## 1. 授权与依据（不需重新提方案）
- 第9节已获用户明确实施授权，直接进入 OpenSpec apply（任务9.1–9.7）。
- 需求与验收依据：design.md 第9节；tasks.md 第9节；`specs/guided-production-workspaces/spec.md` 行246–269 已含全部验收要求（规范已备好，不用补spec）。

## 2. 基线与文件足迹（先读这段再动手）
- Git 基线：main@8539806 + 约158个**相邻未提交改动**（他人在途工作，禁止重置、清理、覆盖）。
- 本会话产物（全部未提交）：
  - **新增** 6个文件（未跟踪，删除即彻底移除）：
    - `apps/api/app/studio_skills/studio.product.audience-need/v1/{SKILL.md, STUDIO-META.md, STUDIO-CONTRACT.json}`
    - `apps/api/app/studio_skills/studio.product.purchase-reason/v1/{SKILL.md, STUDIO-META.md, STUDIO-CONTRACT.json}`
  - **修改** 2个文件（⚠️ 这两个文件在动手前就已有相邻未提交修改，本会话hunk叠加其上）：
    - `apps/api/app/services/studio_creative_catalog.py`
    - `apps/api/app/services/form_assistance.py`
- **严禁** `git checkout -- ` 上述两个services文件（会连带毁掉相邻在途改动）。如需移除本会话改动，按第4节hunk清单手工撤销；6个新增文件直接删除。
- 本会话未改：路由、前端、openspec文档、数据库、正式数据、模型配置。

## 3. 已完成并验证的部分
- **9.1（完成）**：两项自编方法包已落库。方法正文按本平台既有销售标准（七项销售检查、五类表达测试、未知保全、待确认标注）独立编写；dbskill（CC BY-NC 4.0）仅作概念参考并记录在 STUDIO-META.md，未复制/翻译/打包其指令、案例或知识原子。
  - `studio.product.audience-need@1`（受众与购买需求）：适用字段 primary_audience / buyer_situation / main_objection。
  - `studio.product.purchase-reason@1`（购买理由与表达）：适用字段 objective / core_message / cta。
- **9.2 注册部分（完成）**：`studio_creative_catalog.py` 已注册两个 studio_builtin 方法，带 `applicable_fields` 字段（resource与STUDIO-CONTRACT.json镜像，`load_skill` 校验通过）。
- **9.4 后端部分（完成）**：`form_assistance.draft_method_projection()` 把 `explicit_draft_stages` 摊平为 `configured_methods`（含 id/skill_ref/version/package_hash/applicable_fields/instruction）注入 user_prompt；关闭的方法不进入冻结草稿，无指令残留。
- **9.5 后端部分（完成）**：`run_attempt` 中仅当 surface=product_brief ＋ unit为商品域 ＋ 字段值为空 ＋ 字段∈{objective, primary_audience} 时放开批量补齐建议；其他surface、非空值、明确跳过保护全部不变。
- **已跑验证（可复现）**：
  - `load_skill` 回读两个新包通过，package_hash 前缀分别为 `bf67529f65c6…`（audience-need）、`3db754db975f…`（purchase-reason）；既有 `studio.video.product-script@1`（faeff7f28d8e…）、`studio.text.longform@1`、`studio.graphic.qc@1` hash 不变。
  - venv 导入检查通过：`len(SKILLS)==24`；`product_goal_methods`、`draft_method_projection` 可调用；两文件 `py_compile` 通过。

## 4. 本会话确切代码hunk（续作或精确撤销都用它）
`studio_creative_catalog.py`：
1. `_resource(...)` 签名新增 `applicable_fields=()`；返回dict改为先构建 `resource` 变量，末尾 `if applicable_fields: resource["applicable_fields"] = list(applicable_fields)`（不加该参数的既有资源不受影响）。
2. 新增模块级 `PRODUCT_CONTEXT_SKILLS = frozenset({"studio.video.product-script", "studio.video.product-shots", "studio.product.audience-need", "studio.product.purchase-reason"})`，并把原 `required_context` / `prompt_sections` 里的内联集合字面量替换为该常量。
3. `SKILLS` 中 `studio.video.product-shots` 条目之后新增两个 `_resource(...)` 注册（带 applicable_fields，modality="video"）。

`form_assistance.py`：
1. `INTENT_FIELDS` 下新增常量：`GOAL_SUGGESTABLE_FIELDS`、`PRODUCT_METHOD_REFS`、`PRODUCT_METHOD_NAMES`。
2. `field_stage` 之后新增 `product_goal_methods(db, user, project_id, unit_id)`（只读：access→is_product校验→effective_profile→product_production_stages 或 video profile 的 production_stages→按 ref 匹配 script.methods 条目→返回方法卡数据＋`effective_stages`＋script stage 状态）。
3. 同区域新增 `draft_method_projection(frozen_project)`。
4. `run_attempt` 开头新增 `unlock_goal_intent` 计算；循环内 `protected = spec["protected"] and not (unlock_goal_intent and key in GOAL_SUGGESTABLE_FIELDS)`，autofill 条件改用 `protected`。
5. `run_attempt` 的 user_prompt dict 新增 `"configured_methods": draft_method_projection(frozen_project)`。

## 5. 关键设计决定（已定，接手直接沿用，勿重新推导）
1. **方法承载**：代码内 studio_builtin 注册＋studio_skills 包；`modality="video"`、`compatible_stage_schemas=[]`（只在表单助手冻结消费；freeze 带 node 时会判 not_applicable，不进 Recipe 节点执行）；无 tunable 参数（空 parameter_schema 已有先例 studio.graphic.qc）。
2. **请求路径**：助手启用方法组时，前端把**合并后的显式 stages**（effective_stages 的 script stage 内 upsert 两个方法、保留其他方法，其余 stage 原样）通过现有 `productionStages` prop → 请求 `production_stages` → `draft_stages()` 冻结进 `_project_snapshot.explicit_draft_stages`。补齐与润色共用同一选择；feedback 端复用 session 内冻结的 production_stages，不重发（现有行为）。
3. **开关保存**：复用 `PUT /content-projects/{id}/units/{unit_id}/production-profile`（settings.production_stages）。**必须先 GET 回读已存 settings 全量再合并保存**——`ProductionSettings` 是 extra=forbid 且带默认值，部分提交会用默认值覆盖已存设置；GET 已按 model_fields 过滤，round-trip 安全。保存仅更新 script stage 的两项方法选择，不动 SKU/角色默认。
4. **阶段总开关**：开关不改变 stage enabled；script stage 显式 disabled 时方法不执行（freeze 跳过）；stage 未配置时启用方法创建最小 `{enabled: true, methods: [两项]}` 条目。
5. **字段匹配**：请求级**不做** targets 过滤（保证 generate 与 decide 的冻结草稿确定性一致，否则 decide 的 snapshot digest 比对会误报漂移）；适用性由方法正文自限定＋UI 高亮当前焦点字段的适用卡。
6. **漂移阻止（已有机制，勿新增）**：`decide()` 的 project_snapshot digest 比对（409"商品依据、意图或所选方法已变化"）＋前端 `contextMatches()`（`methodIdentity` 已含 productionStages prop，开关变化自动进入）。方法版本/代码变化时 `load_skill` 重新冻结，旧建议按新配置采用被阻止。
7. **旧作品**：未配置两项方法→不传 `production_stages`（走 project_snapshot 既有 effective 路径，原助手行为）；`ProjectBriefTab`（项目级，无unit）完全不动，保护不放宽。
8. **继承顺序**：商品默认/选定SKU方案/当前作品由后端 `effective_profile` 已有逻辑承载；前端不要自己再算继承。

## 6. 剩余工作（按9.1–9.7）
1. **路由挂载**（9.3后端）：`apps/api/app/routers/form_assistance.py` 加 `GET /product-methods`（query: project_id、unit_id 必填）→ `service.product_goal_methods`；**必须声明在 `GET /{session_id}` 之前**。
2. **前端**（9.3/9.4/9.5）：
   - `ProductionWorkspace.tsx`：给 `GuidedProductionGoal` 传 `unitId={unitId}` 与商品域标记（`product` 变量已存在，行66：`unit?.production_domain === "product"`）。
   - `GuidedProductionGoal.tsx`：拉取 product-methods；管理"商品方法"开关状态（未配置不自动启用；显式启用时两项默认开；切换不生成不保存）；动态计算 objective/primary_audience 的 `protected`（商品域且为空→false，否则维持）；把 `stagesForRequest`（方法组激活时为合并显式stages，否则 undefined）传给面板的 `productionStages` prop；保存走设计决定3。
   - `FormAssistancePanel.tsx`：新增可选 `methodArea?: ReactNode` prop，在 aside 展开区内渲染折叠"商品方法"区（卡：名称/版本/适用字段/独立开关＋保存按钮）。面板请求逻辑零改动。
3. **9.6 验证**（命令见第7节）：编译、既有检查子集、四开关组合隔离探针（mock provider 断言实际 user_prompt 的 configured_methods）、空/非空/跳过保全、漂移、跨用户、persona 作品 objective 仍保护、Web 构建、桌面/窄屏只读页面检查、OpenSpec strict、真实模型内容质量样本（场景具体、理由集中、有依据、保留意图；HTTP200不算通过）。
4. **9.7 交接**：更新本目录 README/progress/findings/review＋task_plan ///步骤；evidence 存 `evidence/goal-methods-20261017/`（建议）；只按证据勾选 tasks 9.x；不归档整个change、不push、不覆盖正式沙发资料与历史接受记录。

## 7. 验收命令（沿用既有边界，不新增持久测试代码）
```
apps/api/.venv/bin/python -m compileall apps/api/app/services/studio_creative_catalog.py apps/api/app/services/form_assistance.py
apps/api/.venv/bin/pytest apps/api/tests/test_product_settings.py apps/api/tests/test_creation_recipe_stages.py apps/api/tests/test_persona_creative_studio.py apps/api/tests/test_persona_creative_identity.py -q
npm --prefix apps/web run build
openspec validate improve-product-keyframe-preproduction --strict
```
隔离探针/真实模型样本用既有隔离方式（临时脚本放 /tmp，不入库）；真实调用前核对 form_autofill 模型路由，正式沙发 Project8/Unit14 与既有 Project9/Unit15 记录只读不写，需要样本时新建隔离SKU/作品。

## 8. 本轮Skills使用
using-superpowers、executing-plans（中断于9.2/9.4/9.5后端完成、9.3路由未挂载处）。


## 主Agent返修要求（2026-10-17，优先于前序完成记录）
独立验收未通过。按review.md末节R1–R5继续原第9节：全请求指令关闭、按字段筛选、关闭保存、并发阶段配置保全及选区润色合同。禁止以检查全绿或既有缺陷为由直接关闭验收；每项提供修复前后证据和实际模型请求核对。保留旧数据与相邻修改，不扩展后续方向；修复完成交主Agent复验。当前45/58，未归档。

## 返修完成记录（2026-10-18，交主Agent复验）
R1–R5 全部修复并有对应复验证据：R1 三条嵌套泄漏路径统一清理＋渲染快照正文去重（启用方法正文仅执行投影一次，关闭仅 disabled_method_ids；默认继承可读；decide 不误报漂移）；R2 按本次 eligible 目标过滤、完整选择/执行投影分别记录、反馈重写重匹配、其他生产场景方法不受影响；R3 整组关闭可保存且重载一致，方法修改进入离开提醒；R4 保存基于保存时最新 effective_stages 仅合并两项，其他入口阶段/方法保留或清晰 409；R5 选区片段合同成立，真实模型整字段/开头/中间/结尾/代理对/方法关 6/6 样本无重复、未选文字逐字保留。
门禁：20 项返修探针、浏览器 E2E 19/19（含 B1 回归）、442 既有检查、27 项隔离探针、compileall、tsc+build、openspec strict 全绿（r1-r5-gates.txt）。逐项回应见 review.md"R1–R5 返修回应"；证据四件新增于 evidence/goal-methods-20261017/；real-model-samples.md 第4节。tasks 9.2–9.6 已带证据回勾（50/58）；原8项素材验收未动；未提交、未push、未归档；相邻修改与历史数据保留。


## 2026-10-18 主Agent二次独立验收
最新结论覆盖上节“全部修复”：R1/R3、R5现有样本通过；仅继续原R2/R4和模型回执说明更正。修复要求、复现与验收矩阵见review.md最新节，证据为independent-recheck-*。当前main@8539806未提交工作区，9.2/9.3/9.4/9.6待验、46/58；原8项素材保持未完成。保持相邻改动与正式沙发数据；不得据旧绿灯归档。无需重做已通过项或扩大功能。

## R2/R4 二次返修完成记录（2026-10-18，交主Agent独立验收）
R2：默认继承统一解析——商品域 product_brief 会话省略 stages 时经 apply_inherited_draft_stages 把快照冻结清单作为 explicit_draft_stages 执行源（generate/decide/feedback 同构）；objective/primary_audience/混合/表达字段/feedback 全按目标过滤渲染，继承关闭/阶段关零正文，无 applicable_fields 方法原合同不变，继承配置变化 409 阻止旧建议采用、未变可采用；默认继承保留、未强制发 stages、未删其他方法。R4：保存基准与 revision 同版本（profile 自带 stages 优先；无作品级 stages 回退 effective 且并发写必 409），仅提交用户实际修改的开关、组切换整体语义、409 保留草稿不自动重试；同版本/两GET间/PUT前写入/远端A本地B/同方法双改/整组关闭/回退路径全场景过。模型证据说明按 Session13–18 回执更正（openai_compatible/gemini-3.8-flash-high/rev13），不再标注 MiniMax-M3，历史保留，未新增模型调用。
门禁：442 既有检查、27/20/18 探针、compileall、tsc+build、openspec strict、git diff --check 全绿（r2-r4-gates.txt）。逐项回应与边界见 review.md"R2/R4 返修回应"；证据 evidence/goal-methods-20261017/{r2-r4-before.txt,r2-r4-after.txt,r2-r4-gates.txt}。tasks 9.2/9.3/9.4/9.6 已回勾（50/58）；原8项素材验收未动；未提交、未push、未归档；相邻修改与历史数据保留。


## 2026-10-18 第9节最终复验通过
第9节最终接受，R2/R4无需再交返修。最终实现、证据与边界以review.md「主Agent接续修复与最终复验」为准；50/58。基线main@8539806，两业务文件未提交；API已加载。保留160项工作区变更及全部历史，不以第9节通过代替原8项真实素材/成片及整体收尾；未提交/push/归档。
