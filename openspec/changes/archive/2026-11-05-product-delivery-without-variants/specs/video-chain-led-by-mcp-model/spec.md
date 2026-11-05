## ADDED Requirements

### Requirement: Product delivery step has no channel variants

The 交付 step of a product video SHALL show the publish copy beside the cover and SHALL NOT show the channel variant panel; its hint SHALL speak of checking the cut, cover and publish copy rather than channel adaptation. Other work types SHALL keep their delivery step as before.

#### Scenario: Product work at delivery
- **WHEN** the user opens 交付 of a product video
- **THEN** the publish copy is shown and no 渠道变体 panel appears

#### Scenario: Other work at delivery
- **WHEN** the user opens 交付 of a non-product work
- **THEN** the 渠道变体 panel is shown as before
