## Why

The user does not want to source material by hand. With the storyboard table and the AE template library in place, the platform can fill each row's 素材 by itself, and the user reviews the result once.

Today the pieces exist but are not joined up:

- a material search plans each shot, finds candidates in the own library and licensed stock sites, scores them by looking at them, and marks rows that should be made in post as `motion`;
- the AE templates render a candidate material from row content.

Nothing picks a candidate or renders a template without the user.

## What Changes

- The 分镜表 SHALL get one action, **AI 补齐素材**, started by the user. For every row with no material yet, it works in this order:
  1. **Search**: the existing shot search (own library, then Pexels, Pixabay, Wikimedia and Openverse), each candidate judged by a vision model.
  2. **Pick**: when the best candidate is eligible (seen by the model, score at or above the existing 0.6 line, no conflicts), the platform accepts it into the project. Rights come from its licence, and attribution is kept.
  3. **AE template**: rows marked as made in post, and searched rows with no eligible candidate, go to a model that decides whether a ready template fits and fills its fields from the row's 信息点, 画面 and 备注. The platform renders it and puts it in the row.
  4. Rows that still have nothing stay as **缺口**, with the reason.
- Each filled row SHALL record where its material came from and why: stock site and score, or template, version and content. The 素材 column shows this.
- Rows the user already picked, and the user's own uploads, SHALL never be replaced.
- Changing a row stays a single-row action on the existing shot slot. Material reaches the master the way it does today: the user puts the picks into the draft and saves once.
- Templates that need an image the row cannot supply (map-route needs a real map) are not used automatically.

## Impact

- API:
  - a new auto-fill job per unit, started from the platform, that reuses material matching (`start`, `accept`, `attach`) and `craft_skills.render`;
  - one model call to choose and fill templates;
  - a job state the page can read.
- MCP: an agent can start the job and read its state. It cannot bind or save the master.
- Web: an **AI 补齐素材** button and progress on the 分镜表; the 素材 column shows the source and reason; the shot slot shows auto picks as such.
- Not in this change: AI video generation (stays manual), code-generated animation, automatic binding into the master, and article image slots.
