## ADDED Requirements

### Requirement: Disconnected library is reported

The platform SHALL treat the material library as connected only when a small test write into it succeeds. When it fails, saving and reading library files SHALL report 「素材库未连接」.

#### Scenario: Drive half-disconnected
- **WHEN** the library folder is listed but writes fail
- **THEN** the library float shows 「素材库未连接」 and saving a material returns 「素材库未连接」

#### Scenario: Reading while disconnected
- **WHEN** a page reads a file stored in the library while it is disconnected
- **THEN** the response says 「素材库未连接」, not 「素材文件缺失」 or 「素材存储不可用」

### Requirement: Local files play without a size limit

Reading a material file SHALL stream it from local disk with range support and no size limit, keeping the content check.

#### Scenario: Large final cut
- **WHEN** the user plays the 119 MB 成片
- **THEN** it plays and can be scrubbed

### Requirement: Show the file's location from the player

Video players in the video progress panel and the material detail drawer SHALL offer 「在访达中显示」 and 「复制路径」 at the top right. The path SHALL come from the platform's record, never from the page.

#### Scenario: Reveal in Finder
- **WHEN** the user clicks 「在访达中显示」 on the 成片
- **THEN** Finder opens with `海底光缆/导出/成片/…final.mp4` selected

#### Scenario: Copy path
- **WHEN** the user clicks 「复制路径」
- **THEN** the full file path is on the clipboard
