## ADDED Requirements

### Requirement: Work code tag before the work title
Every place in the 角色内容, 商品视频 and 搜索推广 workbenches and the 待审成稿 page that shows a work's title as a heading or list row SHALL show a tag 「作品 <id>」 in front of the Chinese title, where id is the work's existing id.

#### Scenario: Production page
- **WHEN** the user opens any step of work 97's production page
- **THEN** the page title reads 「作品 97」 tag followed by the work title

#### Scenario: Work list
- **WHEN** the user opens the 角色内容工作台 list
- **THEN** each row starts with its 「作品 <id>」 tag before the title
