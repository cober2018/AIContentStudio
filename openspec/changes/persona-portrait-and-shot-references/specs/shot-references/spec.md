## ADDED Requirements

### Requirement: Persona portrait

A persona MAY carry one to three real portrait photos, set at creation or later, used as the person reference for generated pictures of its works.

### Requirement: Automatic references for generated shots

When a shot has no supplied material, generated pictures SHALL use the product's primary image for the product and the persona's portrait for people. Every generated picture showing the product SHALL be checked against the primary image and redrawn alone if it fails. Without a portrait, generated pictures SHALL show no person except hands handling the product.

#### Scenario: Persona with portrait
- **WHEN** a work under a persona with a portrait generates its storyboard grid
- **THEN** the cells show that person and the product matches its primary image

#### Scenario: No portrait
- **WHEN** the persona has no portrait
- **THEN** generated cells show only the product and the scene, and the page says those people shots will have no person
