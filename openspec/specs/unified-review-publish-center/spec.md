# unified-review-publish-center Specification

## Purpose
TBD - created by archiving change align-v1-prd2-content-harness. Update Purpose after archive.
## Requirements
### Requirement: Review Center is a projection

Review Center SHALL 是既有实体的 projection：聚合每个目标的 draft/check/media/SEO/candidate/delivery，MUST NOT 创建第二份 approval/delivery state。

#### Scenario: 打开一个 Topic

- **WHEN** 用户打开一个 Topic
- **THEN** 页面聚合每个目标的 draft/check/media/SEO/candidate/delivery
- **AND** 不创建第二份 approval/delivery state

### Requirement: Approval sees actual final payload

Approval SHALL 将 title/body/document/actual media/order/placement/SEO/render/check versions 全部写入 Candidate manifest，且 Candidate Hash MUST 与实际交付包一致。

#### Scenario: reviewer 批准

- **WHEN** reviewer approves
- **THEN** title/body/document/actual media/order/placement/SEO/render/check versions 都进入 Candidate manifest
- **AND** Candidate Hash 与实际交付包一致

