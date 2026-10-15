## MODIFIED Requirements

### Requirement: Registered CPA image execution uses an exact image protocol

Gemini/Grok image execution through CPA SHALL reuse existing registered provider/model/profile credentials and explicitly trusted endpoint configuration. It MUST NOT require unrelated official-provider credentials, infer image capability from a chat model name, probe alternate endpoints or create a second provider configuration truth. The media adapter SHALL declare and freeze its versioned request/response protocol, exact model, supported parameters, MIME/byte constraints and native-count or explicitly authorized fan-out behavior. The protocol SHALL be explicit per operation: a gateway-compatible Grok OpenAI images operation and a gateway-native Gemini generateContent image operation MUST NOT be conflated. Existing V1 tasks SHALL retain their frozen protocol and history; a newly selected protocol requires a new prepared task and explicit current configuration. Effective Preview SHALL expose the server-built safe prompt and exact binding without provider I/O.

Execution SHALL consume that frozen contract and normalize actual image bytes into the same ProviderGenerationTask candidate and explicit MaterialRevision acceptance contracts used by MiniMax. Only bounded validated PNG/JPEG/WebP bytes count as success; returned prose, URLs or an available chat route do not. Unknown execution MUST NOT automatically retry or switch provider/model/protocol. Provider errors and credentials MUST NOT leak into previews, receipts or materials. Confirmed HTTP rejection SHALL expose only a bounded fixed safe status/reason and become a terminal failed or unavailable outcome; a transport exception or uncertain dispatch SHALL remain unknown. A rejected model-operation pair MUST NOT cause automatic protocol or model discovery. No new business table or migration SHALL be introduced for this adapter.

#### Scenario: Registered Gemini chat is not an image binding
- **WHEN** an enabled registered Gemini model can chat but has no implemented exact image protocol
- **THEN** image preview reports unavailable with a safe reason and execution neither calls chat as an assumed image endpoint nor silently chooses another model

#### Scenario: CPA image candidates use the existing acceptance truth
- **WHEN** an explicitly selected executable CPA image binding returns the exact declared candidate count as valid image bytes
- **THEN** the candidates retain exact configuration/runtime/output hashes and explicit selection accepts only the chosen image into MaterialRevision without modifying Master or Variant

#### Scenario: Possible image dispatch cannot trigger protocol discovery
- **WHEN** a CPA image request times out or its external outcome is unknown
- **THEN** the original task remains uncertain and no alternate protocol, model or provider is tried automatically

#### Scenario: Gemini model is rejected by the OpenAI images route
- **WHEN** the gateway confirms HTTP400 that a selected Gemini image model is unsupported on the frozen OpenAI images endpoint
- **THEN** the operation exposes a safe protocol-mismatch rejection without raw provider diagnostics, does not describe the model as incapable of images, and does not automatically resend through another protocol

#### Scenario: A new Gemini native protocol is explicitly selected
- **WHEN** an admin saves the confirmed native image protocol for the registered Gemini profile with the current configuration revision
- **THEN** a new task freezes that exact protocol and uses actual decoded images through the same candidate acceptance service while old tasks remain immutable

#### Scenario: A native Gemini landscape image has model-specific dimensions
- **WHEN** the configured gemini-3.1-flash-image V2 operation returns its native 1K landscape image within the frozen pixel budget
- **THEN** validation uses that exact model-native geometry rather than the legacy locally calculated size, while retaining actual pixel/byte limits and the legacy adapter geometry rules
