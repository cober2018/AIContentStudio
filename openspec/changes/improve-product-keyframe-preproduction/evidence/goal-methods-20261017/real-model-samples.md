> 2026-10-18主Agent回读更正：第4节Session13–18的model_receipt均标记gemini-3.8-flash-high / openai_compatible / configuration_revision13。该节原称MiniMax-M3不准确；保留原执行记录，但样本质量结论以实际回执归属。见independent-recheck-model-receipts.json。

# 真实模型内容质量样本（2026-10-17）

模型路由（2026-10-18按保存回执更正）：form_autofill/field_polish 走系统默认 openai_compatible 注册路由；第4节六份样本的实际保存回执为 provider=openai_compatible、model=gemini-3.8-flash-high、configuration_revision=13、profile=registered.ddd9b006056eae2bfb76b2ee（independent-recheck-model-receipts.json）。回执是平台注册路由标识，不据此推断网关实际上游模型；如需宣称特定模型覆盖须另有匹配回执。2026-10-17 第1–3节历史文本中的"MiniMax-M3"称谓本轮未逐节核对回执，仅作历史记录保留，不作为当前验收归属。
样本载体：隔离用户 goalprobe@studio.local；新建 SKU-000002（便携折叠榨汁杯·探针样本）+ Project11/Unit17（商品域）+ Project12/Unit18（persona 对照）。未触 Project8/Unit14、Project9/Unit15。
脚本：/tmp/probe_real_sample.py、/tmp/probe_real_polish.py（不入库）。

## 1. 真实批量补齐（两项方法同时启用，合入一次请求）

请求：surface=product_brief，mode=autofill，targets=[objective, primary_audience]（均为空），production_stages 两项方法 enabled=true。HTTP 200，两项 suggested。

### objective 建议
> 向有随身鲜榨需求的人群展示标称400ml容量、USB充电及杯体分离拆洗等已知结构特点，达成对便携榨汁基础功能与便携属性的直观认知，并如实标注功率与续航以实物为准。
note：依据已知卖点（便携、USB充电、杯体拆洗、标称400ml容量）拟定。待确认：具体电池续航、功率、噪音以及购买入口均缺失，需待补充确认。

### primary_audience 建议
> 在差旅、通勤或办公等移动场景下有即时鲜榨饮用需求，关注设备随身便携、USB充电补能以及杯体能否拆开清洗的使用者。
note：待确认：当前缺乏实际买家画像、人群统计及具体使用场景频次的依据，仅依据商品已知便携与拆洗属性进行场景推导。

### 质量评审
- 场景具体：✔（差旅/通勤/办公移动场景、随身鲜榨需求，非泛人群）
- 理由集中：✔（objective 收敛到"一条视频达成便携认知"一件事）
- 事实依据：✔（只引用已提供的 400ml/USB/拆洗卖点；功率续航明确"以实物为准"）
- 不编造：✔（受众 note 明确"缺乏买家画像、人口统计依据，仅按已知属性推导"；购买入口缺失在 note 注明，未虚构 CTA 承诺）
- 待确认标注：✔（两条均带）
结论：补齐建议内容质量通过。采纳链路（POST decisions adopt）返回 200，未自动保存任务书。

## 2. 真实定点润色（选区 start=0 end=10"办公室下午来一杯鲜榨"，两项方法启用）

- 样本1：`在办公室下午随手鲜榨一杯，不用洗复杂零件，不用洗复杂零件`（note：保留办公下午茶场景与拆洗卖点；400ml/USB 等规格待确认后补充）
- 样本2：`办公室工位随时鲜榨一杯，不用洗复杂零件，不用洗复杂零件`（note：依据'便携随身携带'与'杯体可拆洗'，保留原意仅对选区紧凑润色；续航/功率/噪音仍待确认）

### 质量评审
- 保留用户意图：✔（选区"办公室下午鲜榨"场景与未选区"不用洗复杂零件"卖点均保留）
- 无编造：✔（规格表现明确待确认）
- 表达缺陷：✘ 两份样本同一缺陷——未选中的后半句"不用洗复杂零件"重复输出两次。

