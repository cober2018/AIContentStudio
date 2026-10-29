## ADDED Requirements

### Requirement: Product workbench templates

The template library SHALL include 15 product-video templates (product-hero, product-angles, selling-points, check-list, spec-table, compare-table, dimension-mark, price-drop, deal-timer, layer-stack, use-steps, review-cards, cert-card, buy-cta, color-swatch), each with 9:16 and 16:9 projects inside the respective playback safe areas, plus documented reuse of callout-label for selling-point callouts and magnifier for ingredient close-ups. Their usage notes SHALL require real prices, offers, reviews, certificates, dimensions and specifications, keep product images undistorted, and avoid any platform's interface or logo.

#### Scenario: Price template
- **WHEN** price-drop is rendered with an original price and a real final price
- **THEN** the original price is struck through and the final price and saving tag appear, as a transparent overlay

#### Scenario: Product library group
- **WHEN** a user opens 设置 → AE 模板库
- **THEN** the product templates appear in their own group with 9:16 and 16:9 previews
