## ADDED Requirements

### Requirement: Storage locations are settings

The settings page SHALL show 素材库位置 and 本地工作位置 with their current paths and whether each is reachable. The current locations SHALL be the defaults.

#### Scenario: View
- **WHEN** the user opens 设置 → 存储位置
- **THEN** they see `/Volumes/T1000/自媒体素材` and the current media folder, each marked 可用 or 未连接

#### Scenario: Change the local location
- **WHEN** the user picks a new 本地工作位置
- **THEN** the platform copies the files, checks each one, switches only when all match, and keeps the old folder

#### Scenario: Change the library location
- **WHEN** the user picks a new 素材库位置
- **THEN** the platform shows how many linked files were found unchanged there and switches only after the user confirms

### Requirement: New materials are stored in the library

Every new material SHALL be written into `<素材库>/AIContentStudio/` and SHALL NOT be written into the user's own folders. When the library is not reachable, adding material SHALL fail with 素材库未连接 and nothing SHALL be written elsewhere.

#### Scenario: AI picture
- **WHEN** AI 补齐素材 creates a picture for a row
- **THEN** the file is in `<素材库>/AIContentStudio/图片/` and the row uses it

#### Scenario: Drive unplugged
- **WHEN** the drive is not connected and a row needs a new material
- **THEN** that row becomes a gap with the reason 素材库未连接

### Requirement: Floating library with drag and drop

A floating library window SHALL open from a button at the bottom right, be movable and collapsible, and list library files. Dragging an item onto a storyboard row's 素材 cell SHALL use it for that shot. Dropping files from Finder onto the window SHALL add them all to the library.

#### Scenario: Drag to a row
- **WHEN** the user drags a library picture onto L03's 素材 cell
- **THEN** L03 uses that picture, the same as picking it before

#### Scenario: Drop many files
- **WHEN** the user drops five files from Finder onto the window
- **THEN** all five are added to the library and appear in the window
