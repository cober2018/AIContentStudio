## ADDED Requirements

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
