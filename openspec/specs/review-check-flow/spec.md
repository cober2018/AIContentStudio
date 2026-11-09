# review-check-flow Specification

## Purpose
TBD - created by archiving change review-checks-as-flow. Update Purpose after archive.
## Requirements
### Requirement: Check warnings are judged by the writing model
每条状态为 warning 的 Content Master 检查，系统 SHALL 交给写作方式对应的模型判断「可以接受」或「不能接受」并给出理由；判断 SHALL 绑定检查 ID 与输入哈希。写作方式为平台模型时由平台调用已配置模型；为第三方模型时 SHALL 挂成待办，由第三方模型经 MCP 交回，平台不得代为判断。

#### Scenario: Platform model judges a warning
- **WHEN** 平台模型写作的作品检查产生 warning
- **THEN** 系统调用平台模型，记录判断结果与理由；调用失败记为判断失败

#### Scenario: Third-party model judges a warning
- **WHEN** 第三方模型写作的作品检查产生 warning
- **THEN** `get_review_tasks` 列出这条待判断项，第三方模型用 `submit_warning_judgment` 交回判断

#### Scenario: Rerun does not reuse old judgment
- **WHEN** 检查重跑产生新的检查 ID 或输入哈希
- **THEN** 旧判断不适用，需要重新判断

### Requirement: Approval follows model judgments
内容批准 SHALL 只在所有 warning 都被模型判断为可以接受时成功，并 SHALL 用模型判断生成处置记录；用户无需填写处置说明。

#### Scenario: All warnings accepted
- **WHEN** 所有 warning 都被判断为可以接受，用户点「批准内容」
- **THEN** 批准成功，处置记录写入模型名与理由

#### Scenario: A warning rejected or unjudged
- **WHEN** 有 warning 被判断为不能接受、尚未判断或判断失败
- **THEN** 批准被拒绝，页面只允许「要求修改」或对失败项「重新判断」

### Requirement: Review page shows checks as a flow
问题与审批页 SHALL 以节点流程展示各项检查：通过为绿色，模型判断可接受的提醒为黄色，其他提醒为红色；详细原因与模型判断 SHALL 只在点击节点后显示，页面不得展示原始检查 JSON 或逐条处置输入框。

#### Scenario: Click a node
- **WHEN** 用户点击某个检查节点
- **THEN** 下方显示该检查的原因和模型判断，其他节点只显示名称与颜色

### Requirement: Flow reflects live approval validation
检查流程 SHALL 先运行与批准相同的实时核对，并以「冻结版本核对」节点展示；核对不通过时该节点 SHALL 为红色并阻止批准。每个节点 SHALL 列出实际核对范围。

#### Scenario: Frozen candidate went stale
- **WHEN** 冻结后来源稿的检查结果或素材发生变化
- **THEN** 「冻结版本核对」显示红色并说明需重新冻结，「批准内容」不可点

### Requirement: Third-party identity review looks at rendered cards
第三方写作的图文身份复核 SHALL 在请求中附上全部成图（绑定内容哈希）；第三方模型交回且无问题时，身份检查 SHALL 记为图片已核对并通过。

#### Scenario: Third-party reviewer checked the images
- **WHEN** 第三方模型看过附带的成图并交回空问题列表
- **THEN** 身份检查状态为 pass，覆盖范围记为看过全部成图

