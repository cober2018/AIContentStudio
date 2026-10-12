## ADDED Requirements

### Requirement: Persona auto configuration reuses executable capability routing

Persona creative auto mode SHALL use the existing deterministic executable model/capability route truth and its limits. It MUST NOT scan unrelated providers or infer capability from model branding. Preview SHALL show the exact selected route and why it is usable.

#### Scenario: Persona Graphic needs image generation
- **WHEN** the selected Graphic style requires generated imagery and no executable image route exists
- **THEN** readiness reports partial/blocked according to the declared typography-only fallback rather than pretending the chat model can generate images

### Requirement: Explicit Persona model preference is a pin

Custom creative profiles MAY pin an exact registered model profile for a purpose. If unavailable, execution blocks unless the stored fallback policy explicitly permits ordinary authorized routing. Historical receipts retain the original route identity.

#### Scenario: Pinned TTS profile disabled
- **WHEN** the Persona audio profile pins a TTS profile that becomes disabled
- **THEN** Audio readiness blocks or uses only its explicitly allowed fallback; it never silently changes voice/provider without disclosure
