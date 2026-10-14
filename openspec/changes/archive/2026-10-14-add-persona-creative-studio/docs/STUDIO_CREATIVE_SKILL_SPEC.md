# Studio Creative Skill Package Specification v1

This specification borrows the successful separation ideas seen in Easel Skills — small routing metadata, concise instructions, references loaded on demand, deterministic tools and continuous validation — while preserving AIContentStudio's stricter domain boundaries.

## Package layout

```
studio_skills/<skill-key>/
├── SKILL.md
├── STUDIO-CONTRACT.json
├── STUDIO-META.md
├── references/              optional
└── tests/                   fixtures/contracts, optional per skill
```

No package file is automatically executable code.

## SKILL.md

Frontmatter should be small and routing-oriented:

- `name`
- `description`
- `modality`: text / graphic / audio / video / general
- `purpose`

Body contains method steps, decision boundaries and when to read references. It should not duplicate long domain references or implementation source.

## STUDIO-CONTRACT.json

Machine truth:

- `key`, `version`
- `modality`, `purpose`
- `compatible_stage_schemas[]`
- `required_context[]`
- `input_schema_key`
- `output_schema_key`
- `tunable_fields{}`
- `defaults{}`
- `prompt_sections[]`
- `registered_tools[]` with exact key/version
- `compatible_style_presets[]`
- `compatible_quality_profiles[]`
- `max_context_bytes`, `max_output_bytes`

A UI control must map to a tunable field actually consumed by resolution/execution.

## STUDIO-META.md

Records:

- origin/provenance;
- self-developed vs adapted method vs referenced method vs vendored code;
- upstream project/paper/product links when relevant;
- license and notice obligations for copied/vendored code;
- implementation notes that should not enter prompts.

## References

References hold detailed method knowledge and are loaded only for a selected Skill. They are not global system prompt material.

## Deterministic tools

If a Skill needs deterministic code, the contract references an application-registered Tool/Rule/Provider. The Skill package does not cause arbitrary Python/shell execution.

Examples:

- `studio.graphic.layout-compose@1`
- `studio.graphic.qc@1`
- `studio.audio.qc@1`

## Validation

Repository validators must fail on:

- invalid/missing metadata/contract;
- broken reference paths;
- missing provenance;
- unknown registered tool/rule/version;
- unknown style/quality reference;
- Persona blueprint/default Recipe references to missing resources;
- declared tunable fields that are not consumed;
- credential-like values, signed URLs or local absolute paths in shipped resources.
