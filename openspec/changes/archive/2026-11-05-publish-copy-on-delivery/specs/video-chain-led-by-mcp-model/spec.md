## ADDED Requirements

### Requirement: Product publish copy lives on the delivery step

For product videos, the publish copy (title, hashtags, cover text, interaction, description) SHALL be edited and saved on the 交付 step, above channel adaptation and beside the work's current cover, through the existing publish-copy API; the 导演稿 step SHALL no longer show it. Without saved copy the page SHALL say the model writes one at finalising and the user may fill it first.

#### Scenario: Copy found after finalising
- **WHEN** the 成片 is approved and the user opens 交付
- **THEN** the five publish copy fields are shown with the work's cover beside them and can be edited and saved

#### Scenario: Not on the 导演稿 step
- **WHEN** the user opens the 导演稿 step of a product video
- **THEN** no publish copy block is shown
