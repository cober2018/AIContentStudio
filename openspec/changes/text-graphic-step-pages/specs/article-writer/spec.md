## ADDED Requirements

### Requirement: Text and graphic works show one step per page
A persona text work SHALL show the steps 选题与资料, 稿子 and 交付; a persona graphic work SHALL show 选题与资料, 稿子, 成图 and 交付. Each step SHALL show only its own content, and a step not yet reached SHALL say so with a link to the current step. The former 制作内容 and 审阅修改 steps, the master editor and the bottom advanced block SHALL NOT appear on these works.

#### Scenario: Graphic work waiting for its images to be checked
- **WHEN** the user opens a graphic work whose rendered images wait for acceptance
- **THEN** the page lands on 成图, which shows each image in order with 验收通过 and 按意见修改

#### Scenario: Old step links
- **WHEN** a link asks for workstep make or review on a text or graphic work
- **THEN** the page opens the step the work is currently at

### Requirement: Platform-written pieces join the same approval chain
A text or graphic piece written by the platform model SHALL wait at 稿件待你看 once its stage master is adopted, and SHALL then follow the same 采用, render, acceptance and sending steps as a third-party-written piece.

#### Scenario: Approve a platform-written graphic piece
- **WHEN** the platform creation flow adopts a graphic master and the user clicks 采用
- **THEN** the platform renders the canvases and the work waits at 成图 for acceptance

## REMOVED Requirements

### Requirement: Manual per-canvas render workbench
**Reason**: Rendering is done automatically after 采用; the per-canvas render, accept and bind workbench and its two endpoints are no longer used.
**Migration**: None; the product has not launched.
