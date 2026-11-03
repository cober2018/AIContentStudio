# web-material-search Specification

## Purpose
TBD - created by archiving change web-material-search. Update Purpose after archive.
## Requirements
### Requirement: Web search finds pictures on readable sites

The platform SHALL search the web with the configured search provider for a product (name and variant) or a tech product, skip large marketplaces it cannot read (Taobao, Tmall, JD, Pinduoduo), read at most 10 pages with the safe fetcher, and list each page's site, title, link and content pictures, excluding icons and small images. When the direct read returns a page without content, the platform SHALL render the page with the local Chrome in headless mode using a throwaway profile (never the user's own profile), waiting up to about 20 seconds, and read it again. Pages that still cannot be read (blocked or unreachable) SHALL be marked unreadable.

#### Scenario: Script-rendered official site
- **WHEN** a found page is the OPPO Find X8 official page, whose direct read has no pictures
- **THEN** it is rendered in headless Chrome and its product pictures are listed

#### Scenario: Snack product
- **WHEN** the user searches for a product named 敏贝贝动物小饼干
- **THEN** candidates are grouped by source page with the site, title and link, and no Taobao, Tmall or JD page is read

### Requirement: Candidates are kept and only picked pictures are saved

Search runs SHALL be stored and shown again when the user returns, and SHALL be cleaned after 30 days. Only pictures the user picks SHALL be downloaded and saved as materials, each recording its source page. Each picture SHALL carry a suggested category; when the product has a variant not found in the page title the group SHALL be flagged as possibly a different item; sites on the user's preferred-site list SHALL be ranked first and marked.

#### Scenario: Pick for a product
- **WHEN** the user ticks two pictures under 网上找图 and saves the product
- **THEN** both are saved as materials with their source pages and appear in the product's info images with the chosen categories

### Requirement: Page text can be saved as a source

Each source page SHALL offer saving its text as a source document that goes through the existing fact confirmation.

#### Scenario: Spec page text
- **WHEN** the user clicks 存为资料 on a spec page
- **THEN** a URL source document is created from that page

### Requirement: The third-party model can start a search but not pick

An MCP tool SHALL start a web material search for a product work or a project and return the picking page link; another SHALL read the results. Neither SHALL accept or save pictures for the user.

#### Scenario: Missing certificate
- **WHEN** the model finds no certificate picture for a product work
- **THEN** it starts a search and sends the user the picking page link

