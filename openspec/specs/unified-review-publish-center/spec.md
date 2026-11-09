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

### Requirement: The review list filters by content domain
The review list SHALL offer a 内容分类 filter with 全部, 角色内容 (persona), 商品视频 (product) and 搜索推广 (search), applied together with the status filter and search, and kept in the URL.

The list SHALL also offer a 角色 filter listing the personas of the listed works, applied together with the other filters and kept in the URL.

#### Scenario: Filtering persona works
- **WHEN** the user picks 角色内容
- **THEN** only works whose production_domain is persona are listed

### Requirement: The delivery step opens the local output folder
The 交付与回填 step SHALL show 打开成果文件夹 between the ZIP download and the receipt. For a video work it SHALL reveal the latest approved 成片 file in Finder; otherwise it SHALL open the project's 导出 folder. Only platform-recorded paths SHALL be opened.

#### Scenario: Opening a finalized video's output
- **WHEN** the user clicks 打开成果文件夹 on a video work with an approved 成片
- **THEN** Finder opens with that 成片 file selected

### Requirement: Older versions are deleted once the 成片 is approved
After a video work's 成片 is approved and its candidate frozen, the system SHALL permanently delete the work's older edit tasks, their output records, materials used only by them, their files under 工作 and 导出, and older review candidates with their reviews, keeping only the approved 成片 task and its 小样. An older candidate that has delivery records SHALL be kept. Each deletion SHALL write one project log entry shown in 历史与变更.

#### Scenario: Approving the final cut
- **WHEN** the user approves 成片 v3 after v1 and v2
- **THEN** v1 and v2 tasks, records and files are gone, and 历史与变更 shows one log entry describing what was deleted

#### Scenario: Old candidate already delivered
- **WHEN** an older candidate has a delivery target
- **THEN** that candidate and its delivery records are kept

