## ADDED Requirements

### Requirement: Card text scales to fill the canvas
The deterministic card layout tool SHALL choose, for each card, the largest uniform text scale between the density base sizes (1×) and the size caps. At that scale the estimated stack of title, visual, body, bullets and diagram labels SHALL fit within 90% of the safe area height. At medium density the caps are: cover title 120px, body-card title 84px, body and bullets 56px, diagram labels 40px; at low and high density the caps are multiplied by the density's body base size divided by 34, so density still changes short cards. Text SHALL never be smaller than the density base sizes.

#### Scenario: Short cover fills the canvas
- **WHEN** a 3:4 cover card has an 18-character title and a one-line body
- **THEN** the title is rendered larger than 60px, and the content block is placed in the vertical middle region of the canvas rather than at the top

#### Scenario: Dense card keeps base sizes
- **WHEN** a card's content only fits at the density base sizes
- **THEN** the tool uses the base sizes, and the overflow and geometry checks behave as before

#### Scenario: Overflow still blocks
- **WHEN** a card's content does not fit even at base sizes
- **THEN** composition fails with `graphic_composition_text_overflow`

### Requirement: Content block is vertically placed
The layout tool SHALL position the whole content block (accent bar through last bullet) so that the space above it is 45% of the free vertical space in the safe area. Title box height SHALL use the title's estimated line count instead of a fixed two lines.

#### Scenario: Free space split
- **WHEN** a card's content block is 600px tall in a 1296px safe area
- **THEN** the block starts 313px below the top margin
