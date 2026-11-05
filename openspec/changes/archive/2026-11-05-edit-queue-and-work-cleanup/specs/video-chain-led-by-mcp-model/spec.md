## ADDED Requirements

### Requirement: One DaVinci edit at a time

The platform SHALL let only one video edit task (executor `codex-video-production`) be worked at a time across all works. A claim SHALL be refused with `video_edit_queue_busy` while another work's edit task is claimed, in progress or blocked and has had activity (a state change, a progress report or a submitted file) within the last 30 minutes. The refusal SHALL name the work being edited and how many other edit tasks are waiting, and tell the model to try again later. An edit task SHALL stop holding the slot once it reaches result_ready or any later state, or after 30 minutes without activity; the timeout SHALL NOT change that task's state.

#### Scenario: Second work waits
- **WHEN** the model claims work B's edit task while work A's edit task is in progress with a progress report 5 minutes ago
- **THEN** the claim is refused with `video_edit_queue_busy` naming work A, and work B's task stays prepared

#### Scenario: Slot frees on hand-in
- **WHEN** work A's edit task reaches result_ready and the model claims work B's edit task again
- **THEN** the claim succeeds

#### Scenario: Abandoned session
- **WHEN** work A's edit task has had no activity for more than 30 minutes and the model claims work B's edit task
- **THEN** the claim succeeds and work A's task keeps its state

### Requirement: Edit work files on the drive are kept

The platform SHALL NOT delete files in a work's `工作/` folder when a newer 小样 is returned or when the 成片 is approved; renders, AE shots, images and project files there stay.

#### Scenario: 成片 approved
- **WHEN** the user approves a work's 成片 while earlier task folders hold unregistered renders
- **THEN** every file in the work's `工作/` folder is still there

### Requirement: One Resolve project per work

The edit instructions SHALL tell the model to delete the `-reopen` Resolve project right after the reopen check, and, when it starts a new edit task of a work, to delete that work's Resolve projects from earlier tasks, whose exported .drp files stay on the drive.

#### Scenario: Third task of a work
- **WHEN** the model starts task 47 of a work whose tasks 43 to 46 left Resolve projects
- **THEN** after the reopen check only that work's task 47 project remains in the Resolve project list
