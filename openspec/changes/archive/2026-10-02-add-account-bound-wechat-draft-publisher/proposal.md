## Why

2026-10-01短稿实验修订已由用户明确批准：仅对指定new_media/WeWrite同一账号，允许最终HTML正文UTF-8编码严格小于2048字节的单次草稿实验，含token、精确素材上传、创建和回读。不公开发布，不解锁长文，不将实验通过标为完整官方合同/F7验收通过。必须走产品的exact账号、冻结审批和Delivery Attempt链路；默认remote_contract_ready保持false，不能借测试monkeypatch或旧CLI放行。

2026-10-01授权更新：用户已明确允许复用`new_media`现有WeWrite配置中同一公众号的凭据进行真实token、素材上传、草稿创建和回读测试；不允许公开发布/群发。不修改以下历史本地授权记录，不跳过接口合同、exact owned Account/Persona、冻结审批、scope、live rights与网络安全门槛。尚未执行任何账号API，凭据不得复制进仓库。

用户已确认一个Persona可经营多个ContentAccount，但同一个真实自媒体账号不得由多个Persona共享。现有WeWrite全局账号配置和发布时正文转换不能满足精确账号隔离及批准内容不变，阻断F7真实交付闭环。

## What Changes

- 保留Persona → Account一对多，不新增角色账号多对多关系；引入可验证的真实平台账号身份和独占绑定。
- 增加独立 `publisher.wechat.official@1`，只支持微信article的草稿创建与明确回读，不公开发布、不群发。
- 保留旧WeWrite key及历史读取，新适配器不继承旧验证记录，旧远端runtime仍不可执行。
- 凭据与token按具体账号隔离，仅保存安全引用/版本身份；读取库存不获取token或发起网络请求。
- 在Candidate审批前冻结官方接口所需的确定性正文表示、资源槽及哈希；发布阶段不得重写Markdown或增删正文。
- 继续使用DeliveryTarget/Attempt/Receipt和CapabilityRegistration/Verification；未知结果不自动重发。
- 公众号HTTP行为按本机WeWrite已验证实现对齐：标准token GET、原始文件名multipart上传、UTF-8 JSON `draft/add`、成功响应必须包含`media_id`；不移植WeWrite全局凭据、CLI fallback或公开发布能力。
- 本提案不授权真实账号上传、付费请求、部署、生产迁移或F8前置跳过。

## Capabilities

### New Capabilities

- `account-bound-wechat-draft-publisher`: 独占平台账号绑定、账号隔离配置、冻结正文交付、草稿回读和安全诊断。

### Modified Capabilities

- 无现有canonical要求删除或替换；本补充契约收紧既有身份层级和Delivery不变量。F7 active规格的WeWrite-only描述须在本补充批准后显式对齐，不能覆盖旧主规格。

## Impact

涉及ContentAccount、identity服务、能力验证、Candidate冻结/Review、Delivery服务与Settings。预计在既有ContentAccount增加可空真实平台身份列及唯一约束，不增加业务表；历史未绑定账号继续可读和本地交付，但不能自动推断远端身份。用户于2026-09-30批准本地实施和加法迁移开发，不授权生产迁移或真实账号动作。官方公开文档已通过直接HTTPS读取，用户确认权限开放，并批准将正文限制冲突保留为真实远端门槛；task0.1仅本地前置已完成，不表示真实账号/平台验证通过。
