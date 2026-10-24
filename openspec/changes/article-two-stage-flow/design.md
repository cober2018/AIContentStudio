## Context

- `starter_personas._definition("text")` builds nine nodes with `fact_mode` set per blueprint. Each AI node names one built-in method: evidence-brief, angle-lab, outline, longform, humanize, title-hook.
- `stage.creative.method` returns candidates for a typed artifact schema (`research.brief.v1`, `creative.angles.v1`, `content.outline.v1`, `creative.title-hook.v1`). `stage.master.propose` returns title plus Markdown, which becomes `text.master.v2`.
- `stage.checks` runs the text master checks on a saved master. Today the user starts it by hand.

## Decisions

1. **写作方案 is one creative stage** with a new schema, `article.plan.v1`. Each candidate holds:
   - `angle`: one sentence, plus who it is for and why now;
   - `facts`: the facts used, each tied to the confirmed boundary;
   - `unknowns`: what stays open;
   - `outline`: sections with their point.

   Two or three candidates let the user compare angles in one look. A stage loads one method, so the rules of evidence-brief, angle-lab and outline are merged into one built-in method, `studio.text.article-plan@1`. The stage runs on a new creative stage version, `stage.creative.method.v3`, whose schema list adds `article.plan.v1`. This leaves v1 and v2 contracts, and the attempts waiting on them, unchanged.
2. **成稿 is one master stage.** It uses one merged method, `studio.text.article-write@1`, built from longform, humanize and title-hook. The text answer schema gains an optional `alt_titles` (at most 2). The alternative titles are kept on the candidate and are not part of the master. `length` stays long.
3. **Automatic check.** Acceptance already continues to the next ready stage, so the check runs by itself after 成稿 is accepted. New: when every check is `pass`, the continuation accepts the check result itself (adoption key `auto-checks-<attempt>`). Warnings wait for the user's dispositions. Blockers fail the step, which shows as 需要处理.
4. **Persona workflows.** Same as video: a new version saved through the persona default route on the user's say-so. Old versions stay.

## Risks

- One long answer for 成稿 is larger than today's single stages. Current limits handle the long setting; if a model cuts off, the stage fails visibly and can be run again.
- Merging the methods into one stage means one prompt carries more rules. Each method's text is unchanged; only where it is loaded changes.
