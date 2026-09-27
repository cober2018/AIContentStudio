# workflow-rerun-staleness Specification

## Purpose
TBD - created by archiving change align-v1-prd2-content-harness. Update Purpose after archive.
## Requirements
### Requirement: Node can rerun without resetting upstream

系统 SHALL 支持对纯生成 Node 的 `Rerun Node`：上游实体版本不变，新旧 output 均可审计，output 改变时 MUST 将 downstream 标 stale。

#### Scenario: 重跑生成节点

- **WHEN** 用户对一个纯生成 Node 选择 `Rerun Node`
- **THEN** 上游实体版本不变化
- **AND** 新 Node output 与旧 output 都可审计
- **AND** output 改变时 downstream stale

### Requirement: External side effect cannot be generic-rerun

系统 MUST 对 Publisher/remote side effect 节点拒绝 generic rerun API；用户 SHALL 通过 Delivery reconciliation/retry contract 处理 failed/unknown 结果。

#### Scenario: 尝试泛化重跑发布节点

- **WHEN** Node 属于 Publisher/remote side effect 且结果 failed/unknown
- **THEN** generic rerun API MUST reject
- **AND** 用户通过 Delivery reconciliation/retry contract 处理

