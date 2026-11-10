## ADDED Requirements

### Requirement: 视频号 is a publish-only account platform
The platform list for registering a persona's public platform account SHALL include 视频号. 视频号 SHALL NOT appear in the work channel list, channel variants or product creation, and SHALL have no rewrite form.

#### Scenario: Register a 视频号 account
- **WHEN** the user registers a platform account for 知数Talk
- **THEN** 视频号 is in the platform list and the account is saved

#### Scenario: Not a work channel
- **WHEN** the user picks a channel for a work
- **THEN** 视频号 is not offered

#### Scenario: Delivery shows the account
- **WHEN** the user authorizes 视频号 for an approved video in 审阅与交付
- **THEN** the 视频号 option shows the registered account and the delivery target records it
