## ADDED Requirements

### Requirement: Paid generations check the material drive first

Voiceover, image, shot image, shot video and storyboard grid generation SHALL check that the material library is writable before calling the provider. When it is not, the platform SHALL return `material_library_unavailable` with the message 「素材库盘没连接」 and SHALL NOT call the provider. Through MCP the model SHALL receive that code and message.

#### Scenario: Drive unplugged
- **WHEN** the material drive is not mounted and the model calls `generate_video_voiceover`
- **THEN** no request reaches MiniMax and MCP returns `material_library_unavailable` with 「素材库盘没连接」

#### Scenario: Drive mounted
- **WHEN** the drive is mounted and the model calls `generate_video_voiceover`
- **THEN** the voiceover is generated and stored as before
