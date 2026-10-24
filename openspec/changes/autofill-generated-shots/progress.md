# Progress

## 2026-10-23
- Proposal written. No code changed.
- Applied (user confirmed):
  - Templates `photo-push` and `compare-pair` built with `make_templates.py`; manifests with image slots (`source: any`); map-route image slot marked `real_only`; two checked renders each (photo-push: engraving + caption; archive photo + 「AI 示意，非实拍」 tag; compare-pair: labels only; two photos + labels); previews saved; ae-motion index updated.
  - `craft_skills.render`: required image check; passes `_images` (supplied slots) into the data so panels switch between picture and label.
  - Auto-fill: templates with generated-image slots are offered; the choice call returns picture descriptions and a caption; a still-empty row falls back to a generated first-frame picture + photo-push with 「AI 示意」 (proof rows 「AI 示意，非实拍」 and a reason asking for real footage); at most 8 images per run, using the user's last accepted image route; uncertain image sends are never repeated; a failed template choice is written into the row reason and captions fall back to the row's 信息点.
  - Web: `ai_image` source shown.
- Verify on a DB copy (U80, real models):
  - Run 13 (app not started): the own-library pick path worked — shot-1 got an own image of a cable on the seabed (eligible). Image step failed with `adapter_not_loaded` because the script skipped app startup.
  - Run 14 (app started): all three remaining gaps filled with generated pictures + photo-push; tags correct (shot-0 「AI 示意」, proof rows shot-4/5 「AI 示意，非实拍」); 15/15 chosen; earlier picks untouched; master unchanged.
  - But every material-model call failed in run 14 (`provider_request_failed` on the material route gemini-3.8-flash-high via a registered profile; the live API fails the same way now). So the template choice did not run: no captions on those three shots and compare-pair was not tried. Fixed afterwards: caption falls back to 信息点 and the failure is written into the row reason. Not re-run, because the model route is still down.
- API suite: only the 7 pre-existing failures. Web build passes. API restarted while idle.
- After the user restored the material model route (probe ok), re-verified on the DB copy:
  - Run 15: shot-0 → generated picture + photo-push with caption 「手机聊天发送消息并下沉穿入水面」 and 「AI 示意」; shot-4 and shot-5 → compare-pair with two generated pictures each, labels and note. But compare-pair v1 had no tag slot, so the proof rows' frames lacked 「AI 示意，非实拍」 — a defect against the spec.
  - Fix: compare-pair v2 with a corner tag (v1 kept, no longer offered automatically: only the newest ready version is offered); two checked renders; auto-fill sets the tag on any template with a tag field whenever a generated picture is used, and clears it otherwise.
  - Run 16 exposed a second defect: the earlier generated comparison clips were now in the own library, scored as real proof (“完美呼应文案论据”) and auto-picked as stock. Fix: the own pool marks AI pictures and clips rendered from them as `illustration`, and auto-fill never auto-picks an illustration (the user still can by hand).
  - Run 17: shot-4 and shot-5 → compare-pair v2 with generated pictures, labels, notes and the in-frame tag 「AI 示意，非实拍」; 15/15 chosen; earlier picks untouched; master unchanged.
- API suite: only the 7 pre-existing failures. API restarted while idle.
