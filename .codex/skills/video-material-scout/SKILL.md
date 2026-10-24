---
name: video-material-scout
description: Find, verify, register and fit real material (footage, photos, music) for an AIContentStudio video or image-text piece, and rewrite the script when nothing suitable exists. Use while drafting a script or shot plan, when a beat lacks a visual or proof, or when review asks for real footage instead of illustrations.
---

# Video material scout

Script and material shape each other. Plan the story, look for what can show it, and change the recipe when the market has no potatoes: rewrite the beat to what real material can prove, or keep the beat and ask a person for the material. Never invent material, never pass an illustration off as real, and never widen the rights the user gave.

The platform owns materials, rights, revisions and project references. Follow [video-production-handoff](../video-production-handoff/SKILL.md) for platform calls and execution contracts. User authorization for any external download or use comes from the current task, never this Skill.

## When to search

- While drafting the script: right after the beat list exists, before polishing sentences.
- When a shot plan marks a gap, cites only AI illustrations for a factual claim, or holds one still longer than about 5 seconds.
- When review says the piece looks like slides, lacks proof, or needs real footage.
- Before AE/Resolve work: confirm every planned cut is registered and project-referenced.

## Where to look, in order

1. **Project and library material.** Read the project material catalog (planning stages receive it; local-only items are marked). Prefer exact revisions already referenced.
2. **Platform matching (through the creative MCP).** Call `start_material_match` with `scope: "script"` for a whole script, or `scope: "shots"` with `project_id`, `unit_id` and each shot's id, label and text. Send the user the returned `review_url`; the user picks ("用这个") or rejects ("都不合适" with a note) on the platform. Read the outcome with `get_material_match` (`wait_seconds` up to 25, call again while nothing changed): `chosen` is the accepted material revision, `rejected.note` is what to search for next. Never accept, download or bind on the user's behalf. Each segment lists own-library matches first, then Pixabay, Internet Archive, Wikimedia Commons (Openverse and NASA when reachable), with what the vision model saw, score and license. Segments marked `gap` carry a material request: rewrite the beat or ask for footage, never fill it with a loose match. Video candidates were judged on the poster frame only — the user checks the full clip.
3. **Primary sources of the subject.** The project homepage, README and docs images, the official repository, release pages, and the author's or company's own demo posts and videos. These usually hold the most convincing proof. Note the license of each item: a code license (for example MIT) does not by itself license videos or photos.
4. **Free or licensed libraries.** Stock sites with explicit reuse terms; record the license page and attribution.
5. **Platform generation.** Platform image generation for illustrations (always labelled as illustration), website video handoff for motion based on a chosen image.
6. **Human upload or shooting.** A structured request: what the shot must show, what it proves, framing, duration, acceptable sources.
7. **Code motion graphics.** Diagrams, keyword beats, comparisons and limits. Material only, never evidence of real behavior.

If a site asks for sign-in, captcha or bot verification, record the failure and move to the next source. Do not bypass protections or use the user's browser cookies without explicit permission.

## Verify before planning cuts

- Probe each file (duration, size, fps) and make timestamped contact sheets every 2–4 seconds. Write a footage log: time range, what is visible, what it can prove.
- Find the usable region in each frame. Mark crop-out zones: faces of people who did not consent to appear, burned-in captions, watermarks, "sped up" labels, private data.
- Check that the usable region does not move inside a planned in/out range (detect the card or subject box at several points). Choose ranges where it is stable.
- Check effective resolution after crop: if a crop needs more than about 2x upscale, use it as a smaller card instead of full frame.

## Register through the platform

- Upload with `POST /api/v1/materials/upload` including `source_kind` (`web_search` for online finds), `source_url`, `attribution_text`, `rights_status` (`restricted` for local-review-only authorizations, `licensed` for licensed items), `public_use_allowed`, and `model_use_allowed` (needed for AI planning and editing).
- Material the user keeps in a registered folder (for example an external drive) is linked in place, never uploaded: `GET /api/v1/material-sources`, scan with `GET /api/v1/material-sources/{id}/files?subpath=`, then `POST /api/v1/material-sources/{id}/links` with `relative_path`, `kind` and the same rights fields. If the file changed, link it again with `material_id` to create a new version. An unplugged drive reports `material_external_unavailable`; ask the user to connect it rather than looking for a substitute.
- Attach to the project with `POST /api/v1/content-projects/{project_id}/materials/references` and a note stating the authorization.
- Credit the source on screen for every footage cut and in end credits; keep local-only material out of anything public.

## Fit material and script together

For every beat choose one, and say which in the plan:

| Situation | Action |
|---|---|
| Real material shows the claim | Use it on that beat; the claim line is followed by the footage within about 1 second |
| Material shows something close | Rewrite the beat to what the material shows, without changing facts |
| Nothing exists but the beat is essential | Keep it with a structured material request and a temporary code motion graphic |
| Nothing exists and the beat is optional | Drop the beat; shorter is better than illustrated filler |

Record what was searched, where, what failed and why in the work's findings, so the next run starts from that list.
