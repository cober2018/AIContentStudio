## ADDED Requirements

### Requirement: Adopting a cut keeps model use when only public use is blocked

When the user approves a 小样 or 成片, the platform SHALL accept each output as public and model-usable when every input allows it; when public use is refused but every input allows model use, it SHALL accept the output as model-usable and not public; only when model use is refused too SHALL both be off.

#### Scenario: One input cannot be public
- **WHEN** a 小样 uses an AE render of a logo that is model-usable but not public
- **THEN** the accepted 小样 is model-usable and not public, and the 成片 task can be opened on it

### Requirement: A rights refusal names the shot and the upstream material

When opening an edit task is refused with `video_asset_kind_or_rights_invalid` for rights, the error SHALL carry a message naming the material, the shot that uses it when known, the upstream material that is not public or not model-usable (followed through execution inputs and AE render image sources), and what to do; the MCP SHALL pass the message to the model.

#### Scenario: Blocked by a logo two steps up
- **WHEN** the 成片 is opened on a 小样 whose 关注卡 render used a non-public logo
- **THEN** the message names the 小样, the shot with the 关注卡, the render and the logo, and says to make the logo public, re-render and redo the 小样
