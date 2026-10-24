---
name: article-writing
description: Use when asked to write an AIContentStudio text article or graphic (图文) piece yourself over the creative MCP, e.g. 「写海底光缆的文章」.
---

# Article writing over MCP

The page switch decides who writes a text or graphic piece. Only when it is 「第三方模型」 do you write; on 「平台模型」 the platform's stages write and `save_article_draft` is refused — tell the user to flip the switch on the 内容方案 page.

1. `get_article_brief`: brief, facts (with `fact_pack_item_id` / `snapshot_checksum`), sibling source texts, state and the current version. The current payload is the format to follow.
2. Write one complete version. Numbers only from the facts, attributed; no exaggeration.
   - Text: `text.master.v2` — `title` + `document` (`schema: studio.text.document.v1`, `blocks` of heading / paragraph with `content: [{text, marks: []}]`). No citations.
   - Graphic: `graphic.master.v2` — `title` + `canvases` → `layers`. Image layers name a `material_revision_id` from the library or `generate_video_image`. A text layer's `claims` may tie a span (`start`/`end`) to one fact.
3. `save_article_draft`, then STOP. The user reviews on the page.
4. When the user says continue, `get_article_decision`: notes → write the next version and stop again; approved → final, save nothing more (changes go into a copy the user makes).
