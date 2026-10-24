## ADDED Requirements

### Requirement: The director draft keeps the accepted shot plan's shots

When a video director-draft stage has an accepted shot plan upstream, each generated draft SHALL contain exactly the plan's shots, with the same number, order and ids. Each shot's duration SHALL come from the plan. The model SHALL only write each shot's final narration and visual description.

#### Scenario: Fifteen planned shots
- **WHEN** the accepted shot plan has 15 shots and the director draft is generated
- **THEN** every candidate has 15 shots with the plan's ids in the plan's order

#### Scenario: Model returns the wrong number of beats
- **WHEN** the model returns a number of beats different from the plan
- **THEN** the attempt fails as invalid output, nothing is trimmed or padded, and the user can generate again

#### Scenario: No shot plan
- **WHEN** the director-draft stage has no accepted shot plan upstream
- **THEN** the draft is built as before, with at most 8 beats

### Requirement: The request states the plan

The director-draft request SHALL tell the model the exact number of beats and that it must keep one beat per accepted shot, in order, without merging, splitting, adding or dropping shots. The request preview SHALL show this.

#### Scenario: Preview before generating
- **WHEN** the user previews the director-draft request with a 15-shot plan accepted
- **THEN** the preview's stage rules say to return exactly 15 beats in the plan's order

### Requirement: Shot slot material lines up after the draft

Shot slots SHALL keep their material when a director draft built from the plan is accepted, because draft shot ids equal plan shot ids.

#### Scenario: Accepting the draft on U80
- **WHEN** the user accepts a director draft built from the 15-shot plan
- **THEN** all 15 shot slots still show their chosen material
