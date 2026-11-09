## ADDED Requirements

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
