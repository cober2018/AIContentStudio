# 方案复核

2026-10-16，范围仅为提案与计划，不是代码或作品验收。

## 规范校验

`openspec validate add-persona-production-skill-profiles --strict` 返回 `Change 'add-persona-production-skill-profiles' is valid`。

`openspec status --change add-persona-production-skill-profiles --json` 显示 proposal/design/specs/tasks 四类提案成果完成。这里的 isComplete 仅表示提案文件齐备；实际实施任务仍为0/22，不能据此归档。

## 独立计划复核

writing-plans要求的单个只读计划复核Agent检查了README、task_plan、proposal、design、22项任务、五份delta spec和research。结论：**Approved**，未发现会导致实施错误或卡住的矛盾、遗漏。

确认覆盖：Persona核心、三模态参考提炼、阶段多Skill开关、场景BGM可编辑标签、科技优先；保留whole-profile继承/版本冻结；开关要求实际执行生效；Hypit边界、talkcraft/dbskill限制和Resolve/AE分工明确。

## 提案阶段尚未进行的验收（历史）

无第三方Skill安装/试跑，无代码改动/构建/回归，无AE镜头或Resolve新样片，无新音乐导入、声音试听、用户风格采纳。上述均不以方案Approved替代。等待用户确认后才开始apply。

## 2026-10-16选型补充复核

新增三个AE/Resolve仓库的来源、许可证、重点方法和真实脚本逻辑已核对；组合操作映射仍在原22项范围内。补充后再次运行本change strict通过，git diff --check通过。本轮为主Agent来源复核，未重新进行独立计划评审；上面的Approved属于初版计划。AE指南只读请求返回会话ID未知，Resolve仅查询API文档，均不能视为适配运行验收。

## 2026-10-16实施独立复核

| 发现 | 修复及复核证据 |
|---|---|
| 整阶段方法错误分配到所有Recipe节点；angles归错阶段 | 按有效输出schema/模态判断适用性，不适用项保留原因；实际节点冻结及323既有检查通过 |
| 旧use_artifact可绕过新清单的执行状态/CAS | 有production_methods时强制阶段加载；prepared/cancelled真实路径409，无使用记录写入；97既有检查通过 |
| 人工生图实际提示词仍含关闭方法；非法source_kind导致500 | 实际create_package复核：禁用标记缺席、有效清单和技术合同保留；非字符串422；325既有检查通过 |
| 外部音频修订标签后无法验证接受来源 | 纯元数据父链严格追溯已接受原件，当前引用ID保持；89既有检查及独立13项篡改/撤权/字节检查通过 |
| 已采纳风格缺少应用路径；新草案冲突后卡死；旧方法参数不可编辑 | 复用Persona修订API显式应用可信精确风格；可修正重试；读取精确历史schema。356既有检查通过/1跳过、Web构建通过 |
| 应用风格异步刷新可覆盖新编辑；迟到历史显示在其他资产 | 实时草稿保护和历史请求代次；独立前端复核及tsc通过 |

Python独立审阅通过上述修复，并实际验证：同角色已采纳历史版本可用；未采纳/跨角色/伪hash/归档拒绝；伪造规则被可信修订替换；真实执行包中全关可选方法仍保留已应用的角色风格。前端静态复核通过，未通过浏览器点击平台。测试数量属于各自限定范围，不能相加当作去重后的全量结果。

交接Skill新增精确阶段加载与原生执行说明，格式校验及独立文档复核通过。原生三类AE小样已渲染、可重开，Resolve回读及来源哈希在evidence目录；此项不替代完整有声样片。

## 文案对照

同一brief、MiniMax-M3、temperature=0.2，关闭/单方法/三方法组合各一次。独立创意审阅认为三份均需改：全部超长；关闭版有无来源泛称与多余比喻；单方法误写技术合同；组合版编造团队行为并遗漏关键机制。采用关闭版作修订底稿，删无依据陈述、恢复五项事实，得到186汉字/222字符稿。单次定性对照不能证明某组合普遍更好或更差，也不据此提升默认。

