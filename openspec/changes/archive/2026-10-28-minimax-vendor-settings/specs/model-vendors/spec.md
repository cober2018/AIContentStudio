## MODIFIED Requirements

### Requirement: MiniMax shows in 厂商与模型

The 厂商与模型 settings SHALL list MiniMax as a local vendor with the local mmx CLI install state (with version), and SHALL let an admin configure it on the page: an enable switch, an API key (save and clear), an optional API base URL and a region. Keys SHALL only be returned masked, with a source marker showing whether the key was saved on the page or comes from the local mmx login. Values saved on the page SHALL take precedence; when nothing is saved the platform SHALL keep using the mmx login and the startup enable flag as today.

#### Scenario: Logged-in CLI

- **WHEN** mmx 1.0.27 is installed with region cn and a key, and the user opens 厂商与模型
- **THEN** the MiniMax row shows 已安装 1.0.27, the key as first 3 + last 4 characters with source 本机 mmx 登录, and 用于：一键配音

#### Scenario: Save a key on the page

- **WHEN** an admin enters a MiniMax API key and saves
- **THEN** the row shows the masked key with source 本页保存, and later mmx invocations receive the saved key

#### Scenario: Key never returned in plaintext

- **WHEN** the settings are read
- **THEN** no MiniMax key appears in plaintext in the response

#### Scenario: Not installed

- **WHEN** mmx is not installed
- **THEN** the MiniMax row says it is not installed and how to set it up

## ADDED Requirements

### Requirement: Page credentials override CLI login at invocation

When the page has a saved MiniMax API key, base URL or region, platform invocations of the local mmx CLI SHALL pass them as the CLI's override arguments; the subprocess environment whitelist SHALL stay unchanged. When the page has no saved values, invocations SHALL behave exactly as before.

#### Scenario: Saved key is used

- **WHEN** a page-saved key exists and the platform calls mmx for text-to-speech
- **THEN** the invocation includes the saved key override and succeeds or fails by that key's validity

#### Scenario: No page key keeps current behavior

- **WHEN** nothing is saved on the page
- **THEN** mmx authenticates with its own login, as before


### Requirement: MiniMax connection test

The 厂商与模型 settings SHALL offer a test action for MiniMax that runs a lightweight authenticated CLI call with the current override values and reports success with elapsed time, or a plain-language failure reason. The test SHALL NOT echo the key.

#### Scenario: Test with a valid key

- **WHEN** an admin clicks 测试 with a working key
- **THEN** the page shows 连接正常 and the elapsed milliseconds

#### Scenario: Test with a rejected key

- **WHEN** the CLI reports an authentication failure
- **THEN** the page shows 测试失败：Key 无效或没有权限
