# AIContentStudio Persona Creative Studio — OpenSpec package

Change: `add-persona-creative-studio`

This change closes the gap between “controllable workflow” and “out-of-box high-quality creation.”

It establishes:

- Persona-native creative defaults instead of User-global style;
- two starter personas: AI科技研发技术博主 and 日常生活方式博主;
- product-owned Studio Creative Skills inspired by Easel's Skill engineering pattern;
- versioned Text/Graphic/Audio style presets and quality profiles;
- Auto / Custom / Composed method configuration;
- intermediate creative stages and thin exact stage handoff;
- real rendered Graphic and playable Audio production loops;
- deterministic quality gates plus real-provider human-rubric acceptance;
- external professional Agent handoff for final video production.

Core truth boundaries remain:

- Identity = who this Persona is and its creative defaults;
- Workflow/Creation Recipe = execution order;
- Studio Skill Pack = product-owned methods;
- Capability Memory = learned/custom reusable methods;
- Provider/Model/Tool = executor;
- Master/Material/Variant/CreativeExecution = authoritative results;
- Candidate/Review/Delivery = final decision and distribution.

The design targets zero new business tables/migrations.

The separate `complete-multiplatform-content-handoff` change remains complementary and must fix two prior review items before apply: use existing `stage.variant.adapt@1`, and permit small parameterized persistent tests rather than forbidding new tests.
