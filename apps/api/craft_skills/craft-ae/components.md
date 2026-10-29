# Motion toolkit for vertical explainers

A fixed visual system, so each film changes data, not design. Values are defaults that worked on a 1080×1920, 30 fps explainer (2026-10-21, P39 execution 5); change tokens for another persona style, not the layout logic.

## Layout zones (1080×1920)

| Zone | Default | Use |
|---|---|---|
| Headline | y 330, 74 px bold, accent bar 140×8 below | One short claim per shot; auto-fit to width − 120 |
| Card | centre (540, 900), max 980×1060, radius 34 | Real footage or photo, never stretched |
| Credit line | 44 px under the card, 26 px grey | Source of every footage cut |
| Chips | below the card, above captions (about y 1200–1340) | Annotations that appear at cue times |
| Captions | y 1420, 48 px medium on a dark rounded box | Burned subtitles from the accepted spoken script |

Text and key content stay inside the playback safe area in `safe-zones/` (9:16: x 59–1016, y 268–1482, right edge 886 for y 769–1482). Backgrounds may bleed.

## Components

| Component | What it does | When to use | Avoid |
|---|---|---|---|
| Footage card | Rounded window with shadow and a thin edge; source cropped to its usable region; scale-in 95→100% in 0.35 s, slow push 100→104% over the cut | Any real footage or photo | Full-frame upscales over about 2x |
| Blurred same-source background | Same footage, cover-scaled, Gaussian blur 70, dimmed 55–72% | Behind every card; alone (mode `bg`) behind graphics-only beats | Unrelated stock backgrounds |
| Headline + accent bar | Slide up 28 px and fade in 0.4 s; bar grows 0.3–0.8 s | Every shot | More than one line of headline |
| Chip | Rounded label, navy fill with accent stroke (or accent fill for the key point); rises 30 px in 0.4 s at its cue | Naming parts, steps, limits at the moment narration says them | More than three per shot |
| Keyword stack | Big words pop in sequence (60→106→100%) 0.38 s apart, one accent word | "It has three parts" style beats | Long phrases |
| Statement | One to three large lines fading in at set times | A key number or rule | Paragraphs |
| Struck icon | Simple line icon with an alert-colour strike drawn by trim path | "No X needed" beats | Brand logos |
| Phone pair | Two phone outlines; the right one turns black with an alert label | Before/after or "is not mirrored / not visible" | Fake app UI |
| Highlight ring | Accent ellipse placed by source pixel coordinates on a card | Pointing at a label inside real footage or a diagram | Covering the thing it points to |
| End card | Scrim, question lines, credits, fade to black over the last 0.6 s | Closing beat | Calls to action not in the brief |

## Timing rules

- Shot 2–5 s; a still at most about 5 s; alternate card, close crop and graphic beats.
- Headline in by 0.5 s; chips appear on the narration word they name (take the time from the ASR-aligned cues), never earlier.
- Captions follow the cue times exactly; they are not re-timed to shot cuts.

## Builder spec (`scripts/ae_build.py`)

`python3 scripts/ae_build.py spec.json --run` writes `work/build_comps.jsx` and runs it in After Effects, saving `ae/<project_name>`.

Top level: `work_root`, `project_name`, optional `tokens` (overrides the defaults above: colours as [r,g,b] 0–1, fonts, zones), `comps`.

Each comp: `id`, `role` (for example `ae_intermediate_3`), `duration` (seconds), `title`, `mode` (`card` or `bg`), `cuts`, optional `components`, `chips`, `captions`.

- cut: `id`, `file` (an `inputs/` path), `video` (bool), `t0`/`t1` (comp seconds), `trim` (source seconds at t0), `crop` [x0,y0,x1,y1] source pixels, `credit` (text or null), optional `framing` and `camera`.
- `framing` follows the storyboard 景别: `medium` (default) is the footage card; `close` and `wide` fill the frame with the crop (close = tight crop on the subject, wide = the whole frame), with a top scrim for the headline.
- `camera` follows the storyboard 运镜: `push_in` (default), `pull_out`, `pan`, `follow`, `orbit`, `fixed`. Never use the same footage frame in two shots; take a different crop or a graphic beat instead.
- component: `type` plus fields: `keyword_stack` (`words`, `accent_index`, `y0`, `step`); `statement` (`lines` of `text`,`size`,`y`,`at`,`accent`); `struck_icon` (`y`, `strike_at`); `phone_pair` (`y`, `labels`, `content`, `after`, `change_at`); `highlight_ring` (`source_xy`, `size`, `at`, uses the first card); `end_card` (`lines`, `credits`, `credits_y`, `credits_at`).
- chip: `text`, `at`, `x`, `y`, optional `accent`.
- caption: `text`, `in`, `out` (comp seconds, clamped to the shot).

Mode `cinema` (full-bleed, quiet; used from 海底光缆 v13 on): every cut fills the frame with the same grade (`grade`: `exposure`, `tint`, `white`), a bottom scrim, vignette and light grain; no headline, cards or chips. Cut extras: `fade` (dissolve in, seconds), `speed` (slow a clip by layer stretch), `credit`. Camera adds `tilt_down` / `tilt_up`. Comp extras: `fade_out` (to black at the end), `black_from` [start, length] (picture goes to black while later components stay on top), `vignette`, `grain`, `scrim`. Components: `figure` (`value`, `unit`, `label`, `x`, `y`, `at`, `align`, `size`; thin number on a short rule), `title` (`text`, `sub`, `y`, `at`), `tag` (`text`, `x`, `y`, `point`, `align`, `at`), `satellite` (a light point: `from`, `to`, `at`, `len`, optional `color`, `size`, `glow`), `pulse` (screen glow: `x`, `y`, `size`, `at`), `credits` (`lines`, `y`, `at`). Effect parameters are set by match name because After Effects may run in another language.

Check stills at the entry, middle and settled frames of every comp before rendering, then render with the existing render-queue templates.
