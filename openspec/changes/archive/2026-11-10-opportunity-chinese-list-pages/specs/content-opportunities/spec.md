## ADDED Requirements

### Requirement: Plain list pages can be used as sources
When a website source's page has neither structured article data nor an advertised feed, the system SHALL read the page's same-site article links (long enough titles, article-like addresses carrying a date or article number), take the largest group of links sharing one address pattern as the article list, and take each item's date from its address or the text next to the link. The source SHALL pass validation only with at least 2 such items.

#### Scenario: Government news column
- **WHEN** a user adds https://www.nhsa.gov.cn/col/col14/index.html
- **THEN** validation passes and collection yields the column's latest articles with publication dates

#### Scenario: Page that needs scripts to show its list
- **WHEN** the page's article list only appears after scripts run and the HTML holds fewer than 2 article links
- **THEN** validation fails as it does today

### Requirement: Article text is read from pages without an article region
When an article page has no structured article body and no article or main region, the system SHALL take the page block holding the most paragraph text as the article body, and SHALL take the publication time from a labelled date on the page or the address. Bodies that are still too short SHALL fail as they do today.

#### Scenario: Ministry article page
- **WHEN** full text is read for an article on www.moe.gov.cn that has no article or main tag
- **THEN** the article body is returned instead of article_region_missing
