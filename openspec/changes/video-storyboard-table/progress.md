# Progress

## 2026-10-23
- Proposal written. No code changed.
- Applied (user confirmed):
  - API: video definition is `master` (导演稿) → `prepare`; product workflow moves its script and shot rules onto `master` and upgrades an old three-stage product workflow when next used; `video.master.v2` shots take optional `board`; 导演稿 contract is the storyboard table (≤30 rows, or fixed to an accepted shot plan); `_video_plan` builds board, script blocks (none for silent shots) and timeline.
  - Web: `StoryboardTable` (L01 numbers, start–end, nine columns, editable cells) in the 导演稿 review and the saved master's plan view; `VideoShotMaterialPanel` carries a single slot pick, limits the choice to picks when there are several, and adds one button to put all chosen material into the draft.
- Verify: on a DB copy, U80 generated 15 rows with plan ids and filled board columns; the new video definition validates as master → prepare. API suite: 2797 passed, 7 failed — all pre-existing (migration head, model settings, topic route), none in touched code. Web type check and build pass. API restarted while idle.
- User decided persona video recipes also move. Through the platform's own save route, persona 2 and 3 video defaults went from revision 3 to 4 (workflows 63, 64): only 导演稿 (storyboard purpose and instruction, existing method kept) → 专业执行准备. Old versions 18 and 20 are kept; running units keep their own definitions.
