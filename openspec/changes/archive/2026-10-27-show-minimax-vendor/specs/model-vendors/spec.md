## ADDED Requirements

### Requirement: MiniMax shows in 厂商与模型

The 厂商与模型 settings SHALL list MiniMax as a read-only local vendor next to the platform's own vendors, showing whether the local mmx CLI is installed (with version), whether the platform enables it, its region and a masked key, and which platform features use it. The page SHALL NOT show the key in plain text or allow editing it.

#### Scenario: Logged-in CLI
- **WHEN** mmx 1.0.27 is installed with region cn and a key, and the user opens 厂商与模型
- **THEN** a MiniMax row shows 已安装 1.0.27, 已启用, 区域 cn, the key as first 3 + last 4 characters, and 用于：一键配音

#### Scenario: Not installed
- **WHEN** mmx is not installed
- **THEN** the MiniMax row says it is not installed and how to set it up
