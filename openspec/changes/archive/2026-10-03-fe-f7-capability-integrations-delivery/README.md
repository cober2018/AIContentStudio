# FE-F7 — Capability Integrations & Delivery

## 需求背景

按产品North Star建立真实能力登记、逐操作模型/插件路由、Connector执行、精确素材接受及账号隔离交付；不把配置、聊天成功或合成测试冒充远端能力验收。用户授权本轮仅在本地main收尾，实施提交为`3f28a51d0145c49ae558766aeebbdbed68a8fcc1`。

## 目录结构

- `.openspec.yaml`：原工作流元数据。
- `proposal.md`、`design.md`：范围与设计决策。
- `tasks.md`：110/110的最终任务记录。
- `specs/`：五份已同步主规格的ADDED delta。

## 已完成

- 已批准F7实施/本地门禁及生命周期收口；模型路由23/23同步归档，已归档公众号系统记录delta亦同步。
- 真实CPA聊天、MiniMax图像/语音、已授权本机ASR及素材→项目→Master证据按范围分别记录。
- 当前公众号短稿成功、同账号真实人工确认、原子Receipt/CapabilityVerification和精确范围隔离已验收；指定原HTML长文实验另有成功证据。
- F7-only提交快照：1660 passed/28 skipped，Web/FE-P1/state、Ruff及strict通过。七份canonical原有54条要求/146个场景完整保留，生成Purpose已正式化。

## 待完成 / 范围延期

- Commons真实搜索/导入由用户暂缓；10.2为行政关闭，不是实测PASS或provider verified。恢复必须另获授权。
- MiniMax真实视频/H3为当前账号套餐的用户排除范围，不代表厂商没有视频能力；CPA未证明媒体操作与未证明素材权利保持不可用/false。
- 公开发布、其他账号/形态/动作、尚未明确的一般公众号远端合同及F8不由此归档放行。成功草稿不强制API回读，Unknown仍不得自动重发。

## 关键设计决策

Registry与既有SystemSetting是真源；生成只提交一次且人工接受后才进入MaterialRevision，Master仍显式保存。微信验证绑定精确账号/形态/动作、有效期及当前实现/运行身份；历史成功不能借重登记自动晋级。F8认证/MinIO/f8a未混入F7提交，原工作区改动保留。

## 依赖与启动

沿用原Python/FastAPI、React/Vite及本机可选MiniMax/MLX运行环境，无本轮新增依赖。启动仍使用`apps/api/scripts/startup/start_api.sh`、`start_worker.sh`和既有Web脚本；私有运行配置与密钥不入Git。此次归档不运行正式迁移、供应商调用或任何远端推送/部署。

长期契约见[主规格](../../../specs/capability-integrations-delivery/spec.md)，实际门禁与范围证据见[本地验收](../../../../docs/FE_F7_FINAL_LOCAL_GATES.md)、[模型证据](../../../../docs/FE_F7_MODEL_VALIDATION.md)、[公众号证据](../../../../docs/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)。
