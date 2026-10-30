## ADDED Requirements

### Requirement: Reference video breakdown

A work SHALL accept a reference video and produce, locally and without paid models, a word-timed transcript, cut points, per-segment frame grids and loudness. A third-party model SHALL turn them into a whole-piece analysis, a timeline, a draft director document and a shooting list. Brand claims seen in the reference SHALL be recorded as needing the brand's real material.

#### Scenario: Break down the biscuit reference
- **WHEN** the user attaches the 30-second biscuit video to a product work and runs the breakdown
- **THEN** the work shows the timeline, a director draft for its own product, and a shooting list of the child-eating shots to film

### Requirement: Video prompt direction

Video prompts for shots with people SHALL lead with the person's attitude and address when the shot gives one, then a few decisive reactions; still-image prompts SHALL follow capture / person / action-and-camera / setting; each input SHALL carry one responsibility.

#### Scenario: Child tasting shot
- **WHEN** a shot has attitude 第一次吃到自己能吃的零食，又惊又喜
- **THEN** its video prompt begins with that attitude before camera and look

### Requirement: Storyboard grid

The user MAY generate one 3×3 grid image for up to nine people / scene shots so that person, clothing, place and light stay consistent; the platform SHALL cut it into per-shot first-frame candidates, upscale them, and let each be redrawn alone. Product close-ups SHALL be excluded.

#### Scenario: Six people shots
- **WHEN** the user generates a grid for six shots
- **THEN** six first-frame candidates appear on their shots, none adopted until the user picks them
