# 方案复核

当前阶段为方案，尚无实现或作品质量通过结论。自检覆盖：六组来源均有去向；新增六方法与既有后期职责区分；商品与角色不混同；没有引入视频API/自动网页生成/第二套剪辑引擎；实物证据、实际售价、图片确认、开关真实生效、工程重开和完整样片验收有规范。独立计划复核待记录。

2026-10-16独立计划复核：其余内容无阻断问题；指出“正常API”可能被理解为独立操作路径。已统一为通过平台CLI/REST或MCP使用已有能力，保持用户平台不点浏览器的边界。此为措辞明确，不新增执行接口或需求。复核修订后待最终确认。

最终独立复核：APPROVE。已核对平台CLI/REST或MCP措辞，前述问题关闭；未做代码或作品质量验收。

## v2内容与适配审计（2026-10-16）

前一轮APPROVE仅针对当时计划结构；本轮按用户要求深入核对，发现以下实质遗漏并修订同一套规范。

| 发现与证据 | 影响 | 修订 |
|---|---|---|
| product_creation.py:resume_launch用空stage_override直接启动；旧设计把选择放后期 | 首稿未使用商品方法 | 首次Run前保存/冻结，预览、执行、恢复及后期同版；新增场景 |
| creative_configuration.py:frozen_stage确定性分支要求deterministic_parameters | storyboard商品prompt可能使compose阻断 | 分节点适用性；AI/外部加载，确定性节点保持typed config并记录不适用 |
| model_capability_routing._multimedia_controls reference_images=false | 无法凭提示词承诺参考图保真 | 能力检查，已验证外部编辑才用，否则原图/实拍/主体合成；不新增网关 |
| capability_contracts.args_schema是标量且禁止执行载荷，ProductOffer仅自由文本+时间 | 嵌套报价/JSX无法直接放方法 | 报价在现有ProductContext兼容扩展；指令/详细方法卡/原生脚本分层 |
| motiful多角度为服装，shotcraft扫描线/聚光偏UI | 实物风格被软件模板带偏 | main-image/hero visual为主，服装/软件作为适用分支 |
| iart promo-components.md:Countdown取Date.now；motiful consistency-rules列无可回查转化率 | 固定成片时间不稳定、营销依据不实 | 静态截止时间；按事实金额/币种计算，删除未经核实营销数字 |

AE/Resolve仅做文档查询，无编辑/渲染。上游未安装/执行；六项方法仍为候选方案。完整商品验收继续需要实物资料与真正样片。

v2独立复核发现截止日期表述可能误读为必填，已修订：仅已提供并核实的截止时间才展示；无截止日期仍可展示核实价格，不添加紧迫性。已增加对应Scenario。35个来源文件hash一致，20项实施均未勾选。

最终v2独立复核APPROVE：截止日期歧义已关闭；仅方案审查通过，业务实现/原生组合/作品验收尚未开始。

## 实现与作品独立审查

平台Python审查APPROVE；计划/实现规格复核PASS。最终代码复核发现两项真实缺陷：空production_stages破坏无profile旧路径、详细卡外置可变。修复已落地，独立关闭复核继续。

商品作品独立结论ACCEPT_LOCAL_TEST_WITH_BOUNDARIES：全景/推近/定格抽帧，5/10秒切点，无黑帧/外观身份变化；标题清晰、轻缓节奏适合单图测试。仅写可见颜色、草地、休息邀请，未造价格/材质/尺寸/防水/承重。独立核对原图/成片/音频hash，成片1080×1920、30fps、16.020秒；读取工程重开证据缺失媒体0。

没有直接试听，ASR不能证明听感/逐句同步；字幕细分估计。−22.2 LUFS偏轻，发布前可听审，但不据此发明本地测试失败。接受范围仅本地单图样片，不接受商品公开宣传、角色默认风格或商业许可。可选优化为减少重复颜色文案，不阻塞本次测试。

最终代码复核APPROVE：空覆盖和冻结卡两问题已关闭，真实内存函数链render→freeze→external projection→load保持六卡原文/hash一致。受限本地final权限增量经独立真实函数探针审查APPROVE：跨scope、非final、内容漂移/祖先撤权或hash漂移均阻断，Candidate公开仍blocker。真实正常API绑定/字节检查已通过。

纯候选范围/闭包独立APPROVE：24文件hash与补丁一致，两迁移逐字保留原版本链；商品入口/恢复/Brief/搜索/事件与相对依赖完整，排除日批自动hook/runtime/worker/栏目。564项既有检查/1跳过、Web/API/迁移通过。正式8/8接受及本地Master41 render ready/context current，原图/旁白/成片与原生工程同字节。

关闭复核：实际50路径选择性本地提交、20/20归档，规范新增10条；纯候选归档后strict47/47。正式发布检查仍保留blocker/未直接试听，不将本地接受改写为公开发布批准。
