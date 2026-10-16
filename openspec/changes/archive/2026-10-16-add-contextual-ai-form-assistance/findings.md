# 实际发现与决策

- ProductCreationDialog/ProjectBriefTab已有明确表单状态和版本保存；浮窗应通过字段适配和onChange写草稿，不直接修改DOM或替代保存。
- CreativeIntentEditor对应creative.intent.v1，有目标/受众/叙事/视觉/音频等字段；整个区块排除批量写入，单项主动润色仍可用。
- TextStudioShell已有来源和基线校验的AI建议，可借用交互原则；现有正文接口不能直接处理任意商品字段。
- model_registration.PURPOSES和routes上限目前7，generation.providers.ROUTE_KEYS亦需同步添加；设置已有用途页，无需新建配置中心。
- Capability Memory支持project/persona作用域、候选及精确版本采用。capture-preference需要至少两次已保存Master编辑，不能冒充表单反馈使用。显式新偏好可复用候选创建接口。
- LLMRun保存模型输出/usage等，没有owner/project与逐项确认状态；建议一张轻量会话表用于恢复与反馈关联，不把业务状态塞进原始输出。
- 已填内容是用户约束，不自动变成已核实商品证据；模型输入不包含内部经营数据。润色数值/权限/上传不成立，应按类型显示真实可用操作。

- 品类和风格属于适用条件，不能混作Capability已有的项目/Persona/owner权限范围。用户选择的商品风格组合现有阶段方法；不复制Persona账号/身份。当前商品先复用当前项目，无SKU管理扩展。
- 单项事实纠错不能学习成品类或风格规则；本批反馈只改尚未确认且仍为空的建议。

- 已读取video-production-handoff：现有合同已要求先确认精确图片、独立动态提示词、hash匹配、用户网页生成及单独回传接受。新增价值是统一素材导演的质量职责和页面审查状态，不应重新建立视频调用/后期系统。
- 据图提示词不能用文本模型看到文件名冒充图像理解；高质量图片和提示词只是制作条件，返回视频质量必须另行观察。

## 实施实证
- 仅将stage配置用于失效检测不够：风格原revision中enabled方法会回灌。现剔除selected_methods原始stages，独立校验并冻结当前显式stages，创建/任务书/视频三面一致，关闭probe验证实际提示词不含关闭指导。
- actual vision通过现有安全transport传精确本地图片字节，回执保留Master/hash/图片hash及actual observation；纯文本不能冒称看图。实际模型提示词已改为单镜目的/动作/运镜/节奏/限制。
- 历史session无法单靠当前字段字符串认证未保存来源和方法，因此恢复只读供比较，重新生成再采用。pending不能通过历史选择解除。
- startup-cleanup快照可恢复代码；快照包含adjacentdirty，不能当成干净可提交版本，已独立抽取纯候选验证。
