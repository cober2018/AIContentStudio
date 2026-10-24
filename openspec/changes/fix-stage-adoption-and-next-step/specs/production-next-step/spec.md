## ADDED Requirements

### Requirement: Adding material does not invalidate a waiting result

A stage result that is waiting for the user's decision SHALL remain acceptable when the only changes since generation are to the project's shared materials, provided every material the result cites is still usable in the project.

#### Scenario: Shot plan after filling slots
- **WHEN** the user uploads material into shot slots after the shot plan was generated and then accepts the plan
- **THEN** the plan is accepted and no `stage_adoption_context_changed` error is raised

#### Scenario: Cited material no longer usable
- **WHEN** a waiting result cites a material that has since been revoked, archived or had model use withdrawn
- **THEN** acceptance is refused with a plain-language reason

### Requirement: Restarting the platform does not invalidate a waiting result

A waiting result SHALL remain acceptable after the API restarts, when the model's profile, provider, model and configuration revision are unchanged. A real change to any of these SHALL still require regenerating.

#### Scenario: API restarted
- **WHEN** the API restarts between generation and acceptance and the model settings are unchanged
- **THEN** the result is accepted

#### Scenario: Model settings changed
- **WHEN** the stage's model configuration revision changed after generation
- **THEN** acceptance is refused with a plain-language reason naming the model settings and pointing to the stage's regenerate button

### Requirement: Real input changes still require regenerating

Acceptance SHALL be refused when an input the result was based on changed: upstream accepted results, fact boundary, current master, stage method or settings.

#### Scenario: Script changed
- **WHEN** a different script was accepted after the shot plan was generated
- **THEN** accepting the old shot plan is refused with a plain-language reason and a regenerate action

### Requirement: The production page shows the next step

The content production page's left step navigation SHALL list the workflow stages as sub-steps under the planning step (内容方案 / 导演方案), each with a plain-language status (已采用, AI 正在做, 等你确认, 需要处理, 可以开始, 等前一步). The stage that needs the user next SHALL be highlighted, and clicking a sub-step SHALL go to that stage, opening its result when it is waiting for a decision. There SHALL be no separate next-step card.

#### Scenario: Shot plan waiting
- **WHEN** the shots stage is waiting for the user's decision
- **THEN** the 镜头计划 sub-step is highlighted with 等你确认, and clicking it opens the shot-plan candidates

#### Scenario: Everything done
- **WHEN** all stages are accepted
- **THEN** every sub-step shows 已采用 and none is highlighted

### Requirement: Stage errors are shown in plain words

Errors from stage actions on the production page SHALL be shown as plain-language text with the action to take. Unknown codes SHALL show a generic message that keeps the code visible.

#### Scenario: Context changed
- **WHEN** accepting fails because the script changed
- **THEN** the page shows what changed and points to the stage's 「再次生成（新尝试）」 button, instead of a bare code

### Requirement: The user can give up an unknown attempt

When a stage's latest attempt is unknown, the user SHALL be able to give it up explicitly, after a warning that the request may already have reached the model. The stage can then be generated again. The attempt SHALL stay recorded as unknown with who gave it up and when. The platform SHALL NOT resend on its own.

#### Scenario: Director draft stuck as unknown
- **WHEN** the user confirms 放弃这次结果 on a stage whose latest attempt is unknown
- **THEN** the stage can be previewed and generated again, and the original attempt keeps its unknown record

#### Scenario: Only the current unknown attempt
- **WHEN** the attempt is not unknown or is not the stage's current attempt
- **THEN** the request is refused

### Requirement: A failure the provider answered is a failure, not unknown

When the model provider answered a stage call with an error or an unusable body, the attempt SHALL be recorded as failed, with the provider's reason and HTTP status, and SHALL allow a new attempt. Only failures where the request may still be in flight SHALL be recorded as unknown.

#### Scenario: Provider rejects the request
- **WHEN** the provider returns a non-200 answer to a stage call
- **THEN** the attempt is failed with `stage_provider_rejected`, the receipt records the reason and status, and the stage can be run again
