## ADDED Requirements

### Requirement: Tech-style points and summary templates at 60 fps

The template library SHALL provide two full-frame tech-style templates, `tech-points` (a heading and one to five numbered points revealed in turn) and `tech-summary` (one large metallic line, a divider and one or two lines of explanation), each in 9:16 and 16:9 with the same fields, rendered at 60 frames per second. They SHALL carry no third-party brand marks. Existing templates SHALL keep their frame rate.

#### Scenario: Four points
- **WHEN** the model renders `tech-points` with a heading and four points
- **THEN** a 60 fps .mp4 shows the heading and four numbered cards revealed in turn, inside the safe area of the chosen aspect

#### Scenario: Existing template unchanged
- **WHEN** any existing template is rebuilt
- **THEN** its composition is still 30 fps
