## ADDED Requirements

### Requirement: The review center lists only works in progress

The review center SHALL list only works whose lifecycle is active, and SHALL leave out a project that is archived or has no active work.

#### Scenario: Deleted test work
- **WHEN** a work is deleted or its project archived
- **THEN** it no longer appears in 审阅与交付

### Requirement: A finished 成片 can be authorized for several platforms at once

For a finished-video candidate the authorization step SHALL let the user tick several video platforms (抖音, 小红书, 视频号, 公众号, 快手, B站, 百家号, 今日头条, YouTube), taking for each the persona's account bound to that platform when there is one, and SHALL create one delivery target per ticked platform. The candidate SHALL not be fixed to one platform. Each delivery target SHALL offer a button that opens that platform's publishing page, in the persona's Chrome profile when the account has one and in the current browser otherwise.

#### Scenario: Three platforms
- **WHEN** the user ticks 抖音, 公众号 and B站 for work 95 and authorizes
- **THEN** three delivery targets exist, each with the 知数Talk account of that platform, each with its own package, receipt and 去发布 button