### 缺陷归因（对照实验）
同样润色请求、不启用任何方法（production_stages 不传）：`办公室工位下午随手鲜榨，不用洗复杂零件，不用洗复杂零件`——**同样重复**。
结论：尾部重复是既有 field_polish 管线在选区模式下的输出行为（当时路由称谓记为 MiniMax-M3，未经回执核对，见文档头更正），与本批两项方法无关；记录为已知问题（见 review.md），不在 9.1–9.7 最小改动范围内修复（修复需改既有 polish 合同/提示词，影响全部表单润色场景）。

## 3. 开关如何实际影响请求（隔离探针断言，非本真实样本）

见 isolation-probes.txt：假 provider 捕获实际 user_prompt——
- 方法组关闭：configured_methods == []（普通辅助）
- 两项全开：configured_methods 含两包（skill_ref/version/package_hash/applicable_fields 正确）
- 单开：只含对应一包
- script stage disabled：configured_methods == []（阶段总关不执行方法）

## 4. R5 返修：选区片段合同真实模型复验（2026-10-18，修复后）

修复内容：system prompt 明确选区合同（"suggestion 只返回选区范围内改写后的文字片段；未选中的前后文由系统原样保留拼接；无选区时返回整个字段完整内容"），拼接仍为 prefix+片段+suffix，不做任何全句去重。脚本 /tmp/probe_real_r5_samples.py（不入库），原始输出 r1-r5-real-samples 见下；载体：goalprobe@studio.local 新建隔离作品（Project22/Unit28 与复跑 Project23/Unit29，PROBE-GM-001 SKU）。模型归属（2026-10-18按回执更正）：六份样本对应 Session13–18，保存回执均为 provider=openai_compatible、model=gemini-3.8-flash-high、configuration_revision=13（independent-recheck-model-receipts.json）；本节原文"MiniMax-M3"称谓系开发当时误标，质量结论归属于上述保存样本，不据此推断网关实际上游模型。

| 形态 | 原文（选区【】标注） | 模型片段 | 拼装结果 | 结构校验 |
|---|---|---|---|---|
| 整字段·方法开 | 办公室下午来一杯鲜榨，不用洗复杂零件，随身携带很轻松 | （整句改写） | 适合需要随时喝鲜榨的上班族：USB充电随身携带，400ml杯体与主机可分离拆洗，在办公室轻松现榨不繁琐。 | 前后缀无关；无重复 ✔ |
| 开头选区 0..6 | 【办公室下午】来一杯鲜榨，… | 工位下午随时来 | 工位下午随时来一杯鲜榨，不用洗复杂零件，随身携带很轻松 | 后缀原样保留、出现一次 ✔ |
| 中间选区 7..13 | 办公室下午来一【杯鲜榨，不用】洗复杂零件，… | 杯现榨饮品，无需 | 办公室下午来一杯现榨饮品，无需洗复杂零件，随身携带很轻松 | 前后缀原样保留、各出现一次 ✔ |
| 结尾选区 19..26 | …不用洗复杂零件，【随身携带很轻松】 | 装进包里随身带 | 办公室下午来一杯鲜榨，不用洗复杂零件，装进包里随身带 | 前缀原样保留、出现一次 ✔ |
| 代理对选区 5..7(UTF-16码元) | 办公室下午【🥤】来一杯鲜榨，不用洗复杂零件 | 随手 | 办公室下午随手来一杯鲜榨，不用洗复杂零件 | 非BMP字符按UTF-16码元定位，前后缀无损 ✔ |
| 中间选区·方法全关 | 同中间选区 | 杯现榨饮品，无需 | 同上 | 关闭路径同一合同 ✔ |

结论：6/6 通过——选区模式只改写选中片段，未选文字逐字保留且不重复（第2节的"不用洗复杂零件"尾部重复在全部样本中不再出现）；整字段模式返回完整改写。隔离探针另覆盖切半代理对返回 409"选区必须包含完整字符"（r1-r5-probes.txt R5 组）。

