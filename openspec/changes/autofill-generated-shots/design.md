## Context

- Auto-fill (`material_autofill.finish`) accepts eligible stock, then asks a model to pick ready templates without image slots for motion and gap rows. Rows left over become gaps with reasons.
- Each search segment already carries `frame_prompt` (a first-frame image prompt with the frame, subject, light, style and a caption-safe lower third).
- The platform has image generation tasks (`generation_tasks.prepare`, execute and accept) that write AI-generated materials with provenance.
- `craft_skills.render` already accepts `images: {slot: material_revision_id}` and converts each to the PNG the template expects.

## Decisions

1. **Templates.** Built with `make_templates.py` in the same data-in-expressions style.
   - `photo-push`: `@image` cover-fit with a slow 100→108% push over the shot, plus an optional caption in the lower third and an optional corner tag.
   - `compare-pair`: two framed panels (`left_image`, `right_image`, both optional), `left_label`, `right_label`, and a `note` line. Panels without an image show their label large.

   Each template gets two checked renders before it is ready.
2. **Image step.** For each row still a gap after the template step, up to 8 per run:
   - prepare and run an image generation task with the row's `frame_prompt`, aspect 9:16;
   - accept it as project material with `ai_generated` provenance;
   - render `photo-push` with that image, the row's 信息点 as caption and the corner tag 「AI 示意」;
   - attach it with `record_attach`, with auto source `ai_image`.

   A failure, or no image model, leaves the gap and adds the reason.
3. **Templates with images in the choice call.** Image slots are offered to the model as "will be filled with a generated picture of: <describe>". The model returns a short description per image slot. The image step generates those pictures and renders. Templates that need a real map (`map-route`) stay manual.
4. **Proof rows.** When the segment role is `proof`, the corner tag reads 「AI 示意，非实拍」 and the auto reason says real footage is still needed.

## Risks

- Image cost and time: about 10–30 s per image, capped at 8 per run.
- An illustration could be taken for evidence. The tag sits in the picture itself, not only in the platform.
