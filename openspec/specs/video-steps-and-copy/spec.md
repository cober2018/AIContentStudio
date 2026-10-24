# video-steps-and-copy Specification

## Purpose
TBD - created by archiving change video-steps-final-lock-and-copy. Update Purpose after archive.
## Requirements
### Requirement: Persona video is seven single-purpose steps

Persona video production SHALL be split into 选题与资料, 导演稿, 素材, 配音与音乐, 小样, 成片, 交付, each page showing only that step's content. Material and voice pages SHALL show one shot or one item at a time where a list is long. Tools that belong to no step SHALL live on a separate 高级 page outside the numbered steps.

#### Scenario: Material step
- **WHEN** the user opens step 3 素材
- **THEN** one shot is shown with its material request, the bound material preview and any gap, with 上一镜 / 下一镜, and nothing from other steps

### Requirement: Going back before the final cut

Before the final cut is approved, the user SHALL be able to return to the 导演稿 with notes from any later step, sending the chain back to 导演稿 changes.

#### Scenario: Back to the draft during 小样
- **WHEN** the user, at 小样 review, writes notes on the 导演稿 page and clicks 退回导演稿
- **THEN** the chain shows 导演稿按你的意见修改中

### Requirement: An approved final cut is final

After the final cut is approved the unit SHALL be read-only for good: no reopen, every save refused with 「成片已定稿，要调整请复制一份」.

#### Scenario: Save after approval
- **WHEN** anything tries to save a master for a unit whose final cut is approved
- **THEN** the save is refused with that message

### Requirement: Copy a video or graphic unit

The user SHALL be able to copy a video or graphic unit inside the same project. A video copy SHALL carry the approved 导演稿 and start at 导演稿 review; a graphic copy SHALL carry the current master. The original SHALL stay unchanged.

#### Scenario: Copy the finished 海底光缆 video
- **WHEN** the user clicks 复制一份 on the finished video
- **THEN** a new unit 「… · 副本」 appears in the same project, opens at step 2 with the same 导演稿 waiting for review, and the original still shows its 成片

