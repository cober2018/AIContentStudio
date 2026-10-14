# Current System vs. Persona-native Out-of-box Studio

| Area | Current system | Gap closed by this change |
|---|---|---|
| Identity | Brand constraints plus Persona → Account → Series revisions and frozen IdentitySnapshot | Add typed media creative profiles and Persona-native defaults; Brand is not a creative-profile source |
| Workflow | Series/Account/Persona defaults, Project override, Creation Recipe, attempts/feedback | Ship persona-specific default recipes and intermediate creative stages |
| Stage control | Prompt/model/method preview, run override, receipts | Resolve Studio Skill + Style + Quality + Persona profile as first-class inputs |
| Built-in creative methods | Generic stage instructions; legacy local writing helpers; external skills inventory | Product-owned Studio Creative Skill Pack with contracts/references/provenance |
| Styles | `expression_style`, `visual_language`, Brand Voice; no formal media preset catalog | Versioned Text/Graphic/Audio Style Presets selected by Persona |
| Learning | Capability Memory scopes include persona/account/series | Keep learning Persona-scoped and allow explicit composed method stacks |
| Text | Canonical text.master.v2 proposal/adoption and checks | High-quality default methods, technical/lifestyle recipes and quality profiles |
| Graphic | graphic.master.v2, local renderer, media generation | Semantic visual/card plan + deterministic layout composer + Graphic QC |
| Audio | TTS ProviderGenerationTask → MaterialRevision | Spoken adaptation + voice direction + TTS + Audio QC and persona defaults |
| Video | video.master.v2, Director Package, CreativeExecution | Persona script/shot/director methods; final editing remains external Agent |
| Auto config | Global provider/model routing exists | Persona-aware Auto/Custom/Composed method configuration and readiness |
| Quality proof | Contract/browser tests; no fixed shipped creative benchmark | Deterministic gates + real-provider artifact rubric for both starter personas |
| Skill drift | Stage consumed-field checks exist in places | Persistent Studio Skill/reference/tool/blueprint validators inspired by Easel |
| Multiplatform | Separate 12-platform/17-form proposal | Consume same `stage.variant.adapt@1`; no new per-persona channel engine |

## Core conclusion

AIContentStudio already owns the hard business truth. The missing middle is a Persona-native creative method layer that makes those truths immediately useful.

This change deliberately reuses existing Identity, Workflow, Stage receipt, Capability Memory, Master, Material and Review/Delivery objects. The expected implementation is large in behavior but small in new persistence concepts.
