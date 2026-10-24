# local-common-library Specification

## Purpose
TBD - created by archiving change local-common-library. Update Purpose after archive.
## Requirements
### Requirement: Common library lives on the Mac

The common material library SHALL live on the Mac's local disk (default `~/自媒体素材/通用素材库/`, changeable in settings), with the project subfolder structure minus 导演稿 and 导出. Common materials SHALL stay usable when the external drive is unplugged.

#### Scenario: Drive unplugged
- **WHEN** the external drive is disconnected
- **THEN** materials in the common library still preview and can be used

### Requirement: Only the user or the video model decides what is common

The platform SHALL NOT classify materials as common on its own. A material moves to the common library when the user clicks 「归入通用素材库」 or the external model states it in its receipt.

#### Scenario: User moves a clip
- **WHEN** the user clicks 「归入通用素材库」 on a clip in 海底光缆
- **THEN** the clip moves to the local common library's matching subfolder, and any shortcut to it is updated

### Requirement: Old test materials are cleared

Materials used only by projects other than 海底光缆 SHALL be retired from the library (archived, records kept) and their files moved to the Trash; those projects SHALL be archived. 海底光缆's materials SHALL be kept and stored in its project folder. The database SHALL be backed up first.

#### Scenario: After clearing
- **WHEN** the user opens the material library
- **THEN** only 海底光缆's materials are listed, and the old files are in the Trash, not deleted

