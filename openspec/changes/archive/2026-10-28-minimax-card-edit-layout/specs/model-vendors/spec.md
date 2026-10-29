## MODIFIED Requirements

### Requirement: MiniMax shows in 厂商与模型

The 厂商与模型 settings SHALL list MiniMax as a local vendor laid out like the other vendor rows (summary with 编辑 and 测试 actions; configuration fields shown only after 编辑, saved together with one 保存 action) with the local mmx CLI install state (with version), and SHALL let an admin configure it on the page: an enable switch, an API key (save and clear), an optional API base URL and a region. Keys SHALL only be returned masked, with a source marker showing whether the key was saved on the page or comes from the local mmx login. Values saved on the page SHALL take precedence; when nothing is saved the platform SHALL keep using the mmx login and the startup enable flag as today.

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


#### Scenario: Edit like other vendors

- **WHEN** an admin opens 厂商与模型
- **THEN** the MiniMax row shows only its summary with 编辑 and 测试, and clicking 编辑 reveals labeled API Key, 访问地址 and 区域 fields with 启用 and 清除密钥 options saved by one 保存 button
