## ADDED Requirements

### Requirement: A third-party model uploads a publish package as a platform draft
The platform SHALL let a third-party model list delivery targets waiting to be published, read one target's package as absolute read-only file paths plus that platform's title, description and hashtags, and record that it saved the package as a draft on the platform with a screenshot. The model SHALL stop before the platform's final publish action; publishing and the receipt link SHALL stay with the user. Login, QR codes and captchas SHALL stop the run for the user. Step-by-step instructions per platform SHALL be a platform skill readable by any harness.

#### Scenario: Draft saved on 视频号
- **WHEN** the user tells Codex Desktop to upload work 97 to 视频号
- **THEN** Codex Desktop reads the package, uploads the cut and cover in the logged-in browser, fills description and hashtags, stops before 发表 with a screenshot, and the delivery page shows the draft record

#### Scenario: Login needed
- **WHEN** the 视频号 page asks for a QR login
- **THEN** the run stops and asks the user to log in, then continues

#### Scenario: Publishing stays with the user
- **WHEN** the draft is saved
- **THEN** nothing is published and no receipt is filled until the user publishes and fills the link
