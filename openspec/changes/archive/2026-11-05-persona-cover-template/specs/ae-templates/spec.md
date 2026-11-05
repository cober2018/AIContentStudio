## ADDED Requirements

### Requirement: A persona cover template in the library

The AE template library SHALL include a cover template with `category: "封面"` that renders a transparent text layer in 9:16 and 16:9 with fields 大标题, 副标题 and 卖点 1–3: a white title with a thick yellow stroke, a thin right-aligned subtitle with a yellow stroke, and three yellow selling-point lines with a red offset shadow, a thick white stroke and a yellow check mark before each. It SHALL have no background image field, since the cover background is the finished film's opening frame. It SHALL become ready only after the user has seen two renders with different content over real product footage.

#### Scenario: Cover template listed
- **WHEN** templates are listed
- **THEN** the cover template appears with category 封面 and fields title, sub, p1, p2, p3 and no image slot
