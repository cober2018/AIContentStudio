## ADDED Requirements

### Requirement: Deals move through a recorded pipeline

A brand deal SHALL record its stage (enquiry, quoted, briefed, contracted, registered, script review, production, final review, published, reported, paid, closed), each change with time and actor, and SHALL link to the project that produces its works.

#### Scenario: From enquiry to project
- **WHEN** the user accepts a brief for a quoted deal
- **THEN** the deal links a project whose brief and fact boundary carry the brand's claims marked as brand-provided

### Requirement: Brand-sponsored works are checked before review

Works in a deal SHALL pass the ad-law rule check and carry the required sponsorship label, and SHALL warn when the platform order number is missing, before they can be approved for delivery.

#### Scenario: Absolute claim in script
- **WHEN** a script says a product is "全网最好"
- **THEN** the check flags the phrase and approval is blocked until it is changed or the user records why it is acceptable
