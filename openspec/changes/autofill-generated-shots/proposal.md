## Why

On U80, AI 补齐素材 left four of six rows as gaps:

- a deep-sea dive to the cable;
- a real cable cross-section next to a garden hose;
- a bare fibre next to a hair;
- a chat-UI transition.

Free stock does not have such specific pictures, and no template fitted. The user agreed to close these gaps with more AE templates and with generated pictures.

## What Changes

- Two new AE templates, each checked with two renders:
  - **对比卡 (compare-pair)**: two items side by side, each with a label and an optional image, plus one line saying what differs. For example "海缆 ≈ 浇花水管" or "光纤 ≈ 头发丝".
  - **图片推镜 (photo-push)**: one image with a slow push-in and an optional caption, which turns any still into a shot. A small 「AI 示意」 corner tag shows when the image is generated.
- AI 补齐素材 gains a last step, before a row is left as a gap:
  - for rows still empty, it generates one first-frame image with the platform's image generation, from the row's existing first-frame prompt;
  - it saves that image as an AI-generated project material;
  - it renders 图片推镜 with it, tagged 「AI 示意」.

  The row shows 「自动 · AI 示意图」.
- Templates with image slots can now be chosen automatically when the image comes from the row's own generated picture, so 对比卡 can also use two generated images.
- Rows that must prove something real (role 证明) still get the illustration, but it is always tagged 「AI 示意，非实拍」 and the slot says so. Real proof stays the user's own footage.
- Image generation is limited to at most 8 images per auto-fill run, and it is skipped when no image model is configured.

## Impact

- AE: two templates in the template library (`compare-pair`, `photo-push`) with manifests, previews and checks.
- API: an image step in `material_autofill.finish` that uses the existing image generation tasks and `craft_skills.render` with images. The template choice call also sees templates with image slots.
- Web: the 素材 column and the shot slot show the 「AI 示意」 source.
- Not in this change:
  - generated video, because Grok and Gemini web generation stays manual;
  - 3D renders;
  - a custom chat-UI animation.
