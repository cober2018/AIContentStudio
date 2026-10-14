# Batch B 独立代码复核

2026-10-14，本地main@4646ad3 + 未提交工作区；代码hash与回执位于 docs/BATCH_B_RECEIPTS/index.json。仅本change批次B，不替代第7节最终验收。

| 发现 | 代码位置 | 修复/证据 | 复核结果 |
|---|---|---|---|
| 知乎确定性接受遗漏用户问题 | channel_variants.save_revision | 精确answer注入已确认问题；17-form smoke改为deterministic_adapt，先红后绿 | 后端独立关闭 |
| 可选来源/媒体private披露未生效 | production_packages.public_export_metadata | private可选仅留必要ID/hash；required则阻断；test_multiplatform_exports | 后端独立关闭 |
| 嵌套正文/标签绕过配置规则 | channel_variants._variant_visible_text | 收集所有可见文本、列表、代码、问题和标签；旧rule不放宽 | 后端独立关闭 |
| B站图文description/tags丢包 | channel_adapters.GraphicImageNoteAdapter / production_packages | exact新schema保留render字段，image-note.json与content.md完整导出；原XHShash保持 | 后端独立关闭 |
| Unknown可跨普通/Stage入口重发 | guard_unknown_adaptation / stage_domain_integrations | 同binding guard共用；Stage Unknown状态/安全binding持久记录；跨入口负向测试 | 后端独立关闭，事务限制见下 |
| 交付目标账号篡改 | build_v5_package / delivery | 冻结账号与具体target相等；不复用其他账号Candidate | 后端独立关闭 |
| 已声明Profile合同不一致仍可执行 | capability_for | 对已声明schema/adapter字段精确比对，缺省旧profile兼容 | 后端独立关闭 |
| 清空Stage账号恢复继承旧账号 | StageContractControls / _variant_request | 显式0与undefined继承区分；server0→None，key一致；原复现关闭 | TypeScript独立关闭 |
| 图卡可新增不能补齐的空媒体槽 | ChannelVariantModel / ChannelVariantForm | 根据Descriptor递归media_ref阻断新增前置，隐藏unsafe按钮；新负向Node回归 | TypeScript独立关闭 |

后端独立code-reviewer：APPROVE，限定所审合同/导出/账号/Unknown路径；原五hash、private投影、规则/HTML、direct→Stage Unknown与Profile不一致均独立回读。原空行尾随空格已去除并重新diff-check。第一次Python reviewer因额度中断，不将其算作通过。

TypeScript独立首轮两项不通过；修复后窄复核APPROVE，TypeScript和8/8 Node tests通过，两个原纯函数复现已关闭。没有未解决的已确认缺陷，可选架构/样式建议未扩大范围。

限制：独立后端代理未复跑全量或真实模型/发布；Stage→direct Unknown的外层事务由主执行者核对finalize_invocation的提交链，未声称独立实网对账。2624 passed/28 skipped/1既有环境失败、17Production+17Review/ZIP页面验证由主执行者据原输出回执。用户/独立最终质量验收、正式启用与生命周期均仍开放。

## 全权授权后独立最终复核（2026-10-14）

code-reviewer独立发现Profile apply多published、缺失Series回退默认两项；主执行者发现合法旧cover映射误拒。三项先红后绿最小修复，未放宽target/权利/bytes/Unknown规则。二次独立审阅与Python专项均APPROVE，无剩余已确认代码缺陷；Python专项独立Ruff6文件通过，其余日志只读复核，未冒称独立重跑全量。

- Profile：在同一savepoint插入/flush新行后调用现有_demote_other_published，保持单published；ID/旧payload/hash保全。
- 来源封面：仅接受order0的两种已合法source cover表达，映射新target字典；未知placement仍拒绝，不改Master。
- 栏目：显式不存在的Series先404，停止默认回退，query/create有回归。

真实回执：两个原问题测试均红；缺失Series查询原返回200红；修复后集中134 passed/1 warning/13.12s。完整2626 passed/28 skipped/1既有wewrite断链环境失败/80 warnings/122.96s；Web/FE-P1通过，Ruff和diff全绿，strict38/38。日志位于BATCH_B_RECEIPTS的closeout-*、missing-series-red、backend-closeout-final、web-post-enable、strict-post-enable。

独立DB复核：pre-series与pre-profile两备份所含470旧行保全；仅既已获准schema变更和12旧Profilepublished→archived，其profile/结构/hash未变。正式历史Series/Receipt均0行；非空legacy案例由持久测试验证，不冒称正式非空历史。完整性ok/FK0/head a3series00000001/healthready。

独立四账号包复核：4ZIP CRC/hash/exporthash匹配，各4图真实decode/权利/顺序保持，target账号3/4/5/6与Profile/Variant/Candidate/Review/授权分别钉定，换账号409。账号bound_unverified，实际本地交付不冒称远端资格/发布。

正式17浏览器逐行：17可选、3媒体/脚本预览通过；已有复杂Master6的11文字目标因结构需显式映射、3文字目标因素材精确映射明确blocked。formal17-browser.json记录实际边界；不说该Master所有17preview成功。新增源排版明确接受后文章账号流程通过，受控17形态完整UI/API/ZIP原证据仍成立。

最终判断：完成矩阵与最新hash回写后40/43；7.1/7.2保留真实成品人工质量门槛，3.1需全部验收完成，暂不归档。7.6仅为独立核对任务完成，不把相邻Persona人审或Stage收尾自动勾选。授权已充分，不再等待权限确认；QUALITY_ACCEPTED尚无证据。

## 图文修复与委托整模态最终复核

图文平台规则修复两文件经独立code-reviewer与Python reviewer均APPROVE：19项独立测试、24种额外异常输入无运行异常，照片预设、真实bytes/render/hash/rights门槛保全；主执行集中227项通过。

独立质量代理完整阅读2文章、6实际PNG、2全文ASR/声学/QC及4currentchecks，rubric通过，12最终原件hash与初件完全一致。仅确认用户明确委托的AI质量范围；未直接听音频，科技clipping非严格零，原human_review_required保留。可关闭owner7.1/7.2，相邻任务计数原样保全。完整评分与限制见persona-real/quality-review.md/json。

## 实际待提交版本独立复核

选择性候选代码树 c22bd320cc0bcf2ee0d3cb90cbf54062d85e2fe0经独立code-reviewer APPROVE：47候选sha与manifest匹配（content_projects为HEAD无改动），275个生产相对模块引用均解析；六个筛选文件保全精确账号/绑定/冻结检查与HEAD微信路径，无channel_methods依赖。实际暂存46代码路径，后端368通过/1跳过、Web/FE-P1、Node8/8、Ruff均通过。完整工作区2639通过/28跳过/1既有wewrite环境失败如实保留。scope和源/候选hash见commit-scope.json。

## 归档规范保全复核

七capability已同步：23新增、2修改、无删除或改名。逐capability原requirement/scenario及全部delta名称保全，无重复要求；相邻Persona/Stage tasks逐SHA未改变。archive-readback.json与archive-result.log保留实际42/43（生命周期自身）到43/43收尾过程。

正式最终回读：91表470旧行逐PK全列保全，仅12项已获准Profile归档状态差异；integrity ok、FK0、schema a3series00000001。完整证据hash与commit候选blob分别校验，不将共享工作区hash说成最终提交blob。
