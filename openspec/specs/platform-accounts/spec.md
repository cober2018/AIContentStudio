# platform-accounts Specification

## Purpose
TBD - created by archiving change platform-account-records-only. Update Purpose after archive.
## Requirements
### Requirement: A platform account records only the account itself

A platform account SHALL hold only its platform, name, public identifier, owning persona, an optional homepage link and platform connection settings. It SHALL NOT carry a profile, profile revisions, account-scoped series or account default workflows, and generation, delivery and channel variants SHALL use persona and brand profiles only.

#### Scenario: Opening an account
- **WHEN** the user opens the account 知数Talk
- **THEN** one 账号信息 page shows platform 公众号, the public identifier, owning persona, homepage link, 去发布/去写作 buttons and the 公众号 connection, and no 编辑资料, 修订历史, 内容记忆 or 账号栏目 entries

### Requirement: One active account per persona per platform

Every account SHALL be registered with a platform. A persona SHALL have at most one active account on each platform; archived accounts do not count.

#### Scenario: Second account on the same platform
- **WHEN** an admin registers a second active 百家号 account for a persona that already has one
- **THEN** the request is rejected with a message that the persona already has an account on that platform

### Requirement: Jump to the platform's creator pages

The account page SHALL offer buttons that open the platform's own publish and writing pages in the user's browser, without storing passwords or logging in on the user's behalf.

#### Scenario: Going to publish
- **WHEN** the user clicks 去发布 on a 百家号 account
- **THEN** the 百家号 creator backend opens in a new browser tab

### Requirement: Public account identifiers accept ordinary nicknames

For every platform except 公众号, a public account identifier SHALL accept any text of 1–64 characters after trimming, including spaces, full-width punctuation and emoji. It SHALL still reject control characters, URLs, values containing secret words (password, secret, token, appsecret, bearer, api_key, apikey, credential), values starting with `sk-`, and token-like strings of 32 or more characters made only of letters, digits and `+/=_-`. Rejections SHALL NOT echo the submitted value. 公众号 SHALL still require a `wx` AppID.

#### Scenario: Nickname with full-width bar
- **WHEN** an admin registers an X account with identifier 「Kubo酱｜冲浪少女」
- **THEN** the account is created

#### Scenario: Name containing "sk-" in the middle
- **WHEN** the identifier is `desk-talk`
- **THEN** it is accepted

#### Scenario: Secret-looking value
- **WHEN** the identifier is `sk-abc123` or `https://x.com/foo`
- **THEN** it is rejected without echoing the value

