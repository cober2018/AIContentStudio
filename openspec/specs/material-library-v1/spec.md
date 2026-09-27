# material-library-v1 Specification

## Purpose
TBD - created by archiving change align-v1-prd2-content-harness. Update Purpose after archive.
## Requirements
### Requirement: Actual media is globally reusable

系统 SHALL 通过 Material + MaterialRevision 提供全局可复用素材库，多个 Draft MUST 能通过 DraftMedia 引用同一个 MaterialRevision。

#### Scenario: 上传图片

- **WHEN** 用户上传一张图片
- **THEN** 系统建立 Material + MaterialRevision
- **AND** 多个 Draft 可以通过 DraftMedia 引用同一个 MaterialRevision

### Requirement: Web-found media starts as candidate

系统 SHALL 保存网络素材的 source URL/provenance/rights 状态；在 `public_use_allowed != true` 前 MUST NOT 满足 Candidate media readiness。

#### Scenario: 网络图片入库

- **WHEN** Material Search Provider 返回一张网络图片
- **THEN** 系统保存 source URL/provenance/rights 状态
- **AND** 在 `public_use_allowed != true` 前不能满足 Candidate media readiness

### Requirement: Approved material bytes are immutable

被 approved Candidate 引用的 MaterialRevision SHALL 不可变；替换/编辑 MUST 产生新 Revision，且历史 Candidate 可按旧 hash 重建。

#### Scenario: 替换已批准素材

- **WHEN** MaterialRevision 已被 approved Candidate 引用
- **THEN** 替换/编辑必须产生新 Revision
- **AND** 历史 Candidate 可按旧 hash 重建

