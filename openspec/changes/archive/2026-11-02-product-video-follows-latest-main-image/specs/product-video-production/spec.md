## ADDED Requirements

### Requirement: Product works use the product's latest main image

For product video works, shot still generation, the product consistency check, image-to-video reference images and the brief SHALL use the main image of the product's latest revision that has one, while product facts stay frozen at the revision the work started with. A product reference image chosen on the work itself SHALL take precedence. Already generated stills and videos SHALL NOT change.

#### Scenario: Main image replaced after the work started
- **WHEN** work 90 started on product 8 revision 1 (main image 315) and the product is now at revision 3 (main image 319)
- **THEN** the next shot still, consistency check and image-to-video request for work 90 use image 319

#### Scenario: Manually chosen product reference
- **WHEN** a work has its own product reference image set
- **THEN** that image is used, not the product's latest main image
