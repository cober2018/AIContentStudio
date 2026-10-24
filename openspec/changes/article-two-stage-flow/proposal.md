## Why

The article (text) flow has nine stages: 证据简报 → 角度实验 → 内容大纲 → 初稿候选 → 质量检查 → 精修候选 → 标题与开头 → 最终稿确认 → 最终稿质量检查. The user has to run and accept each one and often cannot tell what comes next.

Platform records show the drop-off. Over 25 text units:

- 初稿 was tried 23 times;
- 质量检查 succeeded 13 of 23 times;
- only 10 reached 最终稿.

The user agreed to apply the video principle to articles. Each piece has one master. AI produces it in as few rounds as possible, the user confirms once, and channel versions only change format.

## What Changes

- New article workflows SHALL have two AI stages and one automatic check:
  1. **写作方案**: from the confirmed facts, return 2–3 complete plans. Each plan has an angle, the key facts it uses, the unknowns it keeps open, and an outline. The user picks one. This replaces 证据简报, 角度实验 and 内容大纲.
  2. **成稿**: return the complete article in one answer. It has the title, two alternative titles, the opening, the body, and the methods now spread over 初稿, 精修 and 标题与开头 (long-form writing, human voice, title and hook). The user confirms once. This replaces 初稿候选, 精修候选, 标题与开头 and 最终稿确认.
  3. **质量检查**: runs by itself on the confirmed article. It only asks the user to act when there is a problem. This replaces the two check stages.
- Fact rules stay as they are: grounded or current fact mode, citations from the confirmed boundary, and no invented numbers or sources.
- Channel versions keep using the existing channel variant adapters: format only, no rewriting.
- Existing runs keep their stages. Saved persona text workflows move only on the user's say-so, as was done for video.

## Impact

- API: the text workflow definition (`starter_personas`), the 写作方案 output schema (one new artifact schema that combines angle, facts used, unknowns and outline), and the 成稿 instruction and method list. Automatic checks after acceptance reuse `stage.checks`.
- Web: the left step navigation shows the shorter flow. Nothing else changes in the review UI.
- Not in this change:
  - image slots inside the article and automatic image fill, which follow the shared material-fill work;
  - the graphic (card) flow, which is already plan-then-compose;
  - spoken audio stages.