用户已采纳风格试验标准。最终作品技术/创意评审、直接试听状态及最终默认决策仍独立保留。

## 纯候选验证

从49e4fdc导出独立候选，仅加入本需求21个代码/Skill路径、3个引用资源和成果文档；4个混合代码文件只叠本需求hunk，未带入发现调度、渠道插件及相邻schema变更。9个相关既有后端套件521 passed；Web tsc、Vite及FE-P1通过。本change strict与diff检查通过。具体命令、日志hash和候选清单hash见evidence/pure-candidate-verification.json。未新增测试文件。

原工作区156项已记录相邻文件逐一hash仍一致，见evidence/adjacent-preservation.json。所有本轮角色/素材/执行写入使用隔离SQLite；未把正式库的定时运行或数据字节一致性列作本轮验收。

## 完整试验片评审与回收

独立评审查看45张实际最终帧、21条字幕及首尾/切点，文案与批准稿一致；声学测量-20.1LUFS、true peak -1.9dBFS、无满幅样本。原生工程另由执行者实际重开，AEP/DRP缺失媒体均0。结论为接受试验样片建议，不代替直接试听、精确字词对齐或用户最终风格采纳。详见evidence/trial-independent-quality.md。

原Resolve AAC文件因尾垫导致47.083秒容器时长被平台拒绝。仅stream-copy封装修正后为47.018秒，独立复核证实视频逐包/时间戳/解码全同、保留音频PCM逐字节同，仅去掉峰值8.46e-9的1024个尾部样本/声道，原创意结论可延续至交付hash01dfed359d15b039d6bebc52eb3be89fa0df73a1460bc790f0b4da9cc9da2d77。

平台Execution1回读result_ready/revision22、8个输出staged，尚未accept或绑定新Master；用户已收到完整可播放样片，最终默认采纳待答复。当前20/22，不归档、不提交、不push。

## 完整样片采纳及正式接入授权

2026-10-16用户明确采纳已展示的完整样片作为科技角色首版默认方向，授权余下平台接入、验收、归档、本地提交。此前“用户采纳待定”的记录为历史状态；当前风格采纳已完成，直接试听及精确对齐仍未声明。6.3以技术/AI创意/用户风格三类独立证据完成，不把未知声音听感写为通过。

## 正式本地主稿遗漏修复复核

真实正式绑定被render snapshot的无条件public要求拒绝；已仅在video.master.v2复用既有local_final_use_allowed，保持同owner/project/unit、accepted final、编辑内容和继承授权验证，随后继续校验hash/bytes/MIME。私有快照标local_only，公开freeze/package显式拒绝。

独立Python复核Approved；临时正式库副本正常API绑定成功。跨owner/project/unit、非final、未接受、撤权、编辑/字节/hash/MIME变化、普通私有素材、private graphic均拒绝；原public路径正常。11个相关既有套件268 passed，Ruff及diff通过；无新持久测试。正式API重启readiness通过，实际Master绑定与最终数据回读继续。

## 正式验收结论

32项正常API回读通过，正式Master39绑定同字节accepted final，render ready/local_only且context current；Candidate freeze false与public_use false保持。Project7/Unit13展示完整样片/8个产物；Persona2 v4为用户已采纳的首版默认。独立Python与最终code-reviewer审阅均Approve。

旧2350行无删除；除自然后台的9个来源游标/时间状态及2心跳外旧行一致，75旧媒体全保全。本需求新增266行；并行自然后台新增15行另列，不误认为本需求数据。完整私有保全快照位于backups/persona-production-enable-20261016/。

正常checks含既有Gemini身份语义检查，input_truncated保持partial；schema/render/structure/timeline pass；本地资料未授公开许可，因此evidence/rights阻断及未选渠道的平台适配未通过是预期边界。本轮不声明公开发布能力。最终直接试听和精确字词对齐未声明，用户风格采纳已明确完成。
