## ADDED Requirements

### Requirement: A third-party model publishes a package or saves it as a platform draft
The platform SHALL let a third-party model list delivery targets the user authorized and that wait to be published, read one target's package as absolute read-only file paths plus that platform's title, description and hashtags, and either publish it or save it as a draft on the platform, as the user asked. After publishing, the model SHALL record the result with a screenshot and the link when the platform shows one; the platform SHALL record it as the target's receipt marked as published by a third-party model, without an actual publish time. After a draft, the model SHALL record the draft with a screenshot and stop. Login, QR codes, captchas and risk checks SHALL stop the run for the user. Step-by-step instructions per platform SHALL be a platform skill readable by any harness.

#### Scenario: Published on 视频号
- **WHEN** the user tells Codex Desktop to publish work 97 to 视频号
- **THEN** Codex Desktop uploads the cut and cover in the logged-in browser, fills description and hashtags, clicks 发表, records the result with a screenshot, and the delivery target shows as published by a third-party model

#### Scenario: Draft only
- **WHEN** the user tells the model to save work 97 as a 视频号 draft
- **THEN** the model stops before 发表 with a screenshot, records the draft, and nothing is published

#### Scenario: No link on the platform
- **WHEN** the platform shows no public link for the published work
- **THEN** the receipt uses the screenshot as its evidence

#### Scenario: Login needed
- **WHEN** the 视频号 page asks for a QR login
- **THEN** the run stops and asks the user to log in, then continues

#### Scenario: Target not authorized
- **WHEN** the model asks for a target the user has not authorized
- **THEN** the platform refuses and nothing is uploaded
