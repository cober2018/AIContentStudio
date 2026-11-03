## ADDED Requirements

### Requirement: Product pages accept several pasted info images

The product edit page SHALL let the user paste (⌘V) or pick several images at once as product info images, each with one of the product material categories (now including certificate), shown as removable thumbnails and saved with the product revision. Certificate SHALL be an accepted product material category.

#### Scenario: Paste a certificate
- **WHEN** the user pastes three images, marks one as 证书 and saves
- **THEN** the new product revision holds the three images with their categories

### Requirement: The video brief carries the product's info images

A product work's video brief SHALL list the info images of the product's newest revision with their categories, and the rules SHALL tell the third-party model to put certificate and specification images on matching shots as they are, never generated or altered.

#### Scenario: Image added after the work started
- **WHEN** the user adds a certificate image to a product that already has a work
- **THEN** that work's next video brief lists the certificate image
